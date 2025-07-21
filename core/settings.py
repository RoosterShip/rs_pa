"""
Configuration management for RS Personal Assistant using Pydantic Settings.

This module provides a hierarchical, type-safe configuration system that supports
environment variables, .env files, and validation. All settings are organized
into logical groups and support the RSPA_ prefix for environment variables.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Allowed logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"  
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AgentType(str, Enum):
    """Available agent types."""
    REIMBURSEMENT = "reimbursement"
    TASK_MANAGER = "task_manager"
    CALENDAR = "calendar"
    DOCUMENT_PROCESSOR = "document_processor"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_DATABASE_',
        case_sensitive=False
    )
    
    # Core database settings
    url: Optional[str] = Field(
        None,
        description="Database connection URL. If None, will be auto-generated based on dev_mode"
    )
    
    # Development settings
    dev_mode: bool = Field(
        False,
        description="Enable development mode (uses local project directory for database)"
    )
    
    # Backup settings
    backup_count: int = Field(
        5,
        ge=1,
        le=50,
        description="Number of database backups to retain"
    )
    
    backup_before_migration: bool = Field(
        True,
        description="Create backup before running database migrations"
    )
    
    # Performance settings
    pool_size: int = Field(
        5,
        ge=1,
        le=20,
        description="Database connection pool size"
    )
    
    max_overflow: int = Field(
        10,
        ge=0,
        le=50,
        description="Maximum database connection overflow"
    )
    
    pool_timeout: int = Field(
        30,
        ge=5,
        le=300,
        description="Database connection pool timeout in seconds"
    )
    
    @computed_field
    @property
    def effective_url(self) -> str:
        """Get the effective database URL based on configuration."""
        if self.url:
            return self.url
        
        if self.dev_mode:
            # Development mode - use project directory
            project_root = Path(__file__).parent.parent
            db_path = project_root / "data" / "main.db"
            db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Production mode - use user home directory
            if os.name == 'nt':  # Windows
                home_dir = Path(os.environ['USERPROFILE'])
            else:  # macOS, Linux
                home_dir = Path.home()
            
            data_dir = home_dir / ".rs" / "pa"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "main.db"
        
        return f"sqlite:///{db_path}"
    
    @computed_field
    @property
    def backup_directory(self) -> Path:
        """Get the backup directory path."""
        db_path = Path(self.effective_url.replace("sqlite:///", ""))
        return db_path.parent / "backups"


class OllamaSettings(BaseSettings):
    """Ollama LLM service configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_OLLAMA_',
        case_sensitive=False
    )
    
    # Connection settings
    host: str = Field(
        "localhost",
        description="Hostname where Ollama service is running"
    )
    
    port: int = Field(
        11434,
        ge=1,
        le=65535,
        description="Port where Ollama service is listening"
    )
    
    # Model settings
    default_model: str = Field(
        "llama4:maverick",
        description="Default LLM model to use"
    )
    
    temperature: float = Field(
        0.1,
        ge=0.0,
        le=2.0,
        description="Default temperature for LLM responses"
    )
    
    max_tokens: Optional[int] = Field(
        None,
        gt=0,
        description="Maximum tokens for LLM responses"
    )
    
    # Performance settings
    timeout: int = Field(
        30,
        ge=5,
        le=300,
        description="Request timeout in seconds"
    )
    
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts"
    )
    
    health_check_interval: int = Field(
        60,
        ge=10,
        le=600,
        description="Health check interval in seconds"
    )
    
    @computed_field
    @property
    def base_url(self) -> str:
        """Get the full base URL for Ollama API."""
        return f"http://{self.host}:{self.port}"
    
    @field_validator('default_model')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model name format."""
        if not v or ':' not in v:
            raise ValueError("Model name must be in format 'model:tag'")
        return v.lower()


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_LOGGING_',
        case_sensitive=False
    )
    
    # Core logging settings
    level: LogLevel = Field(
        LogLevel.INFO,
        description="Application logging level"
    )
    
    # File logging settings
    log_to_file: bool = Field(
        True,
        description="Enable logging to file"
    )
    
    log_file_max_size: int = Field(
        10 * 1024 * 1024,  # 10MB
        gt=0,
        description="Maximum log file size in bytes"
    )
    
    log_file_backup_count: int = Field(
        5,
        ge=1,
        le=50,
        description="Number of log file backups to retain"
    )
    
    # Console logging settings
    log_to_console: bool = Field(
        True,
        description="Enable logging to console"
    )
    
    colored_console: bool = Field(
        True,
        description="Enable colored console output"
    )
    
    # Database logging settings
    log_to_database: bool = Field(
        True,
        description="Enable logging to database for UI viewer"
    )
    
    database_log_retention_days: int = Field(
        30,
        ge=1,
        le=365,
        description="Number of days to retain database logs"
    )
    
    @computed_field
    @property
    def log_directory(self) -> Path:
        """Get the logging directory path."""
        if os.getenv("RSPA_DEV_MODE", "false").lower() == "true":
            # Development mode
            project_root = Path(__file__).parent.parent
            return project_root / "data" / "logs"
        else:
            # Production mode
            if os.name == 'nt':  # Windows
                home_dir = Path(os.environ['USERPROFILE'])
            else:  # macOS, Linux
                home_dir = Path.home()
            
            return home_dir / ".rs" / "pa" / "logs"


class SecuritySettings(BaseSettings):
    """Security and credential management settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_SECURITY_',
        case_sensitive=False
    )
    
    # Credential encryption
    credential_encryption: bool = Field(
        True,
        description="Enable credential encryption at rest"
    )
    
    credential_key_rotation_days: int = Field(
        90,
        ge=1,
        le=365,
        description="Days between credential key rotations"
    )
    
    # Token settings
    token_expiration_hours: int = Field(
        24,
        ge=1,
        le=168,  # 1 week max
        description="OAuth token expiration time in hours"
    )
    
    # Security features
    enable_audit_logging: bool = Field(
        True,
        description="Enable security audit logging"
    )
    
    max_failed_attempts: int = Field(
        5,
        ge=1,
        le=50,
        description="Maximum failed authentication attempts"
    )
    
    lockout_duration_minutes: int = Field(
        15,
        ge=1,
        le=1440,  # 24 hours max
        description="Account lockout duration in minutes"
    )


class AgentSettings(BaseSettings):
    """Agent system configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_AGENTS_',
        case_sensitive=False
    )
    
    # Execution settings
    max_concurrent_tasks: int = Field(
        3,
        ge=1,
        le=20,
        description="Maximum number of concurrent agent tasks"
    )
    
    max_execution_time_minutes: int = Field(
        30,
        ge=1,
        le=1440,  # 24 hours max
        description="Maximum agent execution time in minutes"
    )
    
    # Retry settings
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum retry attempts for failed tasks"
    )
    
    retry_backoff_seconds: int = Field(
        5,
        ge=1,
        le=300,
        description="Backoff time between retries in seconds"
    )
    
    # Monitoring settings
    health_check_enabled: bool = Field(
        True,
        description="Enable agent health monitoring"
    )
    
    performance_monitoring: bool = Field(
        True,
        description="Enable agent performance monitoring"
    )
    
    # Enabled agents
    enabled_agents: List[AgentType] = Field(
        default_factory=lambda: [AgentType.REIMBURSEMENT],
        description="List of enabled agent types"
    )


class CacheSettings(BaseSettings):
    """Caching configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_CACHE_',
        case_sensitive=False
    )
    
    # LLM response caching
    enable_llm_cache: bool = Field(
        True,
        description="Enable LLM response caching"
    )
    
    llm_cache_ttl_hours: int = Field(
        24,
        ge=1,
        le=168,  # 1 week max
        description="LLM cache time-to-live in hours"
    )
    
    llm_cache_max_size_mb: int = Field(
        100,
        ge=10,
        le=1000,
        description="Maximum LLM cache size in MB"
    )
    
    # General caching
    enable_data_cache: bool = Field(
        True,
        description="Enable general data caching"
    )
    
    data_cache_ttl_minutes: int = Field(
        60,
        ge=1,
        le=1440,
        description="Data cache time-to-live in minutes"
    )
    
    @computed_field
    @property
    def cache_directory(self) -> Path:
        """Get the cache directory path."""
        if os.getenv("RSPA_DEV_MODE", "false").lower() == "true":
            # Development mode
            project_root = Path(__file__).parent.parent
            return project_root / "data" / "cache"
        else:
            # Production mode
            if os.name == 'nt':  # Windows
                home_dir = Path(os.environ['USERPROFILE'])
            else:  # macOS, Linux
                home_dir = Path.home()
            
            return home_dir / ".rs" / "pa" / "cache"


class UISettings(BaseSettings):
    """User interface configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix='RSPA_UI_',
        case_sensitive=False
    )
    
    # Streamlit settings
    port: int = Field(
        8501,
        ge=1024,
        le=65535,
        description="Streamlit server port"
    )
    
    host: str = Field(
        "localhost",
        description="Streamlit server host"
    )
    
    # UI preferences
    theme: str = Field(
        "auto",
        regex="^(auto|light|dark)$",
        description="UI theme (auto, light, dark)"
    )
    
    page_title: str = Field(
        "RS Personal Assistant",
        description="Application page title"
    )
    
    show_performance_metrics: bool = Field(
        True,
        description="Show performance metrics in UI"
    )
    
    auto_refresh_interval: int = Field(
        30,
        ge=5,
        le=300,
        description="Auto-refresh interval in seconds"
    )


class ApplicationSettings(BaseSettings):
    """Main application settings combining all configuration groups."""
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'  # Ignore extra environment variables
    )
    
    # Application metadata
    app_name: str = Field(
        "RS Personal Assistant",
        description="Application name"
    )
    
    app_version: str = Field(
        "0.1.0",
        description="Application version"
    )
    
    debug: bool = Field(
        False,
        description="Enable debug mode"
    )
    
    # Configuration groups
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="Database configuration"
    )
    
    ollama: OllamaSettings = Field(
        default_factory=OllamaSettings,
        description="Ollama LLM configuration"
    )
    
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging configuration"
    )
    
    security: SecuritySettings = Field(
        default_factory=SecuritySettings,
        description="Security configuration"
    )
    
    agents: AgentSettings = Field(
        default_factory=AgentSettings,
        description="Agent system configuration"
    )
    
    cache: CacheSettings = Field(
        default_factory=CacheSettings,
        description="Caching configuration"
    )
    
    ui: UISettings = Field(
        default_factory=UISettings,
        description="User interface configuration"
    )
    
    # Integration test settings
    integration_tests: bool = Field(
        False,
        description="Enable integration tests (requires external services)"
    )
    
    @field_validator('debug')
    @classmethod
    def validate_debug_mode(cls, v: bool, info) -> bool:
        """Ensure debug mode is only enabled in development."""
        if v and not os.getenv("RSPA_DEV_MODE", "false").lower() == "true":
            import warnings
            warnings.warn(
                "Debug mode enabled in production environment",
                UserWarning
            )
        return v
    
    def model_dump_config(self) -> Dict[str, Any]:
        """Dump configuration as dictionary for logging/debugging."""
        config = self.model_dump()
        
        # Remove sensitive information
        sensitive_keys = ['credential', 'password', 'secret', 'token', 'key']
        for key in list(config.keys()):
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                config[key] = "***REDACTED***"
        
        return config


# Global settings instance
def get_settings() -> ApplicationSettings:
    """Get the global application settings instance."""
    if not hasattr(get_settings, '_instance'):
        get_settings._instance = ApplicationSettings()
    return get_settings._instance


def reload_settings() -> ApplicationSettings:
    """Reload settings from environment (useful for testing)."""
    if hasattr(get_settings, '_instance'):
        delattr(get_settings, '_instance')
    return get_settings()


# Convenience exports
__all__ = [
    'ApplicationSettings',
    'DatabaseSettings', 
    'OllamaSettings',
    'LoggingSettings',
    'SecuritySettings',
    'AgentSettings',
    'CacheSettings',
    'UISettings',
    'LogLevel',
    'AgentType',
    'get_settings',
    'reload_settings'
]