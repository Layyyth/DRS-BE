from sqlalchemy import Column, Integer, String
from app.core.db import Base

class AllergenMapping(Base):
    __tablename__ = "allergen_mapping"

    id = Column(Integer, primary_key=True, index=True)
    food = Column(String, nullable=False)
    allergen = Column(String, nullable=False)
