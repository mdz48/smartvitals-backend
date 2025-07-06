from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text, ForeignKey, Float, TEXT
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.interfaces import userRole
from datetime import datetime
from app.models.user import User

class MedicalRecord(Base):
    __tablename__ = 'medical_record'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    temperature = Column(Float, nullable=False)
    blood_pressure = Column(Float, nullable=False)
    oxygen_saturation = Column(Float, nullable=False)
    heart_rate = Column(Float, nullable=False)
    diagnosis = Column(TEXT, nullable=True)
    treatment = Column(TEXT, nullable=True)
    notes = Column(TEXT, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP')) 
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])