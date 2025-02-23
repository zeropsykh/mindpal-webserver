from datetime import datetime, timezone, timedelta
from uuid import UUID
import os

from typing import Literal
from dotenv import load_dotenv
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette import status

from .crud import get_user_by_id
from .database import get_db

load_dotenv()

ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def create_token(user_id: str, token_type: Literal["access", "refresh"]):
    payload = {
        "sub": user_id,
        "user_role": "user",
        "token_type": token_type,
        "iat": datetime.now(timezone.utc),
    }

    if token_type == "access":
        key = ACCESS_SECRET_KEY
        payload.update({"exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    elif token_type == "refresh":
        key = REFRESH_SECRET_KEY
        payload.update({"exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)})

    encoded_token = jwt.encode(
        payload,
        key=key,
        algorithm=ALGORITHM 
    )

    return encoded_token

def verify_token(token: str, token_type: Literal["access", "refresh"]) -> UUID:
    try:
        if token_type == "access":
            payload = jwt.decode(token, key=ACCESS_SECRET_KEY, algorithms=[ALGORITHM])
        elif token_type == "refresh":
            payload = jwt.decode(token, key=REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

        if int(datetime.now(timezone.utc).timestamp()) > payload.get("exp"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        user_id = payload.get("sub")
        if not user_id or payload.get("token_type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail=f"Invalid {token_type} token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Invalid {token_type} token",
            headers={"WWW-Authenticate": "Bearer"}
        )

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    current_user_id = verify_token(token, "access")
    current_user = get_user_by_id(db, current_user_id) 

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return current_user
