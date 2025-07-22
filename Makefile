# 🚀 RS Personal Agent - Professional Makefile
# ===================================================
# A comprehensive build system for the RS Personal Agent
# using UV - the fastest Python package manager
# ===================================================

.PHONY: help install env run test clean lint format type-check setup dev-install build package docs

# Default target
.DEFAULT_GOAL := help

# 🎨 Colors for output
BOLD := \033[1m
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# 📋 Project Configuration
PROJECT_NAME := rs-personal-agent
PYTHON_VERSION := 3.12
SOURCE_DIR := src
TEST_DIR := tests
VENV_DIR := .venv

# 🔧 UV Commands
UV_RUN := uv run
UV_PIP := uv pip
UV_VENV := uv venv
UV_ADD := uv add
UV_SYNC := uv sync

## 📚 Help - Show available commands
help:
	@echo "$(BOLD)$(MAGENTA)🚀 RS Personal Agent - Makefile Commands$(RESET)"
	@echo "$(BOLD)$(CYAN)================================================$(RESET)"
	@echo ""
	@echo "$(BOLD)📦 Environment Management:$(RESET)"
	@echo "  $(GREEN)make env$(RESET)          🏗️  Create UV virtual environment"
	@echo "  $(GREEN)make install$(RESET)      📥 Install production dependencies"
	@echo "  $(GREEN)make dev-install$(RESET)  🛠️  Install development dependencies"
	@echo "  $(GREEN)make setup$(RESET)        ⚡ Complete setup (env + dev-install)"
	@echo ""
	@echo "$(BOLD)🏃 Development:$(RESET)"
	@echo "  $(GREEN)make run$(RESET)          🖥️  Run the desktop application"
	@echo "  $(GREEN)make test$(RESET)         🧪 Run all tests with coverage"
	@echo "  $(GREEN)make test-fast$(RESET)    ⚡ Run tests without coverage"
	@echo "  $(GREEN)make test-watch$(RESET)   👀 Run tests in watch mode"
	@echo ""
	@echo "$(BOLD)🔍 Code Quality:$(RESET)"
	@echo "  $(GREEN)make lint$(RESET)         🔍 Run linting checks"
	@echo "  $(GREEN)make format$(RESET)       ✨ Format code with black & isort"
	@echo "  $(GREEN)make type-check$(RESET)   🔒 Run type checking with mypy"
	@echo "  $(GREEN)make quality$(RESET)      🎯 Run all quality checks"
	@echo ""
	@echo "$(BOLD)🏗️  Build & Package:$(RESET)"
	@echo "  $(GREEN)make build$(RESET)        📦 Build standalone executable"
	@echo "  $(GREEN)make package$(RESET)      📦 Create distribution packages"
	@echo "  $(GREEN)make docs$(RESET)         📖 Generate documentation"
	@echo ""
	@echo "$(BOLD)🧹 Maintenance:$(RESET)"
	@echo "  $(GREEN)make clean$(RESET)        🧹 Clean all build artifacts"
	@echo "  $(GREEN)make clean-cache$(RESET)  💾 Clean Python cache files"
	@echo "  $(GREEN)make clean-env$(RESET)    🗑️  Remove virtual environment"
	@echo "  $(GREEN)make reset$(RESET)        🔄 Complete reset (clean + setup)"
	@echo ""
	@echo "$(BOLD)$(YELLOW)💡 Examples:$(RESET)"
	@echo "  $(CYAN)make setup && make run$(RESET)     # Complete setup and run"
	@echo "  $(CYAN)make quality && make test$(RESET)  # Check code quality and test"
	@echo "  $(CYAN)make reset$(RESET)                 # Start fresh"
	@echo ""

## 🏗️ Create UV virtual environment
env:
	@echo "$(BOLD)$(BLUE)🏗️  Creating UV virtual environment...$(RESET)"
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(UV_VENV) --python $(PYTHON_VERSION); \
		echo "$(GREEN)✅ Virtual environment created successfully!$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Virtual environment already exists!$(RESET)"; \
	fi

## 📥 Install production dependencies
install: env
	@echo "$(BOLD)$(BLUE)📥 Installing production dependencies...$(RESET)"
	@$(UV_PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Production dependencies installed!$(RESET)"

## 🛠️ Install development dependencies
dev-install: env
	@echo "$(BOLD)$(BLUE)🛠️  Installing development dependencies...$(RESET)"
	@$(UV_PIP) install -r requirements-dev.txt
	@$(UV_PIP) install -e .
	@echo "$(GREEN)✅ Development environment ready!$(RESET)"

## ⚡ Complete setup (environment + dev dependencies)
setup: env dev-install
	@echo "$(BOLD)$(GREEN)⚡ Setup complete! Ready to develop.$(RESET)"
	@echo "$(CYAN)💡 Try 'make run' to start the application$(RESET)"

## 🖥️ Run the desktop application
run:
	@echo "$(BOLD)$(BLUE)🖥️  Starting RS Personal Agent...$(RESET)"
	@$(UV_RUN) python main.py

## 🧪 Run all tests with coverage
test:
	@echo "$(BOLD)$(BLUE)🧪 Running tests with coverage...$(RESET)"
	@$(UV_RUN) pytest $(TEST_DIR) \
		--cov=$(SOURCE_DIR) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml \
		-v
	@echo "$(GREEN)✅ Tests completed! Check htmlcov/index.html for coverage report$(RESET)"

## ⚡ Run tests without coverage (faster)
test-fast:
	@echo "$(BOLD)$(BLUE)⚡ Running fast tests...$(RESET)"
	@$(UV_RUN) pytest $(TEST_DIR) -v --tb=short

## 👀 Run tests in watch mode
test-watch:
	@echo "$(BOLD)$(BLUE)👀 Running tests in watch mode...$(RESET)"
	@$(UV_RUN) pytest-watch $(TEST_DIR) -- -v --tb=short

## 🔍 Run linting checks
lint:
	@echo "$(BOLD)$(BLUE)🔍 Running linting checks...$(RESET)"
	@echo "$(CYAN)📝 Running flake8...$(RESET)"
	@$(UV_RUN) flake8 $(SOURCE_DIR) $(TEST_DIR)
	@echo "$(CYAN)🔧 Running ruff...$(RESET)"
	@$(UV_RUN) ruff check $(SOURCE_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Linting checks passed!$(RESET)"

## ✨ Format code with black and isort
format:
	@echo "$(BOLD)$(BLUE)✨ Formatting code...$(RESET)"
	@echo "$(CYAN)🎨 Running black...$(RESET)"
	@$(UV_RUN) black $(SOURCE_DIR) $(TEST_DIR)
	@echo "$(CYAN)📚 Running isort...$(RESET)"
	@$(UV_RUN) isort $(SOURCE_DIR) $(TEST_DIR)
	@echo "$(GREEN)✅ Code formatted successfully!$(RESET)"

## 🔒 Run type checking with mypy
type-check:
	@echo "$(BOLD)$(BLUE)🔒 Running type checks...$(RESET)"
	@$(UV_RUN) mypy $(SOURCE_DIR)
	@echo "$(GREEN)✅ Type checking passed!$(RESET)"

## 🎯 Run all quality checks
quality:
	@echo "$(BOLD)$(BLUE)🎯 Running comprehensive quality checks...$(RESET)"
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test
	@echo "$(BOLD)$(GREEN)🎯 All quality checks completed!$(RESET)"

## 📦 Build standalone executable
build: dev-install
	@echo "$(BOLD)$(BLUE)📦 Building standalone executable...$(RESET)"
	@mkdir -p dist
	@$(UV_RUN) python scripts/build_standalone.py
	@echo "$(GREEN)✅ Build completed! Check dist/ directory$(RESET)"

## 📦 Create distribution packages
package: dev-install
	@echo "$(BOLD)$(BLUE)📦 Creating distribution packages...$(RESET)"
	@$(UV_RUN) python -m build
	@echo "$(GREEN)✅ Packages created in dist/ directory$(RESET)"

## 📖 Generate documentation
docs: dev-install
	@echo "$(BOLD)$(BLUE)📖 Generating documentation...$(RESET)"
	@$(UV_RUN) mkdocs build
	@echo "$(GREEN)✅ Documentation generated in site/ directory$(RESET)"

## 🧹 Clean all build artifacts
clean:
	@echo "$(BOLD)$(BLUE)🧹 Cleaning build artifacts...$(RESET)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf site/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf coverage.xml
	@rm -rf .pytest_cache/
	@rm -rf .mypy_cache/
	@rm -rf .ruff_cache/
	@echo "$(GREEN)✅ Build artifacts cleaned!$(RESET)"

## 💾 Clean Python cache files
clean-cache:
	@echo "$(BOLD)$(BLUE)💾 Cleaning Python cache files...$(RESET)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Python cache cleaned!$(RESET)"

## 🗑️ Remove virtual environment
clean-env:
	@echo "$(BOLD)$(BLUE)🗑️  Removing virtual environment...$(RESET)"
	@rm -rf $(VENV_DIR)
	@echo "$(GREEN)✅ Virtual environment removed!$(RESET)"

## 🔄 Complete reset (clean everything + setup)
reset: clean clean-cache clean-env setup
	@echo "$(BOLD)$(GREEN)🔄 Complete reset finished! Environment is fresh and ready.$(RESET)"

## 🚀 Quick development workflow
dev: format lint type-check test-fast
	@echo "$(BOLD)$(GREEN)🚀 Development workflow completed!$(RESET)"

## 📊 Project status
status:
	@echo "$(BOLD)$(MAGENTA)📊 RS Personal Agent - Project Status$(RESET)"
	@echo "$(BOLD)$(CYAN)================================$(RESET)"
	@echo ""
	@echo "$(BOLD)🐍 Python Version:$(RESET)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "  $(GREEN)✅ Virtual Environment: $$($(VENV_DIR)/bin/python --version 2>/dev/null || echo 'Unknown')$(RESET)"; \
	fi
	@if command -v python3 >/dev/null 2>&1; then \
		echo "  $(GREEN)✅ System Python: $$(python3 --version 2>/dev/null)$(RESET)"; \
	elif command -v python >/dev/null 2>&1; then \
		echo "  $(GREEN)✅ System Python: $$(python --version 2>/dev/null)$(RESET)"; \
	else \
		echo "  $(RED)❌ No Python found in PATH$(RESET)"; \
	fi
	@echo ""
	@echo "$(BOLD)⚡ UV Status:$(RESET)"
	@uv --version 2>/dev/null || echo "  $(RED)❌ UV not installed$(RESET)"
	@echo ""
	@echo "$(BOLD)📁 Virtual Environment:$(RESET)"
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "  $(GREEN)✅ Virtual environment exists$(RESET)"; \
	else \
		echo "  $(RED)❌ Virtual environment missing$(RESET)"; \
	fi
	@echo ""
	@echo "$(BOLD)📦 Dependencies:$(RESET)"
	@if [ -f "requirements.txt" ]; then \
		echo "  $(GREEN)✅ requirements.txt found$(RESET)"; \
	else \
		echo "  $(RED)❌ requirements.txt missing$(RESET)"; \
	fi
	@if [ -f "requirements-dev.txt" ]; then \
		echo "  $(GREEN)✅ requirements-dev.txt found$(RESET)"; \
	else \
		echo "  $(RED)❌ requirements-dev.txt missing$(RESET)"; \
	fi
	@if [ -d "$(VENV_DIR)" ]; then \
		if $(VENV_DIR)/bin/python -c "import pkg_resources; pkg_resources.get_distribution('rs-personal-agent')" 2>/dev/null; then \
			echo "  $(GREEN)✅ Package installed in development mode$(RESET)"; \
		else \
			echo "  $(YELLOW)⚠️  Package not installed (run 'make dev-install')$(RESET)"; \
		fi; \
	fi
	@echo ""

## 🔧 Install pre-commit hooks
hooks: dev-install
	@echo "$(BOLD)$(BLUE)🔧 Installing pre-commit hooks...$(RESET)"
	@$(UV_RUN) pre-commit install
	@echo "$(GREEN)✅ Pre-commit hooks installed!$(RESET)"

# 🎯 Advanced targets for CI/CD
.PHONY: ci-test ci-quality ci-build

## 🤖 CI: Run tests for continuous integration
ci-test:
	@echo "$(BOLD)$(BLUE)🤖 Running CI tests...$(RESET)"
	@$(UV_RUN) pytest $(TEST_DIR) \
		--cov=$(SOURCE_DIR) \
		--cov-report=xml \
		--junitxml=test-results.xml \
		-v

## 🤖 CI: Run quality checks for continuous integration
ci-quality:
	@echo "$(BOLD)$(BLUE)🤖 Running CI quality checks...$(RESET)"
	@$(UV_RUN) black --check $(SOURCE_DIR) $(TEST_DIR)
	@$(UV_RUN) isort --check-only $(SOURCE_DIR) $(TEST_DIR)
	@$(UV_RUN) flake8 $(SOURCE_DIR) $(TEST_DIR)
	@$(UV_RUN) mypy $(SOURCE_DIR)

## 🤖 CI: Full CI pipeline
ci: ci-quality ci-test
	@echo "$(BOLD)$(GREEN)🤖 CI pipeline completed successfully!$(RESET)"