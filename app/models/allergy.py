from sqlalchemy import Column, Integer, String
from app.core.db import Base

class Allergy(Base):
    __tablename__ = "allergy"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)