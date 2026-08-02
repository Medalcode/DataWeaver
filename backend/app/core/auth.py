import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

try:
    import jwt
    from jwt.exceptions import PyJWTError as JWTError
except ImportError:  # pragma: no cover
    from jose import JWTError, jwt

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if "$" in hashed_password and not hashed_password.startswith("$2"):
            salt, h = hashed_password.split("$", 1)
            computed = hashlib.sha256((salt + plain_password).encode()).hexdigest()
            return hmac.compare_digest(computed, h)
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

except ImportError:  # pragma: no cover
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        salt, h = hashed_password.split("$", 1) if "$" in hashed_password else ("", hashed_password)
        computed = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return hmac.compare_digest(computed, h)

    def get_password_hash(password: str) -> str:
        salt = uuid.uuid4().hex[:16]
        h = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}${h}"


from .config import settings
from .database import get_db
from .models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _decode_token(token: str) -> dict:
    """Shared token decoding with validation"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("sub") is None:
            raise JWTError("Missing subject claim")
        return payload
    except (JWTError, Exception):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = _decode_token(token)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_company_id(token: str = Depends(oauth2_scheme)) -> str:
    payload = _decode_token(token)
    company_id = payload.get("company_id")
    if company_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No company associated with this user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return company_id
