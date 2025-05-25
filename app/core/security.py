import os
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "fallback-refresh-secret")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 30 
REFRESH_TOKEN_EXPIRE_DAYS = 1  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    payload = decode_token(token, SECRET_KEY)
    email: str = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token: No email found")
    return {"email": email}

def verify_refresh_token(refresh_token: str) -> str:
    payload = decode_token(refresh_token, REFRESH_SECRET_KEY)
    email: str = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return email
