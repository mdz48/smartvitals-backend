from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Verificar que la URL de la base de datos se haya cargado correctamente
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada en las variables de entorno")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base() 


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()