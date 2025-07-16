from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text, ForeignKey, Float, TEXT
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.interfaces import userRole
from datetime import datetime
from app.models.user import User

class MedicalRecord(Base):
    __tablename__ = 'medical_record'

    id = Column(Integer, primary_key=True, index=True)
    medical_file_id = Column(Integer, ForeignKey('medical_file.id'), nullable=False)
    temperature = Column(Float, nullable=False)
    blood_pressure = Column(Float, nullable=False)
    oxygen_saturation = Column(Float, nullable=False)
    heart_rate = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP')) 
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    medical_file = relationship("MedicalFile", back_populates="records")