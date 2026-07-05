import os
from typing import List, Dict, Optional
from google.cloud import vision
from google.oauth2 import service_account
from app.config import Settings

settings = Settings()


class VisionAIService:
    def __init__(self, project_id: str = None):
        self.client = None
        self.project_id = project_id or settings.GCP_PROJECT_ID
        
        try:
            # Try to load credentials from file
            cred_path = settings.FIREBASE_CREDENTIALS_PATH
            if os.path.isfile(cred_path):
                credentials = service_account.Credentials.from_service_account_file(
                    cred_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                print("✓ Vision AI initialized successfully")
            else:
                self.client = vision.ImageAnnotatorClient()
                print("✓ Vision AI initialized with default credentials")
        except Exception as e:
            print(f"⚠ Vision AI initialization error: {e}")
            print("  Image analysis will be disabled. Add GCP credentials to enable it.")
            self.client = None

    def _get_image_source(self, image_path: str):
        """Get image source for Vision API"""
        if image_path.startswith("gs://"):
            return vision.Image(source=vision.ImageSource(gcs_image_uri=image_path))
        else:
            with open(image_path, "rb") as image_file:
                return vision.Image(content=image_file.read())

    def get_labels(self, image_path: str, max_results: int = 10) -> List[str]:
        """Get labels from an image using Vision API"""
        if self.client is None:
            print("Vision AI not initialized - returning empty labels")
            return []
        
        try:
            image = self._get_image_source(image_path)
            response = self.client.label_detection(image=image)
            labels = response.label_annotations
            return [label.description for label in labels[:max_results]]
        except Exception as e:
            print(f"Error detecting labels: {e}")
            return []

    def detect_faces(self, image_path: str) -> int:
        """Detect number of faces in an image"""
        if self.client is None:
            print("Vision AI not initialized - returning 0 faces")
            return 0
        
        try:
            image = self._get_image_source(image_path)
            response = self.client.face_detection(image=image)
            return len(response.face_annotations)
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return 0

    def extract_text(self, image_path: str) -> str:
        """Extract text (OCR) from an image"""
        if self.client is None:
            print("Vision AI not initialized - returning empty text")
            return ""
        
        try:
            image = self._get_image_source(image_path)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            return texts[0].description if texts else ""
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def detect_colors(self, image_path: str) -> List[str]:
        """Detect dominant colors in an image"""
        if self.client is None:
            print("Vision AI not initialized - returning empty colors")
            return []
        
        try:
            image = self._get_image_source(image_path)
            response = self.client.image_properties(image=image)
            colors = response.image_properties_annotation.dominant_colors.colors
            hex_colors = []
            for color in colors[:5]:
                rgb = color.color
                hex_color = f"#{int(rgb.red):02x}{int(rgb.green):02x}{int(rgb.blue):02x}"
                hex_colors.append(hex_color)
            return hex_colors
        except Exception as e:
            print(f"Error detecting colors: {e}")
            return []

    def detect_objects(self, image_path: str, max_results: int = 10) -> List[str]:
        """Detect objects in an image"""
        if self.client is None:
            print("Vision AI not initialized - returning empty objects")
            return []
        
        try:
            image = self._get_image_source(image_path)
            response = self.client.object_localization(image=image)
            objects = response.localized_object_annotations
            return [obj.name for obj in objects[:max_results]]
        except Exception as e:
            print(f"Error detecting objects: {e}")
            return []

    def generate_caption(self, image_path: str) -> str:
        """Generate a caption for an image"""
        if self.client is None:
            print("Vision AI not initialized - returning empty caption")
            return ""
        
        try:
            labels = self.get_labels(image_path, max_results=5)
            if labels:
                return f"Image contains: {', '.join(labels)}"
            return "No caption could be generated"
        except Exception as e:
            print(f"Error generating caption: {e}")
            return ""

    def analyze_image(self, image_path: str) -> Dict:
        """Comprehensive image analysis"""
        if self.client is None:
            print("Vision AI not initialized - returning empty analysis")
            return {
                "labels": [],
                "faces": 0,
                "text": "",
                "colors": [],
                "objects": [],
                "caption": ""
            }
        
        try:
            return {
                "labels": self.get_labels(image_path),
                "faces": self.detect_faces(image_path),
                "text": self.extract_text(image_path),
                "colors": self.detect_colors(image_path),
                "objects": self.detect_objects(image_path),
                "caption": self.generate_caption(image_path)
            }
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return {
                "labels": [],
                "faces": 0,
                "text": "",
                "colors": [],
                "objects": [],
                "caption": ""
            }


# Initialize Vision AI service
vision_ai_service = VisionAIService()
