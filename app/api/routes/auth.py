from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError, ExpiredSignatureError
import secrets, os, json, traceback
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from fastapi import Form



from app.core.db import get_db
from app.logic.predictor import predict_safe_meals
from app.models.user import User
from app.models.blacklisted_token import BlacklistedToken
from app.schemas.login import LoginResponse
from app.schemas.token import RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserLogin
from app.schemas.auth import TokenBlacklistRequest
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    SECRET_KEY, REFRESH_SECRET_KEY, ALGORITHM
)
from app.core.email import send_verification_email, send_password_reset_email
from app.core.oauth import oauth
from app.core.cache import redis_client
from app.models.user_meals import UserMeal
from app.utils.calorie_calculator import calculate_calories

load_dotenv()

router = APIRouter(tags=["Authentication"])

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/signup")
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists.")
    hashed_pw = hash_password(user_data.password)
    token = secrets.token_urlsafe(16)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pw,
        verification_token=token,
        is_verified=False
    )
    try:
        db.add(new_user)
        db.commit()
        await send_verification_email(user_data.email, token)
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error.")
    return {"message": "User registered. Check email for verification."}

@router.post("/login", response_model=LoginResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified.")
    
    daily_cals, protein, carbs, fats = calculate_calories(user)
    
    return {
    "access_token": create_access_token({"sub": user.email}),
    "refresh_token": create_refresh_token({"sub": user.email}),
    "token_type": "bearer",
    "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "age": user.age if not callable(user.age) else user.age(),
            "weight": user.weight,
            "height": user.height,
            "activity_level": user.activity_level,
            "goal": user.goal,
            "preferred_diet": user.preferred_diet,
            "info_gathered": user.info_gathered,
            "allergies": user.allergies,
            "daily_calories": daily_cals,
            "protein": protein,
            "carbs": carbs,
            "fats": fats
        }
}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    token = data.refresh_token  # 👈 this is from the request body now

    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    if db.query(BlacklistedToken).filter_by(token=token).first():
        raise HTTPException(status_code=401, detail="Blacklisted token")

    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return TokenResponse(
            access_token=create_access_token({"sub": email}),
            refresh_token=token,  # optionally generate a new refresh token
            token_type="bearer"
        )

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token") 


@router.get("/verify-page", response_class=HTMLResponse)
def verify_email_html(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        return HTMLResponse("""
        <h2>Invalid or Expired Verification Link</h2>
        <p>Please try signing up again or request a new verification email.</p>
        """, status_code=400)

    user.is_verified = True
    user.verification_token = None
    db.commit()

    return """
    <h2>Email Verified</h2>
    <p>Your email has been successfully verified. You may now log in.</p>
    """

@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, os.getenv("GOOGLE_REDIRECT_URI"))

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = (await oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo", token=token)).json()
        email = user_info["email"]
        name = user_info.get("name", "Google User")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, name=name, is_verified=True, oauth_provider="google")
            db.add(user)
            db.commit()
            db.refresh(user)
        access_token = create_access_token({"sub": user.email})
        refresh_token = create_refresh_token({"sub": user.email})
        frontend_url = os.getenv("GOOGLE_FRONTEND_URL", "https://whippet-just-endlessly.ngrok-free.app")
        html = f"""
        <html><script>
        window.opener.postMessage({json.dumps({"type": "google-auth", "access_token": access_token, "refresh_token": refresh_token})},"{frontend_url}");
        window.close();
        </script></html>
        """
        return HTMLResponse(content=html)
    except:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="OAuth error")

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    user.reset_token = token
    user.reset_token_expiry = expiry
    db.commit()

    await send_password_reset_email(user.email, token)
    return {"message": "Password reset email sent."}

@router.get("/reset-password-page", response_class=HTMLResponse)
def serve_reset_password_page(token: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reset Your Password</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 30px;
                background: #f4f4f4;
            }}
            .container {{
                max-width: 400px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            input {{
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 4px;
                border: 1px solid #ccc;
            }}
            button {{
                padding: 10px 20px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Reset Your Password</h2>
            <form action="/auth/reset-password" method="post">
                <input type="hidden" name="token" value="{token}" />
                <label>New Password:</label>
                <input type="password" name="new_password" required />
                <button type="submit">Reset Password</button>
            </form>
        </div>
    </body>
    </html>
    """

@router.post("/reset-password")
def reset_password(
    token: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.reset_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    db.commit()

    return {"message": "Password reset successful"}

@router.post("/logout")
def logout(request: Request, token_data: TokenBlacklistRequest, db: Session = Depends(get_db)):
    token = token_data.refresh_token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        db.add(BlacklistedToken(token=token))
        db.commit()
        redis_client.delete(f"user_profile:{payload.get('sub')}")
        return {"message": "Logged out"}
    except:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
