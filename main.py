from fastapi import FastAPI, Depends,status, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.shared.config.database import engine, Base, SessionLocal

from app.routes.userRoutes import userRouter
from app.routes.medicalRecordRoutes import medicalRecordRouter
from app.routes.stadisticsRoutes import stadisticsRouter
from app.models.recordSensorData import RecordSensorData

app = FastAPI()

app.include_router(userRouter, prefix="/api", tags=["users"])
app.include_router(medicalRecordRouter, prefix="/api", tags=["medical_records"])
app.include_router(stadisticsRouter, prefix="/api", tags=["stadistics"])
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cambiar en producción para permitir solo dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
