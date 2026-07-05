from sqlalchemy import Column, String, DateTime, Boolean, Float, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    firebase_uid = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)  # ✅ ADD THIS
    full_name = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    storage_quota_gb = Column(Float, default=100.0)
    storage_used_gb = Column(Float, default=0.0)


class Image(Base):
    __tablename__ = "images"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    gcs_uri = Column(String, nullable=False, unique=True)
    thumbnail_uri = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)


class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id = Column(String, primary_key=True, index=True)
    image_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    labels = Column(Text, nullable=True)  # JSON string
    faces_detected = Column(Integer, default=0)
    text_detected = Column(Text, nullable=True)
    colors = Column(Text, nullable=True)  # JSON string
    objects = Column(Text, nullable=True)  # JSON string
    caption = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class Album(Base):
    __tablename__ = "albums"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cover_image_id = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)


class AlbumImage(Base):
    __tablename__ = "album_images"

    id = Column(String, primary_key=True, index=True)
    album_id = Column(String, nullable=False, index=True)
    image_id = Column(String, nullable=False, index=True)
    order = Column(Integer, default=0)
    added_at = Column(DateTime, server_default=func.now())


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
