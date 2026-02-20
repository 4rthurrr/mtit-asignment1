from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


# ── POST /auth/register ──────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=schemas.RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new account.

    - **email**: valid e-mail address (must be unique)
    - **username**: 3–30 chars, alphanumeric + underscores (must be unique)
    - **password**: minimum 8 characters
    """
    # Check uniqueness
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken",
        )

    user = models.User(
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.RegisterResponse(
        message="Account created successfully",
        user=schemas.UserResponse.model_validate(user),
    )


# ── POST /auth/login ─────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtain a JWT access token",
)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate with email + password and receive a JWT bearer token
    valid for **15 minutes**.
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    # Use the same error message for missing user and wrong password to
    # avoid user-enumeration attacks.
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return schemas.TokenResponse(access_token=access_token)


# ── GET /auth/me ─────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the currently authenticated user",
)
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Returns the profile of the user identified by the Bearer token in the
    `Authorization` header.
    """
    return schemas.UserResponse.model_validate(current_user)
