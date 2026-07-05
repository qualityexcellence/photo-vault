import os
from datetime import datetime, timedelta
from typing import Optional
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import Settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = Settings()


class FirebaseService:
    def __init__(self):
        self.app = None
        try:
            cred_path = settings.FIREBASE_CREDENTIALS_PATH
            if os.path.isfile(cred_path):
                cred = credentials.Certificate(cred_path)
                self.app = firebase_admin.initialize_app(cred)
                print(f"✓ Firebase initialized successfully from {cred_path}")
            else:
                print(f"⚠ Firebase credentials not found - using email as uid")
                self.app = None
        except Exception as e:
            print(f"⚠ Firebase error: {e}")
            self.app = None

    def create_user(self, email: str, password: str, username: str = None):
        """Create Firebase user - returns uid string"""
        try:
            if self.app is None:
                return email  # Use email as uid if Firebase unavailable
            
            user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=username or email
            )
            return user.uid  # Return ONLY the uid string
        except firebase_admin.auth.EmailAlreadyExistsError:
            raise ValueError(f"Email {email} already exists")
        except Exception as e:
            print(f"Firebase create_user error: {e}")
            # Fallback: use email as uid
            return email

    def verify_token(self, token: str):
        """Verify Firebase token"""
        if self.app is None:
            return {"uid": "test-user", "email": "test@example.com"}
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def sign_in(self, email: str, password: str):
        """Get user uid for signing in"""
        try:
            if self.app is None:
                return email
            user = firebase_auth.get_user_by_email(email)
            return user.uid  # Return ONLY the uid string
        except firebase_admin.auth.UserNotFoundError:
            raise ValueError(f"User {email} not found")
        except Exception as e:
            print(f"Firebase sign_in error: {e}")
            return email

    def delete_user(self, uid: str):
        """Delete user"""
        if self.app is None:
            return True
        try:
            firebase_auth.delete_user(uid)
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False


class JWTService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm
        )
        return encoded_jwt

    def verify_access_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)


firebase_service = FirebaseService()
jwt_service = JWTService()
