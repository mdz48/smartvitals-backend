from fastapi import FastAPI, Depends,status, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.shared.config.database import engine, Base, SessionLocal

from app.routes.userRoutes import userRouter
from app.routes.medicalRecordRoutes import medicalRecordRouter
from app.routes.stadisticsRoutes import stadisticsRouter

app = FastAPI()

app.include_router(userRouter, tags=["users"])
app.include_router(medicalRecordRouter, tags=["medical_records"])
app.include_router(stadisticsRouter, tags=["stadistics"])
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cambiar en producción para permitir solo dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
