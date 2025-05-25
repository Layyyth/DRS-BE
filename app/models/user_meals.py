from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.db import Base
import datetime

class UserMeal(Base):
    __tablename__ = "user_meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    meal_id = Column(Integer, ForeignKey("meals.id"))
    date_shown = Column(Date, default=datetime.date.today)

    
    name = Column(String(255), nullable=False)
    total_calories = Column(Float)
    fats = Column(Float)
    carbs = Column(Float)
    protein = Column(Float)
    instruction = Column(Text, nullable=False)
    diet_type = Column(ARRAY(String))
    meal_difficulty = Column(String(50))
    meal_cooking_time = Column(String(50))
    meal_cooking_method = Column(ARRAY(String), nullable=False, default=[])
    country_origin = Column(String(100))
    ingredients = Column(ARRAY(String), default=[], nullable=False)
    meal_type = Column(String(50))


    user = relationship("User", back_populates="meals_shown")
    meal = relationship("Meal", back_populates="shown_to_users")
