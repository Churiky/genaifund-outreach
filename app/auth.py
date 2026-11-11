from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.max_sends_per_day * 60)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.session_secret, algorithm=ALGORITHM)


def ensure_default_user():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            db.add(
                User(
                    username="admin",
                    password_hash=get_password_hash("admin"),
                )
            )
            db.commit()
            print("Default user created: admin / admin (change SESSION_SECRET & password in .env)")
    finally:
        db.close()
