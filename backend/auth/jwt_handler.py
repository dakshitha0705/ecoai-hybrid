# backend/auth/jwt_handler.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, USERS_DB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def authenticate_user(username: str, password: str):
    """Returns user dict if credentials are valid, else None."""
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict) -> str:
    """Creates a JWT token with an expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decodes and validates a JWT. Raises JWTError if invalid."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
