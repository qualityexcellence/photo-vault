"""
Configuration management for the application
"""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://user:password@localhost:5432/photo_vault",
        description="PostgreSQL connection string"
    )
    SQLALCHEMY_ECHO: bool = Field(default=False, description="SQL echo in logs")
    
    # Google Cloud
    GCP_PROJECT_ID: str = Field(description="GCP Project ID")
    GCP_REGION: str = Field(default="us-central1", description="GCP Region")
    GCS_BUCKET_NAME: str = Field(description="Google Cloud Storage bucket name")
    
    # BigQuery
    BIGQUERY_DATASET: str = Field(default="photo_vault", description="BigQuery dataset name")
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default="./firebase-credentials.json",
        description="Path to Firebase service account key"
    )
    
    # API
    API_TITLE: str = Field(default="AI Smart Photo Vault", description="API title")
    API_VERSION: str = Field(default="1.0.0", description="API version")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="CORS allowed origins"
    )
    
    # Authentication
    JWT_SECRET_KEY: str = Field(description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token expiration hours")
    
    # File Upload
    MAX_FILE_SIZE_MB: int = Field(default=100, description="Maximum file size in MB")
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/gif"],
        description="Allowed image MIME types"
    )
    
    # AI Models
    VISION_AI_MODEL: str = Field(default="vision-1.0", description="Vision AI model")
    VERTEX_AI_ENDPOINT: str = Field(default="us-central1-aiplatform.googleapis.com")
    
    # Cache
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    CACHE_TTL_SECONDS: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default pagination size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination size")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Create global settings instance
settings = Settings()
