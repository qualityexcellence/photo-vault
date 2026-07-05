from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Auth Schemas
class SignUpRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    firebase_uid: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Image Schemas
class ImageUploadRequest(BaseModel):
    filename: str
    file_size: int
    mime_type: str


class ImageResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    gcs_uri: str
    created_at: datetime

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    total: int
    images: list[ImageResponse]


# Analytics Schemas
class UserStats(BaseModel):
    total_images: int
    total_storage_gb: float
    created_at: datetime


class SystemStats(BaseModel):
    total_users: int
    total_images: int
    total_storage_gb: float


class UserStatsResponse(BaseModel):
    user_id: str
    stats: UserStats


class SystemStatsResponse(BaseModel):
    stats: SystemStats


# Search Schemas
class SearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    limit: int = 10
    offset: int = 0


class SearchResponse(BaseModel):
    total: int
    results: list[ImageResponse]
