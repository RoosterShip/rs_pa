# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL SECURITY WARNING

**NEVER read, access, or load `.env` files in this project!**

Claude Code automatically loads environment variables from `.env` files, which can expose sensitive credentials. To maintain security:

1. **DO NOT use any commands that read `.env` files** (e.g., `cat .env`, `Read tool on .env`)
2. **DO NOT reference or include `.env` file contents** in any code or responses
3. **DO NOT execute code that loads `.env` files** (e.g., `python-dotenv`, `load_dotenv()`)
4. **ALWAYS use `.env.example`** as a template reference instead
5. **NEVER store real credentials** in files that Claude Code might access

If you need to work with environment variables:
- Reference the `docs/ENVIRONMENT.md` file for variable documentation
- Use `.env.example` to understand required variables
- Instruct users to set environment variables in their shell or deployment platform
- Use the application's secure credential manager for sensitive data

## Project Overview

RS Personal Agent (rs_pa) is a local AI-powered personal agent platform built with Python. It uses a modular agent-based architecture with complete privacy - all AI processing happens locally using Ollama and Meta's Llama 4 models.

**Current Status**: The project is in the design/planning phase with comprehensive documentation but no implementation code yet. TASKS.md contains a detailed implementation plan for native desktop development using an iterative UI-first approach.

## 🔄 Iterative Development Strategy

**IMPORTANT**: This project follows an iterative UI-first development methodology to ensure continuous progress visibility and allow for changes without major redesign:

### Core Philosophy
1. **UI First**: Create visible interface elements that users can interact with before implementing backend functionality
2. **Framework Second**: Add the underlying framework code to support the UI components  
3. **Agent Integration Last**: Connect real AI agents when the foundation is solid and proven

### Benefits of This Approach
- ✅ **Visible Progress**: Every development phase delivers a working application that can be demonstrated
- ✅ **Early Feedback**: Users can interact with the interface and provide feedback before complex backend is built
- ✅ **Reduced Risk**: Changes can be made without major redesign since UI drives the architecture
- ✅ **Continuous Testing**: Working application is maintained throughout development
- ✅ **Motivation**: Developers can see tangible results at every step

### Implementation Pattern
Each major feature follows this three-step pattern:

1. **Build UI with Mock Data**: Create the complete user interface with realistic mock data to demonstrate the feature
2. **Add Framework Support**: Implement the underlying services, APIs, and data structures needed to support the UI
3. **Integrate Real Functionality**: Connect the UI to real agents, databases, and external services

### Example: Reimbursement Agent Feature
- **Step 1**: Create reimbursement dashboard page showing mock scan results, buttons, and workflows
- **Step 2**: Add Gmail API connection, database models, and basic data flow  
- **Step 3**: Implement the actual AI-powered reimbursement detection agent

This ensures that at any point in development, there's a functional application that demonstrates the intended user experience.

## Code Standards

**IMPORTANT**: All Python code in this project MUST follow our [Python Style Guide](docs/standards/PYTHON-STYLE-GUIDE.md). Key requirements:
- Use Python 3.9+ features
- Type hints are REQUIRED for all functions
- Google-style docstrings are MANDATORY
- Black formatting with 88-character line limit
- Comprehensive error handling and logging

## Key Technologies

- **Python 3.9+** - Primary language
- **PySide6** - Native desktop UI framework (Qt6 bindings)
- **SQLAlchemy + Alembic** - Database ORM and migrations  
- **Ollama** - Local LLM runtime (using Llama 4 models, default: `llama4:maverick`)
- **LangChain & ChatOllama** - LLM integration using langchain-ollama for standardized AI model interaction
- **LangGraph** - Stateful LLM agent orchestration framework with workflow management (ready for Task 2.3)
- **LangSmith** - Agent monitoring, debugging, and observability platform (ready for Task 2.3)
- **Gmail API** - For reimbursement agent

## Build and Development Commands

```bash
# Create virtual environment with UV
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies with UV (10x faster!)
uv pip install -r requirements.txt

# Install in development mode
uv pip install -e .

# Database operations
python -m alembic upgrade head              # Apply migrations
alembic revision --autogenerate -m "desc"   # Create new migration
alembic downgrade -1                        # Rollback migration

# Run native desktop application
python main.py

# Build standalone desktop executable
uv pip install pyinstaller nuitka
python scripts/build_standalone.py

# Installing Ollama (required dependency)
# For macOS/Linux:
curl -fsSL https://ollama.com/install.sh | sh
# For Windows: Download from https://www.ollama.com/download

# Start Ollama service
ollama serve

# Download Llama 4 Maverick model (recommended for best performance)
ollama pull llama4:maverick
# Alternative Llama 4 models:
# ollama pull llama4:scout    # 17B params, 16 experts, 10M context
# ollama pull llama4:behemoth # 288B params (when available)

# LangSmith Setup (Optional but recommended for monitoring)
# 1. Create account at https://smith.langchain.com/
# 2. Get API key from LangSmith dashboard
# 3. Set environment variables:
export LANGSMITH_API_KEY="your-api-key-here"
export LANGSMITH_TRACING=true
export LANGSMITH_PROJECT="rs-personal-agent"

# Install LangGraph and LangSmith dependencies (included in requirements.txt)
uv pip install langgraph>=0.2.0 langsmith>=0.1.0
```

## Architecture Overview

The system follows a modular agent-based architecture:

1. **Core Infrastructure** (`core/`)
   - `database.py` - SQLAlchemy session management
   - `llm_manager.py` - Centralized Ollama/LLM integration
   - `agent_manager.py` - Agent lifecycle management

2. **Agent System** (`agents/`)
   - All agents inherit from `BaseAgent` abstract class
   - Each agent has its own directory with agent code and config YAML
   - Agents are self-contained and communicate through the database

3. **Data Models** (`models/`)
   - SQLAlchemy models for Agent, Task, User, ReimbursementAgent entities
   - Alembic manages database migrations

4. **UI Layer** (`ui/`)
   - PySide6 native desktop interface with MVC architecture
   - Model classes in `ui/models/`, View classes in `ui/views/`
   - Controller classes in `ui/controllers/`, Custom widgets in `ui/widgets/`

## Development Guidelines

1. **Adding New Agents**:
   - Create directory in `agents/`
   - Inherit from `BaseAgent` class
   - Implement required methods: `initialize()`, `execute()`, `cleanup()`
   - Add configuration YAML
   - Register in agent manager

2. **Database Changes**:
   - Modify models in `models/`
   - Generate migration: `alembic revision --autogenerate -m "description"`
   - Apply migration: `alembic upgrade head`

3. **Testing**:
   - Test files should mirror source structure in `tests/`
   - Use pytest for testing framework
   - Use pytest-qt for PySide6 UI testing
   - Mock Ollama responses in tests

## Important Design Documents

- `DESIGN.md` - Complete system design overview
- `docs/design/DESIGN_FRAMEWORK.md` - Framework architecture details
- `docs/design/agents/DESIGN.md` - Agent development guide
- `TASKS.md` - Detailed implementation task breakdown for native desktop development

## Claude Code Custom Slash Commands

When asked to create a new Claude command:

1. Create the `.claude/commands/` directory if it doesn't exist: `mkdir -p .claude/commands`
2. Create a markdown file in `.claude/commands/` with the command name (e.g., `my-command.md`)
3. Write the command prompt in natural language inside the markdown file
4. The command will be available as `/my-command` in Claude Code
5. Use `$ARGUMENTS` placeholder to accept parameters in commands
6. Organize commands in subdirectories for namespacing (e.g., `.claude/commands/project/test.md` → `/project:test`)

Example command locations:
- `.claude/commands/execute-prompt.md` → `/execute-prompt`
- `.claude/commands/test/unit.md` → `/test:unit`
- `.claude/commands/debug/logs.md` → `/debug:logs`