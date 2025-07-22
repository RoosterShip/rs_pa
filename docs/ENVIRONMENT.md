# Environment Variables Configuration

This document lists all environment variables used in the RS Personal Agent project, organized by configuration group. The system uses **hierarchical settings** with pydantic-settings for type-safe configuration management.

## Configuration Groups Overview

Environment variables are organized into logical groups with the `RSPA_` prefix followed by the group name:

- **Application**: `RSPA_APP_*` - Core application settings
- **Database**: `RSPA_DATABASE_*` - SQLite database configuration (no connection pooling needed)
- **Ollama**: `RSPA_OLLAMA_*` - LLM service configuration
- **Logging**: `RSPA_LOGGING_*` - Logging system configuration
- **Security**: `RSPA_SECURITY_*` - Security and credential management
- **Cache**: `RSPA_CACHE_*` - Caching system configuration
- **UI**: `RSPA_UI_*` - User interface settings

---

## 🚀 Application Settings (Phase 1: Task 1.1)

### `RSPA_APP_NAME`
**Default**: `RS Personal Agent`  
**Type**: String  
**Purpose**: Application name displayed in UI and logs.  
**First Used**: Task 1.1 - Basic PySide6 window setup

### `RSPA_APP_VERSION`
**Default**: `0.1.0`  
**Type**: String (semantic version)  
**Purpose**: Application version string.  
**First Used**: Task 1.1 - Basic PySide6 window setup

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

## 🗄️ Database Settings (Phase 1: Task 1.3)

### `RSPA_DATABASE_URL`
**Default**: Auto-computed based on dev_mode and Qt standard paths  
**Type**: String (SQLAlchemy connection URL)  
**Purpose**: Override the default database connection string.

**Default Locations**:
- **Development Mode** (`RSPA_DATABASE_DEV_MODE=true`): `sqlite:///./data/main.db`
- **Production Mode** (uses Qt AppLocalDataLocation):
  - **Windows**: `sqlite:///%LOCALAPPDATA%\Roostership\RSPersonalAgent\main.db`
  - **macOS**: `sqlite:///~/Library/Application Support/RSPersonalAgent/main.db`
  - **Linux**: `sqlite:///~/.local/share/RSPersonalAgent/main.db`

**Usage**:
```bash
# Custom SQLite path
export RSPA_DATABASE_URL="sqlite:///path/to/custom.db"

# PostgreSQL for production
export RSPA_DATABASE_URL="postgresql://user:password@localhost/rspa"

# MySQL example
export RSPA_DATABASE_URL="mysql://user:password@localhost/rspa"
```

**Note**: Qt standard paths are automatically determined at runtime and require proper QApplication setup with organization name "Roostership" and application name "RSPersonalAgent".

### `RSPA_DATABASE_DEV_MODE`
**Default**: `false`  
**Type**: Boolean  
**Purpose**: Enable development mode for database paths and debugging.

**Usage**:
```bash
export RSPA_DATABASE_DEV_MODE=true
```

**Effects**:
- Database stored in `./data/main.db` instead of Qt standard paths
- Enables additional database debugging  
- Uses project directory for all data storage instead of:
  - **Windows**: `%LOCALAPPDATA%\Roostership\RSPersonalAgent\`
  - **macOS**: `~/Library/Application Support/RSPersonalAgent/`
  - **Linux**: `~/.local/share/RSPersonalAgent/`

### `RSPA_DATABASE_BACKUP_COUNT`
**Default**: `5`  
**Type**: Integer (1-50)  
**Purpose**: Number of database backup files to retain.

### `RSPA_DATABASE_BACKUP_BEFORE_MIGRATION`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Create database backup before running migrations.

**Note**: Connection pool settings (POOL_SIZE, MAX_OVERFLOW, POOL_TIMEOUT) are not applicable to SQLite and have been removed from the configuration. SQLite uses file-based access with internal locking mechanisms instead of connection pools.

---

## 🤖 Ollama LLM Settings (Phase 2: Task 2.2, Enhanced Phase 3: Task 3.1)

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
export RSPA_OLLAMA_DEFAULT_MODEL=llama4:maverick  # General use, 17B params, 128 experts
export RSPA_OLLAMA_DEFAULT_MODEL=llama4:scout     # Large context, 10M tokens, 16 experts
export RSPA_OLLAMA_DEFAULT_MODEL=llama4:behemoth  # Most powerful (when available)
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

## 📋 Logging Settings (Phase 1+: Throughout Implementation)

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


### `RSPA_LOGGING_LOG_TO_CONSOLE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable console logging output.


### `RSPA_LOGGING_LOG_TO_DATABASE`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Store logs in database for UI log viewer.


---

## 🔒 Security Settings (Phase 2: Task 2.2 - OAuth/Credentials)

### `RSPA_SECURITY_CREDENTIAL_ENCRYPTION`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable credential encryption at rest.

### `RSPA_SECURITY_CREDENTIAL_KEY_ROTATION_DAYS`
**Default**: `90`  
**Type**: Integer (1-365)  
**Purpose**: Days between credential key rotations.

**Note**: `RSPA_SECURITY_TOKEN_EXPIRATION_HOURS` has been removed as OAuth token expiration is managed by service providers (Gmail, etc.) and cannot be configured locally.

### `RSPA_SECURITY_ENABLE_AUDIT_LOGGING`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable security audit logging.

**Note**: `RSPA_SECURITY_MAX_FAILED_ATTEMPTS` and `RSPA_SECURITY_LOCKOUT_DURATION_MINUTES` have been removed as they are not applicable to a standalone desktop application with no authentication system.

---


## 💾 Cache Settings (Phase 3: Task 3.1 - LLM Response Caching)

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

## 🎨 Native Desktop UI Settings (Phase 4: Task 4.1 - Advanced Styling)

### `RSPA_UI_WINDOW_WIDTH`
**Default**: `1200`  
**Type**: Integer (800-3840)  
**Purpose**: Default main window width in pixels.

**Usage**:
```bash
export RSPA_UI_WINDOW_WIDTH=1400  # Larger initial window
```

### `RSPA_UI_WINDOW_HEIGHT`
**Default**: `800`  
**Type**: Integer (600-2160)  
**Purpose**: Default main window height in pixels.

### `RSPA_UI_THEME`
**Default**: `auto`  
**Type**: String (auto/light/dark)  
**Purpose**: Native desktop theme selection (follows OS theme when auto).

### `RSPA_UI_PAGE_TITLE`
**Default**: `RS Personal Agent`  
**Type**: String  
**Purpose**: Main application window title.


### `RSPA_UI_MINIMIZE_TO_TRAY`
**Default**: `true`  
**Type**: Boolean  
**Purpose**: Enable minimizing application to system tray.


### `RSPA_UI_FONT_SIZE`
**Default**: `10`  
**Type**: Integer (8-18)  
**Purpose**: Base application font size in points.

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
   - Name it "RS Personal Agent"
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