from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint
from app.core.db import Base
from datetime import date
from sqlalchemy.orm import relationship

class UserDailyConsumption(Base):
    __tablename__ = "user_daily_consumption"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    date = Column(Date, default=date.today, nullable=False)

    calories = Column(Float, default=0.0)
    protein = Column(Float, default=0.0)
    carbs = Column(Float, default=0.0)
    fats = Column(Float, default=0.0)

    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='unique_user_date'),
    )

    user = relationship("User", back_populates="daily_consumptions")