from pydantic import BaseModel, EmailStr
from typing import Optional, List

class LoginUser(BaseModel):
    id: int
    email: EmailStr
    name: str
    age: Optional[int]
    weight: Optional[float]
    height: Optional[float]
    activity_level: Optional[str]
    goal: Optional[str]
    preferred_diet: Optional[str]
    info_gathered: bool
    allergies: Optional[List[str]]
    daily_calories: Optional[float]
    protein: Optional[float]
    carbs: Optional[float]
    fats: Optional[float]


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: LoginUser
