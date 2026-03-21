"""Database backend implementations for session storage."""

import json
from typing import Optional
from datetime import datetime, timedelta

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

try:
    from motor import motor_asyncio
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False

from session_async import SessionBackend, UserSession


class PostgreSQLBackend(SessionBackend):
    """PostgreSQL backend for session storage using asyncpg."""
    
    def __init__(
        self,
        dsn: str,
        table_name: str = "user_sessions",
        pool_min_size: int = 10,
        pool_max_size: int = 20
    ):
        """
        Initialize PostgreSQL backend.
        
        Args:
            dsn: PostgreSQL connection string (e.g., "postgresql://user:pass@localhost/db")
            table_name: Name of the table to store sessions
            pool_min_size: Minimum connection pool size
            pool_max_size: Maximum connection pool size
        """
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is required for PostgreSQL backend. Install with: pip install asyncpg")
        
        self.dsn = dsn
        self.table_name = table_name
        self.pool_min_size = pool_min_size
        self.pool_max_size = pool_max_size
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.dsn,
                min_size=self.pool_min_size,
                max_size=self.pool_max_size
            )
            await self._create_table()
    
    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def _create_table(self) -> None:
        """Create sessions table if it doesn't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    case_id VARCHAR(255) NOT NULL,
                    session_data JSONB NOT NULL,
                    last_activity_time TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on last_activity_time for efficient cleanup
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_last_activity 
                ON {self.table_name}(last_activity_time)
            """)
    
    async def save(self, session: UserSession) -> None:
        """
        Save session to PostgreSQL.
        
        Args:
            session: The user session to save
        """
        if not self._pool:
            await self.connect()
        
        session_data = session.serialize()
        
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self.table_name} 
                (session_id, user_id, case_id, session_data, last_activity_time, updated_at)
                VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                ON CONFLICT (session_id) 
                DO UPDATE SET 
                    session_data = EXCLUDED.session_data,
                    last_activity_time = EXCLUDED.last_activity_time,
                    updated_at = CURRENT_TIMESTAMP
            """, session.session_id, session.user_id, session.case_id, 
                session_data, session.last_activity_time)
    
    async def load(self, session_id: str) -> Optional[UserSession]:
        """
        Load session from PostgreSQL.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            UserSession if found and not expired, None otherwise
        """
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f"""
                SELECT session_data, last_activity_time 
                FROM {self.table_name}
                WHERE session_id = $1
            """, session_id)
            
            if not row:
                return None
            
            try:
                session = UserSession.deserialize(row['session_data'])
                
                # Check if session is expired
                if session.is_expired(retention_hours=24):
                    await self.delete(session_id)
                    return None
                
                return session
            except Exception:
                # If we can't parse the session, delete it
                await self.delete(session_id)
                return None
    
    async def delete(self, session_id: str) -> None:
        """
        Delete a session from PostgreSQL.
        
        Args:
            session_id: The session ID to delete
        """
        if not self._pool:
            await self.connect()
        
        async with self._pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM {self.table_name}
                WHERE session_id = $1
            """, session_id)
    
    async def cleanup_expired(self, retention_hours: int = 24) -> int:
        """
        Remove all expired sessions from PostgreSQL.
        
        Args:
            retention_hours: Number of hours to retain sessions
            
        Returns:
            Number of sessions cleaned up
        """
        if not self._pool:
            await self.connect()
        
        expiry_time = datetime.now() - timedelta(hours=retention_hours)
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(f"""
                DELETE FROM {self.table_name}
                WHERE last_activity_time < $1
            """, expiry_time)
            
            # Extract count from result string like "DELETE 5"
            return int(result.split()[-1]) if result else 0


class MongoDBBackend(SessionBackend):
    """MongoDB backend for session storage using motor."""
    
    def __init__(
        self,
        connection_string: str,
        database_name: str = "veritas",
        collection_name: str = "user_sessions",
        max_pool_size: int = 20
    ):
        """
        Initialize MongoDB backend.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database
            collection_name: Name of the collection to store sessions
            max_pool_size: Maximum connection pool size
        """
        if not MOTOR_AVAILABLE:
            raise ImportError("motor is required for MongoDB backend. Install with: pip install motor")
        
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        self.max_pool_size = max_pool_size
        self._client: Optional[motor_asyncio.AsyncIOMotorClient] = None
        self._collection = None
    
    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        if self._client is None:
            self._client = motor_asyncio.AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=self.max_pool_size
            )
            db = self._client[self.database_name]
            self._collection = db[self.collection_name]
            
            # Create index on session_id for fast lookups
            await self._collection.create_index("session_id", unique=True)
            
            # Create index on last_activity_time for efficient cleanup
            await self._collection.create_index("last_activity_time")
    
    async def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._collection = None
    
    async def save(self, session: UserSession) -> None:
        """
        Save session to MongoDB.
        
        Args:
            session: The user session to save
        """
        if not self._collection:
            await self.connect()
        
        # Convert session to dict for MongoDB storage
        session_dict = json.loads(session.serialize())
        session_dict["_id"] = session.session_id
        session_dict["updated_at"] = datetime.now()
        
        await self._collection.replace_one(
            {"_id": session.session_id},
            session_dict,
            upsert=True
        )
    
    async def load(self, session_id: str) -> Optional[UserSession]:
        """
        Load session from MongoDB.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            UserSession if found and not expired, None otherwise
        """
        if not self._collection:
            await self.connect()
        
        doc = await self._collection.find_one({"_id": session_id})
        
        if not doc:
            return None
        
        try:
            # Remove MongoDB-specific fields
            doc.pop("_id", None)
            doc.pop("updated_at", None)
            
            # Convert back to JSON string for deserialization
            json_str = json.dumps(doc)
            session = UserSession.deserialize(json_str)
            
            # Check if session is expired
            if session.is_expired(retention_hours=24):
                await self.delete(session_id)
                return None
            
            return session
        except Exception:
            # If we can't parse the session, delete it
            await self.delete(session_id)
            return None
    
    async def delete(self, session_id: str) -> None:
        """
        Delete a session from MongoDB.
        
        Args:
            session_id: The session ID to delete
        """
        if not self._collection:
            await self.connect()
        
        await self._collection.delete_one({"_id": session_id})
    
    async def cleanup_expired(self, retention_hours: int = 24) -> int:
        """
        Remove all expired sessions from MongoDB.
        
        Args:
            retention_hours: Number of hours to retain sessions
            
        Returns:
            Number of sessions cleaned up
        """
        if not self._collection:
            await self.connect()
        
        expiry_time = datetime.now() - timedelta(hours=retention_hours)
        
        result = await self._collection.delete_many({
            "lastActivityTime": {"$lt": expiry_time.isoformat()}
        })
        
        return result.deleted_count
