from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text, func
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.interfaces import userRole, userGender
from datetime import datetime

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False) 
    gender = Column(Enum(userGender, values_callable=lambda enum_cls: [item.value for item in enum_cls]), nullable=False)
    pregnant = Column(Boolean, default=False, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_picture = Column(String(255), nullable=True, default=None)
    role = Column(
        Enum(userRole, values_callable=lambda enum_cls: [item.value for item in enum_cls]), 
        default=userRole.PATIENT,  # Default a nivel de SQLAlchemy
        server_default=text(f"'{userRole.PATIENT.value}'"),
        nullable=False
    )
    created_at = Column(
        DateTime,
        default=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        server_default=func.now(),
        nullable=False,
    )
    deleted = Column(DateTime, nullable=True, default=None)