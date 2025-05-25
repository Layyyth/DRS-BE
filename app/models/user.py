from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    birthdate = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    activity_level = Column(String(20), nullable=False, default="moderate")
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    goal = Column(String(50), nullable=False, default="maintain weight")
    preferred_diet = Column(String(50), nullable=True)

    allergies = Column(ARRAY(String), default=[])

    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    oauth_provider = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    info_gathered = Column(Boolean, default=False)
    info_gathered_init = Column(Boolean,default=False);
    meals_initialized = Column(Boolean, default=False)

    meals_shown = relationship("UserMeal", back_populates="user", cascade="all, delete-orphan")
    
    favorite_meals = relationship("UserFavoriteMeal", back_populates="user", cascade="all, delete-orphan")

    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    
    def age(self):
        if self.birthdate:
            today = datetime.utcnow().date()
            return today.year - self.birthdate.year - (
                (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
            )
        return None

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


    daily_consumptions = relationship("UserDailyConsumption", back_populates="user", cascade="all, delete-orphan")
    