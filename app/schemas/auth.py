from pydantic import BaseModel

class TokenBlacklistRequest(BaseModel):
    refresh_token: str  
