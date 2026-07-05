from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Image, ImageMetadata
from app.services.gcs import gcs_service
from app.services.vision_ai import vision_ai_service
from app.services.auth import jwt_service
from app.schemas import ImageResponse, ImageListResponse
import uuid
import logging
from typing import Optional

router = APIRouter(prefix="/api/v1/images", tags=["images"])
logger = logging.getLogger(__name__)


def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """Verify JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    # Extract token from "Bearer <token>"
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


@router.post("/upload")
def upload_image(
    file: UploadFile = File(...),
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload an image"""
    try:
        user_id = payload.get("sub")
        
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Read file
        file_content = file.file.read()
        file_size = len(file_content)
        
        # Check storage quota
        if user.storage_used_gb + (file_size / 1e9) > user.storage_quota_gb:
            raise HTTPException(status_code=400, detail="Storage quota exceeded")

        # Create image record
        image_id = str(uuid.uuid4())
        gcs_path = f"users/{user_id}/images/{image_id}/{file.filename}"
        
        image = Image(
            id=image_id,
            user_id=user_id,
            filename=file.filename,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            gcs_uri=f"gs://aivaultphotosgcp-images/{gcs_path}"
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        # Update user storage
        user.storage_used_gb += file_size / 1e9
        db.commit()
        
        logger.info(f"Image uploaded: {image_id} by user {user_id}")

        return {
            "id": image.id,
            "filename": image.filename,
            "gcs_uri": image.gcs_uri,
            "created_at": image.created_at,
            "message": "Image uploaded successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=ImageListResponse)
def list_images(
    payload: dict = Depends(verify_token),
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List user's images"""
    try:
        user_id = payload.get("sub")
        
        images = db.query(Image).filter(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).offset(offset).limit(limit).all()
        
        total = db.query(Image).filter(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).count()
        
        return ImageListResponse(total=total, images=images)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: str,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get image details"""
    try:
        user_id = payload.get("sub")
        
        image = db.query(Image).filter(
            Image.id == image_id,
            Image.user_id == user_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return image
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{image_id}")
def delete_image(
    image_id: str,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete an image"""
    try:
        user_id = payload.get("sub")
        
        image = db.query(Image).filter(
            Image.id == image_id,
            Image.user_id == user_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Soft delete
        image.is_deleted = True
        db.commit()
        
        logger.info(f"Image deleted: {image_id}")
        
        return {"message": "Image deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{image_id}/analyze")
def analyze_image(
    image_id: str,
    payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Analyze image with Vision AI"""
    try:
        user_id = payload.get("sub")
        
        image = db.query(Image).filter(
            Image.id == image_id,
            Image.user_id == user_id
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Analyze with Vision AI
        analysis = vision_ai_service.analyze_image(image.gcs_uri)
        
        # Store metadata
        metadata = ImageMetadata(
            id=str(uuid.uuid4()),
            image_id=image_id,
            user_id=user_id,
            labels=str(analysis.get("labels", [])),
            faces_detected=analysis.get("faces", 0),
            text_detected=analysis.get("text", ""),
            colors=str(analysis.get("colors", [])),
            objects=str(analysis.get("objects", [])),
            caption=analysis.get("caption", "")
        )
        
        db.add(metadata)
        db.commit()
        
        logger.info(f"Image analyzed: {image_id}")
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
