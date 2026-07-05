"""
Admin API routes
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, Image, Analytics, AuditLog
from app.schemas import UserStatsResponse, SystemStatsResponse
from app.routes.auth import get_current_user
from app.services.bigquery import bigquery_service

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verify user is admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/users", response_model=list[UserStatsResponse])
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Get all users with statistics
    
    Args:
        page: Page number
        page_size: Items per page
        admin_user: Current admin user
        db: Database session
        
    Returns:
        List of users with statistics
    """
    try:
        users = db.query(User).order_by(desc(User.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        users_stats = []
        for user in users:
            images_count = db.query(func.count(Image.id)).filter(
                Image.user_id == user.id
            ).scalar()
            
            users_stats.append({
                "user": user,
                "total_images": images_count or 0,
                "total_albums": 0,
                "storage_used_gb": user.storage_used_gb,
                "last_activity": None,
                "created_at": user.created_at,
            })
        
        # Log audit
        audit_log = AuditLog(
            admin_id=admin_user.id,
            action="list_users",
            resource_type="users",
            resource_id="system",
            details={"page": page, "page_size": page_size},
        )
        db.add(audit_log)
        db.commit()
        
        return users_stats
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users",
        )


@router.get("/users/{user_id}", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: str,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Get specific user statistics
    
    Args:
        user_id: User ID
        admin_user: Current admin user
        db: Database session
        
    Returns:
        User statistics
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        images_count = db.query(func.count(Image.id)).filter(
            Image.user_id == user_id
        ).scalar()
        
        # Log audit
        audit_log = AuditLog(
            admin_id=admin_user.id,
            action="view_user_stats",
            resource_type="user",
            resource_id=user_id,
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "user": user,
            "total_images": images_count or 0,
            "total_albums": 0,
            "storage_used_gb": user.storage_used_gb,
            "last_activity": None,
            "created_at": user.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user stats",
        )


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: str,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Disable user account
    
    Args:
        user_id: User ID to disable
        admin_user: Current admin user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        user.is_active = False
        
        # Log audit
        audit_log = AuditLog(
            admin_id=admin_user.id,
            action="disable_user",
            resource_type="user",
            resource_id=user_id,
            details={"reason": "admin_action"},
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"User disabled: {user_id}")
        
        return {"message": f"User {user_id} disabled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Disable user error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable user",
        )


@router.get("/statistics", response_model=SystemStatsResponse)
async def get_system_statistics(
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Get system-wide statistics
    
    Args:
        admin_user: Current admin user
        db: Database session
        
    Returns:
        System statistics
    """
    try:
        total_users = db.query(func.count(User.id)).scalar()
        total_images = db.query(func.count(Image.id)).scalar()
        total_storage_gb = db.query(func.sum(User.storage_used_gb)).scalar() or 0
        
        # Get daily uploads for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_uploads = db.query(
            func.date(Image.created_at).label("date"),
            func.count(Image.id).label("count"),
        ).filter(
            Image.created_at >= thirty_days_ago
        ).group_by(
            func.date(Image.created_at)
        ).all()
        
        daily_uploads_dict = {str(d[0]): d[1] for d in daily_uploads}
        
        # Get most common tags
        all_images = db.query(Image).all()
        tag_counts = {}
        for image in all_images:
            for tag in image.tags or []:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        most_common_tags = sorted(
            tag_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]
        most_common_tags = [tag for tag, _ in most_common_tags]
        
        # Log audit
        audit_log = AuditLog(
            admin_id=admin_user.id,
            action="view_system_stats",
            resource_type="system",
            resource_id="system",
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "total_users": total_users or 0,
            "total_images": total_images or 0,
            "total_storage_gb": float(total_storage_gb),
            "total_searches": 0,
            "avg_storage_per_user_gb": float(total_storage_gb) / (total_users or 1),
            "daily_uploads": daily_uploads_dict,
            "most_common_tags": most_common_tags,
            "duplicate_detection_rate": 0.05,
        }
    except Exception as e:
        logger.error(f"Get system stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system statistics",
        )


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    admin_user: User = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """
    Get audit logs
    
    Args:
        page: Page number
        page_size: Items per page
        action: Filter by action type
        admin_user: Current admin user
        db: Database session
        
    Returns:
        List of audit logs
    """
    try:
        query = db.query(AuditLog)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "items": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except Exception as e:
        logger.error(f"Get audit logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit logs",
        )
