import re

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_password_hash, verify_password
from app.core.database import get_db
from app.core.models import Company, Membership, Role, User
from app.core.schemas import Token, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter",
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter",
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number",
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    _validate_password_strength(user_data.password)
    hashed_password = get_password_hash(user_data.password)
    user = User(email=user_data.email, password_hash=hashed_password)
    db.add(user)
    db.flush()
    company_name = user_data.company_name or f"{user_data.email}'s Company"
    company = Company(name=company_name)
    db.add(company)
    db.flush()
    owner_role = db.query(Role).filter(Role.name == "owner").first() or Role(name="owner")
    db.add(owner_role)
    db.flush()
    membership = Membership(user_id=user.id, company_id=company.id, role_id=owner_role.id)
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    access_token = create_access_token(
        data={"sub": str(user.id), "company_id": str(membership.company_id) if membership else None}
    )
    return {"access_token": access_token, "token_type": "bearer"}
