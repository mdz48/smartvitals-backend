from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.interfaces import userRole
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_picture = Column(String(255), nullable=True, default=None) 
    role = Column(
        Enum(userRole), 
        default=userRole.PATIENT,  # Default a nivel de SQLAlchemy
        server_default=text(f"'{userRole.PATIENT.value}'"),  # Default a nivel de MySQL
        nullable=False
    )
    created_at = Column( DateTime, default=datetime.utcnow,  # Default a nivel de SQLAlchemy
        server_default=text('CURRENT_TIMESTAMP'),  # Default a nivel de MySQL
        nullable=False
    )
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow,  # Para SQLAlchemy
        server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),  # Para MySQL
        nullable=False
    )
    deleted = Column(DateTime, nullable=True, default=None, server_default=text('NULL ON UPDATE CURRENT_TIMESTAMP'))  # Para MySQL 
