from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SignUpRequest, LoginRequest, AuthResponse
from app.models import User
from app.services.auth import firebase_service, jwt_service
from datetime import timedelta
import uuid
import logging

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    """Register a new user with email and password"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create Firebase user (optional, falls back to email)
        firebase_uid = firebase_service.create_user(
            email=request.email,
            password=request.password,
            username=request.username
        )

        # Hash the password
        hashed_password = jwt_service.hash_password(request.password)
        
        # Create database user
        new_user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            firebase_uid=firebase_uid,
            password_hash=hashed_password,  # Store hashed password
            full_name=request.full_name,
            is_active=True,
            is_admin=False,
            storage_quota_gb=100.0,
            storage_used_gb=0.0
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered: {request.email}")

        # Create JWT token
        access_token = jwt_service.create_access_token(
            data={"sub": new_user.id, "email": new_user.email}
        )

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=new_user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login with email and password"""
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            logger.error(f"User not found: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password hash exists
        if not user.password_hash:
            logger.error(f"User has no password set: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password matches
        if not jwt_service.verify_password(request.password, user.password_hash):
            logger.error(f"Invalid password for: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create JWT token
        access_token = jwt_service.create_access_token(
            data={"sub": user.id, "email": user.email}
        )

        logger.info(f"User logged in: {request.email}")

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me")
def get_current_user(db: Session = Depends(get_db)):
    """Get current user info (requires valid JWT token)"""
    return {"message": "User endpoint - Add Authorization header with JWT token"}


@router.post("/logout")
def logout():
    """Logout user"""
    return {"message": "Logged out successfully"}


@router.post("/refresh-token")
def refresh_token(token: str):
    """Refresh access token"""
    try:
        payload = jwt_service.verify_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        new_token = jwt_service.create_access_token(
            data={"sub": payload.get("sub"), "email": payload.get("email")}
        )
        
        return {"access_token": new_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
