# RS Personal Agent (rs_pa)

🤖 **A Privacy-First, Local AI-Powered Personal Agent Platform**

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Design Phase](https://img.shields.io/badge/Status-Design%20Phase-orange)](TASKS.md)

</div>

## 📋 Project Overview

RS Personal Agent (rs_pa) is an innovative, modular AI platform designed to automate personal productivity tasks while maintaining complete privacy. Unlike cloud-based assistants, all AI processing happens locally on your machine using Ollama and Meta's Llama 4 models.

### 🎯 Vision

Create a powerful personal agent that:
- **Respects Privacy**: 100% local AI processing, no data leaves your machine
- **Adapts to You**: Extensible agent system that grows with your needs
- **Works Everywhere**: Cross-platform standalone application
- **Stays Modern**: Beautiful, responsive UI with real-time monitoring

### 🏗️ Architecture Highlights

- **Agent-Based Design**: Specialized AI agents for different tasks
- **Modern Tech Stack**: Python, LangChain, PySide6, SQLAlchemy
- **Robust Infrastructure**: Database migrations, task scheduling, performance monitoring
- **Enterprise Patterns**: Clean architecture, dependency injection, comprehensive logging

### 📊 Project Status

**Current Phase**: Design & Planning  
**Estimated Completion**: 210 hours across 7 phases  
**Documentation**: Complete system design available

See [TASKS.md](TASKS.md) for detailed implementation roadmap.

## ✨ Key Features

### 🔐 Privacy & Security
- **100% Local Processing**: All AI computations run on your machine
- **No Cloud Dependencies**: Works offline (except optional Gmail integration)
- **Encrypted Storage**: Sensitive data encrypted using industry standards
- **Secure Credentials**: OAuth2 for external services, local credential management

### 🤖 Intelligent Agents
- **Reimbursement Agent**: Automatically processes emails, detects bills, extracts reimbursement data
- **Extensible Framework**: Easy to add custom agents for your specific needs
- **Smart Scheduling**: Agents run on customizable schedules
- **Performance Tracking**: Monitor agent efficiency and resource usage

### 💻 User Experience  
- **Modern Dashboard**: Clean, intuitive native desktop interface built with PySide6
- **Real-time Monitoring**: Live agent status, task progress, and system health
- **Dark/Light Themes**: Comfortable viewing in any environment
- **Native Desktop**: Cross-platform native application with OS integration

### 🛠️ Technical Excellence
- **Robust Architecture**: Clean code, SOLID principles, comprehensive testing
- **Database Migrations**: Version-controlled schema changes with Alembic
- **Performance Optimized**: Efficient caching, connection pooling, async operations
- **Cross-Platform**: Runs on Windows, macOS, and Linux
- **Standalone Packaging**: Single executable distribution with PyInstaller/Nuitka

## 📦 System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM**: 8GB (16GB recommended for optimal performance)
- **Storage**: 15GB free space (for models and data)
- **CPU**: 4 cores (8 cores recommended)
- **Python**: 3.9 or higher

### GPU Support (Optional)
- NVIDIA GPU with CUDA 11.8+ for accelerated inference
- AMD GPU with ROCm 5.6+ (Linux only)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ 
- [UV](https://github.com/astral-sh/uv) (Fast Python package manager)
- Git

### 0. Install UV (Python Package Manager)

UV is a blazing-fast Python package installer and resolver, written in Rust.

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv
```

### 1. Install Ollama

#### macOS
```bash
# Using Homebrew
brew install ollama

# Or download from https://ollama.ai/
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
brew services start ollama
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
sudo systemctl start ollama
```

#### Windows
Download and install from [https://ollama.ai/](https://ollama.ai/)

### 2. Install Llama 4 Model

```bash
# Pull Llama 4 Maverick (recommended for general use)
ollama pull llama4:maverick

# Alternative Llama 4 models:
# ollama pull llama4:scout    # 17B params, 16 experts, 10M context window
# ollama pull llama4:behemoth # 288B params (when available)

# Verify installation
ollama list
```

### 3. Set Up RS Personal Agent

```bash
# Clone the repository
git clone <repository-url>
cd rs_pa

# Create virtual environment with UV
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies with UV (10x faster than pip!)
uv pip install -r requirements.txt

# For development, install with dev dependencies
uv pip install -r requirements-dev.txt

# Set development mode (uses local data directory)
export RSPA_DEV_MODE=true  # macOS/Linux
set RSPA_DEV_MODE=true     # Windows

# Initialize database (automatic on first run)
python -m alembic upgrade head

# Run the native desktop application
python main.py
```

The application will:
1. Automatically check Ollama installation
2. Verify the Llama 4 model availability
3. Initialize the database if needed
4. Open the native desktop dashboard

### 4. Configure Gmail (For Reimbursement Agent)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials
5. Download `credentials.json` to `config/credentials/`
6. First run will prompt for Gmail authorization

## 📁 Project Structure

```
rs_pa/
├── main.py                     # Application entry point
├── agents/                     # Agent implementations
│   ├── base_agent.py          # Abstract base agent
│   └── reimbursement/         # Reimbursement agent
├── core/                      # Core infrastructure
│   ├── database.py            # SQLAlchemy models & session
│   ├── llm_manager.py         # Ollama integration
│   └── agent_manager.py       # Agent lifecycle management
├── ui/                        # PySide6 native desktop UI
│   ├── main_window.py         # Main desktop window
│   ├── views/                 # UI view components
│   ├── models/                # Qt data models
│   └── widgets/               # Custom Qt widgets
├── models/                    # SQLAlchemy database models
├── alembic/                   # Database migrations
└── config/                    # Configuration files
```

## 🤖 Available Agents

### Reimbursement Agent
- Scans Gmail for unprocessed emails
- Detects bills and reimbursable expenses using AI
- Extracts payment and expense information
- Generates comprehensive reimbursement reports
- Marks emails as processed with appropriate labels

## 📖 Documentation

- **[DESIGN.md](DESIGN.md)** - Complete system design overview
- **[DESIGN_FRAMEWORK.md](DESIGN_FRAMEWORK.md)** - Framework architecture details
- **[Agent Design](docs/design/agents/DESIGN.md)** - Agent development guide
- **[DESIGN_UI.md](DESIGN_UI.md)** - User interface design system
- **[TASKS.md](TASKS.md)** - Implementation task breakdown

## 🔧 Development

### Adding New Agents

1. Create agent directory in `agents/`
2. Inherit from `BaseAgent` class
3. Implement required methods
4. Add configuration YAML
5. Register in agent manager

See [Agent Design](docs/design/agents/DESIGN.md) for detailed instructions.

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Downgrade if needed
alembic downgrade -1
```

## 🚢 Distribution

### Creating Standalone Package

```bash
# Ensure you're in the virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install PyInstaller and Nuitka
uv pip install pyinstaller nuitka

# Create standalone executable
python scripts/build_standalone.py

# Output locations:
# Windows: dist/RS_Personal_Agent/RS_Personal_Agent.exe
# macOS: dist/RS_Personal_Agent/RS_Personal_Agent.app
# Linux: dist/RS_Personal_Agent/RS_Personal_Agent
```

The standalone package includes:
- All Python dependencies
- PySide6 Qt runtime
- Database migrations
- Configuration templates
- **Note**: Ollama must be installed separately

### Docker Distribution

```bash
# Build Docker image
docker build -t rs_pa:latest .

# Run with persistent data
docker run -d \
  --name rs_pa \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v ~/.rs/pa:/root/.rs/pa \
  --network host \
  rs_pa:latest

# View logs
docker logs -f rs_pa

# Stop container
docker stop rs_pa
```

### Package Structure

```
dist/RS_Personal_Agent/
├── RS_Personal_Agent[.exe/.app]  # Main executable
├── _internal/                         # Dependencies
├── config/                            # Configuration templates
│   ├── settings.yaml
│   └── agents/                        # Agent configs
├── alembic/                           # Database migrations
└── README.txt                         # Quick start guide
```

## 🔒 Privacy & Security

- **Local Processing**: All AI processing via local Ollama
- **No External API Calls**: Except for Gmail API (optional)
- **Encrypted Storage**: Sensitive data encrypted at rest
- **OAuth2 Security**: Standard Gmail authentication

## 🐛 Troubleshooting

### Common Issues

#### Ollama Connection Error
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
# macOS:
brew services start ollama
# Linux:
sudo systemctl start ollama
# Windows:
# Start from system tray or run: ollama serve

# Verify connection
ollama list
```

#### Model Loading Issues
```bash
# Check available models
ollama list

# Re-download model if corrupted
ollama rm llama4:maverick
ollama pull llama4:maverick

# Check model size (should be ~8GB)
du -sh ~/.ollama/models/
```

#### Database Issues
```bash
# Check current migration status
alembic current

# Reset database (WARNING: Deletes all data!)
# Note: Database location depends on platform and mode:
# Development: ./data/main.db
# Production Windows: %LOCALAPPDATA%\Roostership\RSPersonalAgent\main.db
# Production macOS: ~/Library/Application Support/RSPersonalAgent/main.db
# Production Linux: ~/.local/share/RSPersonalAgent/main.db

# For development mode reset:
rm -rf data/main.db data/cache.db data/performance.db
alembic upgrade head

# Create backup before reset (development mode):
cp data/main.db data/main.db.backup
```

#### Performance Issues
- **High Memory Usage**: Reduce concurrent agents in settings
- **Slow Response**: Check CPU/GPU utilization, consider upgrading hardware
- **Database Locks**: Ensure only one instance is running

#### UI Not Loading
```bash
# Check PySide6 is installed
uv pip show PySide6

# Try running with debug output
python main.py --debug

# Check Qt platform plugins
python -c "from PySide6.QtWidgets import QApplication; print('Qt works')"
```

### Debug Mode

Enable detailed logging:
```bash
# Set log level
export RSPA_LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --debug
```

### Getting Help

1. Check logs in platform-specific location:
   - **Development**: `./data/logs/rs_pa.log`
   - **Windows**: `%LOCALAPPDATA%\Roostership\RSPersonalAgent\logs\rs_pa.log`
   - **macOS**: `~/Library/Application Support/RSPersonalAgent/logs/rs_pa.log`
   - **Linux**: `~/.local/share/RSPersonalAgent/logs/rs_pa.log`
2. Run built-in diagnostics: `python -m rs_pa.diagnostics`
3. Visit [Issues](https://github.com/your-repo/issues)

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow our [Python Style Guide](docs/standards/PYTHON-STYLE-GUIDE.md)
4. Write tests for new functionality
5. Ensure all tests pass (`pytest tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 🗺️ Roadmap

### Phase 1: Foundation (Current)
- ✅ System design and architecture
- ✅ Database schema and migrations
- ✅ Core infrastructure setup
- 🔄 Base agent implementation

### Phase 2: Core Agents
- 📋 Email Scanner Agent
- 📋 Task Manager Agent
- 📋 Calendar Integration Agent
- 📋 Document Processor Agent

### Phase 3: Advanced Features
- 📋 Multi-agent collaboration
- 📋 Advanced scheduling system
- 📋 Plugin architecture
- 📋 Mobile companion app

### Phase 4: Enterprise Features
- 📋 Team collaboration
- 📋 Advanced security features
- 📋 Compliance tools (GDPR, HIPAA)
- 📋 Enterprise deployment options

See [TASKS.md](TASKS.md) for detailed implementation timeline.

## 📚 Resources

- **Documentation**: [Full documentation](docs/)
- **Design Docs**: [System design](DESIGN.md) | [UI Design](docs/design/DESIGN_UI.md)
- **Agent Guide**: [Creating custom agents](docs/design/agents/DESIGN.md)
- **API Reference**: [Coming soon]
- **Video Tutorials**: [Coming soon]

## 💬 Community

- **Discord**: [Join our community](https://discord.gg/rs-assistant)
- **Forum**: [Discussion board](https://forum.rs-assistant.dev)
- **Twitter**: [@rs_assistant](https://twitter.com/rs_assistant)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[LangChain](https://langchain.com/)** - LLM orchestration framework
- **[Ollama](https://ollama.ai/)** - Local LLM runtime
- **[PySide6](https://doc.qt.io/qtforpython/)** - Native desktop UI framework
- **[SQLAlchemy](https://sqlalchemy.org/)** - Database ORM
- **[UV](https://github.com/astral-sh/uv)** - Fast Python package manager

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-username/rs_pa&type=Date)](https://star-history.com/#your-username/rs_pa&Date)

---

<div align="center">
Made with ❤️ by the RS Personal Agent Team
</div>
