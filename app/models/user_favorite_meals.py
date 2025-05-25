from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.db import Base

class UserFavoriteMeal(Base):
    __tablename__ = "user_favorite_meals"

    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    meal_id = Column(Integer, ForeignKey("meals.id"), primary_key=True)

    user = relationship("User", back_populates="favorite_meals")
    meal = relationship("Meal", back_populates="favorited_by")
