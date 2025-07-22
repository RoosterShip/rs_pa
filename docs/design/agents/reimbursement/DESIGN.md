# Reimbursement Agent Design - RS Personal Assistant

## 📋 Overview

The Reimbursement Agent is an AI-powered component that automatically scans Gmail emails to detect bills and invoices, extracts relevant information, and generates reimbursement reports. This agent helps users track expenses and prepare reimbursement submissions.

## 🎯 Purpose and Scope

### Primary Functions
- Scan Gmail inbox for emails containing bills or invoices
- Use LLM to intelligently detect and classify expense-related emails
- Extract structured data from bills (amount, due date, vendor, etc.)
- Generate formatted reimbursement reports
- Track processed emails to avoid duplication
- Maintain audit trail of detected expenses

### Key Benefits
- Automates tedious expense tracking
- Reduces missed reimbursement opportunities
- Provides consistent expense categorization
- Generates professional reimbursement reports
- Maintains complete audit trail

## 📧 Agent Implementation

### Agent Structure

**Reimbursement Agent (`src/agents/reimbursement/agent.py`)**
```python
from src.agents.base_agent import BaseAgent, AgentResult
from src.agents.reimbursement.prompts import BILL_DETECTION_PROMPT, EXTRACT_BILL_INFO_PROMPT
from src.agents.reimbursement.models import EmailData, BillData, ScanResult
from src.core.gmail_service import GmailService
from typing import Dict, Any, List
import json
from datetime import datetime

class ReimbursementAgent(BaseAgent):
    """Agent for scanning emails and detecting reimbursable expenses"""
    
    def setup_resources(self):
        """Set up Gmail service and LLM model"""
        self.gmail_service = GmailService(
            credentials_path=self.config.get('gmail_credentials_path'),
            scopes=self.config.get('gmail_scopes', ['https://mail.google.com/'])
        )
        
        self.llm = self.llm_manager.get_model(
            model_name=self.config.get('llm_model', 'llama4:maverick')
        )
        
        # Agent-specific configuration
        self.batch_size = self.config.get('batch_size', 10)
        self.processed_label = self.config.get('processed_label', 'rspa_processed')
        self.reimbursable_label = self.config.get('reimbursable_label', 'rspa_reimbursable')
        self.expense_categories = self.config.get('expense_categories', [
            'travel', 'meals', 'supplies', 'software', 'equipment', 'other'
        ])
    
    def validate_config(self) -> bool:
        """Validate reimbursement agent configuration"""
        required_fields = ['gmail_credentials_path']
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required configuration: {field}")
        return True
    
    def cleanup_resources(self):
        """Clean up resources"""
        if hasattr(self, 'gmail_service'):
            self.gmail_service.close()
    
    def execute_task(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute reimbursement scanning task"""
        try:
            # Get task parameters
            max_emails = input_data.get('max_emails', self.batch_size)
            force_rescan = input_data.get('force_rescan', False)
            date_range = input_data.get('date_range', None)  # e.g., {'start': '2025-01-01', 'end': '2025-01-31'}
            
            # Fetch unprocessed emails
            emails = self.fetch_unprocessed_emails(max_emails, force_rescan, date_range)
            
            if not emails:
                return AgentResult(
                    success=True,
                    data={'processed_count': 0, 'reimbursable_found': 0},
                    message="No unprocessed emails found"
                )
            
            # Process emails
            scan_results = []
            reimbursable_found = 0
            
            for email in emails:
                result = self.process_email(email)
                scan_results.append(result)
                
                if result.is_reimbursable:
                    reimbursable_found += 1
                    self.gmail_service.add_label(email['id'], self.reimbursable_label)
                
                # Mark as processed
                self.gmail_service.add_label(email['id'], self.processed_label)
            
            # Generate reimbursement report
            report = self.generate_reimbursement_report(scan_results, date_range)
            
            # Store results
            self.save_scan_results(scan_results)
            
            return AgentResult(
                success=True,
                data={
                    'processed_count': len(scan_results),
                    'reimbursable_found': reimbursable_found,
                    'scan_results': [result.to_dict() for result in scan_results],
                    'reimbursement_report': report
                },
                message=f"Processed {len(scan_results)} emails, found {reimbursable_found} reimbursable expenses"
            )
            
        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message="Reimbursement scanning failed",
                error=str(e)
            )
    
    def fetch_unprocessed_emails(self, max_emails: int, force_rescan: bool, date_range: Dict = None) -> List[Dict]:
        """Fetch emails that haven't been processed"""
        query_parts = []
        
        if not force_rescan:
            query_parts.append(f"-label:{self.processed_label}")
        
        if date_range:
            if 'start' in date_range:
                query_parts.append(f"after:{date_range['start']}")
            if 'end' in date_range:
                query_parts.append(f"before:{date_range['end']}")
        
        # Add keywords that might indicate bills/invoices
        bill_keywords = "subject:(bill OR invoice OR receipt OR payment OR statement)"
        query_parts.append(bill_keywords)
        
        query = " ".join(query_parts) if query_parts else "in:inbox"
        
        emails = self.gmail_service.search_messages(
            query=query,
            max_results=max_emails
        )
        
        # Get email content
        email_data = []
        for email in emails:
            content = self.gmail_service.get_message_content(email['id'])
            email_data.append({
                'id': email['id'],
                'subject': content.get('subject', ''),
                'sender': content.get('from', ''),
                'content': content.get('body', ''),
                'received_date': content.get('date', ''),
                'attachments': content.get('attachments', [])
            })
        
        return email_data
    
    def process_email(self, email: Dict) -> ScanResult:
        """Process individual email for reimbursable expense detection"""
        try:
            # Create email data object
            email_data = EmailData(
                email_id=email['id'],
                subject=email['subject'],
                sender=email['sender'],
                content=email['content'],
                received_date=email['received_date']
            )
            
            # Use LLM to detect if email contains reimbursable expense
            is_reimbursable = self.detect_reimbursable_expense(email_data)
            
            expense_data = None
            if is_reimbursable:
                # Extract expense information
                expense_data = self.extract_expense_information(email_data)
            
            return ScanResult(
                email_data=email_data,
                is_reimbursable=is_reimbursable,
                expense_data=expense_data,
                processed_at=datetime.now()
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to process email {email['id']}: {e}")
            return ScanResult(
                email_data=EmailData(
                    email_id=email['id'],
                    subject=email.get('subject', ''),
                    sender=email.get('sender', ''),
                    content='',
                    received_date=''
                ),
                is_reimbursable=False,
                error=str(e),
                processed_at=datetime.now()
            )
    
    def detect_reimbursable_expense(self, email_data: EmailData) -> bool:
        """Use LLM to detect if email contains a reimbursable expense"""
        prompt = BILL_DETECTION_PROMPT.format(
            subject=email_data.subject,
            sender=email_data.sender,
            content=email_data.content[:2000]  # Truncate for efficiency
        )
        
        try:
            response = self.llm.invoke(prompt)
            # Parse response - expect "YES" or "NO"
            return "YES" in response.content.upper()
        except Exception as e:
            self.logger.error(f"LLM expense detection failed: {e}")
            return False
    
    def extract_expense_information(self, email_data: EmailData) -> BillData:
        """Extract structured expense information using LLM"""
        prompt = EXTRACT_BILL_INFO_PROMPT.format(
            subject=email_data.subject,
            sender=email_data.sender,
            content=email_data.content,
            categories=", ".join(self.expense_categories)
        )
        
        try:
            response = self.llm.invoke(prompt)
            # Parse JSON response
            expense_info = json.loads(response.content)
            
            return BillData(
                company_name=expense_info.get('company_name', ''),
                amount=float(expense_info.get('amount', 0.0)),
                expense_date=expense_info.get('expense_date', ''),
                category=expense_info.get('category', 'other'),
                description=expense_info.get('description', ''),
                payment_method=expense_info.get('payment_method', ''),
                project_code=expense_info.get('project_code', ''),
                is_reimbursable=True
            )
            
        except Exception as e:
            self.logger.error(f"Expense information extraction failed: {e}")
            return BillData(
                company_name=email_data.sender,
                amount=0.0,
                expense_date='',
                category='other',
                description=f"Extraction failed: {str(e)}",
                is_reimbursable=False
            )
    
    def generate_reimbursement_report(self, scan_results: List[ScanResult], date_range: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive reimbursement report"""
        reimbursable_expenses = [
            result for result in scan_results 
            if result.is_reimbursable and result.expense_data
        ]
        
        total_amount = sum(
            expense.expense_data.amount for expense in reimbursable_expenses
        )
        
        # Group expenses by category
        expenses_by_category = {}
        for expense in reimbursable_expenses:
            category = expense.expense_data.category
            if category not in expenses_by_category:
                expenses_by_category[category] = {
                    'expenses': [],
                    'total': 0.0
                }
            expenses_by_category[category]['expenses'].append(expense.expense_data)
            expenses_by_category[category]['total'] += expense.expense_data.amount
        
        # Generate formatted report
        report_text = self.format_reimbursement_report(
            expenses_by_category, 
            total_amount,
            date_range
        )
        
        return {
            'report_date': datetime.now().isoformat(),
            'date_range': date_range,
            'total_expenses': len(reimbursable_expenses),
            'total_amount': total_amount,
            'expenses_by_category': {
                cat: {
                    'count': len(data['expenses']),
                    'total': data['total'],
                    'expenses': [exp.to_dict() for exp in data['expenses']]
                }
                for cat, data in expenses_by_category.items()
            },
            'formatted_report': report_text,
            'csv_data': self.generate_csv_data(reimbursable_expenses)
        }
    
    def format_reimbursement_report(self, expenses_by_category: Dict, total_amount: float, date_range: Dict = None) -> str:
        """Format professional reimbursement report"""
        report_lines = [
            "# Reimbursement Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ""
        ]
        
        if date_range:
            report_lines.append(f"Period: {date_range.get('start', 'N/A')} to {date_range.get('end', 'N/A')}")
            report_lines.append("")
        
        report_lines.extend([
            "## Summary",
            f"Total Reimbursable Amount: ${total_amount:.2f}",
            f"Number of Expenses: {sum(len(data['expenses']) for data in expenses_by_category.values())}",
            "",
            "## Expenses by Category"
        ])
        
        for category, data in sorted(expenses_by_category.items()):
            report_lines.extend([
                "",
                f"### {category.title()} - ${data['total']:.2f}",
                ""
            ])
            
            for expense in data['expenses']:
                report_lines.extend([
                    f"- **{expense.company_name}**",
                    f"  - Amount: ${expense.amount:.2f}",
                    f"  - Date: {expense.expense_date}",
                    f"  - Description: {expense.description}",
                    f"  - Payment Method: {expense.payment_method}" if expense.payment_method else "",
                    f"  - Project Code: {expense.project_code}" if expense.project_code else "",
                    ""
                ])
        
        return "\n".join(line for line in report_lines if line is not None)
    
    def generate_csv_data(self, expenses: List[ScanResult]) -> str:
        """Generate CSV data for expense export"""
        csv_lines = [
            "Date,Vendor,Category,Amount,Description,Payment Method,Project Code"
        ]
        
        for expense in expenses:
            if expense.expense_data:
                data = expense.expense_data
                csv_lines.append(
                    f'"{data.expense_date}","{data.company_name}","{data.category}",'
                    f'"{data.amount:.2f}","{data.description}","{data.payment_method}",'
                    f'"{data.project_code}"'
                )
        
        return "\n".join(csv_lines)
    
    def save_scan_results(self, scan_results: List[ScanResult]):
        """Save scan results to database"""
        results_data = {
            'scan_date': datetime.now().isoformat(),
            'results': [result.to_dict() for result in scan_results]
        }
        
        self.save_agent_data('last_reimbursement_scan', results_data)
```

### Agent Prompts

**Prompt Templates (`src/agents/reimbursement/prompts.py`)**
```python
BILL_DETECTION_PROMPT = """
Analyze the following email to determine if it contains a reimbursable expense (bill, invoice, or receipt).

Email Details:
Subject: {subject}
Sender: {sender}
Content: {content}

A reimbursable expense typically contains:
- Payment amounts or monetary values
- Purchase/transaction dates
- Vendor/company information
- Description of goods or services
- Receipt or invoice number
- Payment confirmation

Business expenses that are typically reimbursable include:
- Travel expenses (flights, hotels, transportation)
- Meals and entertainment (business meals)
- Office supplies and equipment
- Software subscriptions
- Professional services
- Conference or training fees

Personal expenses that are NOT reimbursable:
- Personal shopping
- Personal subscriptions (Netflix, Spotify, etc.)
- Personal travel
- Groceries (unless for business event)

Respond with exactly "YES" if this email contains a reimbursable business expense, or "NO" if it does not.

Response:
"""

EXTRACT_BILL_INFO_PROMPT = """
Extract structured information from this reimbursable expense email.

Email Details:
Subject: {subject}
Sender: {sender}
Content: {content}

Available expense categories: {categories}

Please extract the following information and respond with valid JSON:

{{
  "company_name": "Name of the vendor/company",
  "amount": "Total amount (number only, no currency symbols)",
  "expense_date": "Date of expense in YYYY-MM-DD format",
  "category": "One of the available categories that best fits",
  "description": "Brief description of the expense",
  "payment_method": "Credit card, debit card, cash, check, etc.",
  "project_code": "Project or client code if mentioned",
  "invoice_number": "Invoice or receipt number if available"
}}

If any information is not available, use empty string "" for text fields or 0.0 for amount.

JSON Response:
"""

GENERATE_REPORT_PROMPT = """
Generate a professional reimbursement report based on the following expense information:

Expenses Found:
{expenses_data}

Total Amount: ${total_amount}
Report Period: {report_period}

Create a formatted report that includes:
1. Executive summary with total reimbursable amount
2. Itemized list of expenses by category
3. Subtotals for each category
4. Any special notes or observations
5. Submission instructions

Format the report professionally for submission to management or accounting.

Report:
"""
```

### Data Models

**Pydantic Models (`src/agents/reimbursement/models.py`)**
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EmailData(BaseModel):
    """Email data structure"""
    email_id: str
    subject: str
    sender: str
    content: str
    received_date: str
    attachments: Optional[List[str]] = []
    
class BillData(BaseModel):
    """Reimbursable expense information extracted from email"""
    company_name: str
    amount: float = Field(ge=0)
    expense_date: Optional[str] = None
    category: str = "other"
    description: Optional[str] = None
    payment_method: Optional[str] = None
    project_code: Optional[str] = None
    invoice_number: Optional[str] = None
    is_reimbursable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
class ScanResult(BaseModel):
    """Result of scanning a single email"""
    email_data: EmailData
    is_reimbursable: bool
    expense_data: Optional[BillData] = None
    error: Optional[str] = None
    processed_at: datetime
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'email_id': self.email_data.email_id,
            'subject': self.email_data.subject,
            'sender': self.email_data.sender,
            'is_reimbursable': self.is_reimbursable,
            'processed_at': self.processed_at.isoformat()
        }
        
        if self.expense_data:
            result['expense_data'] = self.expense_data.to_dict()
        
        if self.error:
            result['error'] = self.error
            
        if self.confidence_score:
            result['confidence_score'] = self.confidence_score
            
        return result

class ReimbursementReport(BaseModel):
    """Generated reimbursement report"""
    report_date: datetime
    date_range: Optional[Dict[str, str]] = None
    total_expenses: int
    total_amount: float
    expenses_by_category: Dict[str, List[BillData]]
    formatted_report: str
    csv_data: str
```

## 🔧 Configuration

### Agent Configuration File

**Configuration (`config/agents/reimbursement.yaml`)**
```yaml
name: "Reimbursement Agent"
description: "Automatically scans Gmail for reimbursable expenses and generates reports"
version: "1.0.0"

# Gmail Configuration
gmail_credentials_path: "config/credentials/gmail_credentials.json"
gmail_scopes:
  - "https://mail.google.com/"

# Processing Configuration
batch_size: 20
processed_label: "rspa_processed"
reimbursable_label: "rspa_reimbursable"

# LLM Configuration
llm_model: "llama4:maverick"
temperature: 0.1
max_retries: 3

# Expense Categories
expense_categories:
  - travel
  - meals
  - supplies
  - software
  - equipment
  - services
  - training
  - other

# Caching
enable_cache: true
cache_ttl_hours: 24

# Performance
max_concurrent_emails: 5
timeout_seconds: 30
```

## 🧪 Testing

### Unit Tests

**Test Cases (`tests/agents/test_reimbursement.py`)**
```python
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.agents.reimbursement.agent import ReimbursementAgent
from src.agents.reimbursement.models import EmailData, BillData, ScanResult

class TestReimbursementAgent(unittest.TestCase):
    """Test cases for Reimbursement Agent"""
    
    def setUp(self):
        self.config = {
            'gmail_credentials_path': 'test_creds.json',
            'batch_size': 5,
            'expense_categories': ['travel', 'meals', 'supplies']
        }
        
    def test_detect_reimbursable_positive(self):
        """Test detection of reimbursable expense"""
        # Test implementation
        pass
    
    def test_extract_expense_information(self):
        """Test expense information extraction"""
        # Test implementation
        pass
    
    def test_generate_report(self):
        """Test report generation"""
        # Test implementation
        pass
```

## 📊 Usage Examples

### Basic Usage

```python
# Initialize agent
reimbursement_agent = ReimbursementAgent(
    agent_id="reimb-001",
    config=config,
    db_manager=db_manager,
    llm_manager=llm_manager,
    config_manager=config_manager
)

# Scan emails for current month
result = reimbursement_agent.run({
    'max_emails': 50,
    'date_range': {
        'start': '2025-01-01',
        'end': '2025-01-31'
    }
})

# Access the report
if result.success:
    print(f"Found {result.data['reimbursable_found']} expenses")
    print(f"Total amount: ${result.data['reimbursement_report']['total_amount']}")
    print(result.data['reimbursement_report']['formatted_report'])
```

### Advanced Usage

```python
# Force rescan with specific parameters
result = reimbursement_agent.run({
    'max_emails': 100,
    'force_rescan': True,
    'date_range': {
        'start': '2024-01-01',
        'end': '2024-12-31'
    }
})

# Export to CSV
if result.success:
    csv_data = result.data['reimbursement_report']['csv_data']
    with open('expenses_2024.csv', 'w') as f:
        f.write(csv_data)
```

## 🚀 Performance Optimization

### Caching Strategy
- Cache LLM responses for similar emails
- Store processed email IDs to avoid reprocessing
- Cache expense categorization patterns

### Batch Processing
- Process emails in configurable batches
- Parallel processing for email analysis
- Rate limiting to avoid Gmail API limits

### Resource Management
- Automatic connection pooling for Gmail API
- LLM request queuing and throttling
- Memory-efficient email content processing

## 🔒 Security Considerations

### Data Protection
- Credentials stored securely using encryption
- No sensitive data logged
- Secure handling of financial information

### Access Control
- Gmail OAuth2 authentication
- Minimal required permissions
- Audit trail of all operations

### Privacy
- Local processing only
- No data sent to external services
- User control over data retention

## 🎯 Future Enhancements

### Planned Features
1. **Receipt Image Processing**: OCR for attached receipt images
2. **Multi-Currency Support**: Handle expenses in different currencies
3. **Approval Workflow**: Integration with approval systems
4. **Tax Categorization**: Identify tax-deductible expenses
5. **Mileage Tracking**: Integrate with calendar for travel expenses
6. **Corporate Card Integration**: Match expenses with card statements
7. **Policy Compliance**: Check expenses against company policies
8. **Mobile App Integration**: Submit expenses from mobile devices

### Integration Opportunities
- QuickBooks/Xero export
- Slack notifications
- Calendar integration for travel expenses
- Corporate expense management systems