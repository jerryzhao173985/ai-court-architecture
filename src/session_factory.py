"""Factory for creating session stores based on configuration."""

from typing import Optional
from config import SessionStorageConfig
from session_async import AsyncSessionStore, FileBackend


def create_session_store(config: SessionStorageConfig) -> AsyncSessionStore:
    """
    Create a session store based on configuration.
    
    Args:
        config: Session storage configuration
        
    Returns:
        Configured AsyncSessionStore instance
        
    Raises:
        ValueError: If backend type is invalid or required settings are missing
    """
    backend = None
    
    if config.backend == "file":
        backend = FileBackend(storage_dir=config.file_storage_dir)
    
    elif config.backend == "postgresql":
        if not config.postgresql_dsn:
            raise ValueError("PostgreSQL DSN is required when using postgresql backend")
        
        try:
            from session_backends import PostgreSQLBackend
        except ImportError as e:
            raise ImportError(
                "PostgreSQL backend requires asyncpg. Install with: pip install asyncpg"
            ) from e
        
        backend = PostgreSQLBackend(
            dsn=config.postgresql_dsn,
            table_name=config.postgresql_table,
            pool_min_size=config.postgresql_pool_min,
            pool_max_size=config.postgresql_pool_max
        )
    
    elif config.backend == "mongodb":
        if not config.mongodb_connection_string:
            raise ValueError("MongoDB connection string is required when using mongodb backend")
        
        try:
            from session_backends import MongoDBBackend
        except ImportError as e:
            raise ImportError(
                "MongoDB backend requires motor. Install with: pip install motor"
            ) from e
        
        backend = MongoDBBackend(
            connection_string=config.mongodb_connection_string,
            database_name=config.mongodb_database,
            collection_name=config.mongodb_collection,
            max_pool_size=config.mongodb_pool_size
        )
    
    else:
        raise ValueError(f"Invalid session storage backend: {config.backend}")
    
    return AsyncSessionStore(
        backend=backend,
        batch_size=config.batch_size,
        batch_interval=config.batch_interval
    )
