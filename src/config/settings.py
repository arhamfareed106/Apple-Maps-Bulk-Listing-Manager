from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class AppleSettings(BaseSettings):
    """Apple Business Connect API settings"""
    client_id: str
    client_secret: str
    team_id: str
    key_id: str
    private_key_path: Path
    
    model_config = SettingsConfigDict(
        env_prefix="APPLE_",
        case_sensitive=False
    )


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    
    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        case_sensitive=False
    )


class YextSettings(BaseSettings):
    """Yext API settings"""
    api_key: str
    account_id: str
    
    model_config = SettingsConfigDict(
        env_prefix="YEXT_",
        case_sensitive=False
    )


class UberallSettings(BaseSettings):
    """Uberall API settings"""
    api_key: str
    account_id: str
    
    model_config = SettingsConfigDict(
        env_prefix="UBERALL_",
        case_sensitive=False
    )


class RioSeoSettings(BaseSettings):
    """Rio SEO API settings"""
    api_key: str
    account_id: str
    
    model_config = SettingsConfigDict(
        env_prefix="RIO_SEO_",
        case_sensitive=False
    )


class NotificationSettings(BaseSettings):
    """Notification settings"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    notification_email: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False
    )


class Settings(BaseSettings):
    """Main application settings"""
    # Core settings
    debug: bool = False
    testing: bool = False
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance settings
    max_concurrent_requests: int = 10
    batch_size: int = 100
    retry_max_attempts: int = 3
    retry_backoff_factor: float = 2.0
    
    # API configurations
    apple: AppleSettings
    database: DatabaseSettings
    yext: YextSettings
    uberall: UberallSettings
    rio_seo: RioSeoSettings
    notifications: NotificationSettings
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )