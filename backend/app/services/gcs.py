import os
from typing import Optional
from google.cloud import storage
from google.oauth2 import service_account
from app.config import Settings

settings = Settings()


class GCSService:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.client = None
        self.bucket = None
        
        try:
            # Try to load credentials from file
            cred_path = settings.FIREBASE_CREDENTIALS_PATH
            if os.path.isfile(cred_path):
                credentials = service_account.Credentials.from_service_account_file(
                    cred_path,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                self.client = storage.Client(project=settings.GCP_PROJECT_ID, credentials=credentials)
                self.bucket = self.client.bucket(bucket_name)
                print(f"✓ GCS initialized successfully for bucket: {bucket_name}")
            else:
                # Fallback to default credentials
                self.client = storage.Client(project=settings.GCP_PROJECT_ID)
                self.bucket = self.client.bucket(bucket_name)
                print(f"✓ GCS initialized with default credentials for bucket: {bucket_name}")
        except Exception as e:
            print(f"⚠ GCS initialization error: {e}")
            print("  GCS uploads will be disabled. Add GCP credentials to enable it.")
            self.client = None
            self.bucket = None

    def upload_file(self, file_path: str, destination_blob_name: str) -> Optional[str]:
        """Upload a file to GCS"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - skipping upload")
            return f"gs://{self.bucket_name}/{destination_blob_name}"
        
        try:
            blob = self.bucket.blob(destination_blob_name)
            blob.upload_from_filename(file_path)
            return blob.public_url
        except Exception as e:
            print(f"Error uploading to GCS: {e}")
            return None

    def download_file(self, source_blob_name: str, destination_file_path: str) -> bool:
        """Download a file from GCS"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - skipping download")
            return False
        
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(destination_file_path)
            return True
        except Exception as e:
            print(f"Error downloading from GCS: {e}")
            return False

    def delete_file(self, blob_name: str) -> bool:
        """Delete a file from GCS"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - skipping delete")
            return True
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting from GCS: {e}")
            return False

    def file_exists(self, blob_name: str) -> bool:
        """Check if a file exists in GCS"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - assuming file doesn't exist")
            return False
        
        try:
            blob = self.bucket.blob(blob_name)
            return blob.exists()
        except Exception as e:
            print(f"Error checking file in GCS: {e}")
            return False

    def get_file_metadata(self, blob_name: str) -> Optional[dict]:
        """Get metadata of a file in GCS"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - returning dummy metadata")
            return {"size": 0, "created": None, "updated": None}
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.reload()
            return {
                "size": blob.size,
                "created": blob.time_created,
                "updated": blob.updated,
                "content_type": blob.content_type
            }
        except Exception as e:
            print(f"Error getting metadata from GCS: {e}")
            return None

    def list_files(self, prefix: str = "") -> list:
        """List files in GCS bucket"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - returning empty list")
            return []
        
        try:
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            print(f"Error listing files in GCS: {e}")
            return []

    def copy_file(self, source_blob_name: str, destination_blob_name: str) -> bool:
        """Copy a file within GCS bucket"""
        if self.client is None or self.bucket is None:
            print("GCS not initialized - skipping copy")
            return True
        
        try:
            source_blob = self.bucket.blob(source_blob_name)
            destination_blob = self.bucket.copy_blob(source_blob, self.bucket, destination_blob_name)
            return True
        except Exception as e:
            print(f"Error copying file in GCS: {e}")
            return False


# Initialize GCS service
gcs_service = GCSService(settings.GCS_BUCKET_NAME)
