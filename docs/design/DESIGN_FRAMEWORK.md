# Framework Design - RS Personal Assistant

## 📋 Overview

This document details the core infrastructure and framework components that form the foundation of the RS Personal Assistant system. The framework provides shared services, data management, and system utilities that all agents and UI components depend upon.

## 🗄️ Database Architecture

### SQLAlchemy + Alembic Design

The system uses SQLAlchemy as the ORM with Alembic for database migrations, providing robust, version-controlled data management.

#### Core Database Components

**Database Session Management (`core/database.py`)**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from pathlib import Path
from core.settings import get_settings, DatabaseSettings

class DatabaseManager:
    def __init__(self, db_settings: DatabaseSettings = None):
        if db_settings is None:
            db_settings = get_settings().database
        
        self.db_settings = db_settings
        
        # Configure engine with connection pooling
        self.engine = create_engine(
            db_settings.effective_url, 
            echo=False,
            pool_size=db_settings.pool_size,
            max_overflow=db_settings.max_overflow,
            pool_timeout=db_settings.pool_timeout
        )
        
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))
        
        # Run migrations on initialization
        from core.migration_manager import initialize_database
        initialize_database(db_settings)
        
    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def backup_database(self) -> Path:
        """Create a database backup and return the backup path"""
        if not self.db_settings.backup_before_migration:
            return None
        
        from datetime import datetime
        import shutil
        
        db_path = Path(self.db_settings.effective_url.replace("sqlite:///", ""))
        if not db_path.exists():
            return None  # No database to backup
        
        backup_dir = self.db_settings.backup_directory
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"main_{timestamp}.db"
        
        shutil.copy2(db_path, backup_path)
        
        # Maintain backup count limit
        backups = sorted(backup_dir.glob("main_*.db"))
        if len(backups) > self.db_settings.backup_count:
            for old_backup in backups[:-self.db_settings.backup_count]:
                old_backup.unlink()
        
        return backup_path
```

#### Database Models Structure

**Base Models (`models/base.py`)**
```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Agent Models (`models/agent.py`)**
```python
from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum

class AgentStatus(enum.Enum):
    REGISTERED = "registered"
    ACTIVE = "active"
    IDLE = "idle"
    ERROR = "error"
    DISABLED = "disabled"

class Agent(BaseModel):
    __tablename__ = "agents"
    
    name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.REGISTERED)
    configuration = Column(Text)  # JSON configuration
    description = Column(Text)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent")
    data_entries = relationship("AgentData", back_populates="agent")
```

**Task Models (`models/task.py`)**
```python
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum

class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Task(BaseModel):
    __tablename__ = "tasks"
    
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    input_data = Column(Text)  # JSON input
    output_data = Column(Text)  # JSON output
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")
```

#### Alembic Migration Setup

**Alembic Environment (`alembic/env.py`)**
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from models.base import Base
from models import agent, task  # Import all models
from core.settings import get_settings

# Alembic Config object
config = context.config

# Target metadata
target_metadata = Base.metadata

def get_database_url():
    """Get database URL from hierarchical settings"""
    settings = get_settings()
    return settings.database.effective_url

def run_migrations_online():
    """Run migrations in 'online' mode."""
    # Override database URL with settings-derived path
    config.set_main_option("sqlalchemy.url", get_database_url())
    
    # Get database settings for connection pooling
    db_settings = get_settings().database
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # Enable type comparison for better migrations
            compare_server_default=True  # Compare server defaults
        )
        with context.begin_transaction():
            context.run_migrations()
```

**Automatic Migration Runner (`core/migration_manager.py`)**
```python
import sys
from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
import logging
from core.settings import get_settings, DatabaseSettings

class MigrationManager:
    """Handles automatic database migrations for standalone app"""
    
    def __init__(self, db_settings: DatabaseSettings = None):
        self.logger = logging.getLogger(__name__)
        if db_settings is None:
            db_settings = get_settings().database
        
        self.db_settings = db_settings
        self.db_url = db_settings.effective_url
        
    def _get_alembic_config(self):
        """Get Alembic configuration"""
        # Handle frozen executable path
        if getattr(sys, 'frozen', False):
            # Running as a frozen executable
            base_path = Path(sys._MEIPASS)
        else:
            # Running normally
            base_path = Path(__file__).parent.parent
        
        alembic_ini = base_path / "alembic.ini"
        alembic_dir = base_path / "alembic"
        
        config = Config(str(alembic_ini))
        config.set_main_option("script_location", str(alembic_dir))
        config.set_main_option("sqlalchemy.url", self.db_url)
        
        return config
    
    def check_migration_status(self):
        """Check if migrations are needed"""
        engine = create_engine(
            self.db_url,
            pool_size=self.db_settings.pool_size,
            max_overflow=self.db_settings.max_overflow
        )
        
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_revision = context.get_current_revision()
            
        return current_revision
    
    def run_migrations(self):
        """Run pending migrations automatically"""
        try:
            self.logger.info("Checking database migrations...")
            
            # Create backup before migrations if enabled
            backup_path = None
            if self.db_settings.backup_before_migration:
                backup_path = self._backup_database()
            
            # Get Alembic configuration
            config = self._get_alembic_config()
            
            # Run migrations
            command.upgrade(config, "head")
            
            self.logger.info("Database migrations completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            if backup_path:
                self._restore_backup(backup_path)
            return False
    
    def _backup_database(self) -> Path:
        """Create database backup before migration"""
        db_path = Path(self.db_url.replace("sqlite:///", ""))
        if not db_path.exists():
            return None  # No database to backup
        
        from datetime import datetime
        import shutil
        
        backup_dir = self.db_settings.backup_directory
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"main_{timestamp}.db"
        
        shutil.copy2(db_path, backup_path)
        self.logger.info(f"Database backed up to {backup_path}")
        
        # Maintain backup count limit using settings
        backups = sorted(backup_dir.glob("main_*.db"))
        if len(backups) > self.db_settings.backup_count:
            for old_backup in backups[:-self.db_settings.backup_count]:
                old_backup.unlink()
        
        return backup_path
    
    def _restore_backup(self, backup_path: Path):
        """Restore database from specific backup after failed migration"""
        if not backup_path or not backup_path.exists():
            self.logger.error("No backup available for restoration")
            return
        
        db_path = Path(self.db_url.replace("sqlite:///", ""))
        
        import shutil
        shutil.copy2(backup_path, db_path)
        self.logger.info(f"Database restored from {backup_path}")

# Application startup code
def initialize_database(db_settings: DatabaseSettings = None):
    """Initialize database and run migrations on app startup"""
    migration_manager = MigrationManager(db_settings)
    
    # Check if this is first run
    db_path = Path(migration_manager.db_url.replace("sqlite:///", ""))
    first_run = not db_path.exists()
    
    if first_run:
        logging.info("First run detected, initializing database...")
    
    # Run migrations (will create database if needed)
    success = migration_manager.run_migrations()
    
    if not success and first_run:
        logging.error("Failed to initialize database on first run")
        sys.exit(1)
    
    return success
```

### Database Performance Optimization

**Indexing Strategy**
- Primary keys: UUID-based for distributed compatibility
- Foreign keys: Automatic indexing on relationships
- Search columns: Indexed fields for agent names, task status, timestamps
- Composite indexes: Multi-column indexes for complex queries

**Connection Management**
- Connection pooling for multi-threaded operations
- Scoped sessions for request-based lifecycle
- Automatic connection cleanup and error recovery

**SQLite Storage Location**
- Default location: `~/.rs/pa/main.db`
- All user data stored in home directory for persistence across updates
- Separate databases for cache (`~/.rs/pa/cache.db`) and performance metrics (`~/.rs/pa/performance.db`)

**Migration Strategy for Updates**
- Alembic handles schema migrations automatically
- Version tracking in `alembic_version` table
- Backup created before migrations: `~/.rs/pa/backups/main_<timestamp>.db`
- Rollback capability preserves user data integrity

---

## 🤖 LLM Management System

### Ollama Integration Architecture

The LLM Manager provides centralized access to Ollama models with connection pooling, health monitoring, and fallback mechanisms.

**LLM Manager (`core/llm_manager.py`)**
```python
from langchain_ollama import ChatOllama
from typing import Dict, Optional, List
import requests
import logging
import time
import threading
from dataclasses import dataclass
from core.settings import get_settings, OllamaSettings

@dataclass
class ModelConfig:
    name: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 30

class LLMManager:
    def __init__(self, ollama_settings: OllamaSettings = None):
        if ollama_settings is None:
            ollama_settings = get_settings().ollama
        
        self.ollama_settings = ollama_settings
        self.models: Dict[str, ChatOllama] = {}
        self.model_configs: Dict[str, ModelConfig] = {}
        self.logger = logging.getLogger(__name__)
        
        # Health monitoring
        self._health_status = False
        self._last_health_check = 0
        self._health_check_lock = threading.Lock()
        
        # Register default model configuration
        self.register_model(ModelConfig(
            name=ollama_settings.default_model,
            temperature=ollama_settings.temperature,
            max_tokens=ollama_settings.max_tokens,
            timeout=ollama_settings.timeout
        ))
        
    def register_model(self, config: ModelConfig):
        """Register a model configuration"""
        self.model_configs[config.name] = config
        
    def get_model(self, model_name: str = None) -> ChatOllama:
        """Get or create a model instance"""
        if model_name is None:
            model_name = self.ollama_settings.default_model
            
        if model_name not in self.models:
            config = self.model_configs.get(
                model_name, 
                ModelConfig(
                    name=model_name,
                    temperature=self.ollama_settings.temperature,
                    max_tokens=self.ollama_settings.max_tokens,
                    timeout=self.ollama_settings.timeout
                )
            )
            
            self.models[model_name] = ChatOllama(
                model=config.name,
                base_url=self.ollama_settings.base_url,
                temperature=config.temperature,
                timeout=config.timeout
            )
            
        return self.models[model_name]
    
    def health_check(self, force_refresh: bool = False) -> bool:
        """Check Ollama service health with caching"""
        current_time = time.time()
        
        with self._health_check_lock:
            # Use cached result if within health check interval
            if (not force_refresh and 
                current_time - self._last_health_check < self.ollama_settings.health_check_interval):
                return self._health_status
            
            try:
                response = requests.get(
                    f"{self.ollama_settings.base_url}/api/tags", 
                    timeout=5
                )
                self._health_status = response.status_code == 200
                self._last_health_check = current_time
                
                if self._health_status:
                    self.logger.debug(f"Ollama health check passed: {self.ollama_settings.base_url}")
                else:
                    self.logger.warning(f"Ollama health check failed with status {response.status_code}")
                    
            except requests.RequestException as e:
                self._health_status = False
                self._last_health_check = current_time
                self.logger.error(f"Ollama health check failed: {e}")
            
            return self._health_status
    
    def list_available_models(self) -> List[str]:
        """List all available models on Ollama"""
        try:
            response = requests.get(
                f"{self.ollama_settings.base_url}/api/tags",
                timeout=self.ollama_settings.timeout
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch available models: {e}")
        return []
    
    def invoke_with_retry(self, model_name: str = None, prompt: str = "", **kwargs):
        """Invoke model with automatic retry logic"""
        if model_name is None:
            model_name = self.ollama_settings.default_model
        
        model = self.get_model(model_name)
        
        for attempt in range(self.ollama_settings.max_retries + 1):
            try:
                # Check health before attempting
                if not self.health_check():
                    raise requests.RequestException("Ollama service is not healthy")
                
                response = model.invoke(prompt, **kwargs)
                return response
                
            except Exception as e:
                if attempt < self.ollama_settings.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"LLM invocation attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"LLM invocation failed after {self.ollama_settings.max_retries} retries: {e}")
                    raise
    
    def get_model_info(self, model_name: str = None) -> Optional[Dict]:
        """Get detailed information about a specific model"""
        if model_name is None:
            model_name = self.ollama_settings.default_model
        
        try:
            response = requests.get(
                f"{self.ollama_settings.base_url}/api/show",
                json={"name": model_name},
                timeout=self.ollama_settings.timeout
            )
            if response.status_code == 200:
                return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get model info for {model_name}: {e}")
        
        return None
```

### Response Caching System

**LLM Response Cache (`core/llm_cache.py`)**
```python
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Any

class LLMCache:
    def __init__(self, cache_db: str = None, ttl_hours: int = 24):
        if cache_db is None:
            home_dir = Path.home()
            cache_dir = home_dir / ".rs" / "pa"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_db = str(cache_dir / "cache.db")
        
        self.cache_db = cache_db
        self.ttl = timedelta(hours=ttl_hours)
        self._init_cache_db()
    
    def _init_cache_db(self):
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    hash_key TEXT PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    def _generate_hash(self, prompt: str, model_name: str) -> str:
        content = f"{model_name}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cached_response(self, prompt: str, model_name: str) -> Optional[str]:
        hash_key = self._generate_hash(prompt, model_name)
        cutoff_time = datetime.now() - self.ttl
        
        with sqlite3.connect(self.cache_db) as conn:
            cursor = conn.execute(
                "SELECT response FROM llm_cache WHERE hash_key = ? AND created_at > ?",
                (hash_key, cutoff_time)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    
    def cache_response(self, prompt: str, response: str, model_name: str):
        hash_key = self._generate_hash(prompt, model_name)
        
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache (hash_key, prompt, response, model_name) VALUES (?, ?, ?, ?)",
                (hash_key, prompt, response, model_name)
            )
```

---

## ⚙️ Configuration Management

### Hierarchical Settings Architecture

The configuration system uses **Pydantic Settings** for type-safe, hierarchical configuration management with environment variable support, validation, and computed properties.

**Settings Import and Usage**
```python
from core.settings import get_settings, DatabaseSettings, OllamaSettings

# Get global settings instance (singleton)
settings = get_settings()

# Access nested configuration groups
db_url = settings.database.effective_url
ollama_endpoint = settings.ollama.base_url
log_level = settings.logging.level

# Use settings in managers
db_manager = DatabaseManager(settings.database)
llm_manager = LLMManager(settings.ollama)
```

### Configuration Groups

**Database Settings (`DatabaseSettings`)**
- `url`: Optional explicit database URL (defaults to computed path)
- `dev_mode`: Enable development mode (uses project directory)
- `backup_count`: Number of backups to retain (1-50)
- `backup_before_migration`: Create backup before migrations
- `pool_size`, `max_overflow`, `pool_timeout`: Connection pool configuration
- **Computed Properties**:
  - `effective_url`: Final database URL based on dev_mode
  - `backup_directory`: Backup storage path

**Ollama Settings (`OllamaSettings`)**
- `host`, `port`: Ollama service connection details
- `default_model`: Default LLM model (validated format)
- `temperature`, `max_tokens`: Model generation parameters
- `timeout`, `max_retries`: Request handling configuration
- `health_check_interval`: Health monitoring frequency
- **Computed Properties**:
  - `base_url`: Full Ollama API endpoint URL

**Logging Settings (`LoggingSettings`)**
- `level`: Application logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- `log_to_file`, `log_to_console`, `log_to_database`: Output destinations
- `log_file_max_size`, `log_file_backup_count`: File rotation settings
- `colored_console`: Enable colored console output
- `database_log_retention_days`: Database log cleanup period
- **Computed Properties**:
  - `log_directory`: Log storage path (dev vs production)

**Security Settings (`SecuritySettings`)**
- `credential_encryption`: Enable at-rest credential encryption
- `credential_key_rotation_days`: Key rotation frequency
- `token_expiration_hours`: OAuth token lifetime
- `enable_audit_logging`: Security event logging
- `max_failed_attempts`, `lockout_duration_minutes`: Account protection

**Agent Settings (`AgentSettings`)**
- `max_concurrent_tasks`: Task execution limits
- `max_execution_time_minutes`: Task timeout
- `max_retries`, `retry_backoff_seconds`: Failure handling
- `health_check_enabled`, `performance_monitoring`: Monitoring features
- `enabled_agents`: List of active agent types

**Cache Settings (`CacheSettings`)**
- `enable_llm_cache`, `llm_cache_ttl_hours`: LLM response caching
- `llm_cache_max_size_mb`: Cache size limits
- `enable_data_cache`, `data_cache_ttl_minutes`: General data caching
- **Computed Properties**:
  - `cache_directory`: Cache storage path

**UI Settings (`UISettings`)**
- `host`, `port`: Streamlit server configuration
- `theme`: UI theme (auto/light/dark)
- `page_title`: Application title
- `show_performance_metrics`: Performance display toggle
- `auto_refresh_interval`: UI refresh frequency

### Environment Variable Mapping

All settings support environment variable overrides with the **`RSPA_`** prefix:

```bash
# Database configuration
RSPA_DATABASE_URL="sqlite:///custom/path/main.db"
RSPA_DATABASE_DEV_MODE=true
RSPA_DATABASE_BACKUP_COUNT=10

# Ollama configuration  
RSPA_OLLAMA_HOST=remote-server.local
RSPA_OLLAMA_PORT=11434
RSPA_OLLAMA_DEFAULT_MODEL=llama4:latest
RSPA_OLLAMA_TEMPERATURE=0.2

# Logging configuration
RSPA_LOGGING_LEVEL=DEBUG
RSPA_LOGGING_LOG_TO_FILE=true

# Agent configuration
RSPA_AGENTS_MAX_CONCURRENT_TASKS=5
RSPA_AGENTS_ENABLED_AGENTS=["reimbursement", "task_manager"]

# UI configuration
RSPA_UI_PORT=8502
RSPA_UI_THEME=dark
```

### Configuration Validation and Type Safety

**Automatic Validation**
```python
# Type validation
settings.database.pool_size = "invalid"  # Raises ValidationError

# Range validation  
settings.ollama.temperature = 5.0  # Raises ValidationError (must be 0.0-2.0)

# Format validation
settings.ollama.default_model = "invalid-format"  # Raises ValidationError

# Enum validation
settings.logging.level = "INVALID"  # Raises ValidationError
```

**Computed Properties with Logic**
```python
# Database URL determination
@computed_field
@property
def effective_url(self) -> str:
    if self.url:  # Explicit URL takes precedence
        return self.url
    
    # Auto-generate based on dev_mode
    if self.dev_mode:
        # Development: ./data/main.db
        project_root = Path(__file__).parent.parent
        db_path = project_root / "data" / "main.db"
    else:
        # Production: ~/.rs/pa/main.db
        home_dir = Path.home()
        db_path = home_dir / ".rs" / "pa" / "main.db"
    
    return f"sqlite:///{db_path}"
```

### Configuration Loading Priority

1. **Default Values**: Built-in defaults in settings classes
2. **Environment Variables**: `RSPA_*` prefixed variables
3. **.env File**: Project-level `.env` file (if exists)
4. **Explicit Override**: Direct parameter passing to managers

### Testing and Development

**Settings Override for Tests**
```python
from core.settings import reload_settings
import os

def test_with_custom_settings():
    # Set test environment variables
    os.environ["RSPA_DATABASE_DEV_MODE"] = "true"
    os.environ["RSPA_OLLAMA_HOST"] = "test-ollama"
    
    # Reload settings to pick up changes
    settings = reload_settings()
    
    assert settings.database.dev_mode is True
    assert settings.ollama.host == "test-ollama"
```

**Configuration Debugging**
```python
settings = get_settings()

# Dump configuration (with sensitive data redacted)
config_dict = settings.model_dump_config()
logger.info(f"Application configuration: {config_dict}")

# Access individual setting groups
db_config = settings.database.model_dump()
logger.debug(f"Database configuration: {db_config}")
```

### Secure Credential Management

**Credential Storage (`core/encryption.py`)**
```python
from cryptography.fernet import Fernet
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class CredentialManager:
    def __init__(self, credentials_dir: str = "config/credentials"):
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.credentials_dir / "encryption_key.key"
        self._ensure_key_exists()
        self.cipher = Fernet(self._load_key())
    
    def _ensure_key_exists(self):
        """Generate encryption key if it doesn't exist"""
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            os.chmod(self.key_file, 0o600)  # Secure permissions
    
    def _load_key(self) -> bytes:
        """Load encryption key"""
        with open(self.key_file, 'rb') as f:
            return f.read()
    
    def store_credentials(self, service: str, credentials: Dict[str, Any]):
        """Store encrypted credentials"""
        credential_data = json.dumps(credentials).encode()
        encrypted_data = self.cipher.encrypt(credential_data)
        
        credential_file = self.credentials_dir / f"{service}_encrypted.json"
        with open(credential_file, 'wb') as f:
            f.write(encrypted_data)
        os.chmod(credential_file, 0o600)
    
    def load_credentials(self, service: str) -> Optional[Dict[str, Any]]:
        """Load and decrypt credentials"""
        credential_file = self.credentials_dir / f"{service}_encrypted.json"
        if not credential_file.exists():
            return None
        
        with open(credential_file, 'rb') as f:
            encrypted_data = f.read()
        
        try:
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logging.error(f"Failed to decrypt credentials for {service}: {e}")
            return None
```

---

## 📋 Task Scheduling System

### Background Task Management

**Task Scheduler (`core/task_scheduler.py`)**
```python
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass
from queue import PriorityQueue
import logging
from enum import IntEnum

class TaskPriority(IntEnum):
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    CRITICAL = 0

@dataclass
class ScheduledTask:
    id: str
    name: str
    agent_id: str
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    priority: TaskPriority = TaskPriority.MEDIUM
    schedule_time: datetime = None
    recurring: bool = False
    interval_minutes: Optional[int] = None
    max_retries: int = 3
    retry_count: int = 0
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.schedule_time is None:
            self.schedule_time = datetime.now()
    
    def __lt__(self, other):
        # For priority queue comparison
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.schedule_time < other.schedule_time

class TaskScheduler:
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.task_queue = PriorityQueue()
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.worker_threads = []
        self.shutdown_event = threading.Event()
        self.logger = logging.getLogger(__name__)
        self._start_workers()
        self._start_scheduler()
    
    def schedule_task(self, task: ScheduledTask):
        """Schedule a task for execution"""
        self.scheduled_tasks[task.id] = task
        self.task_queue.put((task.priority, task.schedule_time, task))
        self.logger.info(f"Scheduled task {task.name} for {task.schedule_time}")
    
    def schedule_recurring_task(self, task: ScheduledTask, interval_minutes: int):
        """Schedule a recurring task"""
        task.recurring = True
        task.interval_minutes = interval_minutes
        self.schedule_task(task)
    
    def cancel_task(self, task_id: str):
        """Cancel a scheduled task"""
        if task_id in self.scheduled_tasks:
            del self.scheduled_tasks[task_id]
            self.logger.info(f"Cancelled task {task_id}")
    
    def _start_workers(self):
        """Start worker threads"""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f"TaskWorker-{i}")
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
    
    def _start_scheduler(self):
        """Start the main scheduler thread"""
        scheduler_thread = threading.Thread(target=self._scheduler_loop, name="TaskScheduler")
        scheduler_thread.daemon = True
        scheduler_thread.start()
    
    def _worker(self):
        """Worker thread for executing tasks"""
        while not self.shutdown_event.is_set():
            try:
                _, _, task = self.task_queue.get(timeout=1)
                if task.schedule_time <= datetime.now():
                    self._execute_task(task)
                else:
                    # Put task back in queue if not ready
                    self.task_queue.put((task.priority, task.schedule_time, task))
                self.task_queue.task_done()
            except Exception as e:
                if not self.shutdown_event.is_set():
                    self.logger.error(f"Worker error: {e}")
    
    def _execute_task(self, task: ScheduledTask):
        """Execute a single task"""
        try:
            self.logger.info(f"Executing task: {task.name}")
            result = task.function(*task.args, **task.kwargs)
            
            # Handle recurring tasks
            if task.recurring and task.interval_minutes:
                next_run = datetime.now() + timedelta(minutes=task.interval_minutes)
                next_task = ScheduledTask(
                    id=f"{task.id}_{int(next_run.timestamp())}",
                    name=task.name,
                    agent_id=task.agent_id,
                    function=task.function,
                    args=task.args,
                    kwargs=task.kwargs,
                    priority=task.priority,
                    schedule_time=next_run,
                    recurring=True,
                    interval_minutes=task.interval_minutes,
                    max_retries=task.max_retries
                )
                self.schedule_task(next_task)
            
            self.logger.info(f"Completed task: {task.name}")
            
        except Exception as e:
            self.logger.error(f"Task {task.name} failed: {e}")
            self._handle_task_failure(task, e)
    
    def _handle_task_failure(self, task: ScheduledTask, error: Exception):
        """Handle task execution failure"""
        task.retry_count += 1
        
        if task.retry_count < task.max_retries:
            # Reschedule with exponential backoff
            delay_minutes = 2 ** task.retry_count
            retry_time = datetime.now() + timedelta(minutes=delay_minutes)
            task.schedule_time = retry_time
            self.task_queue.put((task.priority, task.schedule_time, task))
            self.logger.info(f"Retrying task {task.name} in {delay_minutes} minutes")
        else:
            self.logger.error(f"Task {task.name} failed permanently after {task.max_retries} retries")
    
    def shutdown(self):
        """Shutdown the task scheduler"""
        self.shutdown_event.set()
        for worker in self.worker_threads:
            worker.join(timeout=5)
```

---

## 🚢 Build and Deployment

### PyInstaller Configuration

**Standalone Build Script (`scripts/build_standalone.py`)**
```python
import PyInstaller.__main__
import platform
import os
from pathlib import Path

def build_standalone():
    """Build standalone executable with PyInstaller"""
    
    # Common options
    options = [
        'main.py',
        '--name=RS_Personal_Assistant',
        '--onedir',  # One directory with dependencies
        '--windowed' if platform.system() == 'Windows' else '--console',
        '--noconfirm',
        '--clean',
        
        # Include data files
        '--add-data=config:config',
        '--add-data=ui/styles:ui/styles',
        '--add-data=agents/*/config.yaml:agents',
        
        # Hidden imports
        '--hidden-import=langchain_ollama',
        '--hidden-import=streamlit',
        '--hidden-import=sqlalchemy',
        '--hidden-import=alembic',
        '--hidden-import=cryptography',
        
        # Exclude unnecessary modules
        '--exclude-module=matplotlib',
        '--exclude-module=pandas.plotting',
        '--exclude-module=IPython',
        
        # Output directory
        '--distpath=dist',
        '--workpath=build',
    ]
    
    # Platform-specific options
    if platform.system() == 'Windows':
        options.extend([
            '--icon=assets/icon.ico',
            '--version-file=version_info.txt'
        ])
    elif platform.system() == 'Darwin':
        options.extend([
            '--icon=assets/icon.icns',
            '--osx-bundle-identifier=com.roostership.rspa'
        ])
    
    # Run PyInstaller
    PyInstaller.__main__.run(options)
    
    print(f"Build completed for {platform.system()}")
    print(f"Executable location: {Path('dist/RS_Personal_Assistant').absolute()}")

if __name__ == "__main__":
    build_standalone()
```

### Ollama Installation and Configuration

**Installing Ollama**

Ollama must be installed separately as a desktop application. It is not bundled with RS Personal Assistant.

**Installation Guide:**
- **Official Download Page**: https://www.ollama.com/download
- **macOS/Linux**: `curl -fsSL https://ollama.com/install.sh | sh`
- **Windows**: Download and run the installer from the official website

**Post-Installation Setup:**
```bash
# Start Ollama service
ollama serve

# Pull the required Llama 4 Maverick model
ollama pull llama4:maverick

# Verify installation
ollama list
```

**System Requirements:**
- **RAM**: Minimum 16GB recommended
- **Storage**: 12GB+ for models
- **GPU**: Optional but recommended (NVIDIA CUDA 5.0+ or AMD ROCm)

**Integration Configuration:**

The RS Personal Assistant connects to Ollama via its local API:
- Default endpoint: `http://localhost:11434`
- Configure in `config/settings.yaml` or via environment variable `RSPA_OLLAMA_HOST`
- Health checks automatically verify Ollama availability on startup

---

## 📊 Performance Monitoring

### System Performance Tracking

**Performance Monitor (`core/performance_monitor.py`)**
```python
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sqlite3
import threading

@dataclass
class PerformanceMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    active_tasks: int
    llm_response_time_ms: Optional[float] = None
    database_query_time_ms: Optional[float] = None

class PerformanceMonitor:
    def __init__(self, db_path: str = None):
        if db_path is None:
            home_dir = Path.home()
            data_dir = home_dir / ".rs" / "pa"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "performance.db")
        
        self.db_path = db_path
        self.monitoring_active = False
        self.monitoring_thread = None
        self.collection_interval = 60  # seconds
        self._init_db()
    
    def _init_db(self):
        """Initialize performance metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    timestamp DATETIME,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    disk_usage_percent REAL,
                    active_tasks INTEGER,
                    llm_response_time_ms REAL,
                    database_query_time_ms REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON performance_metrics(timestamp)
            """)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop, 
                daemon=True
            )
            self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                time.sleep(self.collection_interval)
            except Exception as e:
                logging.error(f"Performance monitoring error: {e}")
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics"""
        # CPU and memory
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # Disk usage (for data directory)
        disk = psutil.disk_usage("data/")
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            disk_usage_percent=(disk.used / disk.total) * 100,
            active_tasks=self._count_active_tasks()
        )
    
    def _count_active_tasks(self) -> int:
        """Count currently active tasks"""
        # This would integrate with the task scheduler
        # For now, return a placeholder
        return 0
    
    def _store_metrics(self, metrics: PerformanceMetrics):
        """Store metrics in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_metrics 
                (timestamp, cpu_percent, memory_percent, memory_used_mb, 
                 disk_usage_percent, active_tasks, llm_response_time_ms, 
                 database_query_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp,
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.memory_used_mb,
                metrics.disk_usage_percent,
                metrics.active_tasks,
                metrics.llm_response_time_ms,
                metrics.database_query_time_ms
            ))
    
    def get_metrics_history(self, hours: int = 24) -> List[PerformanceMetrics]:
        """Get performance metrics history"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM performance_metrics 
                WHERE timestamp > ?
                ORDER BY timestamp ASC
            """, (cutoff_time,))
            
            metrics = []
            for row in cursor.fetchall():
                metrics.append(PerformanceMetrics(
                    timestamp=datetime.fromisoformat(row[0]),
                    cpu_percent=row[1],
                    memory_percent=row[2],
                    memory_used_mb=row[3],
                    disk_usage_percent=row[4],
                    active_tasks=row[5],
                    llm_response_time_ms=row[6],
                    database_query_time_ms=row[7]
                ))
            
            return metrics
```

---

## 📝 Logging System

### Centralized Logging Architecture

The logging system provides comprehensive application logging with file rotation, color formatting, and real-time UI viewing capabilities.

**Logging Manager (`core/logging_manager.py`)**
```python
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import sqlite3
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    exception: Optional[str] = None
    context: Optional[Dict] = None

class LoggingManager:
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            home_dir = Path.home()
            log_dir = home_dir / ".rs" / "pa" / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log database for UI viewing
        self.log_db = self.log_dir / "logs.db"
        self._init_log_db()
        
        # Configure root logger
        self._configure_logging()
    
    def _init_log_db(self):
        """Initialize SQLite database for log storage"""
        with sqlite3.connect(self.log_db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    level TEXT,
                    logger_name TEXT,
                    message TEXT,
                    module TEXT,
                    function TEXT,
                    line_number INTEGER,
                    exception TEXT,
                    context TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON logs(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_level ON logs(level)
            """)
    
    def _configure_logging(self):
        """Configure the logging system"""
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "rs_pa.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        
        # Database handler for UI
        db_handler = DatabaseLogHandler(self.log_db)
        db_handler.setFormatter(file_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(db_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(name)
    
    def query_logs(
        self, 
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 1000
    ) -> List[LogEntry]:
        """Query logs from database for UI display"""
        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if search_text:
            query += " AND (message LIKE ? OR exception LIKE ?)"
            params.extend([f"%{search_text}%", f"%{search_text}%"])
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.log_db) as conn:
            cursor = conn.execute(query, params)
            logs = []
            
            for row in cursor.fetchall():
                logs.append(LogEntry(
                    timestamp=datetime.fromisoformat(row[1]),
                    level=row[2],
                    logger_name=row[3],
                    message=row[4],
                    module=row[5],
                    function=row[6],
                    line_number=row[7],
                    exception=row[8],
                    context=json.loads(row[9]) if row[9] else None
                ))
        
        return logs

class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)

class DatabaseLogHandler(logging.Handler):
    """Custom handler to store logs in SQLite database"""
    
    def __init__(self, db_path: str):
        super().__init__()
        self.db_path = db_path
    
    def emit(self, record):
        """Store log record in database"""
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'logger_name': record.name,
                'message': self.format(record),
                'module': record.module,
                'function': record.funcName,
                'line_number': record.lineno,
                'exception': None,
                'context': None
            }
            
            if record.exc_info:
                log_entry['exception'] = self.format(record)
            
            # Add any extra context
            if hasattr(record, 'context'):
                log_entry['context'] = json.dumps(record.context)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO logs 
                    (timestamp, level, logger_name, message, module, 
                     function, line_number, exception, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry['timestamp'],
                    log_entry['level'],
                    log_entry['logger_name'],
                    log_entry['message'],
                    log_entry['module'],
                    log_entry['function'],
                    log_entry['line_number'],
                    log_entry['exception'],
                    log_entry['context']
                ))
        except Exception:
            self.handleError(record)
```

### Log Viewer UI Component

**Log Viewer Component (`ui/components/log_viewer.py`)**
```python
import streamlit as st
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from core.logging_manager import LoggingManager, LogLevel, LogEntry

class LogViewerComponent:
    def __init__(self, logging_manager: LoggingManager):
        self.logging_manager = logging_manager
    
    def render(self):
        """Render the log viewer component"""
        st.header("📋 System Logs")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            level_filter = st.selectbox(
                "Log Level",
                options=["All"] + [level.value for level in LogLevel],
                key="log_level_filter"
            )
        
        with col2:
            time_range = st.selectbox(
                "Time Range",
                options=["Last Hour", "Last 24 Hours", "Last 7 Days", "Custom"],
                key="log_time_range"
            )
        
        with col3:
            if time_range == "Custom":
                start_date = st.date_input("Start Date", key="log_start_date")
                start_time = st.time_input("Start Time", key="log_start_time")
            else:
                start_date = start_time = None
        
        with col4:
            search_text = st.text_input(
                "Search Logs",
                placeholder="Enter search text...",
                key="log_search"
            )
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("Auto-refresh (5s)", key="log_auto_refresh")
        
        if auto_refresh:
            st.empty()  # Placeholder for auto-refresh
        
        # Determine time range
        end_time = datetime.now()
        if time_range == "Last Hour":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "Last 24 Hours":
            start_time = end_time - timedelta(days=1)
        elif time_range == "Last 7 Days":
            start_time = end_time - timedelta(days=7)
        elif time_range == "Custom" and start_date and start_time:
            start_time = datetime.combine(start_date, start_time)
        else:
            start_time = None
        
        # Query logs
        logs = self.logging_manager.query_logs(
            level=level_filter if level_filter != "All" else None,
            start_time=start_time,
            end_time=end_time,
            search_text=search_text if search_text else None,
            limit=500
        )
        
        # Display logs
        if logs:
            # Convert to DataFrame for better display
            df = pd.DataFrame([
                {
                    "Time": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Level": log.level,
                    "Logger": log.logger_name,
                    "Message": log.message[:100] + "..." if len(log.message) > 100 else log.message,
                    "Module": f"{log.module}:{log.line_number}"
                }
                for log in logs
            ])
            
            # Apply color styling based on level
            def highlight_level(row):
                colors = {
                    'DEBUG': 'background-color: #e3f2fd',
                    'INFO': 'background-color: #e8f5e9',
                    'WARNING': 'background-color: #fff3e0',
                    'ERROR': 'background-color: #ffebee',
                    'CRITICAL': 'background-color: #f3e5f5'
                }
                return [colors.get(row['Level'], '')] * len(row)
            
            styled_df = df.style.apply(highlight_level, axis=1)
            
            # Display with expandable details
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=400
            )
            
            # Show detailed view for selected log
            st.subheader("Log Details")
            selected_index = st.number_input(
                "Select log entry (by row number)",
                min_value=0,
                max_value=len(logs)-1,
                value=0,
                key="log_detail_index"
            )
            
            if 0 <= selected_index < len(logs):
                selected_log = logs[selected_index]
                
                # Display detailed information
                detail_cols = st.columns(2)
                
                with detail_cols[0]:
                    st.text(f"Timestamp: {selected_log.timestamp}")
                    st.text(f"Level: {selected_log.level}")
                    st.text(f"Logger: {selected_log.logger_name}")
                    st.text(f"Module: {selected_log.module}")
                    st.text(f"Function: {selected_log.function}")
                    st.text(f"Line: {selected_log.line_number}")
                
                with detail_cols[1]:
                    st.text_area("Message", selected_log.message, height=100)
                    
                    if selected_log.exception:
                        st.text_area("Exception", selected_log.exception, height=100)
                    
                    if selected_log.context:
                        st.json(selected_log.context)
        else:
            st.info("No logs found matching the current filters.")
        
        # Export functionality
        if st.button("Export Logs", key="export_logs"):
            if logs:
                export_data = "\n".join([
                    f"{log.timestamp} | {log.level} | {log.logger_name} | {log.message}"
                    for log in logs
                ])
                st.download_button(
                    label="Download Log Export",
                    data=export_data,
                    file_name=f"rs_pa_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

# Usage in main UI
def show_log_viewer(logging_manager: LoggingManager):
    """Show log viewer in a modal dialog"""
    with st.expander("System Logs", expanded=True):
        log_viewer = LogViewerComponent(logging_manager)
        log_viewer.render()
```

This framework design provides a solid foundation for building the RS Personal Assistant system with robust data management, efficient LLM integration, secure configuration handling, comprehensive monitoring capabilities, and a powerful logging system with UI visualization.
