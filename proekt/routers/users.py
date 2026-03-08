import random
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from proekt.backend.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from proekt.backend.database import SessionLocal
from proekt.backend.models import User

# EMAIL адміністратора
ADMIN_EMAIL = "prosvet333stellarastra@gmail.com"


from pydantic import validator


class RegisterRequest(BaseModel):
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Неверный формат email")
        if len(v) < 5:
            raise ValueError("Email слишком короткий")
        return v.strip().lower()

    @validator("password")
    def validate_password(cls, v):
        if not (6 <= len(v) <= 15):
            raise ValueError("Пароль має бути від 6 до 15 символів")
        if not re.match(r"^[A-Za-z0-9]+$", v):
            raise ValueError("Пароль може містити лише латинські літери та цифри")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль має містити хоча б одну велику літеру")
        if not re.search(r"[a-z]", v):
            raise ValueError("Пароль має містити хоча б одну малу літеру")
        if not re.search(r"[0-9]", v):
            raise ValueError("Пароль має містити хоча б одну цифру")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.strip().lower()


router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        # поиск по нормализованному email
        user = db.query(User).filter(User.email == data.email).first()
        if user:
            raise HTTPException(
                status_code=400, detail="Этот e-mail уже зарегистрирован"
            )

        # Визначаємо роль - якщо це адмін email, то роль "admin", інакше "user"
        role = "admin" if data.email == ADMIN_EMAIL else "user"

        new_user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            room_id=str(uuid.uuid4()),
            role=role,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token(
            {
                "user_id": new_user.id,
                "room_id": new_user.room_id,
                "email": new_user.email,
                "role": new_user.role,
            }
        )
        return {
            "message": "Пользователь успешно создан",
            "access_token": token,
            "token_type": "bearer",
            "role": new_user.role,
        }
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверные данные для входа")

    token = create_access_token(
        {
            "user_id": user.id,
            "room_id": user.room_id,
            "email": user.email,
            "role": user.role,
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
    }


class ProfileUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None


@users_router.post("/update")
def update_profile(
    data: ProfileUpdate,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    # token может прийти как query param (совместимо с frontend)
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Name handling: if provided and non-empty -> set it.
    # If not provided (or provided empty) and user has no name -> generate unique username userXXXXXXXXXX
    def generate_unique_username():
        for _ in range(100):
            gen = "user" + "".join(str(random.randint(0, 9)) for _ in range(10))
            if not db.query(User).filter(User.name == gen).first():
                return gen
        raise HTTPException(
            status_code=500, detail="Could not generate unique username"
        )

    if data.firstName is not None:
        candidate = data.firstName.strip()
        if candidate == "":
            if not user.name:
                user.name = generate_unique_username()
        else:
            user.name = candidate
    else:
        if not user.name:
            user.name = generate_unique_username()

    # Other fields — only update if provided and non-empty
    if data.lastName is not None and data.lastName.strip() != "":
        user.surname = data.lastName.strip()
    if data.phone is not None and data.phone.strip() != "":
        user.phone = data.phone.strip()
    if data.location is not None and data.location.strip() != "":
        user.location = data.location.strip()
    if data.about is not None and data.about.strip() != "":
        user.about = data.about.strip()

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Profile updated"}


class ProfileResponse(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    role: str


@users_router.get("/me/profile")
def get_profile(token: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """Получить профиль текущего пользователя"""
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return ProfileResponse(
        firstName=user.name,
        lastName=user.surname,
        email=user.email,
        phone=user.phone,
        location=user.location,
        about=user.about,
        role=user.role,
    )
