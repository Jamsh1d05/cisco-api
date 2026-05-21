# app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.settings import settings
from app.core.log_config import get_logger

logger = get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer  = HTTPBearer() 

class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int  # seconds


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(username: str, password: str) -> bool:
    if username != settings.API_USERNAME:
        return False
    if password != settings.API_PASSWORD:
        return False
    return True


def create_access_token(username: str) -> tuple[str, int]:
    expire    = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    payload = {
        "sub": username,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.info("security.token_created", username=username)
    return token, expires_in


def decode_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return TokenData(username=username)

    except JWTError:
        logger.warning("security.invalid_token")
        raise credentials_exception


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer),) -> TokenData:
    return decode_token(credentials.credentials)


def get_ws_user(token: str) -> TokenData:
    return decode_token(token)