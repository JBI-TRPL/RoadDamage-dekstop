"""
Supabase service for cloud synchronization
"""
from supabase import create_client, Client
from typing import List, Dict, Optional
import logging
import time

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self, url: str, anon_key: str, table: str = "detections"):
        """
        Initialize Supabase client
        
        Args:
            url: Supabase project URL
            anon_key: Supabase anon key
            table: Table name (default: detections)
        """
        self.url = url
        self.anon_key = anon_key
        self.table = table
        self.client: Optional[Client] = None
        self._initialized = False
        
        try:
            self.client = create_client(url, anon_key)
            self._initialized = True
            logger.info("✅ Supabase initialized")
        except Exception as e:
            logger.error(f"❌ Supabase initialization failed: {e}")

    @property
    def is_available(self) -> bool:
        """Check if Supabase is available"""
        return self._initialized and self.client is not None

    def upsert_detections(self, rows: List[Dict]) -> bool:
        """
        Upload/update detections to Supabase
        
        Args:
            rows: List of detection dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available or not rows:
            return False

        # Convert rows
        supabase_rows = []
        for row in rows:
            supabase_row = {
                'camera_id': row.get('camera_id'),
                'class': row.get('road_class'),  # Match Flutter app field name
                'confidence': row.get('confidence'),
                'width_cm': row.get('width_cm'),
                'depth_cm': row.get('depth_cm'),
                'latitude': row.get('latitude'),
                'longitude': row.get('longitude'),
                'image_path': row.get('image_path'),
                'timestamp': row.get('timestamp'),
                'synced': True
            }
            # Remove None values
            supabase_rows.append({k: v for k, v in supabase_row.items() if v is not None})

        # Retry with exponential backoff
        attempts = 0
        delay = 1.0
        while attempts < 3:
            try:
                self.client.table(self.table).upsert(supabase_rows).execute()
                logger.info(f"✅ Uploaded {len(supabase_rows)} detections to Supabase")
                return True
            except Exception as e:
                attempts += 1
                logger.warning(f"⚠️ Supabase upsert failed (attempt {attempts}/3): {e}")
                time.sleep(delay)
                delay *= 2
        logger.error("❌ Supabase upsert failed after 3 attempts")
        return False

    def get_detections(self, limit: int = 100) -> List[Dict]:
        """
        Get detections from Supabase
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of detection dictionaries
        """
        if not self.is_available:
            return []

        try:
            response = self.client.table(self.table)\
                .select("*")\
                .order("timestamp", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
            
        except Exception as e:
            logger.error(f"❌ Error fetching from Supabase: {e}")
            return []

    def delete_detection(self, detection_id: int) -> bool:
        """
        Delete a detection from Supabase
        
        Args:
            detection_id: ID of detection to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available:
            return False

        try:
            self.client.table(self.table).delete().eq('id', detection_id).execute()
            logger.info(f"✅ Deleted detection {detection_id} from Supabase")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting from Supabase: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test Supabase connection
        
        Returns:
            True if connection is working, False otherwise
        """
        if not self.is_available:
            return False

        try:
            # Try to fetch 1 record
            self.client.table(self.table).select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False
