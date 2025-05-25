import os
import certifi
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi_mail import ConnectionConfig
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from app.core.scheduler import scheduler, stop_scheduler
from app.middleware.auth_middleware import JWTAuthenticationMiddleware


from app.api.routes.auth import router as auth_router
from app.api.routes.predict import router as predict_router
from app.api.routes.user import router as user_router

os.environ["SSL_CERT_FILE"] = certifi.where()
load_dotenv(dotenv_path=".env", override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI app started, scheduler is running.")
    yield
    stop_scheduler()

app = FastAPI(lifespan=lifespan)


app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "default-secret-key"),
    session_cookie="session",
    max_age=86400
)

app.add_middleware(JWTAuthenticationMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization"]
)


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "False") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "True") == "True"
)


app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(predict_router, prefix="/predict", tags=["Prediction"])
app.include_router(user_router, prefix="/user", tags=["User"])
