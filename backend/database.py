from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
import redis

# Database
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_db() -> Session:
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Get Redis client"""
    return redis_client
