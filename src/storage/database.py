from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager
from typing import Generator, AsyncGenerator
import asyncio

from ..config.settings import Settings
from .models import Base


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
    
    def init_sync_engine(self):
        """Initialize synchronous database engine"""
        if self.engine is None:
            self.engine = create_engine(
                self.settings.database.url,
                pool_size=self.settings.database.pool_size,
                max_overflow=self.settings.database.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
    
    def init_async_engine(self):
        """Initialize asynchronous database engine"""
        if self.async_engine is None:
            # Convert postgresql:// to postgresql+asyncpg:// for async support
            async_url = self.settings.database.url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
            
            self.async_engine = create_async_engine(
                async_url,
                pool_size=self.settings.database.pool_size,
                max_overflow=self.settings.database.max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            self.AsyncSessionLocal = sessionmaker(
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                bind=self.async_engine
            )
    
    @contextmanager
    def get_sync_session(self) -> Generator[Session, None, None]:
        """Get synchronous database session"""
        if self.SessionLocal is None:
            self.init_sync_engine()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get asynchronous database session"""
        if self.AsyncSessionLocal is None:
            self.init_async_engine()
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    def create_tables(self):
        """Create all database tables"""
        if self.engine is None:
            self.init_sync_engine()
        
        Base.metadata.create_all(bind=self.engine)
    
    async def create_tables_async(self):
        """Create all database tables asynchronously"""
        if self.async_engine is None:
            self.init_async_engine()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    def drop_tables(self):
        """Drop all database tables"""
        if self.engine is None:
            self.init_sync_engine()
        
        Base.metadata.drop_all(bind=self.engine)
    
    async def drop_tables_async(self):
        """Drop all database tables asynchronously"""
        if self.async_engine is None:
            self.init_async_engine()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
        if self.async_engine:
            self.async_engine.dispose()


# Global database manager instance
db_manager: DatabaseManager = None


def get_db_manager(settings: Settings) -> DatabaseManager:
    """Get or create database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager(settings)
    return db_manager


def get_sync_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    
    with db_manager.get_sync_session() as session:
        yield session


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency for FastAPI to get database session"""
    if db_manager is None:
        raise RuntimeError("Database manager not initialized")
    
    async for session in db_manager.get_async_session():
        yield session