import os
from typing import List, Dict, Optional, Any
from google.cloud import bigquery
from google.oauth2 import service_account
from app.config import Settings

settings = Settings()


class BigQueryService:
    def __init__(self):
        self.client = None
        self.project_id = settings.GCP_PROJECT_ID
        
        try:
            # Try to load credentials from file
            cred_path = settings.FIREBASE_CREDENTIALS_PATH
            if os.path.isfile(cred_path):
                credentials = service_account.Credentials.from_service_account_file(
                    cred_path,
                    scopes=['https://www.googleapis.com/auth/bigquery']
                )
                self.client = bigquery.Client(project=self.project_id, credentials=credentials)
                # Test connection
                self.client.list_datasets(max_results=1)
                print("✓ BigQuery initialized successfully")
            else:
                self.client = bigquery.Client(project=self.project_id)
                self.client.list_datasets(max_results=1)
                print("✓ BigQuery initialized with default credentials")
        except Exception as e:
            print(f"⚠ BigQuery initialization error: {e}")
            print("  BigQuery analytics will be disabled. Add GCP credentials to enable it.")
            self.client = None

    def ensure_tables(self) -> bool:
        """Create tables if they don't exist"""
        if self.client is None:
            print("BigQuery not initialized - skipping table creation")
            return False
        
        try:
            dataset_id = "photo_vault"
            dataset_ref = self.client.dataset(dataset_id)
            
            try:
                self.client.get_dataset(dataset_ref)
            except:
                dataset = bigquery.Dataset(dataset_ref)
                dataset = self.client.create_dataset(dataset, timeout=30)
                print(f"Created dataset {dataset.project}.{dataset.dataset_id}")
            
            return True
        except Exception as e:
            print(f"Error ensuring tables: {e}")
            return False

    def insert_event(self, user_id: int, event_type: str, data: Dict[str, Any]) -> bool:
        """Insert an event into BigQuery"""
        if self.client is None:
            print("BigQuery not initialized - skipping event insert")
            return False
        
        try:
            table_id = f"{self.project_id}.photo_vault.events"
            rows_to_insert = [
                {
                    "user_id": user_id,
                    "event_type": event_type,
                    "data": str(data),
                    "timestamp": bigquery.datetime.datetime.utcnow()
                }
            ]
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            
            if errors:
                print(f"Error inserting event: {errors}")
                return False
            return True
        except Exception as e:
            print(f"Error inserting event: {e}")
            return False

    def insert_image_metadata(self, user_id: int, image_id: int, metadata: Dict) -> bool:
        """Insert image metadata into BigQuery"""
        if self.client is None:
            print("BigQuery not initialized - skipping metadata insert")
            return False
        
        try:
            table_id = f"{self.project_id}.photo_vault.image_metadata"
            rows_to_insert = [
                {
                    "user_id": user_id,
                    "image_id": image_id,
                    "metadata": str(metadata),
                    "inserted_at": bigquery.datetime.datetime.utcnow()
                }
            ]
            errors = self.client.insert_rows_json(table_id, rows_to_insert)
            
            if errors:
                print(f"Error inserting metadata: {errors}")
                return False
            return True
        except Exception as e:
            print(f"Error inserting metadata: {e}")
            return False

    def query(self, sql: str) -> Optional[List[Dict]]:
        """Execute a query and return results"""
        if self.client is None:
            print("BigQuery not initialized - returning empty results")
            return []
        
        try:
            query_job = self.client.query(sql)
            results = query_job.result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def get_user_statistics(self, user_id: int) -> Optional[Dict]:
        """Get statistics for a specific user"""
        if self.client is None:
            print("BigQuery not initialized - returning empty stats")
            return {"total_images": 0, "total_storage": 0}
        
        try:
            sql = f"""
            SELECT 
                COUNT(*) as total_images,
                SUM(file_size) as total_storage
            FROM `{self.project_id}.photo_vault.images`
            WHERE user_id = {user_id}
            """
            results = self.query(sql)
            if results:
                return results[0]
            return {"total_images": 0, "total_storage": 0}
        except Exception as e:
            print(f"Error getting user statistics: {e}")
            return {"total_images": 0, "total_storage": 0}

    def get_popular_tags(self, limit: int = 10) -> List[Dict]:
        """Get popular tags across all images"""
        if self.client is None:
            print("BigQuery not initialized - returning empty tags")
            return []
        
        try:
            sql = f"""
            SELECT tag, COUNT(*) as count
            FROM `{self.project_id}.photo_vault.image_tags`
            GROUP BY tag
            ORDER BY count DESC
            LIMIT {limit}
            """
            results = self.query(sql)
            return results if results else []
        except Exception as e:
            print(f"Error getting popular tags: {e}")
            return []

    def get_storage_breakdown(self, user_id: int) -> Optional[Dict]:
        """Get storage breakdown by file type for a user"""
        if self.client is None:
            print("BigQuery not initialized - returning empty breakdown")
            return {}
        
        try:
            sql = f"""
            SELECT 
                mime_type,
                COUNT(*) as file_count,
                SUM(file_size) as total_size
            FROM `{self.project_id}.photo_vault.images`
            WHERE user_id = {user_id}
            GROUP BY mime_type
            ORDER BY total_size DESC
            """
            results = self.query(sql)
            return {row['mime_type']: row for row in results} if results else {}
        except Exception as e:
            print(f"Error getting storage breakdown: {e}")
            return {}


# Initialize BigQuery service
bigquery_service = BigQueryService()
