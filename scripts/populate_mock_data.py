#!/usr/bin/env python3
"""
Script to populate the database with mock agent data.

This script creates sample agents in the database for development and testing purposes.
It can be run standalone or imported as a module.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database import get_db_session
from src.models.agent import Agent, AgentStatus, AgentType


def create_mock_agents() -> None:
    """Create mock agents in the database."""
    
    # Mock agent data
    mock_agents = [
        {
            "name": "Email Scanner",
            "agent_type": AgentType.EMAIL_SCANNER.value,
            "status": AgentStatus.RUNNING.value,
            "description": "Scans emails for reimbursable expenses and important information",
            "last_run": datetime.utcnow() - timedelta(minutes=2),
            "run_count": 156,
            "enabled": True,
            "auto_start": True,
            "config": {
                "scan_interval": 300,
                "inbox_folder": "INBOX", 
                "keywords": ["receipt", "invoice", "bill", "expense"],
                "confidence_threshold": 0.8
            }
        },
        {
            "name": "Task Manager",
            "agent_type": AgentType.TASK_MANAGER.value,
            "status": AgentStatus.IDLE.value,
            "description": "Manages and organizes daily tasks and productivity workflows",
            "last_run": datetime.utcnow() - timedelta(hours=1, minutes=15),
            "run_count": 89,
            "enabled": True,
            "auto_start": False,
            "config": {
                "priority_levels": ["high", "medium", "low"],
                "auto_categorize": True,
                "reminder_intervals": [60, 30, 10]
            }
        },
        {
            "name": "Calendar Agent", 
            "agent_type": AgentType.CALENDAR_AGENT.value,
            "status": AgentStatus.ERROR.value,
            "description": "Handles calendar events, scheduling, and meeting coordination",
            "last_run": datetime.utcnow() - timedelta(hours=3, minutes=45),
            "last_error": "Failed to authenticate with calendar service - token expired",
            "run_count": 234,
            "enabled": True,
            "auto_start": True,
            "config": {
                "calendar_sources": ["primary", "work"],
                "sync_interval": 900,
                "notification_lead_time": 15
            }
        },
        {
            "name": "Document Processor",
            "agent_type": AgentType.DOCUMENT_PROCESSOR.value,
            "status": AgentStatus.DISABLED.value,
            "description": "Processes and analyzes documents for content extraction",
            "last_run": datetime.utcnow() - timedelta(days=2, hours=5),
            "run_count": 45,
            "enabled": False,
            "auto_start": False,
            "config": {
                "supported_formats": ["pdf", "docx", "txt"],
                "ocr_enabled": True,
                "max_file_size_mb": 10
            }
        },
        {
            "name": "Reimbursement Agent",
            "agent_type": AgentType.REIMBURSEMENT_AGENT.value,
            "status": AgentStatus.RUNNING.value,
            "description": "Specialized agent for processing reimbursement requests from emails",
            "last_run": datetime.utcnow() - timedelta(minutes=8),
            "run_count": 312,
            "enabled": True,
            "auto_start": True,
            "config": {
                "expense_categories": ["travel", "meals", "office", "equipment"],
                "currency": "USD",
                "min_amount": 5.00,
                "require_receipts": True
            }
        }
    ]
    
    with get_db_session() as session:
        # Check if we already have agents (avoid duplicates)
        existing_count = session.query(Agent).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} agents. Skipping mock data creation.")
            return
        
        # Create agents
        created_agents = []
        for agent_data in mock_agents:
            agent = Agent(**agent_data)
            session.add(agent)
            created_agents.append(agent)
        
        # Commit all agents
        session.commit()
        
        print(f"Successfully created {len(created_agents)} mock agents:")
        for agent in created_agents:
            print(f"  - {agent.name} ({agent.agent_type}) - {agent.status}")


def clear_agents() -> None:
    """Clear all agents from the database."""
    with get_db_session() as session:
        deleted_count = session.query(Agent).delete()
        session.commit()
        print(f"Deleted {deleted_count} agents from the database.")


def list_agents() -> None:
    """List all agents in the database."""
    with get_db_session() as session:
        agents = session.query(Agent).all()
        
        if not agents:
            print("No agents found in the database.")
            return
        
        print(f"Found {len(agents)} agents:")
        print("-" * 80)
        for agent in agents:
            print(f"ID: {agent.id}")
            print(f"Name: {agent.name}")
            print(f"Type: {agent.agent_type}")
            print(f"Status: {agent.status}")
            print(f"Enabled: {agent.enabled}")
            print(f"Last Run: {agent.last_run}")
            print(f"Run Count: {agent.run_count}")
            if agent.last_error:
                print(f"Last Error: {agent.last_error}")
            print("-" * 80)


def main() -> None:
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python populate_mock_data.py [create|clear|list]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        if command == "create":
            create_mock_agents()
        elif command == "clear":
            clear_agents()
        elif command == "list":
            list_agents()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: create, clear, list")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()