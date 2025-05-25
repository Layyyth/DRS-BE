from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from typing_extensions import Annotated 
from datetime import date

# ------------------------ User Signup ------------------------
class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="Full name of the user")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=64, description="Password must be at least 8 characters")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one number.")
        if not any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for c in value):
            raise ValueError("Password must contain at least one special character.")
        return value

# ------------------------ User Login ------------------------
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=64, description="Password must be at least 8 characters")

# ------------------------ User Response ------------------------
class UserResponse(BaseModel):
    email: EmailStr
    name: str
    id: int
    birthdate: Optional[date] = None 
    gender: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    preferred_diet: Optional[str] = None
    allergies: Optional[list[str]] = None
    info_gathered: bool
    daily_calories: Optional[float] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None    
    fats: Optional[float] = None
    info_gathered_init: Optional[bool] = False 
    

    class Config:
        from_attributes = True 

# ------------------------ User Health Form ------------------------
class UserProfile(BaseModel):
    name: Optional[str] = None 
    birthdate: Optional[date] = None 
    gender: Optional[str] = None
    weight: Optional[Annotated[float, Field(ge=30, le=300)]] = None  
    height: Optional[Annotated[float, Field(ge=100, le=250)]] = None  
    activity_level: Optional[str] = None
    goal: Optional[str] = None
    preferred_diet: Optional[str] = None
    allergies: Optional[list[str]] = None
    info_gathered: bool = False  

    class Config:
        from_attributes = True


class FavoriteMeal(BaseModel):
    id: int
    name: str
    instruction: str
    ingredients: str
    calories: Optional[float]
    fats: Optional[float]
    carbs: Optional[float]
    protein: Optional[float]
    diet_type: Optional[List[str]]
    difficulty: Optional[str]
    meal_cooking_time: Optional[str]
    meal_cooking_method: Optional[List[str]] = None
    origin: Optional[str]
    meal_type: Optional[str]


class ToggleFavoriteResponse(BaseModel):
    message: str

class FavoriteToggleRequest(BaseModel):
    user_id: int
    meal_id: int



#------------------ reset pass ------

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    