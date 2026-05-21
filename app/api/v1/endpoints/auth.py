# app/api/v1/endpoints/auth.py

import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import authenticate_user, create_access_token, Token
from app.core.log_config import get_logger
from app.schemas.response import LoginRequest

logger = get_logger(__name__)

router = APIRouter()

@router.post("/login", response_model=Token, summary="Login", description="Authentication, returns JWT token")
async def login(body: LoginRequest): 
    if not authenticate_user(body.username, body.password):
        logger.warning("security.login_failed", username=body.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(body.username)
    logger.info("security.login_success", username=body.username)

    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )