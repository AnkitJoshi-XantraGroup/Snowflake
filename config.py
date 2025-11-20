"""
Configuration management for SOGS (Snowflake Optimizer & Governance Suite)
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application settings
    APP_NAME: str = "Snowflake Optimizer & Governance Suite (SOGS)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Snowflake credentials (can be set via environment or UI)
    SNOWFLAKE_ACCOUNT: Optional[str] = None
    SNOWFLAKE_USER: Optional[str] = None
    SNOWFLAKE_PASSWORD: Optional[str] = None
    SNOWFLAKE_WAREHOUSE: Optional[str] = None
    SNOWFLAKE_DATABASE: Optional[str] = None
    SNOWFLAKE_SCHEMA: Optional[str] = None
    SNOWFLAKE_ROLE: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis (for caching)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Cost thresholds
    COST_ALERT_THRESHOLD: float = 100.0  # USD
    CREDIT_ALERT_THRESHOLD: float = 50.0  # Credits

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
