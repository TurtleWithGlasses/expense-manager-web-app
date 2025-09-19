from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password

def create_user(db: Session, email: str, password: str, full_name: str = None):
    """Create a new user account"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("User with this email already exists")
    
    # Create new user
    hashed_password = hash_password(password)
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user