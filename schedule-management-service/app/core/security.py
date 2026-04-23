from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from typing import Any, Union
from uuid import UUID
import os

# En un entorno real esto vendría de variables de entorno (env)
SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-rbac-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, int, UUID], expires_delta: timedelta = None, custom_claims: dict = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    if custom_claims:
        to_encode.update(custom_claims)
        
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
