from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Admin(Base):
    __tablename__ = "admin"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)