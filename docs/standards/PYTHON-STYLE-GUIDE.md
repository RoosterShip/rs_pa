# Python Style Guide for RS Personal Assistant

This style guide is based on the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with specific adaptations for the RS Personal Assistant project.

## 1. Python Language Rules

### 1.1 Python Version
- Use Python 3.9+ features
- Type hints are **required** for all functions and class methods
- Use modern Python idioms (f-strings, pathlib, etc.)

### 1.2 Imports
```python
# Standard library imports first
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

# Third-party imports second
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from pydantic import BaseModel

# Local imports last
from core.database import DatabaseManager
from models.agent import Agent
```

**Import Rules:**
- Use absolute imports for clarity
- Group imports: standard library, third-party, local
- Sort alphabetically within each group
- Avoid wildcard imports (`from module import *`)
- Use `__all__` in `__init__.py` files

### 1.3 Exception Handling
```python
# Good
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise

# Bad - too broad
try:
    result = risky_operation()
except Exception:
    pass  # Never silently ignore
```

## 2. Python Style Rules

### 2.1 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Package/Module | lowercase_with_underscores | `email_scanner` |
| Class | CapitalizedWords | `EmailScannerAgent` |
| Function/Method | lowercase_with_underscores | `process_email()` |
| Constant | UPPERCASE_WITH_UNDERSCORES | `MAX_RETRIES` |
| Private | Leading underscore | `_internal_method()` |

### 2.2 Line Length and Formatting
- Maximum line length: 88 characters (Black default)
- Use Black for automatic formatting
- Configure in `pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py39']
```

### 2.3 Docstrings

**IMPORTANT**: All public modules, classes, and functions **MUST** have docstrings.

Use Google-style docstrings:

```python
def fetch_emails(
    self,
    label: str = "INBOX",
    max_results: int = 100,
    after_date: Optional[datetime] = None
) -> List[EmailMessage]:
    """Fetch emails from Gmail with specified filters.
    
    Retrieves emails from the user's Gmail account based on the provided
    filters. Results are sorted by date in descending order.
    
    Args:
        label: Gmail label to filter by. Defaults to "INBOX".
        max_results: Maximum number of emails to return. Defaults to 100.
        after_date: Only fetch emails after this date. If None, fetches all.
        
    Returns:
        List of EmailMessage objects containing email data.
        
    Raises:
        GmailAPIError: If the Gmail API request fails.
        AuthenticationError: If credentials are invalid.
        
    Example:
        >>> scanner = EmailScanner()
        >>> emails = scanner.fetch_emails(
        ...     label="Bills",
        ...     max_results=50,
        ...     after_date=datetime(2024, 1, 1)
        ... )
    """
```

### 2.4 Type Hints

Type hints are **mandatory** for all function signatures:

```python
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime
from models.email import EmailMessage

def process_emails(
    emails: List[EmailMessage],
    config: Dict[str, Any],
    dry_run: bool = False
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Process emails and return results and errors."""
    pass

# For complex types, use type aliases
EmailBatch = List[EmailMessage]
ProcessingResult = Dict[str, Union[str, float, List[str]]]

def batch_process(
    batches: List[EmailBatch]
) -> List[ProcessingResult]:
    """Process multiple email batches."""
    pass
```

## 3. RS Personal Assistant Specific Guidelines

### 3.1 Agent Development

All agents must follow this structure:

```python
from typing import Any, Dict, Optional
from agents.base_agent import BaseAgent
from core.database import DatabaseManager
from core.llm_manager import LLMManager

class MyAgent(BaseAgent):
    """One-line summary of agent purpose.
    
    Detailed description of what the agent does, its responsibilities,
    and any important implementation details.
    
    Attributes:
        config: Agent configuration dictionary.
        db_manager: Database manager instance.
        llm_manager: LLM manager instance.
    """
    
    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any],
        db_manager: DatabaseManager,
        llm_manager: LLMManager
    ) -> None:
        """Initialize the agent with required dependencies."""
        super().__init__(agent_id, config, db_manager)
        self.llm_manager = llm_manager
        
    def initialize(self) -> None:
        """Initialize agent resources and validate configuration."""
        self._validate_config()
        self._setup_resources()
        
    def execute(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's main task.
        
        Args:
            task_data: Input data for the task.
            
        Returns:
            Result dictionary with status and output data.
        """
        pass
        
    def cleanup(self) -> None:
        """Clean up agent resources."""
        pass
```

### 3.2 Database Models

All SQLAlchemy models must:

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Agent(BaseModel):
    """Agent database model.
    
    Represents an AI agent in the system with its configuration
    and execution status.
    """
    __tablename__ = "agents"
    
    # Always use descriptive column definitions
    name = Column(
        String(100),
        nullable=False,
        doc="Human-readable agent name"
    )
    agent_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type identifier for agent class"
    )
    status = Column(
        Enum(AgentStatus),
        default=AgentStatus.REGISTERED,
        nullable=False,
        doc="Current agent status"
    )
    
    # Relationships
    tasks = relationship(
        "Task",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
```

### 3.3 Error Handling

Create specific exception classes:

```python
class RSPAError(Exception):
    """Base exception for RS Personal Assistant."""
    pass

class AgentError(RSPAError):
    """Base exception for agent-related errors."""
    pass

class EmailScannerError(AgentError):
    """Specific to email scanner agent."""
    pass

# Usage
def process_email(email_id: str) -> None:
    """Process a single email."""
    try:
        email = fetch_email(email_id)
    except GmailAPIError as e:
        logger.error(f"Failed to fetch email {email_id}: {e}")
        raise EmailScannerError(f"Cannot process email {email_id}") from e
```

### 3.4 Logging

Use structured logging:

```python
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

def process_task(task_id: str, data: Dict[str, Any]) -> None:
    """Process a task with proper logging."""
    logger.info(
        "Starting task processing",
        extra={
            "task_id": task_id,
            "data_size": len(data),
            "agent": self.__class__.__name__
        }
    )
    
    try:
        result = self._execute_task(data)
        logger.info(
            "Task completed successfully",
            extra={"task_id": task_id, "result": result}
        )
    except Exception as e:
        logger.error(
            "Task failed",
            extra={"task_id": task_id, "error": str(e)},
            exc_info=True
        )
        raise
```

### 3.5 Testing

All code must have tests:

```python
import pytest
from unittest.mock import Mock, patch
from agents.email_scanner import EmailScannerAgent

class TestEmailScannerAgent:
    """Test suite for EmailScannerAgent."""
    
    @pytest.fixture
    def agent(self, mock_db_manager, mock_llm_manager):
        """Create agent instance for testing."""
        return EmailScannerAgent(
            agent_id="test-agent",
            config={"threshold": 0.8},
            db_manager=mock_db_manager,
            llm_manager=mock_llm_manager
        )
    
    def test_initialize_validates_config(self, agent):
        """Test that initialize validates required config."""
        agent.config = {}  # Invalid config
        
        with pytest.raises(ValueError, match="Missing required config"):
            agent.initialize()
    
    @patch("agents.email_scanner.fetch_emails")
    def test_execute_processes_emails(self, mock_fetch, agent):
        """Test email processing workflow."""
        # Arrange
        mock_fetch.return_value = [create_test_email()]
        
        # Act
        result = agent.execute({"label": "INBOX"})
        
        # Assert
        assert result["status"] == "success"
        assert result["processed_count"] == 1
        mock_fetch.assert_called_once_with(label="INBOX")
```

## 4. Code Organization

### 4.1 File Structure
- One class per file (with rare exceptions)
- Test files mirror source structure
- Group related functionality in packages

### 4.2 Module Design
- Keep modules focused and cohesive
- Use `__init__.py` to control public API
- Document module purpose in docstring

## 5. Performance Guidelines

### 5.1 Database Queries
```python
# Good - single query with joins
agents = session.query(Agent).options(
    joinedload(Agent.tasks)
).filter(Agent.status == AgentStatus.ACTIVE).all()

# Bad - N+1 query problem
agents = session.query(Agent).all()
for agent in agents:
    tasks = agent.tasks  # Additional query per agent
```

### 5.2 Async Operations
Use async/await for I/O operations when beneficial:
```python
async def fetch_all_emails(labels: List[str]) -> List[EmailMessage]:
    """Fetch emails from multiple labels concurrently."""
    tasks = [fetch_emails_async(label) for label in labels]
    results = await asyncio.gather(*tasks)
    return [email for batch in results for email in batch]
```

## 6. Security Guidelines

### 6.1 Input Validation
Always validate external input:
```python
from pydantic import BaseModel, validator

class EmailScanRequest(BaseModel):
    """Request model for email scanning."""
    
    label: str
    max_results: int = 100
    
    @validator("max_results")
    def validate_max_results(cls, v):
        """Ensure max_results is within bounds."""
        if v < 1 or v > 1000:
            raise ValueError("max_results must be between 1 and 1000")
        return v
```

### 6.2 Secrets Management
Never hardcode secrets:
```python
# Good
import os
from core.config_manager import ConfigManager

config = ConfigManager()
api_key = config.get_secret("gmail_api_key")

# Bad
API_KEY = "hardcoded-secret-key"  # NEVER DO THIS
```

## 7. Documentation Standards

### 7.1 README Files
Each package should have a README.md explaining:
- Purpose and responsibilities
- Usage examples
- Configuration options
- Dependencies

### 7.2 Code Comments
- Explain "why", not "what"
- Keep comments up-to-date
- Remove commented-out code

```python
# Good - explains reasoning
# Use exponential backoff to avoid overwhelming the API
retry_delay = 2 ** attempt

# Bad - states the obvious
# Increment counter by 1
counter += 1
```

## Tools and Enforcement

### Required Tools
- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **pylint**: Linting
- **pytest**: Testing

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## Summary

Following this style guide ensures:
1. **Consistency** across the codebase
2. **Readability** for all contributors
3. **Maintainability** as the project grows
4. **Quality** through enforced standards

Remember: **When in doubt, prioritize readability and clarity over cleverness.**