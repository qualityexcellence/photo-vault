"""
Search API routes
"""

import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import User, Image
from app.schemas import SearchRequest, SearchResponse, ImageResponse
from app.routes.auth import get_current_user
from app.services.bigquery import bigquery_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_images(
    request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search images using different methods
    
    Args:
        request: Search request with query and search type
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    start_time = time.time()
    
    try:
        results = []
        
        if request.search_type == "text":
            # Search by caption, tags, or OCR text
            query = db.query(Image).filter(
                and_(
                    Image.user_id == current_user.id,
                    or_(
                        Image.caption.ilike(f"%{request.query}%"),
                        Image.tags.contains([request.query]),
                        Image.ocr_text.ilike(f"%{request.query}%"),
                    ),
                ),
            )
            results = query.limit(request.limit).offset(request.offset).all()
            
        elif request.search_type == "tag":
            # Search by specific tag
            query = db.query(Image).filter(
                and_(
                    Image.user_id == current_user.id,
                    Image.tags.contains([request.query]),
                ),
            )
            results = query.limit(request.limit).offset(request.offset).all()
            
        elif request.search_type == "object":
            # Search by detected objects
            query = db.query(Image).filter(
                Image.user_id == current_user.id,
            )
            # Filter results in Python (could be optimized with JSON operators)
            all_images = query.all()
            results = [
                img for img in all_images
                if request.query.lower() in str(img.detected_objects).lower()
            ][:request.limit]
            
        elif request.search_type == "color":
            # Search by dominant color
            query = db.query(Image).filter(
                Image.user_id == current_user.id,
            )
            all_images = query.all()
            results = [
                img for img in all_images
                if request.query.lower() in [c.lower() for c in img.dominant_colors]
            ][:request.limit]
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid search type: {request.search_type}",
            )
        
        # Get total count
        count_query = db.query(Image).filter(Image.user_id == current_user.id)
        if request.search_type == "text":
            count_query = count_query.filter(
                or_(
                    Image.caption.ilike(f"%{request.query}%"),
                    Image.tags.contains([request.query]),
                    Image.ocr_text.ilike(f"%{request.query}%"),
                )
            )
        elif request.search_type == "tag":
            count_query = count_query.filter(Image.tags.contains([request.query]))
        
        total = count_query.count()
        
        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Track search event
        bigquery_service.insert_event(
            current_user.id,
            "search_performed",
            {
                "query": request.query,
                "search_type": request.search_type,
                "results_count": len(results),
                "execution_time_ms": execution_time_ms,
            },
        )
        
        logger.info(f"Search performed: {request.search_type} - {request.query} - {len(results)} results")
        
        return SearchResponse(
            results=[ImageResponse.model_validate(img) for img in results],
            total=total,
            query=request.query,
            search_type=request.search_type,
            execution_time_ms=execution_time_ms,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed",
        )


@router.get("/suggestions")
async def search_suggestions(
    q: Optional[str] = Query(None, min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get search suggestions based on user's images
    
    Args:
        q: Search query prefix
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of suggestions
    """
    try:
        # Get all tags from user's images
        images = db.query(Image).filter(Image.user_id == current_user.id).all()
        
        all_tags = set()
        for image in images:
            all_tags.update(image.tags or [])
        
        suggestions = []
        if q:
            # Filter tags that start with query
            suggestions = [tag for tag in all_tags if tag.lower().startswith(q.lower())]
        else:
            # Return most common tags
            tag_counts = {}
            for image in images:
                for tag in image.tags or []:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            suggestions = sorted(
                tag_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
            suggestions = [tag for tag, _ in suggestions]
        
        return {"suggestions": suggestions[:10]}
    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions",
        )


@router.get("/duplicates")
async def find_duplicates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Find potential duplicate images
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of potential duplicates
    """
    try:
        # Get user's images
        images = db.query(Image).filter(Image.user_id == current_user.id).all()
        
        duplicates = []
        processed = set()
        
        for i, img1 in enumerate(images):
            if img1.id in processed:
                continue
            
            for img2 in images[i+1:]:
                if img2.id in processed:
                    continue
                
                # Simple duplicate detection based on tags and objects
                # In production, use perceptual hashing or ML model
                if (
                    set(img1.tags or []) & set(img2.tags or []) and
                    img1.file_size_bytes > 0 and
                    img2.file_size_bytes > 0 and
                    abs(img1.file_size_bytes - img2.file_size_bytes) < img1.file_size_bytes * 0.1
                ):
                    duplicates.append({
                        "image1": ImageResponse.model_validate(img1),
                        "image2": ImageResponse.model_validate(img2),
                        "confidence": 0.8,
                    })
                    processed.add(img2.id)
        
        logger.info(f"Found {len(duplicates)} potential duplicates")
        
        return {"duplicates": duplicates}
    except Exception as e:
        logger.error(f"Duplicates search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find duplicates",
        )
