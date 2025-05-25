from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

class MealItem(BaseModel):
    id: int 
    name: str
    instruction: str
    calories: Optional[float]
    protein: Optional[float]
    carbs: Optional[float]
    fats: Optional[float]
    origin: Optional[str]
    meal_cooking_time: Optional[str]
    difficulty: Optional[str]
    diet_type: Optional[List[str]]
    meal_type: Optional[str]
    meal_cooking_method: Optional[List[str]] = None
    ingredients : str

class Macros(BaseModel):
    protein: float
    carbs: float
    fats: float

class PredictionResponse(BaseModel):
    daily_calories: float
    macros: Macros
    recommended_meals: List[MealItem]

class MealDetailResponse(BaseModel):
    id: int
    name: str
    ingredients : str
    instruction: str
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

class MealSearchResult(BaseModel):
    id: UUID
    name: str
    instruction: str
    calories: Optional[float]
    protein: Optional[float]
    carbs: Optional[float]
    fats: Optional[float]
    diet_type: Optional[List[str]]
    difficulty: Optional[str]
    meal_cooking_time: Optional[str]     
    meal_cooking_method: Optional[List[str]] = None   
    origin: Optional[str]
    meal_type: Optional[str]        
