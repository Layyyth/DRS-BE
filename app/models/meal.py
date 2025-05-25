from sqlalchemy.orm import validates
from sqlalchemy import Column, Integer, Float, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.db import Base

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
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
    ingredients = Column(ARRAY(String), nullable=False, default=[])
    meal_type = Column(String(50))
        

    shown_to_users = relationship("UserMeal", back_populates="meal", cascade="all, delete-orphan")
    favorited_by = relationship("UserFavoriteMeal", back_populates="meal", cascade="all, delete-orphan")

    @validates("meal_time")
    def normalize_meal_time(self, key, value):
        return value.strip().lower() if value else None
    

    