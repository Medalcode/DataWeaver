from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Company, Membership, Role
from app.schemas import UserLogin, UserRegister, Token, UserResponse
from app.auth import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and create their company"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password
    )
    db.add(user)
    db.flush()
    
    # Create company
    company_name = user_data.company_name or f"{user_data.email}'s Company"
    company = Company(name=company_name)
    db.add(company)
    db.flush()
    
    # Get owner role (create if not exists)
    owner_role = db.query(Role).filter(Role.name == "owner").first()
    if not owner_role:
        owner_role = Role(name="owner")
        db.add(owner_role)
        db.flush()
    
    # Create membership
    membership = Membership(
        user_id=user.id,
        company_id=company.id,
        role_id=owner_role.id
    )
    db.add(membership)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Get user's primary company (first membership)
    membership = db.query(Membership).filter(Membership.user_id == user.id).first()
    
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "company_id": str(membership.company_id) if membership else None
        }
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
