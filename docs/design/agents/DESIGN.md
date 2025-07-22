# Agent Design - RS Personal Assistant

## 📋 Overview

This document details the agent architecture and development guidelines for the RS Personal Assistant system. Agents are autonomous AI-powered components that perform specific tasks using LangChain and LangGraph patterns.

## 🤖 Agent Architecture

### Base Agent Framework

All agents inherit from a common base class that provides standardized interfaces, lifecycle management, and integration with the core system.

**Base Agent Class (`src/agents/base_agent.py`)**
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import uuid

from src.core.database import DatabaseManager
from src.core.llm_manager import LLMManager
from src.core.config_manager import ConfigManager
from src.models.task import Task, TaskStatus
from src.models.agent import Agent, AgentStatus

@dataclass
class AgentResult:
    """Standardized result structure for agent execution"""
    success: bool
    data: Dict[str, Any]
    message: str
    execution_time_ms: int
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(
        self,
        agent_id: str,
        config: Dict[str, Any],
        db_manager: DatabaseManager,
        llm_manager: LLMManager,
        config_manager: ConfigManager
    ):
        self.agent_id = agent_id
        self.config = config
        self.db_manager = db_manager
        self.llm_manager = llm_manager
        self.config_manager = config_manager
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Agent metadata
        self.name = self.config.get('name', self.__class__.__name__)
        self.description = self.config.get('description', '')
        self.version = self.config.get('version', '1.0.0')
        
        # Runtime state
        self.status = AgentStatus.REGISTERED
        self.last_execution = None
        self.execution_count = 0
        
        # Initialize agent
        self._initialize()
    
    def _initialize(self):
        """Initialize agent-specific resources"""
        try:
            self.validate_config()
            self.setup_resources()
            self.status = AgentStatus.IDLE
            self.logger.info(f"Agent {self.name} initialized successfully")
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Agent {self.name} initialization failed: {e}")
            raise
    
    @abstractmethod
    def execute_task(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute the main agent task"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate agent configuration"""
        pass
    
    @abstractmethod
    def setup_resources(self):
        """Set up agent-specific resources"""
        pass
    
    @abstractmethod
    def cleanup_resources(self):
        """Clean up agent-specific resources"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status.value,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'execution_count': self.execution_count,
            'version': self.version,
            'description': self.description
        }
    
    def save_agent_data(self, key: str, value: Any):
        """Save agent-specific data to database"""
        with self.db_manager.get_session() as session:
            # Implementation would save to AgentData table
            pass
    
    def load_agent_data(self, key: str) -> Optional[Any]:
        """Load agent-specific data from database"""
        with self.db_manager.get_session() as session:
            # Implementation would load from AgentData table
            pass
    
    def create_task_record(self, input_data: Dict[str, Any]) -> str:
        """Create a task record in database"""
        task_id = str(uuid.uuid4())
        with self.db_manager.get_session() as session:
            task = Task(
                id=task_id,
                agent_id=self.agent_id,
                name=f"{self.name} Task",
                status=TaskStatus.RUNNING,
                input_data=json.dumps(input_data),
                started_at=datetime.now()
            )
            session.add(task)
        return task_id
    
    def update_task_record(self, task_id: str, result: AgentResult):
        """Update task record with execution result"""
        with self.db_manager.get_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                task.output_data = json.dumps(result.data)
                task.error_message = result.error
                task.completed_at = datetime.now()
    
    def run(self, input_data: Dict[str, Any]) -> AgentResult:
        """Main entry point for agent execution"""
        start_time = datetime.now()
        task_id = self.create_task_record(input_data)
        
        try:
            self.status = AgentStatus.ACTIVE
            self.logger.info(f"Starting execution for agent {self.name}")
            
            # Execute the agent task
            result = self.execute_task(input_data)
            
            # Update execution tracking
            self.last_execution = start_time
            self.execution_count += 1
            self.status = AgentStatus.IDLE
            
            # Calculate execution time
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            result.execution_time_ms = execution_time
            
            # Update database
            self.update_task_record(task_id, result)
            
            self.logger.info(f"Agent {self.name} completed successfully in {execution_time}ms")
            return result
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            error_msg = f"Agent {self.name} execution failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Create error result
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            error_result = AgentResult(
                success=False,
                data={},
                message="Agent execution failed",
                execution_time_ms=execution_time,
                error=str(e)
            )
            
            self.update_task_record(task_id, error_result)
            return error_result
```

---

## 📋 Example Agent Implementation

### Agent Structure Template

This section provides a generic template for implementing new agents in the system. For specific agent implementations, see the individual agent design documents in the `docs/design/agents/` directory.

**Example Agent Template (`src/agents/example_agent/agent.py`)**
```python
from src.agents.base_agent import BaseAgent, AgentResult
from typing import Dict, Any, List
import json
from datetime import datetime

class ExampleAgent(BaseAgent):
    """Example agent demonstrating the base implementation pattern"""
    
    def setup_resources(self):
        """Set up agent-specific resources and connections"""
        # Initialize LLM model
        self.llm = self.llm_manager.get_model(
            model_name=self.config.get('llm_model', 'llama4:maverick')
        )
        
        # Initialize any external services
        # self.external_service = ExternalService(config=self.config.get('service_config'))
        
        # Load agent-specific configuration
        self.processing_mode = self.config.get('processing_mode', 'batch')
        self.max_items = self.config.get('max_items', 100)
        self.retry_attempts = self.config.get('retry_attempts', 3)
    
    def validate_config(self) -> bool:
        """Validate agent configuration"""
        required_fields = ['processing_mode']  # Add your required fields
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required configuration: {field}")
        
        # Validate configuration values
        if self.config.get('max_items', 0) <= 0:
            raise ValueError("max_items must be greater than 0")
        
        return True
    
    def cleanup_resources(self):
        """Clean up resources when agent shuts down"""
        # Close any open connections
        # if hasattr(self, 'external_service'):
        #     self.external_service.close()
        pass
    
    def execute_task(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute the main agent task"""
        try:
            # Extract and validate input parameters
            task_type = input_data.get('task_type', 'default')
            items_to_process = input_data.get('items', [])
            
            if not items_to_process:
                return AgentResult(
                    success=True,
                    data={'processed_count': 0},
                    message="No items to process"
                )
            
            # Process items
            results = []
            errors = []
            
            for item in items_to_process[:self.max_items]:
                try:
                    result = self.process_item(item, task_type)
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Failed to process item {item.get('id', 'unknown')}: {e}")
                    errors.append({'item': item, 'error': str(e)})
            
            # Generate summary
            summary = self.generate_summary(results, errors)
            
            # Store results for future reference
            self.save_processing_results(results, summary)
            
            return AgentResult(
                success=True,
                data={
                    'processed_count': len(results),
                    'error_count': len(errors),
                    'results': results,
                    'errors': errors,
                    'summary': summary
                },
                message=f"Processed {len(results)} items successfully"
            )
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return AgentResult(
                success=False,
                data={},
                message="Task execution failed",
                error=str(e)
            )
    
    def process_item(self, item: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Process a single item"""
        # Use LLM for intelligent processing
        prompt = self.build_prompt(item, task_type)
        response = self.llm.invoke(prompt)
        
        # Parse and structure the response
        processed_data = self.parse_llm_response(response.content)
        
        return {
            'item_id': item.get('id'),
            'processed_data': processed_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def build_prompt(self, item: Dict[str, Any], task_type: str) -> str:
        """Build prompt for LLM processing"""
        return f"""
        Process the following item according to task type: {task_type}
        
        Item Data: {json.dumps(item, indent=2)}
        
        Please analyze and provide a structured response.
        
        Response:
        """
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data"""
        try:
            # Attempt to parse as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to text response
            return {'text_response': response}
    
    def generate_summary(self, results: List[Dict], errors: List[Dict]) -> Dict[str, Any]:
        """Generate a summary of processing results"""
        return {
            'total_processed': len(results),
            'total_errors': len(errors),
            'success_rate': len(results) / (len(results) + len(errors)) if results or errors else 0,
            'processing_time': datetime.now().isoformat()
        }
    
    def save_processing_results(self, results: List[Dict], summary: Dict):
        """Save processing results to database"""
        results_data = {
            'execution_date': datetime.now().isoformat(),
            'results': results,
            'summary': summary
        }
        
        self.save_agent_data('last_execution_results', results_data)
```

### Generic Agent Components

**Prompt Templates (`src/agents/example_agent/prompts.py`)**
```python
# Define your agent-specific prompts
ANALYSIS_PROMPT = """
Analyze the following data and provide insights:

Data: {data}

Please provide:
1. Key observations
2. Patterns identified
3. Recommendations

Format your response as JSON.
"""

VALIDATION_PROMPT = """
Validate the following information:

{content}

Respond with:
- is_valid: true/false
- issues: list of any validation issues found
- confidence: confidence score (0-1)
"""
```

**Data Models (`src/agents/example_agent/models.py`)**
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProcessingInput(BaseModel):
    """Input data for processing"""
    id: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = {}
    
class ProcessingResult(BaseModel):
    """Result of processing a single item"""
    item_id: str
    status: str = Field(pattern="^(success|failed|partial)$")
    processed_data: Dict[str, Any]
    processing_time_ms: int
    confidence_score: Optional[float] = Field(ge=0, le=1)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

class AgentConfiguration(BaseModel):
    """Agent configuration schema"""
    processing_mode: str = Field(pattern="^(batch|stream|real-time)$")
    max_items: int = Field(gt=0, default=100)
    retry_attempts: int = Field(ge=0, default=3)
    timeout_seconds: int = Field(gt=0, default=30)
    llm_model: str = "llama4:maverick"
    enable_cache: bool = True
```

### Configuration Template

**Agent Configuration (`config/agents/example_agent.yaml`)**
```yaml
name: "Example Agent"
description: "Template agent for demonstration purposes"
version: "1.0.0"

# Processing settings
processing_mode: "batch"
max_items: 100
retry_attempts: 3
timeout_seconds: 30

# LLM settings
llm_model: "llama4:maverick"
temperature: 0.7
max_tokens: 1000

# Caching
enable_cache: true
cache_ttl_hours: 24

# Agent-specific settings
custom_setting_1: "value1"
custom_setting_2: 42
```

---

## 🔗 LangGraph Integration Patterns

### Graph-Based Agent Workflows

For complex agents that require multi-step processing, LangGraph provides structured workflow management.

**LangGraph Workflow Example (`src/agents/email_scanner/workflow.py`)**
```python
from langgraph import StateGraph, END
from typing import Dict, Any, List
from src.agents.email_scanner.models import EmailData, ScanResult

class EmailScannerState:
    """State management for email scanning workflow"""
    
    def __init__(self):
        self.emails: List[EmailData] = []
        self.scan_results: List[ScanResult] = []
        self.current_email_index: int = 0
        self.total_processed: int = 0
        self.errors: List[str] = []
        self.summary: Dict[str, Any] = {}

def create_email_scanner_workflow() -> StateGraph:
    """Create LangGraph workflow for email scanning"""
    
    def fetch_emails_node(state: EmailScannerState) -> EmailScannerState:
        """Node: Fetch emails from Gmail"""
        # Implementation for fetching emails
        pass
    
    def process_email_node(state: EmailScannerState) -> EmailScannerState:
        """Node: Process individual email"""
        # Implementation for processing single email
        pass
    
    def extract_bill_info_node(state: EmailScannerState) -> EmailScannerState:
        """Node: Extract bill information if email is a bill"""
        # Implementation for bill information extraction
        pass
    
    def update_gmail_labels_node(state: EmailScannerState) -> EmailScannerState:
        """Node: Update Gmail labels"""
        # Implementation for updating labels
        pass
    
    def generate_report_node(state: EmailScannerState) -> EmailScannerState:
        """Node: Generate summary report"""
        # Implementation for report generation
        pass
    
    def should_continue_processing(state: EmailScannerState) -> str:
        """Conditional edge: Check if more emails to process"""
        if state.current_email_index < len(state.emails):
            return "process_email"
        else:
            return "generate_report"
    
    def is_bill_detected(state: EmailScannerState) -> str:
        """Conditional edge: Check if current email is a bill"""
        current_result = state.scan_results[-1]
        if current_result.is_bill:
            return "extract_bill_info"
        else:
            return "update_labels"
    
    # Build the graph
    workflow = StateGraph(EmailScannerState)
    
    # Add nodes
    workflow.add_node("fetch_emails", fetch_emails_node)
    workflow.add_node("process_email", process_email_node)
    workflow.add_node("extract_bill_info", extract_bill_info_node)
    workflow.add_node("update_labels", update_gmail_labels_node)
    workflow.add_node("generate_report", generate_report_node)
    
    # Add edges
    workflow.set_entry_point("fetch_emails")
    workflow.add_edge("fetch_emails", "process_email")
    workflow.add_conditional_edges(
        "process_email",
        is_bill_detected,
        {
            "extract_bill_info": "extract_bill_info",
            "update_labels": "update_labels"
        }
    )
    workflow.add_edge("extract_bill_info", "update_labels")
    workflow.add_conditional_edges(
        "update_labels",
        should_continue_processing,
        {
            "process_email": "process_email",
            "generate_report": "generate_report"
        }
    )
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()
```

---

## 🧪 Agent Testing Strategies

### Unit Testing Framework

**Agent Test Base Class (`tests/test_agents/base_agent_test.py`)**
```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any
import json
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentResult
from src.core.database import DatabaseManager
from src.core.llm_manager import LLMManager
from src.core.config_manager import ConfigManager

class BaseAgentTest(unittest.TestCase):
    """Base test class for all agent tests"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock dependencies
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_llm_manager = Mock(spec=LLMManager)
        self.mock_config_manager = Mock(spec=ConfigManager)
        
        # Mock database session
        self.mock_session = MagicMock()
        self.mock_db_manager.get_session.return_value.__enter__.return_value = self.mock_session
        
        # Default test configuration
        self.test_config = {
            'name': 'TestAgent',
            'description': 'Test agent for unit testing',
            'version': '1.0.0'
        }
        
        # Mock LLM response
        self.mock_llm = Mock()
        self.mock_llm_manager.get_model.return_value = self.mock_llm
    
    def create_test_agent(self, agent_class, config_override=None):
        """Create test agent instance with mocked dependencies"""
        config = {**self.test_config, **(config_override or {})}
        
        return agent_class(
            agent_id="test-agent-id",
            config=config,
            db_manager=self.mock_db_manager,
            llm_manager=self.mock_llm_manager,
            config_manager=self.mock_config_manager
        )
    
    def create_mock_llm_response(self, content: str):
        """Create mock LLM response"""
        mock_response = Mock()
        mock_response.content = content
        return mock_response
    
    def assert_agent_result(self, result: AgentResult, success: bool = True, 
                          required_data_keys: list = None):
        """Assert agent result structure and content"""
        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.success, success)
        self.assertIsInstance(result.data, dict)
        self.assertIsInstance(result.message, str)
        self.assertIsInstance(result.execution_time_ms, int)
        
        if required_data_keys:
            for key in required_data_keys:
                self.assertIn(key, result.data)
        
        if not success:
            self.assertIsNotNone(result.error)
```

**Email Scanner Agent Tests (`tests/test_agents/test_email_scanner.py`)**
```python
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from tests.test_agents.base_agent_test import BaseAgentTest
from src.agents.email_scanner.agent import EmailScannerAgent
from src.agents.email_scanner.models import EmailData, BillData, ScanResult

class TestEmailScannerAgent(BaseAgentTest):
    """Test cases for Email Scanner Agent"""
    
    def setUp(self):
        super().setUp()
        
        # Email scanner specific config
        self.email_config = {
            'gmail_credentials_path': 'test_credentials.json',
            'gmail_scopes': ['https://mail.google.com/'],
            'llm_model': 'llama4:maverick',
            'batch_size': 5,
            'processed_label': 'processed',
            'bill_label': 'bill'
        }
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_agent_initialization(self, mock_gmail_service):
        """Test agent initializes correctly"""
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        
        self.assertEqual(agent.name, 'TestAgent')
        self.assertEqual(agent.batch_size, 5)
        mock_gmail_service.assert_called_once()
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_validate_config_success(self, mock_gmail_service):
        """Test config validation passes with required fields"""
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        self.assertTrue(agent.validate_config())
    
    def test_validate_config_failure(self):
        """Test config validation fails with missing required fields"""
        incomplete_config = {'batch_size': 5}
        
        with self.assertRaises(ValueError):
            self.create_test_agent(EmailScannerAgent, incomplete_config)
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_execute_task_no_emails(self, mock_gmail_service):
        """Test task execution with no emails to process"""
        # Setup mocks
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        agent.fetch_unprocessed_emails = Mock(return_value=[])
        
        # Execute task
        result = agent.execute_task({'max_emails': 10})
        
        # Assert result
        self.assert_agent_result(result, success=True, 
                               required_data_keys=['processed_count', 'bills_found'])
        self.assertEqual(result.data['processed_count'], 0)
        self.assertEqual(result.data['bills_found'], 0)
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_execute_task_with_emails(self, mock_gmail_service):
        """Test task execution with emails to process"""
        # Setup test data
        test_emails = [
            {
                'id': 'email1',
                'subject': 'Your electricity bill',
                'sender': 'billing@electric.com',
                'content': 'Your bill is $150.00 due on 2025-08-15',
                'received_date': '2025-07-20'
            },
            {
                'id': 'email2', 
                'subject': 'Newsletter',
                'sender': 'news@example.com',
                'content': 'Check out our latest updates',
                'received_date': '2025-07-20'
            }
        ]
        
        # Setup mocks
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        agent.fetch_unprocessed_emails = Mock(return_value=test_emails)
        agent.process_email = Mock(side_effect=[
            ScanResult(
                email_data=EmailData(**test_emails[0]),
                is_bill=True,
                bill_data=BillData(company_name='Electric Co', amount=150.0),
                processed_at=datetime.now()
            ),
            ScanResult(
                email_data=EmailData(**test_emails[1]),
                is_bill=False,
                processed_at=datetime.now()
            )
        ])
        agent.gmail_service.add_label = Mock()
        agent.save_scan_results = Mock()
        agent.generate_summary_report = Mock(return_value={'summary': 'test'})
        
        # Execute task
        result = agent.execute_task({'max_emails': 10})
        
        # Assert result
        self.assert_agent_result(result, success=True,
                               required_data_keys=['processed_count', 'bills_found', 'scan_results'])
        self.assertEqual(result.data['processed_count'], 2)
        self.assertEqual(result.data['bills_found'], 1)
        
        # Verify Gmail service calls
        self.assertEqual(agent.gmail_service.add_label.call_count, 3)  # 2 processed + 1 bill
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_detect_bill_positive(self, mock_gmail_service):
        """Test bill detection returns positive result"""
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        
        # Mock LLM response
        self.mock_llm.invoke.return_value = self.create_mock_llm_response("YES")
        
        email_data = EmailData(
            email_id='test1',
            subject='Your monthly bill',
            sender='billing@company.com',
            content='Amount due: $100.00',
            received_date='2025-07-20'
        )
        
        result = agent.detect_bill(email_data)
        self.assertTrue(result)
    
    @patch('agents.email_scanner.agent.GmailService')  
    def test_detect_bill_negative(self, mock_gmail_service):
        """Test bill detection returns negative result"""
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        
        # Mock LLM response
        self.mock_llm.invoke.return_value = self.create_mock_llm_response("NO")
        
        email_data = EmailData(
            email_id='test2',
            subject='Weekly newsletter',
            sender='news@company.com', 
            content='Check out our latest products',
            received_date='2025-07-20'
        )
        
        result = agent.detect_bill(email_data)
        self.assertFalse(result)
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_extract_bill_information(self, mock_gmail_service):
        """Test bill information extraction"""
        agent = self.create_test_agent(EmailScannerAgent, self.email_config)
        
        # Mock LLM response with JSON
        bill_json = {
            'company_name': 'Electric Company',
            'amount': 150.75,
            'due_date': '2025-08-15',
            'bill_type': 'utilities',
            'account_number': '12345',
            'description': 'Monthly electricity bill'
        }
        self.mock_llm.invoke.return_value = self.create_mock_llm_response(
            json.dumps(bill_json)
        )
        
        email_data = EmailData(
            email_id='test3',
            subject='Electric bill',
            sender='billing@electric.com',
            content='Your electricity bill for July 2025',
            received_date='2025-07-20'
        )
        
        result = agent.extract_bill_information(email_data)
        
        self.assertIsInstance(result, BillData)
        self.assertEqual(result.company_name, 'Electric Company')
        self.assertEqual(result.amount, 150.75)
        self.assertEqual(result.due_date, '2025-08-15')

if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

**Integration Test Framework (`tests/integration/test_agent_integration.py`)**
```python
import unittest
import tempfile
import os
from pathlib import Path
import sqlite3

from src.core.database import DatabaseManager
from src.core.llm_manager import LLMManager
from src.core.config_manager import ConfigManager
from src.agents.email_scanner.agent import EmailScannerAgent

class AgentIntegrationTest(unittest.TestCase):
    """Integration tests for agents with real dependencies"""
    
    def setUp(self):
        """Set up test environment with real components"""
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db.close()
        
        # Initialize real components
        self.db_manager = DatabaseManager(f"sqlite:///{self.test_db.name}")
        self.llm_manager = LLMManager()
        self.config_manager = ConfigManager()
        
        # Create database tables
        from src.models.base import Base
        Base.metadata.create_all(self.db_manager.engine)
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary database
        os.unlink(self.test_db.name)
    
    @unittest.skipIf(not os.getenv('INTEGRATION_TESTS'), 
                     "Integration tests disabled")
    def test_email_scanner_full_workflow(self):
        """Test complete email scanner workflow"""
        # This would test with real Gmail API and Ollama
        # Only run when INTEGRATION_TESTS environment variable is set
        pass
```

---

## 🚀 Performance Optimization

### LLM Response Optimization

**Response Caching for Agents**
```python
from functools import wraps
import hashlib
import json
from typing import Any, Callable

def cache_llm_response(cache_key_fields: list = None):
    """Decorator to cache LLM responses for agents"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key
            if cache_key_fields:
                key_data = {field: kwargs.get(field) for field in cache_key_fields}
            else:
                key_data = {'args': args, 'kwargs': kwargs}
            
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True).encode()
            ).hexdigest()
            
            # Check cache
            if hasattr(self, 'llm_cache'):
                cached_response = self.llm_cache.get_cached_response(
                    cache_key, 
                    self.llm.model
                )
                if cached_response:
                    return cached_response
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            
            if hasattr(self, 'llm_cache') and result:
                self.llm_cache.cache_response(cache_key, result, self.llm.model)
            
            return result
        return wrapper
    return decorator

class OptimizedEmailScannerAgent(EmailScannerAgent):
    """Email scanner with performance optimizations"""
    
    @cache_llm_response(cache_key_fields=['subject', 'sender'])
    def detect_bill(self, email_data: EmailData) -> bool:
        """Cached bill detection"""
        return super().detect_bill(email_data)
    
    @cache_llm_response(cache_key_fields=['content'])
    def extract_bill_information(self, email_data: EmailData) -> BillData:
        """Cached bill information extraction"""
        return super().extract_bill_information(email_data)
```

### Batch Processing Patterns

**Batch Email Processing**
```python
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

class BatchProcessingMixin:
    """Mixin for batch processing capabilities"""
    
    def process_emails_batch(self, emails: List[Dict], batch_size: int = 5) -> List[ScanResult]:
        """Process emails in batches for better performance"""
        results = []
        
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            batch_results = self._process_email_batch_parallel(batch)
            results.extend(batch_results)
            
            # Rate limiting
            time.sleep(0.1)
        
        return results
    
    def _process_email_batch_parallel(self, email_batch: List[Dict]) -> List[ScanResult]:
        """Process a batch of emails in parallel"""
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(self.process_email, email) 
                for email in email_batch
            ]
            
            results = []
            for future in futures:
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Batch processing error: {e}")
                    # Create error result
                    error_result = ScanResult(
                        email_data=EmailData(email_id='unknown', subject='', sender='', content='', received_date=''),
                        is_bill=False,
                        error=str(e),
                        processed_at=datetime.now()
                    )
                    results.append(error_result)
            
            return results
```

---

## 🔧 Agent Development Guidelines

### Creating New Agents

**Step-by-Step Agent Development Process**

1. **Use Agent Template Generator**
   ```bash
   python scripts/generate_agent.py --name MyNewAgent --type service
   ```

2. **Define Agent Purpose and Scope**
   - Clearly define what the agent does
   - Identify required external services
   - Specify input/output data formats
   - Define success/failure criteria

3. **Implement Core Methods**
   ```python
   class MyNewAgent(BaseAgent):
       def validate_config(self) -> bool:
           # Validate required configuration
           pass
       
       def setup_resources(self):
           # Initialize external services, LLM models, etc.
           pass
       
       def execute_task(self, input_data: Dict[str, Any]) -> AgentResult:
           # Main agent logic
           pass
       
       def cleanup_resources(self):
           # Clean up resources
           pass
   ```

4. **Create Data Models**
   ```python
   # src/agents/my_new_agent/models.py
   from pydantic import BaseModel
   
   class MyAgentInput(BaseModel):
       parameter1: str
       parameter2: int
   
   class MyAgentOutput(BaseModel):
       result: str
       metadata: Dict[str, Any]
   ```

5. **Design Prompts**
   ```python
   # src/agents/my_new_agent/prompts.py
   MAIN_PROMPT = """
   You are an AI assistant specialized in [specific task].
   
   Input: {input_data}
   
   Please [specific instructions]...
   
   Response:
   """
   ```

6. **Write Comprehensive Tests**
   - Unit tests for individual methods
   - Integration tests with real dependencies
   - Error handling tests
   - Performance tests

7. **Create Configuration**
   ```yaml
   # config/agents/my_new_agent.yaml
   name: "My New Agent"
   description: "Agent for doing specific tasks"
   version: "1.0.0"
   
   # Agent-specific settings
   batch_size: 10
   timeout_seconds: 30
   retry_attempts: 3
   
   # External service configuration
   service_config:
     api_endpoint: "https://api.example.com"
     timeout: 10
   ```

### Best Practices

**Code Organization**
- Keep agent logic focused and single-purpose
- Use dependency injection for testability
- Implement proper error handling and logging
- Follow consistent naming conventions
- Document all methods and classes

**Performance Considerations**
- Implement caching for expensive operations
- Use batch processing for multiple items
- Add appropriate timeouts
- Monitor resource usage
- Optimize LLM prompt lengths

**Error Handling**
- Gracefully handle external service failures
- Provide meaningful error messages
- Implement retry logic with exponential backoff
- Log errors with appropriate detail
- Never expose sensitive information in errors

**Security**
- Validate all input data
- Sanitize outputs
- Use secure credential storage
- Implement rate limiting
- Log security-relevant events

### Agent Registry System

**Dynamic Agent Registration (`src/agents/registry.py`)**
```python
from typing import Dict, Type, List
import importlib
import inspect
from pathlib import Path

from src.agents.base_agent import BaseAgent

class AgentRegistry:
    """Central registry for all available agents"""
    
    def __init__(self):
        self.registered_agents: Dict[str, Type[BaseAgent]] = {}
        self.agent_metadata: Dict[str, Dict] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Automatically discover and register agents"""
        agents_dir = Path(__file__).parent
        
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name not in ['__pycache__', 'template']:
                self._register_agent_from_directory(agent_dir)
    
    def _register_agent_from_directory(self, agent_dir: Path):
        """Register agent from directory"""
        try:
            # Import agent module
            module_name = f"src.agents.{agent_dir.name}.agent"
            module = importlib.import_module(module_name)
            
            # Find agent class
            agent_classes = [
                cls for name, cls in inspect.getmembers(module, inspect.isclass)
                if issubclass(cls, BaseAgent) and cls != BaseAgent
            ]
            
            if agent_classes:
                agent_class = agent_classes[0]
                agent_type = agent_dir.name
                
                self.registered_agents[agent_type] = agent_class
                
                # Load metadata from config
                config_file = agent_dir / "config.yaml"
                if config_file.exists():
                    import yaml
                    with open(config_file) as f:
                        self.agent_metadata[agent_type] = yaml.safe_load(f)
                
        except Exception as e:
            print(f"Failed to register agent from {agent_dir}: {e}")
    
    def get_agent_class(self, agent_type: str) -> Type[BaseAgent]:
        """Get agent class by type"""
        if agent_type not in self.registered_agents:
            raise ValueError(f"Agent type '{agent_type}' not found")
        return self.registered_agents[agent_type]
    
    def list_available_agents(self) -> List[Dict]:
        """List all available agents"""
        agents = []
        for agent_type, agent_class in self.registered_agents.items():
            metadata = self.agent_metadata.get(agent_type, {})
            agents.append({
                'type': agent_type,
                'name': metadata.get('name', agent_type),
                'description': metadata.get('description', ''),
                'version': metadata.get('version', '1.0.0'),
                'class': agent_class.__name__
            })
        return agents
    
    def create_agent(self, agent_type: str, agent_id: str, config: Dict,
                    db_manager, llm_manager, config_manager) -> BaseAgent:
        """Create agent instance"""
        agent_class = self.get_agent_class(agent_type)
        return agent_class(
            agent_id=agent_id,
            config=config,
            db_manager=db_manager,
            llm_manager=llm_manager,
            config_manager=config_manager
        )

# Global agent registry
agent_registry = AgentRegistry()
```

This agent design provides a comprehensive framework for building, testing, and optimizing AI agents in the RS Personal Assistant system. The architecture ensures consistency, maintainability, and scalability across all agent implementations.

## Testing Strategy

**Important**: All agent testing must follow the comprehensive patterns and guidelines defined in [Testing Standards](../TESTING.md). The examples below demonstrate agent-specific testing approaches.

### Unit Testing Framework

**Base Test Class (`tests/test_agents/base_agent_test.py`)**
```python
import unittest
from unittest.mock import Mock, patch
from src.agents.base_agent import BaseAgent, AgentResult
from src.core.database import DatabaseManager
from src.core.llm_manager import LLMManager
from src.core.config_manager import ConfigManager

class BaseAgentTest(unittest.TestCase):
    """Base test class for agent testing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_llm_manager = Mock(spec=LLMManager)
        self.mock_config_manager = Mock(spec=ConfigManager)
        
        self.test_config = {
            'name': 'TestAgent',
            'description': 'Test agent for unit testing',
            'version': '1.0.0'
        }
    
    def create_test_agent(self, agent_class, additional_config=None):
        """Helper to create agent instance for testing"""
        config = self.test_config.copy()
        if additional_config:
            config.update(additional_config)
            
        return agent_class(
            agent_id='test-agent-123',
            config=config,
            db_manager=self.mock_db_manager,
            llm_manager=self.mock_llm_manager,
            config_manager=self.mock_config_manager
        )
    
    def assert_agent_result(self, result: AgentResult, expected_success: bool):
        """Helper to assert agent result structure"""
        self.assertIsInstance(result, AgentResult)
        self.assertEqual(result.success, expected_success)
        self.assertIsInstance(result.data, dict)
        self.assertIsInstance(result.message, str)
        self.assertGreater(result.execution_time_ms, 0)
```

**Email Scanner Agent Tests (`tests/test_agents/test_email_scanner.py`)**
```python
import unittest
from unittest.mock import Mock, patch, MagicMock
from src.agents.email_scanner.agent import EmailScannerAgent
from src.agents.email_scanner.models import EmailData, BillData, ScanResult
from tests.test_agents.base_agent_test import BaseAgentTest

class TestEmailScannerAgent(BaseAgentTest):
    """Test cases for Email Scanner Agent"""
    
    def setUp(self):
        super().setUp()
        self.email_scanner_config = {
            'gmail_credentials_path': 'test_credentials.json',
            'batch_size': 5,
            'processed_label': 'processed',
            'bill_label': 'bill'
        }
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_agent_initialization(self, mock_gmail_service):
        """Test agent initializes correctly"""
        agent = self.create_test_agent(
            EmailScannerAgent, 
            self.email_scanner_config
        )
        
        self.assertEqual(agent.name, 'TestAgent')
        self.assertEqual(agent.batch_size, 5)
        mock_gmail_service.assert_called_once()
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test missing required config
        with self.assertRaises(ValueError):
            self.create_test_agent(EmailScannerAgent, {})
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_execute_task_no_emails(self, mock_gmail_service):
        """Test execution with no emails to process"""
        agent = self.create_test_agent(
            EmailScannerAgent,
            self.email_scanner_config
        )
        
        # Mock no emails found
        agent.fetch_unprocessed_emails = Mock(return_value=[])
        
        result = agent.execute_task({'max_emails': 10})
        
        self.assert_agent_result(result, True)
        self.assertEqual(result.data['processed_count'], 0)
        self.assertEqual(result.data['bills_found'], 0)
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_bill_detection(self, mock_gmail_service):
        """Test bill detection functionality"""
        agent = self.create_test_agent(
            EmailScannerAgent,
            self.email_scanner_config
        )
        
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.invoke.return_value = Mock(content="YES")
        agent.llm = mock_llm
        
        email_data = EmailData(
            email_id='test123',
            subject='Your electricity bill',
            sender='power@utility.com',
            content='Your bill is $150.00 due on 2024-01-15',
            received_date='2024-01-01'
        )
        
        result = agent.detect_bill(email_data)
        self.assertTrue(result)
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_bill_information_extraction(self, mock_gmail_service):
        """Test bill information extraction"""
        agent = self.create_test_agent(
            EmailScannerAgent,
            self.email_scanner_config
        )
        
        # Mock LLM response with JSON
        mock_response = Mock()
        mock_response.content = '''{
            "company_name": "Electric Company",
            "amount": 150.00,
            "due_date": "2024-01-15",
            "bill_type": "utilities",
            "account_number": "123456789",
            "description": "Monthly electricity bill"
        }'''
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        agent.llm = mock_llm
        
        email_data = EmailData(
            email_id='test123',
            subject='Your electricity bill',
            sender='power@utility.com',
            content='Your bill is $150.00 due on 2024-01-15',
            received_date='2024-01-01'
        )
        
        result = agent.extract_bill_information(email_data)
        
        self.assertEqual(result.company_name, "Electric Company")
        self.assertEqual(result.amount, 150.00)
        self.assertEqual(result.bill_type, "utilities")
    
    @patch('agents.email_scanner.agent.GmailService')
    def test_error_handling(self, mock_gmail_service):
        """Test error handling in agent execution"""
        agent = self.create_test_agent(
            EmailScannerAgent,
            self.email_scanner_config
        )
        
        # Mock Gmail service to raise exception
        agent.fetch_unprocessed_emails = Mock(
            side_effect=Exception("Gmail API error")
        )
        
        result = agent.execute_task({'max_emails': 10})
        
        self.assert_agent_result(result, False)
        self.assertIn("Gmail API error", result.error)

class TestEmailScannerModels(unittest.TestCase):
    """Test cases for Email Scanner data models"""
    
    def test_email_data_model(self):
        """Test EmailData model validation"""
        email_data = EmailData(
            email_id='test123',
            subject='Test Subject',
            sender='test@example.com',
            content='Test content',
            received_date='2024-01-01'
        )
        
        self.assertEqual(email_data.email_id, 'test123')
        self.assertEqual(email_data.attachments, [])
    
    def test_bill_data_model(self):
        """Test BillData model validation"""
        bill_data = BillData(
            company_name='Test Company',
            amount=100.50,
            due_date='2024-01-15',
            bill_type='utilities'
        )
        
        self.assertEqual(bill_data.amount, 100.50)
        self.assertEqual(bill_data.bill_type, 'utilities')
        
        # Test negative amount validation
        with self.assertRaises(ValueError):
            BillData(
                company_name='Test',
                amount=-50.0
            )
    
    def test_scan_result_to_dict(self):
        """Test ScanResult serialization"""
        email_data = EmailData(
            email_id='test123',
            subject='Test',
            sender='test@example.com',
            content='Test content',
            received_date='2024-01-01'
        )
        
        bill_data = BillData(
            company_name='Test Company',
            amount=100.00
        )
        
        scan_result = ScanResult(
            email_data=email_data,
            is_bill=True,
            bill_data=bill_data,
            processed_at=datetime.now()
        )
        
        result_dict = scan_result.to_dict()
        
        self.assertIn('email_id', result_dict)
        self.assertIn('bill_data', result_dict)
        self.assertTrue(result_dict['is_bill'])

if __name__ == '__main__':
    unittest.main()
```

---

## 🚀 Performance Optimization

### Agent Performance Monitoring

**Performance Tracking (`src/agents/base_agent.py` extension)**
```python
import time
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class PerformanceMetrics:
    """Agent performance metrics"""
    execution_count: int
    average_execution_time_ms: float
    success_rate: float
    error_count: int
    last_execution_time_ms: int
    memory_usage_mb: float
    llm_call_count: int
    llm_total_time_ms: int

class PerformanceTracker:
    """Track agent performance metrics"""
    
    def __init__(self):
        self.execution_times: List[int] = []
        self.success_count: int = 0
        self.error_count: int = 0
        self.llm_call_times: List[int] = []
    
    def record_execution(self, execution_time_ms: int, success: bool):
        """Record execution metrics"""
        self.execution_times.append(execution_time_ms)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def record_llm_call(self, call_time_ms: int):
        """Record LLM call performance"""
        self.llm_call_times.append(call_time_ms)
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        total_executions = len(self.execution_times)
        
        if total_executions == 0:
            return PerformanceMetrics(
                execution_count=0,
                average_execution_time_ms=0,
                success_rate=0,
                error_count=0,
                last_execution_time_ms=0,
                memory_usage_mb=0,
                llm_call_count=0,
                llm_total_time_ms=0
            )
        
        return PerformanceMetrics(
            execution_count=total_executions,
            average_execution_time_ms=sum(self.execution_times) / total_executions,
            success_rate=self.success_count / total_executions,
            error_count=self.error_count,
            last_execution_time_ms=self.execution_times[-1],
            memory_usage_mb=self._get_memory_usage(),
            llm_call_count=len(self.llm_call_times),
            llm_total_time_ms=sum(self.llm_call_times)
        )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
```

### LLM Response Caching

**Agent-Level Caching (`src/agents/mixins/caching_mixin.py`)**
```python
import hashlib
import json
from typing import Optional, Any
from src.core.llm_cache import LLMCache

class CachingMixin:
    """Mixin to add caching capabilities to agents"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = LLMCache(
            cache_db=f"data/cache/{self.__class__.__name__.lower()}_cache.db",
            ttl_hours=self.config.get('cache_ttl_hours', 24)
        )
        self.cache_enabled = self.config.get('enable_cache', True)
    
    def cached_llm_invoke(self, prompt: str, model_name: str = None) -> str:
        """Invoke LLM with caching"""
        if not self.cache_enabled:
            return self.llm.invoke(prompt).content
        
        model_name = model_name or 'default'
        
        # Check cache first
        cached_response = self.cache.get_cached_response(prompt, model_name)
        if cached_response:
            self.logger.debug(f"Cache hit for prompt hash: {self._hash_prompt(prompt)}")
            return cached_response
        
        # Get fresh response
        response = self.llm.invoke(prompt).content
        
        # Cache the response
        self.cache.cache_response(prompt, response, model_name)
        self.logger.debug(f"Cached new response for prompt hash: {self._hash_prompt(prompt)}")
        
        return response
    
    def _hash_prompt(self, prompt: str) -> str:
        """Generate hash for prompt (for logging)"""
        return hashlib.md5(prompt.encode()).hexdigest()[:8]
    
    def clear_agent_cache(self):
        """Clear agent-specific cache"""
        # Implementation to clear cache
        pass
```

---

## 📚 Agent Development Best Practices

### Prompt Engineering Guidelines

1. **Clear Instructions**: Use specific, unambiguous language
2. **Structured Output**: Request JSON or specific formats
3. **Context Management**: Provide relevant context, truncate when necessary
4. **Error Handling**: Include fallback instructions
5. **Validation**: Request self-validation in prompts

### Error Handling Patterns

1. **Graceful Degradation**: Continue operation with reduced functionality
2. **Retry Logic**: Implement exponential backoff for transient failures
3. **Detailed Logging**: Log context and error details
4. **User Communication**: Provide meaningful error messages
5. **State Recovery**: Maintain state for recovery after errors

### Configuration Management

1. **Environment Overrides**: Support environment variable configuration
2. **Validation**: Validate all configuration at startup
3. **Defaults**: Provide sensible defaults for optional settings
4. **Documentation**: Document all configuration options
5. **Hot Reloading**: Support configuration updates without restart

### Testing Standards

1. **Unit Tests**: Test all methods in isolation
2. **Integration Tests**: Test agent interactions with external services
3. **Mock External Services**: Use mocks for Gmail, LLM, database
4. **Error Scenarios**: Test failure modes and error handling
5. **Performance Tests**: Monitor execution time and resource usage

This comprehensive agent design provides a robust framework for building intelligent, maintainable, and testable agents within the RS Personal Assistant system.
