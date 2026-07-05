from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Image, Analytics
from app.services.auth import jwt_service
import logging
from typing import Optional

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    payload = jwt_service.verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload


@router.get("/dashboard")
def get_dashboard(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get analytics dashboard"""
    try:
        user_id = payload.get("sub")
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get image stats
        total_images = db.query(Image).filter(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).count()
        
        total_storage_gb = db.query(Image).filter(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).count()
        
        return {
            "user_id": user_id,
            "email": user.email,
            "total_images": total_images,
            "storage_used_gb": user.storage_used_gb,
            "storage_quota_gb": user.storage_quota_gb,
            "created_at": user.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images")
def get_image_analytics(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get image analytics"""
    try:
        user_id = payload.get("sub")
        
        images = db.query(Image).filter(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).all()
        
        return {
            "total_images": len(images),
            "images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "size_mb": img.file_size / 1e6,
                    "created_at": img.created_at
                }
                for img in images
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
def get_storage_analytics(
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get storage analytics"""
    try:
        user_id = payload.get("sub")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        images = db.query(Image).filter(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).all()
        
        # Group by file type
        mime_types = {}
        for img in images:
            mime_type = img.mime_type or "unknown"
            if mime_type not in mime_types:
                mime_types[mime_type] = {"count": 0, "size_mb": 0}
            mime_types[mime_type]["count"] += 1
            mime_types[mime_type]["size_mb"] += img.file_size / 1e6
        
        return {
            "user_id": user_id,
            "total_storage_gb": user.storage_used_gb,
            "quota_gb": user.storage_quota_gb,
            "by_type": mime_types
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Storage analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-event")
def log_event(
    event_type: str,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Log an analytics event"""
    try:
        user_id = payload.get("sub")
        
        event = Analytics(
            user_id=user_id,
            event_type=event_type,
            data="{}"
        )
        
        db.add(event)
        db.commit()
        
        return {"message": "Event logged"}
    except Exception as e:
        logger.error(f"Log event error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
