from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.userSchema import userSchema, userCreateSchema, userResponseSchema, userLoginSchema
from app.shared.config.database import SessionLocal
from sqlalchemy.orm import Session
from app.shared.config.database import get_db

userRouter = APIRouter()

@userRouter.post("/users", response_model=userResponseSchema, status_code=201, tags=["users"])
async def create_user(user: userCreateSchema, db: Session = Depends(get_db)):
    db_user = User(
        name=user.name,
        lastname=user.lastname,
        email=user.email,
        password=user.password,  # Asegúrate de hashear la contraseña antes de guardarla
        role=user.role,
        profile_picture=user.profile_picture
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@userRouter.get("/users", response_model=list[userResponseSchema], tags=["users"], status_code=200)
async def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
 