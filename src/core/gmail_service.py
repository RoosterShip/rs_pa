"""
Gmail service for OAuth2 authentication and email access.

This module provides Gmail API integration with OAuth2 desktop flow
for accessing and processing emails in the RS Personal Agent.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class GmailService(QObject):
    """
    Gmail service for OAuth2 authentication and email access.

    This service handles OAuth2 authentication flow and provides
    methods for accessing Gmail emails with proper error handling.
    """

    # Signals for UI updates
    connection_status_changed = Signal(str)  # "connected", "disconnected", "error"
    authentication_required = Signal()
    error_occurred = Signal(str)

    # Gmail API scopes - readonly for safety
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the Gmail service.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service: Optional[Any] = None
        self._credentials: Optional[Credentials] = None
        self._credentials_file: Optional[str] = None
        self._token_file: Optional[str] = None
        self._is_connected = False

        # Set up file paths
        self._setup_file_paths()

    def _setup_file_paths(self) -> None:
        """Set up file paths for credentials and tokens."""
        # Get app data directory
        from appdirs import user_data_dir

        app_dir = Path(user_data_dir("RS Personal Agent", "Roostership"))
        app_dir.mkdir(parents=True, exist_ok=True)

        self._token_file = str(app_dir / "gmail_token.json")

        # Credentials file should be provided by user
        # Default location for development
        self._credentials_file = str(Path.cwd() / "credentials.json")

    def set_credentials_file(self, file_path: str) -> None:
        """
        Set the path to the OAuth2 credentials file.

        Args:
            file_path: Path to the credentials.json file from Google Cloud Console
        """
        self._credentials_file = file_path

    def is_connected(self) -> bool:
        """
        Check if Gmail service is connected and authenticated.

        Returns:
            True if connected and authenticated
        """
        return self._is_connected and self._service is not None

    def get_connection_status(self) -> str:
        """
        Get current connection status.

        Returns:
            Connection status: "connected", "disconnected", or "error"
        """
        if self.is_connected():
            return "connected"
        elif self._credentials and not self._credentials.valid:
            return "error"
        else:
            return "disconnected"

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail using OAuth2 desktop flow.

        Returns:
            True if authentication successful
        """
        try:
            logger.info("Starting Gmail authentication")

            # Load existing credentials
            self._load_credentials()

            # Check if credentials need refresh
            if (
                self._credentials
                and self._credentials.expired
                and self._credentials.refresh_token
            ):
                logger.info("Refreshing expired credentials")
                self._credentials.refresh(Request())

            # If no valid credentials, run OAuth flow
            if not self._credentials or not self._credentials.valid:
                if not self._credentials_file or not os.path.exists(
                    self._credentials_file
                ):
                    logger.error(
                        f"Credentials file not found: {self._credentials_file}"
                    )
                    self.error_occurred.emit(
                        "Gmail credentials file not found. Please add "
                        "credentials.json to the project directory."
                    )
                    return False

                logger.info("Running OAuth2 flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_file, self.SCOPES
                )
                self._credentials = flow.run_local_server(port=0)

            # Save credentials for next run
            self._save_credentials()

            # Build Gmail service
            self._service = build("gmail", "v1", credentials=self._credentials)
            self._is_connected = True

            logger.info("Gmail authentication successful")
            self.connection_status_changed.emit("connected")
            return True

        except FileNotFoundError:
            error_msg = "Gmail credentials file not found"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.connection_status_changed.emit("error")
            return False

        except HttpError as error:
            error_msg = f"Gmail API error: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.connection_status_changed.emit("error")
            return False

        except Exception as error:
            error_msg = f"Gmail authentication failed: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.connection_status_changed.emit("error")
            return False

    def _load_credentials(self) -> None:
        """Load credentials from token file."""
        if self._token_file and os.path.exists(self._token_file):
            try:
                with open(self._token_file, "r") as token:
                    creds_data = json.load(token)
                    self._credentials = Credentials.from_authorized_user_info(
                        creds_data, self.SCOPES
                    )
                logger.info("Loaded existing credentials")
            except Exception as error:
                logger.warning(f"Could not load credentials: {error}")

    def _save_credentials(self) -> None:
        """Save credentials to token file."""
        if self._credentials and self._token_file:
            try:
                with open(self._token_file, "w") as token:
                    token.write(self._credentials.to_json())
                logger.info("Saved credentials to token file")
            except Exception as error:
                logger.warning(f"Could not save credentials: {error}")

    def test_connection(self) -> bool:
        """
        Test the Gmail connection by making a simple API call.

        Returns:
            True if connection test successful
        """
        if not self.is_connected() or not self._service:
            return False

        try:
            # Simple test - get user profile
            profile = self._service.users().getProfile(userId="me").execute()
            logger.info(
                f"Gmail connection test successful for {profile.get('emailAddress')}"
            )
            return True

        except HttpError as error:
            error_msg = f"Gmail connection test failed: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        except Exception as error:
            error_msg = f"Gmail connection test error: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def get_recent_messages(
        self, query: str = "", max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent Gmail messages based on query.

        Args:
            query: Gmail search query (e.g., "has:attachment")
            max_results: Maximum number of messages to retrieve

        Returns:
            List of message dictionaries with basic info
        """
        if not self.is_connected() or not self._service:
            logger.error("Gmail service not connected")
            return []

        try:
            # Search for messages
            results = (
                self._service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])
            message_details = []

            # Get details for each message
            for message in messages:
                msg_detail = (
                    self._service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message["id"],
                        format="metadata",
                        metadataHeaders=["Subject", "From", "Date"],
                    )
                    .execute()
                )

                # Extract headers
                headers = {
                    header["name"]: header["value"]
                    for header in msg_detail["payload"].get("headers", [])
                }

                message_info = {
                    "id": message["id"],
                    "subject": headers.get("Subject", "No Subject"),
                    "from": headers.get("From", "Unknown Sender"),
                    "date": headers.get("Date", "Unknown Date"),
                    "snippet": msg_detail.get("snippet", ""),
                    "thread_id": msg_detail.get("threadId", ""),
                }

                message_details.append(message_info)

            logger.info(f"Retrieved {len(message_details)} Gmail messages")
            return message_details

        except HttpError as error:
            error_msg = f"Failed to retrieve Gmail messages: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []

        except Exception as error:
            error_msg = f"Gmail message retrieval error: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return []

    def get_message_content(self, message_id: str) -> Dict[str, Any]:
        """
        Get full content of a specific Gmail message.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with message content and metadata
        """
        if not self.is_connected() or not self._service:
            logger.error("Gmail service not connected")
            return {}

        try:
            message = (
                self._service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            # Extract headers
            headers = {
                header["name"]: header["value"]
                for header in message["payload"].get("headers", [])
            }

            # Extract body content
            body = self._extract_message_body(message["payload"])

            return {
                "id": message_id,
                "subject": headers.get("Subject", "No Subject"),
                "from": headers.get("From", "Unknown Sender"),
                "date": headers.get("Date", "Unknown Date"),
                "to": headers.get("To", "Unknown Recipient"),
                "body": body,
                "snippet": message.get("snippet", ""),
                "thread_id": message.get("threadId", ""),
                "label_ids": message.get("labelIds", []),
            }

        except HttpError as error:
            error_msg = f"Failed to retrieve Gmail message content: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return {}

        except Exception as error:
            error_msg = f"Gmail message content error: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return {}

    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract text body from Gmail message payload.

        Args:
            payload: Gmail message payload

        Returns:
            Message body as string
        """
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    import base64

                    body += base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
        elif payload["mimeType"] == "text/plain" and "data" in payload["body"]:
            import base64

            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")

        return body

    def disconnect_service(self) -> None:
        """Disconnect from Gmail service."""
        self._service = None
        self._is_connected = False
        logger.info("Gmail service disconnected")
        self.connection_status_changed.emit("disconnected")

    def get_user_email(self) -> str:
        """
        Get the authenticated user's email address.

        Returns:
            User's email address or empty string if not connected
        """
        if not self.is_connected() or not self._service:
            return ""

        try:
            profile = self._service.users().getProfile(userId="me").execute()
            return str(profile.get("emailAddress", ""))
        except Exception as error:
            logger.error(f"Could not get user email: {error}")
            return ""
