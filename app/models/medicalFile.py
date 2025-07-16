from sqlalchemy import Column, Integer, DateTime, ForeignKey, text, TEXT
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from datetime import datetime

class MedicalFile(Base):
    __tablename__ = 'medical_file'

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    diagnosis = Column(TEXT, nullable=True)
    treatment = Column(TEXT, nullable=True)
    notes = Column(TEXT, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    records = relationship("MedicalRecord", back_populates="medical_file") 