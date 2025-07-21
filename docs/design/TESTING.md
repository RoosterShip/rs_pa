# Testing Standards and Guidelines

This document defines the testing standards, patterns, and best practices for the RS Personal Assistant project. All test implementations must follow these guidelines to ensure consistency, maintainability, and comprehensive coverage.

## Testing Philosophy

1. **Test Early, Test Often**: Write tests as you develop, not after
2. **Test at Multiple Levels**: Unit, integration, and end-to-end tests
3. **Mock External Dependencies**: Isolate tests from external services
4. **Readable Tests**: Tests serve as documentation
5. **Fast and Reliable**: Tests should run quickly and consistently

## Testing Stack

### Required Testing Tools

```python
# Core testing framework
pytest>=7.4.0
pytest-asyncio>=0.21.0  # For async test support
pytest-cov>=4.1.0       # Coverage reporting
pytest-mock>=3.11.0     # Enhanced mocking

# Mocking and fixtures
unittest.mock          # Built-in mocking (preferred)
factory-boy>=3.3.0     # Test data factories
faker>=19.0.0          # Fake data generation

# Testing utilities
freezegun>=1.2.0       # Time mocking
responses>=0.23.0      # HTTP response mocking
testcontainers>=3.7.0  # Docker containers for integration tests
```

## Test Organization

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── fixtures/                # Test data files
│   ├── email_samples.json
│   ├── llm_responses.json
│   └── agent_configs.yaml
├── unit/                    # Unit tests
│   ├── test_core/
│   │   ├── test_database.py
│   │   ├── test_llm_manager.py
│   │   └── test_config_manager.py
│   ├── test_agents/
│   │   ├── base_agent_test.py
│   │   └── test_email_scanner.py
│   └── test_models/
│       └── test_agent.py
├── integration/             # Integration tests
│   ├── test_agent_lifecycle.py
│   └── test_gmail_integration.py
└── e2e/                    # End-to-end tests
    └── test_full_workflow.py
```

### Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<what_is_being_tested>`
- Fixtures: `<resource>_fixture` (e.g., `agent_fixture`)

## Testing Patterns

### 1. Base Test Classes

Create base test classes for common functionality:

```python
# tests/unit/test_agents/base_agent_test.py
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional

from agents.base_agent import BaseAgent, AgentResult
from core.database import DatabaseManager
from core.llm_manager import LLMManager
from core.config_manager import ConfigManager

class BaseAgentTest:
    """Base test class for all agent tests."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures before each test."""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_llm_manager = Mock(spec=LLMManager)
        self.mock_config_manager = Mock(spec=ConfigManager)
        
        # Default test configuration
        self.test_config = {
            'name': 'TestAgent',
            'description': 'Test agent for unit testing',
            'version': '1.0.0',
            'enabled': True
        }
        
    def create_test_agent(
        self, 
        agent_class: type[BaseAgent],
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """Factory method to create test agent instances."""
        config = self.test_config.copy()
        if config_overrides:
            config.update(config_overrides)
            
        return agent_class(
            agent_id='test-agent-123',
            config=config,
            db_manager=self.mock_db_manager,
            llm_manager=self.mock_llm_manager,
            config_manager=self.mock_config_manager
        )
    
    def assert_agent_result_success(
        self, 
        result: AgentResult,
        expected_data_keys: Optional[list] = None
    ):
        """Assert that agent result indicates success."""
        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.error is None
        assert isinstance(result.data, dict)
        assert result.execution_time_ms > 0
        
        if expected_data_keys:
            for key in expected_data_keys:
                assert key in result.data
    
    def assert_agent_result_failure(
        self,
        result: AgentResult,
        expected_error_substring: Optional[str] = None
    ):
        """Assert that agent result indicates failure."""
        assert isinstance(result, AgentResult)
        assert result.success is False
        assert result.error is not None
        assert isinstance(result.message, str)
        
        if expected_error_substring:
            assert expected_error_substring in result.error
```

### 2. Mock Patterns

#### LLM Mocking

```python
# tests/mocks/llm_mocks.py
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional
import json

class MockLLMResponse:
    """Mock LLM response object."""
    def __init__(self, content: str):
        self.content = content
        self.metadata = {}

class LLMMockFactory:
    """Factory for creating LLM mocks with predefined behaviors."""
    
    @staticmethod
    def create_mock_llm(
        default_response: str = "Mock LLM response"
    ) -> Mock:
        """Create a basic mock LLM."""
        mock_llm = Mock()
        mock_llm.invoke.return_value = MockLLMResponse(default_response)
        return mock_llm
    
    @staticmethod
    def create_bill_detection_llm(is_bill: bool = True) -> Mock:
        """Create mock LLM for bill detection."""
        mock_llm = Mock()
        response = "YES" if is_bill else "NO"
        mock_llm.invoke.return_value = MockLLMResponse(response)
        return mock_llm
    
    @staticmethod
    def create_extraction_llm(extracted_data: Dict[str, Any]) -> Mock:
        """Create mock LLM for data extraction."""
        mock_llm = Mock()
        response_json = json.dumps(extracted_data, indent=2)
        mock_llm.invoke.return_value = MockLLMResponse(response_json)
        return mock_llm
    
    @staticmethod
    def create_error_llm(error_message: str = "LLM Error") -> Mock:
        """Create mock LLM that raises errors."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception(error_message)
        return mock_llm
```

#### Database Mocking

```python
# tests/mocks/db_mocks.py
from unittest.mock import Mock, MagicMock, PropertyMock
from contextlib import contextmanager
from typing import List, Optional, Any
from sqlalchemy.orm import Session

class MockDatabaseManager:
    """Mock database manager with session support."""
    
    def __init__(self):
        self.session_mock = Mock(spec=Session)
        self.committed = False
        self.rolled_back = False
        
    @contextmanager
    def get_session(self):
        """Mock session context manager."""
        try:
            yield self.session_mock
            self.committed = True
        except Exception:
            self.rolled_back = True
            raise
            
    def add_query_result(self, model_class: type, results: List[Any]):
        """Add mock query results for a model class."""
        query_mock = Mock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = results
        query_mock.first.return_value = results[0] if results else None
        
        self.session_mock.query.return_value = query_mock
        
    def verify_committed(self) -> bool:
        """Check if transaction was committed."""
        return self.committed
```

#### Gmail Service Mocking

```python
# tests/mocks/gmail_mocks.py
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any, Optional
import base64

class MockGmailService:
    """Mock Gmail service for testing."""
    
    def __init__(self):
        self.messages = []
        self.labels = ['INBOX', 'SENT', 'DRAFT']
        
    def add_mock_email(
        self,
        email_id: str,
        subject: str,
        sender: str,
        body: str,
        labels: Optional[List[str]] = None
    ):
        """Add a mock email to the service."""
        email_data = {
            'id': email_id,
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': subject},
                    {'name': 'From', 'value': sender}
                ],
                'body': {
                    'data': base64.b64encode(body.encode()).decode()
                }
            },
            'labelIds': labels or ['INBOX']
        }
        self.messages.append(email_data)
        
    def list_messages(
        self,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Mock list messages response."""
        filtered_messages = self.messages
        
        if label_ids:
            filtered_messages = [
                m for m in filtered_messages
                if any(label in m['labelIds'] for label in label_ids)
            ]
            
        return {
            'messages': [{'id': m['id']} for m in filtered_messages],
            'resultSizeEstimate': len(filtered_messages)
        }
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Mock get message response."""
        for message in self.messages:
            if message['id'] == message_id:
                return message
        return None
        
    def modify_message(
        self,
        message_id: str,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Mock modify message response."""
        for message in self.messages:
            if message['id'] == message_id:
                if add_label_ids:
                    message['labelIds'].extend(add_label_ids)
                if remove_label_ids:
                    message['labelIds'] = [
                        l for l in message['labelIds'] 
                        if l not in remove_label_ids
                    ]
                return message
        raise ValueError(f"Message {message_id} not found")
```

### 3. Fixture Patterns

```python
# tests/conftest.py
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from tests.mocks.llm_mocks import LLMMockFactory
from tests.mocks.db_mocks import MockDatabaseManager
from tests.mocks.gmail_mocks import MockGmailService

# Fixture data directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def mock_llm():
    """Provide mock LLM manager."""
    return LLMMockFactory.create_mock_llm()

@pytest.fixture
def mock_db():
    """Provide mock database manager."""
    return MockDatabaseManager()

@pytest.fixture
def mock_gmail():
    """Provide mock Gmail service."""
    return MockGmailService()

@pytest.fixture
def sample_emails():
    """Load sample email data from fixtures."""
    with open(FIXTURES_DIR / "email_samples.json") as f:
        return json.load(f)

@pytest.fixture
def agent_configs():
    """Load agent configuration samples."""
    with open(FIXTURES_DIR / "agent_configs.yaml") as f:
        import yaml
        return yaml.safe_load(f)

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    def _mock_response(model: str, prompt: str) -> Dict[str, Any]:
        return {
            "model": model,
            "created_at": "2024-01-01T00:00:00Z",
            "response": "Mock response",
            "done": True,
            "context": [],
            "total_duration": 1000000000,
            "load_duration": 500000000,
            "prompt_eval_duration": 250000000,
            "eval_duration": 250000000
        }
    return _mock_response

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Reset any singleton instances that might carry state
    from core.llm_manager import LLMManager
    LLMManager._instance = None
    yield
    LLMManager._instance = None
```

### 4. Test Data Factories

```python
# tests/factories/agent_factories.py
import factory
from factory import fuzzy
from datetime import datetime, timedelta
from models.agent import Agent, AgentStatus
from models.task import Task, TaskStatus

class AgentFactory(factory.Factory):
    """Factory for creating test Agent instances."""
    
    class Meta:
        model = Agent
    
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    agent_type = fuzzy.FuzzyChoice(['email_scanner', 'task_manager', 'calendar'])
    status = fuzzy.FuzzyChoice([s for s in AgentStatus])
    configuration = factory.LazyFunction(
        lambda: {
            'enabled': True,
            'schedule': '0 */6 * * *',
            'max_retries': 3
        }
    )
    created_at = factory.Faker(
        'date_time_between',
        start_date='-30d',
        end_date='now'
    )

class TaskFactory(factory.Factory):
    """Factory for creating test Task instances."""
    
    class Meta:
        model = Task
    
    id = factory.Faker('uuid4')
    agent = factory.SubFactory(AgentFactory)
    name = factory.Faker('sentence', nb_words=4)
    status = fuzzy.FuzzyChoice([s for s in TaskStatus])
    input_data = factory.LazyFunction(
        lambda: {'param1': 'value1', 'param2': 123}
    )
    created_at = factory.Faker('date_time_between', start_date='-7d')
    
    @factory.lazy_attribute
    def started_at(obj):
        if obj.status != TaskStatus.PENDING:
            return obj.created_at + timedelta(seconds=5)
        return None
    
    @factory.lazy_attribute
    def completed_at(obj):
        if obj.status == TaskStatus.COMPLETED:
            return obj.started_at + timedelta(minutes=2)
        return None
```

## Testing Guidelines

### 1. Unit Testing

Unit tests should:
- Test individual functions/methods in isolation
- Mock all external dependencies
- Cover edge cases and error conditions
- Be fast (<100ms per test)

```python
# Example unit test
class TestLLMManager:
    """Unit tests for LLM Manager."""
    
    def test_get_model_creates_new_instance(self, mock_ollama_api):
        """Test that get_model creates new model instance."""
        llm_manager = LLMManager(ollama_host="localhost")
        
        model1 = llm_manager.get_model("llama4:maverick")
        model2 = llm_manager.get_model("llama4:maverick")
        
        assert model1 is model2  # Should reuse instance
        assert mock_ollama_api.called
    
    def test_health_check_success(self, mock_ollama_api):
        """Test health check when Ollama is available."""
        mock_ollama_api.get.return_value.status_code = 200
        
        llm_manager = LLMManager()
        assert llm_manager.health_check() is True
    
    def test_health_check_failure(self, mock_ollama_api):
        """Test health check when Ollama is unavailable."""
        mock_ollama_api.get.side_effect = ConnectionError()
        
        llm_manager = LLMManager()
        assert llm_manager.health_check() is False
```

### 2. Integration Testing

Integration tests should:
- Test interaction between components
- Use test databases and containers
- Mock only external services (APIs)
- Verify data flow and transformations

```python
# Example integration test
@pytest.mark.integration
class TestAgentLifecycle:
    """Integration tests for agent lifecycle."""
    
    @pytest.fixture
    def test_db(self):
        """Provide test database."""
        # Use test container or in-memory SQLite
        from testcontainers.postgres import PostgresContainer
        
        with PostgresContainer("postgres:15") as postgres:
            yield postgres.get_connection_url()
    
    def test_agent_registration_and_execution(self, test_db):
        """Test full agent registration and execution flow."""
        # Create real database manager with test DB
        db_manager = DatabaseManager(test_db)
        
        # Create agent manager
        agent_manager = AgentManager(db_manager)
        
        # Register agent
        agent_id = agent_manager.register_agent(
            agent_type="email_scanner",
            config={"enabled": True}
        )
        
        # Execute agent
        result = agent_manager.execute_agent(agent_id)
        
        assert result.success is True
        
        # Verify database state
        with db_manager.get_session() as session:
            agent = session.query(Agent).filter_by(id=agent_id).first()
            assert agent.status == AgentStatus.IDLE
```

### 3. End-to-End Testing

E2E tests should:
- Test complete user workflows
- Use real services when possible
- Be marked for selective execution
- Verify business requirements

```python
# Example E2E test
@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("E2E_TESTS"),
    reason="E2E tests only run when E2E_TESTS env var is set"
)
class TestEmailScannerWorkflow:
    """End-to-end tests for email scanner workflow."""
    
    def test_complete_email_scanning_workflow(self):
        """Test scanning emails, detecting bills, and generating report."""
        # This test would:
        # 1. Connect to real Gmail (test account)
        # 2. Use real Ollama instance
        # 3. Process emails and detect bills
        # 4. Generate and verify report
        pass
```

## Mocking Guidelines

### When to Mock

1. **Always Mock**:
   - External APIs (Gmail, etc.)
   - LLM responses (Ollama)
   - File system operations
   - Network requests
   - Time-dependent operations

2. **Consider Mocking**:
   - Database for unit tests
   - Complex business logic in integration tests
   - Expensive operations

3. **Don't Mock**:
   - Simple data structures
   - Pure functions
   - The unit under test

### Mock Best Practices

1. **Use Type Specifications**:
   ```python
   mock_db = Mock(spec=DatabaseManager)
   ```

2. **Verify Mock Calls**:
   ```python
   mock_llm.invoke.assert_called_once_with(
       expected_prompt,
       temperature=0.1
   )
   ```

3. **Use Side Effects for Sequences**:
   ```python
   mock_api.get.side_effect = [
       Response(200, {"status": "pending"}),
       Response(200, {"status": "completed"})
   ]
   ```

## Testing Checklist

Before submitting code, ensure:

- [ ] All new code has corresponding tests
- [ ] Tests follow naming conventions
- [ ] Mocks are properly typed and specified
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Tests are independent and can run in any order
- [ ] No hardcoded test data that could become stale
- [ ] Integration tests are marked appropriately
- [ ] Code coverage is above 80%

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest --cov=rs_pa --cov-report=html

# Run specific test file
pytest tests/unit/test_agents/test_email_scanner.py

# Run integration tests
pytest -m integration

# Run all tests except E2E
pytest -m "not e2e"

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

## Continuous Integration

Tests must pass in CI before merging:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest --cov=rs_pa --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## References

- [Python Testing Style Guide](../standards/PYTHON-STYLE-GUIDE.md)
- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)