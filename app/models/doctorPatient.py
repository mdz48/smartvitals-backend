from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, text, ForeignKey, Float, TEXT
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from app.models.interfaces import userRole
from datetime import datetime

class DoctorPatient(Base):
    __tablename__ = 'doctor_patient'

    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])