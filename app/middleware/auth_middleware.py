import os
import logging
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from datetime import datetime, timezone

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
ALGORITHM = "HS256"

EXCLUDED_PATHS = [
    "/auth/login", "/auth/signup", "/auth/google/login", "/auth/google/callback",
    "/docs", "/redoc", "/openapi.json", "/favicon.ico", "/"
]


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(ep) for ep in EXCLUDED_PATHS):
            return await call_next(request)

        token = None

    
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "").strip()
        else:
            token = request.cookies.get("access_token")

        if not token:
            return JSONResponse({"detail": "Missing or invalid token"}, status_code=401)

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            exp = payload.get("exp")

            
            if exp and datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
                logger.warning(f"Expired token used: {token}")
                return JSONResponse({"detail": "Token has expired"}, status_code=401)

            request.state.user = payload
            return await call_next(request)

        except ExpiredSignatureError:
            logger.warning(f"Expired token detected: {token}")
            return JSONResponse({"detail": "Token has expired. Please log in again."}, status_code=401)
        
        except JWTError:
            logger.error(f"Invalid token detected: {token}")
            return JSONResponse({"detail": "Invalid token"}, status_code=401)
