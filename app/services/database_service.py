"""
Database service for SQLite operations
"""
import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseService:
    def __init__(self, db_path: str = "data/app.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        self._closed = False
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _ensure_connection_open(self):
        """Reopen connection if it was closed."""
        if self._closed or self.conn is None:
            self.conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._closed = False

    def _init_schema(self):
        """Initialize database schema"""
        with self._lock:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  camera_id TEXT NOT NULL,
                  road_class TEXT NOT NULL,
                  confidence REAL NOT NULL,
                  width_cm REAL,
                  depth_cm REAL,
                  bbox_x1 REAL,
                  bbox_y1 REAL,
                  bbox_x2 REAL,
                  bbox_y2 REAL,
                  latitude REAL,
                  longitude REAL,
                  image_path TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  synced INTEGER DEFAULT 0
                )
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_synced 
                ON detections(synced)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_class 
                ON detections(road_class)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_timestamp 
                ON detections(timestamp DESC)
            """)
            
            self.conn.commit()

    def insert_detection(self, detection: Dict) -> int:
        """Insert a new detection record"""
        columns = ', '.join(detection.keys())
        placeholders = ', '.join(['?' for _ in detection])
        query = f"INSERT INTO detections ({columns}) VALUES ({placeholders})"
        with self._lock:
            self._ensure_connection_open()
            cursor = self.conn.execute(query, list(detection.values()))
            self.conn.commit()
            return cursor.lastrowid

    def get_unsynced(self, limit: int = 200) -> List[Dict]:
        """Get unsynced detections for upload to Supabase"""
        with self._lock:
            self._ensure_connection_open()
            cursor = self.conn.execute("""
            SELECT * FROM detections 
            WHERE synced = 0 
            ORDER BY id ASC 
            LIMIT ?
        """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def mark_synced(self, ids: List[int]):
        """Mark detections as synced"""
        if not ids:
            return
        
        placeholders = ','.join(['?' for _ in ids])
        query = f"UPDATE detections SET synced = 1 WHERE id IN ({placeholders})"
        with self._lock:
            self._ensure_connection_open()
            self.conn.execute(query, ids)
            self.conn.commit()

    def get_stats(self) -> Dict:
        """Get detection statistics"""
        with self._lock:
            self._ensure_connection_open()
            cursor = self.conn.execute("""
            SELECT 
                road_class,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence,
                AVG(width_cm) as avg_width,
                AVG(depth_cm) as avg_depth
            FROM detections
            GROUP BY road_class
        """)
            stats = {}
            for row in cursor.fetchall():
                stats[row['road_class']] = {
                    'count': row['count'],
                    'avg_confidence': row['avg_confidence'],
                    'avg_width': row['avg_width'],
                    'avg_depth': row['avg_depth']
                }
            return stats

    def get_recent_detections(self, limit: int = 100) -> List[Dict]:
        """Get recent detections"""
        with self._lock:
            self._ensure_connection_open()
            cursor = self.conn.execute("""
            SELECT * FROM detections 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_total_count(self) -> int:
        """Get total detection count"""
        with self._lock:
            self._ensure_connection_open()
            cursor = self.conn.execute("SELECT COUNT(*) as count FROM detections")
            return cursor.fetchone()['count']

    def get_unsynced_count(self) -> int:
        """Get unsynced detection count"""
        with self._lock:
            self._ensure_connection_open()
            cursor = self.conn.execute("""
            SELECT COUNT(*) as count FROM detections WHERE synced = 0
        """)
            return cursor.fetchone()['count']

    def close(self):
        """Close database connection"""
        with self._lock:
            if not self._closed and self.conn is not None:
                try:
                    self.conn.close()
                finally:
                    self._closed = True
                    self.conn = None
