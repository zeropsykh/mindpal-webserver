from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from ..schemas import TokenData, UserLogin, UserRegister
from ..database import get_db
from ..oauth2 import create_token, get_current_user, verify_token
from ..models import User
from .. import crud

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[User, Depends(get_current_user)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.get("/")
def get():
    return {"message": "Authentication Routes"}

@router.post("/register", response_description="User Registeration", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: db_dependency):
    # Check email is already registered
    if crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email is already registered")

    crud.create_user(db, user)
    return {"message": f"User {user.name} created successfully"}

@router.post("/login", response_description="User Login", status_code=status.HTTP_200_OK, response_model=TokenData)
async def login(user_creds: UserLogin, db: db_dependency):
    user = crud.get_user_by_email(db, user_creds.email)

    if user and crud.verify_password(user_creds.password, user.password):
        access_token = create_token(str(user.id), "access")
        refresh_token = create_token(str(user.id), "refresh")

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user credentials")

@router.get("/user", response_description="User Info", status_code=status.HTTP_200_OK)
async def get_user(user: user_dependency):
    return {"name": user.name, "email": user.email}

@router.get("/refresh", response_description="Refresh token", status_code=status.HTTP_200_OK, response_model=TokenData)
async def refresh_token(db: db_dependency, token: str = Depends(oauth2_scheme)):
    user_id = verify_token(token, "refresh")
    user = crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_token(str(user.id), "access")
    refresh_token = create_token(str(user.id), "refresh")

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

