# Environment Variables Configuration

This document lists all environment variables used in the RS Personal Assistant project, organized by configuration group. The system uses **hierarchical settings** with pydantic-settings for type-safe configuration management.

## Configuration Groups Overview

Environment variables are organized into logical groups with the `RSPA_` prefix followed by the group name:

- **Application**: `RSPA_APP_*` - Core application settings
- **Database**: `RSPA_DATABASE_*` - Database configuration and connection pooling
- **Ollama**: `RSPA_OLLAMA_*` - LLM service configuration
- **Logging**: `RSPA_LOGGING_*` - Logging system configuration
- **Security**: `RSPA_SECURITY_*` - Security and credential management
- **Agents**: `RSPA_AGENTS_*` - Agent system configuration
- **Cache**: `RSPA_CACHE_*` - Caching system configuration
- **UI**: `RSPA_UI_*` - User interface settings

---

## 🚀 Application Settings

### `RSPA_APP_NAME`
**Default**: `RS Personal Assistant`  
**Type**: String  
**Purpose**: Application name displayed in UI and logs.

### `RSPA_APP_VERSION`
**Default**: `0.1.0`  
**Type**: String (semantic version)  
**Purpose**: Application version string.

### `RSPA_DEBUG`
**Default**: `false`  
**Type**: Boolean  
**Purpose**: Enable debug mode for additional logging and development features.

**Usage**:
```bash
export RSPA_DEBUG=true
```

**⚠️ Warning**: Debug mode in production will trigger warnings.

### `RSPA_INTEGRATION_TESTS`
**Default**: `false`  
**Type**: Boolean  
**Purpose**: Enable integration tests requiring external services (Ollama, Gmail).

**Usage**:
```bash
export RSPA_INTEGRATION_TESTS=true
pytest tests/  # Runs all tests including integration tests
```

---

## 🗄️ Database Settings

### `RSPA_DATABASE_URL`
**Default**: Auto-computed based on dev_mode  
**Type**: String (SQLAlchemy connection URL)  
**Purpose**: Override the default database connection string.

**Usage**:
```bash
# SQLite (default behavior)
export RSPA_DATABASE_URL="sqlite:///path/to/custom.db"

# PostgreSQL for production
export RSPA_DATABASE_URL="postgresql://user:password@localhost/rspa"

# MySQL example
export RSPA_DATABASE_URL="mysql://user:password@localhost/rspa"
```

### `RSPA_DATABASE_DEV_MODE`
**Default**: `false`  
**Type**: Boolean  
**Purpose**: Enable development mode for database paths and debugging.

**Usage**:
```bash
export RSPA_DATABASE_DEV_MODE=true
```

**Effects**:
- Database stored in `./data/main.db` instead of `~/.rs/pa/main.db`
- Enables additional database debugging
- Uses project directory for all data storage

### `RSPA_DATABASE_BACKUP_COUNT`
**Default**: `5`  
**Type**: Integer (1-50)  
**Purpose**: Number of database backup files to retain.

### `RSPA_DATABASE_BACKUP_BEFORE_MIGRATION`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Create database backup before running migrations.

### `RSPA_DATABASE_POOL_SIZE`
**Default**: `5`  
**Type**: Integer (1-20)  
**Purpose**: Database connection pool size.

### `RSPA_DATABASE_MAX_OVERFLOW`
**Default**: `10`  
**Type**: Integer (0-50)  
**Purpose**: Maximum database connection overflow.

### `RSPA_DATABASE_POOL_TIMEOUT`
**Default**: `30`  
**Type**: Integer (5-300)  
**Purpose**: Database connection pool timeout in seconds.

---

## 🤖 Ollama LLM Settings

### `RSPA_OLLAMA_HOST`
**Default**: `localhost`  
**Type**: String (hostname or IP)  
**Purpose**: Hostname where Ollama service is running.

**Usage**:
```bash
# Local Ollama
export RSPA_OLLAMA_HOST=localhost

# Remote Ollama server
export RSPA_OLLAMA_HOST=192.168.1.100

# Docker container name
export RSPA_OLLAMA_HOST=ollama-container
```

### `RSPA_OLLAMA_PORT`
**Default**: `11434`  
**Type**: Integer (1-65535)  
**Purpose**: Port where Ollama service is listening.

### `RSPA_OLLAMA_DEFAULT_MODEL`
**Default**: `llama4:maverick`  
**Type**: String (format: `model:tag`)  
**Purpose**: Default LLM model to use for generation.

**Usage**:
```bash
export RSPA_OLLAMA_DEFAULT_MODEL=llama4:latest
export RSPA_OLLAMA_DEFAULT_MODEL=mistral:7b
```

**Validation**: Must be in `model:tag` format.

### `RSPA_OLLAMA_TEMPERATURE`
**Default**: `0.1`  
**Type**: Float (0.0-2.0)  
**Purpose**: Default temperature for LLM responses (creativity level).

### `RSPA_OLLAMA_MAX_TOKENS`
**Default**: `null` (unlimited)  
**Type**: Integer (positive) or null  
**Purpose**: Maximum tokens for LLM responses.

### `RSPA_OLLAMA_TIMEOUT`
**Default**: `30`  
**Type**: Integer (5-300)  
**Purpose**: Request timeout in seconds.

### `RSPA_OLLAMA_MAX_RETRIES`
**Default**: `3`  
**Type**: Integer (0-10)  
**Purpose**: Maximum number of retry attempts for failed requests.

### `RSPA_OLLAMA_HEALTH_CHECK_INTERVAL`
**Default**: `60`  
**Type**: Integer (10-600)  
**Purpose**: Health check interval in seconds.

---

## 📋 Logging Settings

### `RSPA_LOGGING_LEVEL`
**Default**: `INFO`  
**Type**: String (DEBUG/INFO/WARNING/ERROR/CRITICAL)  
**Purpose**: Application logging level.

**Usage**:
```bash
export RSPA_LOGGING_LEVEL=DEBUG   # Development
export RSPA_LOGGING_LEVEL=INFO    # Production
export RSPA_LOGGING_LEVEL=ERROR   # Minimal logging
```

### `RSPA_LOGGING_LOG_TO_FILE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable logging to rotating log files.

### `RSPA_LOGGING_LOG_FILE_MAX_SIZE`
**Default**: `10485760` (10MB)  
**Type**: Integer (bytes)  
**Purpose**: Maximum log file size before rotation.

### `RSPA_LOGGING_LOG_FILE_BACKUP_COUNT`
**Default**: `5`  
**Type**: Integer (1-50)  
**Purpose**: Number of log file backups to retain.

### `RSPA_LOGGING_LOG_TO_CONSOLE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable console logging output.

### `RSPA_LOGGING_COLORED_CONSOLE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable colored console output.

### `RSPA_LOGGING_LOG_TO_DATABASE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Store logs in database for UI log viewer.

### `RSPA_LOGGING_DATABASE_LOG_RETENTION_DAYS`
**Default**: `30`  
**Type**: Integer (1-365)  
**Purpose**: Days to retain logs in database.

---

## 🔒 Security Settings

### `RSPA_SECURITY_CREDENTIAL_ENCRYPTION`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable credential encryption at rest.

### `RSPA_SECURITY_CREDENTIAL_KEY_ROTATION_DAYS`
**Default**: `90`  
**Type**: Integer (1-365)  
**Purpose**: Days between credential key rotations.

### `RSPA_SECURITY_TOKEN_EXPIRATION_HOURS`
**Default**: `24`  
**Type**: Integer (1-168)  
**Purpose**: OAuth token expiration time in hours.

### `RSPA_SECURITY_ENABLE_AUDIT_LOGGING`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable security audit logging.

### `RSPA_SECURITY_MAX_FAILED_ATTEMPTS`
**Default**: `5`  
**Type**: Integer (1-50)  
**Purpose**: Maximum failed authentication attempts.

### `RSPA_SECURITY_LOCKOUT_DURATION_MINUTES`
**Default**: `15`  
**Type**: Integer (1-1440)  
**Purpose**: Account lockout duration in minutes.

---

## 🤖 Agent System Settings

### `RSPA_AGENTS_MAX_CONCURRENT_TASKS`
**Default**: `3`  
**Type**: Integer (1-20)  
**Purpose**: Maximum concurrent agent tasks.

### `RSPA_AGENTS_MAX_EXECUTION_TIME_MINUTES`
**Default**: `30`  
**Type**: Integer (1-1440)  
**Purpose**: Maximum agent execution time in minutes.

### `RSPA_AGENTS_MAX_RETRIES`
**Default**: `3`  
**Type**: Integer (0-10)  
**Purpose**: Maximum retry attempts for failed agent tasks.

### `RSPA_AGENTS_RETRY_BACKOFF_SECONDS`
**Default**: `5`  
**Type**: Integer (1-300)  
**Purpose**: Backoff time between retries in seconds.

### `RSPA_AGENTS_HEALTH_CHECK_ENABLED`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable agent health monitoring.

### `RSPA_AGENTS_PERFORMANCE_MONITORING`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable agent performance monitoring.

### `RSPA_AGENTS_ENABLED_AGENTS`
**Default**: `["reimbursement"]`  
**Type**: JSON array of strings  
**Purpose**: List of enabled agent types.

**Usage**:
```bash
# Enable multiple agents
export RSPA_AGENTS_ENABLED_AGENTS='["reimbursement", "task_manager", "calendar"]'

# Enable all agents
export RSPA_AGENTS_ENABLED_AGENTS='["reimbursement", "task_manager", "calendar", "document_processor"]'
```

---

## 💾 Cache Settings

### `RSPA_CACHE_ENABLE_LLM_CACHE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable LLM response caching.

### `RSPA_CACHE_LLM_CACHE_TTL_HOURS`
**Default**: `24`  
**Type**: Integer (1-168)  
**Purpose**: LLM cache time-to-live in hours.

### `RSPA_CACHE_LLM_CACHE_MAX_SIZE_MB`
**Default**: `100`  
**Type**: Integer (10-1000)  
**Purpose**: Maximum LLM cache size in MB.

### `RSPA_CACHE_ENABLE_DATA_CACHE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable general data caching.

### `RSPA_CACHE_DATA_CACHE_TTL_MINUTES`
**Default**: `60`  
**Type**: Integer (1-1440)  
**Purpose**: Data cache time-to-live in minutes.

---

## 🎨 UI Settings

### `RSPA_UI_HOST`
**Default**: `localhost`  
**Type**: String  
**Purpose**: Streamlit server host address.

### `RSPA_UI_PORT`
**Default**: `8501`  
**Type**: Integer (1024-65535)  
**Purpose**: Streamlit server port.

**Usage**:
```bash
export RSPA_UI_PORT=8502  # Use alternate port
```

### `RSPA_UI_THEME`
**Default**: `auto`  
**Type**: String (auto/light/dark)  
**Purpose**: UI theme selection.

### `RSPA_UI_PAGE_TITLE`
**Default**: `RS Personal Assistant`  
**Type**: String  
**Purpose**: Browser page title.

### `RSPA_UI_SHOW_PERFORMANCE_METRICS`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Display performance metrics in UI.

### `RSPA_UI_AUTO_REFRESH_INTERVAL`
**Default**: `30`  
**Type**: Integer (5-300)  
**Purpose**: Auto-refresh interval in seconds.

---

## Third-Party Service Configuration

### Gmail API Configuration

The Gmail API requires OAuth2 authentication. Environment variables are not used directly; instead, credentials are stored securely in the application's credential manager.

**Setup Process**:

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Note the project ID

2. **Enable Gmail API**:
   - In the Cloud Console, go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

3. **Create OAuth2 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Name it "RS Personal Assistant"
   - Download the credentials as `credentials.json`

4. **Install Credentials**:
   - Place `credentials.json` in `config/credentials/`
   - The application will handle the OAuth2 flow on first run
   - Tokens are stored encrypted in the credential manager

**Required OAuth2 Scopes**:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.labels`
- `https://www.googleapis.com/auth/gmail.modify`

---

## Windows-Specific Variables

### `USERPROFILE`
**Type**: String (System-provided)  
**Purpose**: Windows equivalent of `$HOME`, used to determine user directory paths.

**Note**: This is automatically set by Windows and should not be modified.

---

## Docker Environment Variables

When running in Docker, additional environment variables may be needed:

### `OLLAMA_HOST`
**Purpose**: Override Ollama host for container networking
```bash
docker run -e OLLAMA_HOST=host.docker.internal ...
```

### `PYTHONUNBUFFERED`
**Default**: `1`  
**Purpose**: Ensures Python output is not buffered in Docker logs
```bash
docker run -e PYTHONUNBUFFERED=1 ...
```

---

## Development Tools Configuration

### `UV_CACHE_DIR`
**Default**: System default  
**Purpose**: Override UV package manager cache location
```bash
export UV_CACHE_DIR=$HOME/.cache/uv
```

### `BLACK_CACHE_DIR`
**Default**: System default  
**Purpose**: Override Black formatter cache location
```bash
export BLACK_CACHE_DIR=$HOME/.cache/black
```

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use `.env.example`** as a template without sensitive values
3. **Store secrets** in the application's credential manager, not environment variables
4. **Use different values** for development and production
5. **Rotate credentials** regularly

## Example `.env.example` File

```bash
# Development Mode
RSPA_DEV_MODE=false

# Ollama Configuration
RSPA_OLLAMA_HOST=localhost
RSPA_OLLAMA_PORT=11434

# Logging
RSPA_LOG_LEVEL=INFO

# Database (optional - defaults are usually fine)
# RSPA_DATABASE_URL=sqlite:///path/to/database.db

# Testing
# INTEGRATION_TESTS=1
```

## Loading Environment Variables

### For Development
```bash
# Create .env from template
cp .env.example .env

# Edit .env with your values
nano .env

# Load in shell (bash/zsh)
source .env

# Or use direnv for automatic loading
direnv allow
```

### For Production
Set environment variables in your deployment platform:
- **Systemd**: Use `Environment=` in service files
- **Docker**: Use `-e` flags or env files
- **Cloud Platforms**: Use platform-specific environment configuration