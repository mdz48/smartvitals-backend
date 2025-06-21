from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta

from app.models.user import User
from app.schemas.userSchema import userSchema, userCreateSchema, userResponseSchema, userLoginSchema, loginResponseSchema
from app.shared.config.database import SessionLocal
from sqlalchemy.orm import Session
from app.shared.config.database import get_db
from app.shared.config.middleware.security import get_password_hash, get_current_user, verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

userRouter = APIRouter()

@userRouter.post("/users", response_model=userResponseSchema, status_code=201, tags=["users"])
async def create_user(user: userCreateSchema, db: Session = Depends(get_db)):
    # Verifiamos que el usuario no exista
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya existe con este correo electrónico.")

    # Creamos el nuevo usuario con la constraseña hasheada
    hashed_password = get_password_hash(user.password)      
    new_user = User(
        name=user.name,
        lastname=user.lastname,
        email=user.email,
        password=hashed_password,  # Password hasheada
        role=user.role,
        profile_picture=user.profile_picture
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@userRouter.get("/users", response_model=list[userResponseSchema], tags=["users"], status_code=200)
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).where(User.deleted.is_(None)).all()  # Filtramos usuarios no eliminados
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron usuarios") 
    return users
 
@userRouter.get("/users/{user_id}", response_model=userResponseSchema, tags=["users"], status_code=200)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user

@userRouter.put("/users/{user_id}", response_model=userResponseSchema, tags=["users"], status_code=200)
async def update_user(user_id: int, user: userCreateSchema, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.id == user_id).first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Actualizamos los campos del usuario
    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(existing_user, key, value)

    # Si se proporciona una nueva contraseña, la hasheamos
    if user.password:
        existing_user.password = get_password_hash(user.password)

    db.commit()
    db.refresh(existing_user)
    return existing_user

@userRouter.delete("/users/{user_id}", status_code=204, tags=["users"])
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    
    # Eliminacion lógica: ponemos fecha en el campo deleted
    user.deleted = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"detail": "Usuario eliminado exitosamente"}

@userRouter.post("/users/login", response_model=loginResponseSchema, tags=["users"], status_code=200)
async def login_user(user: userLoginSchema, db: Session = Depends(get_db)):
    # Buscar usuario por email
    existing_user = db.query(User).filter(User.email == user.email).first()
    
    # Verificar credenciales
    if not existing_user or not verify_password(user.password, existing_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Email o contraseña incorrectos"
        )
    
    # Crear token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": existing_user.email}, 
        expires_delta=access_token_expires
    )
    
    # Retornar token y datos del usuario
    return loginResponseSchema(
        access_token=access_token,
        token_type="bearer",
        user=existing_user  
    )

@userRouter.get("/users/me", response_model=userResponseSchema, tags=["users"], status_code=200)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


