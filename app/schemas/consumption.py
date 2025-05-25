from pydantic import BaseModel
from datetime import date
from typing import Optional

class ConsumeMealRequest(BaseModel):
    user_id: int
    meal_id: int


class DailyConsumptionResponse(BaseModel):
    date: date
    total_calories: Optional[float]
    protein: Optional[float]
    carbs: Optional[float]
    fats: Optional[float]

    class Config:
        orm_mode = True

class MessageResponse(BaseModel):
    message: str