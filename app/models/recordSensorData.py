from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.shared.config.database import Base
from datetime import datetime

class RecordSensorData(Base):
    __tablename__ = 'record_sensor_data'
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    doctor_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    temperature = Column(Float, nullable=True)
    blood_pressure = Column(Float, nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    heart_rate = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    medical_record_id = Column(Integer, ForeignKey('medical_record.id'), nullable=True)

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    medical_record = relationship("MedicalRecord", foreign_keys=[medical_record_id]) 