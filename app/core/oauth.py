import os
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv

load_dotenv(override=True)

oauth = OAuth()

oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "userinfo_endpoint": "https://www.googleapis.com/oauth2/v3/userinfo"
    },
)
