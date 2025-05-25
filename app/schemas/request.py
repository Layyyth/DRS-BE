from pydantic import BaseModel, validator
from typing import List, Optional

class PredictRequest(BaseModel):
    user_id: int
    meal_type: Optional[str] = None
    meal_cooking_method: Optional[List[str]] = None
    limit: Optional[int] = None
    excluded_ingredients: Optional[List[str]] = []
    meal_cooking_time: Optional[str] = None
    diet_type: Optional[str] = None

    @validator("meal_type", "diet_type", pre=True)
    def normalize_str(cls, v):
        return v.strip().lower() if v else v

    @validator("meal_cooking_method", pre=True)
    def normalize_methods(cls, v):
        if isinstance(v, str):
            return [v.lower()]
        return [i.lower() for i in v] if v else []