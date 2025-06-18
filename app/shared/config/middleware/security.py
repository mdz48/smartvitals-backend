import os
from dotenv import load_dotenv
load_dotenv()
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.models.user import User
from app.shared.config.database import get_db

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY no se encuentra en el archivo .env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # Tiempo de expiración del token en minutos, 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password, hashed_password):
    """Verifica si la contraseña en texto plano coincide con la contraseña hasheada."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Genera un hash para la contraseña proporcionada."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta=None):
    """Crea un token de acceso JWT con los datos proporcionados y una fecha de expiración opcional."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str):
    """Obtiene el usuario actual a partir del token JWT proporcionado."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no válidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db = next(get_db())
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


