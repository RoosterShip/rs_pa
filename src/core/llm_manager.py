"""
Ollama LLM manager for local AI model integration.

This module provides Ollama LangChain integration and management
for local LLM inference in the RS Personal Agent.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama
from PySide6.QtCore import QObject, Signal

from .llm_cache import get_llm_cache

logger = logging.getLogger(__name__)


class OllamaManager(QObject):
    """
    Ollama manager for local LLM integration using LangChain.

    This service handles connection to Ollama server using LangChain ChatOllama
    and provides methods for LLM inference with proper error handling.
    """

    # Signals for UI updates
    connection_status_changed = Signal(str)  # "connected", "disconnected", "error"
    model_loaded = Signal(str)  # model name
    inference_started = Signal()
    inference_completed = Signal(str)  # response
    error_occurred = Signal(str)

    def __init__(
        self,
        host: str = "localhost",
        port: int = 11434,
        default_model: str = "hf.co/unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF:latest",
        parent: Optional[QObject] = None,
    ):
        """
        Initialize the Ollama manager.

        Args:
            host: Ollama server host
            port: Ollama server port
            default_model: Default model to use
            parent: Parent QObject
        """
        super().__init__(parent)
        self._host = host
        self._port = port
        self._default_model = default_model
        self._chat_ollama: Optional[ChatOllama] = None
        self._is_connected = False
        self._available_models: List[str] = []
        self._current_model: Optional[str] = None

        # Initialize cache
        self._cache = get_llm_cache()

        # Load configuration from environment
        self._temperature = float(os.environ.get("RSPA_OLLAMA_TEMPERATURE", "0.7"))
        self._timeout = float(os.environ.get("RSPA_OLLAMA_TIMEOUT", "120.0"))
        self._max_retries = int(os.environ.get("RSPA_OLLAMA_MAX_RETRIES", "3"))

        # Create client
        self._create_client()

    def _create_client(self) -> None:
        """Create ChatOllama client with current settings."""
        try:
            base_url = f"http://{self._host}:{self._port}"
            self._chat_ollama = ChatOllama(
                model=self._default_model,
                base_url=base_url,
                temperature=0.7,
            )
            logger.info(f"Created ChatOllama client for {base_url}")
        except Exception as error:
            logger.error(f"Failed to create ChatOllama client: {error}")
            self._chat_ollama = None

    def set_server_config(self, host: str, port: int) -> None:
        """
        Update Ollama server configuration.

        Args:
            host: New server host
            port: New server port
        """
        self._host = host
        self._port = port
        self._create_client()

        # Reset connection status
        self._is_connected = False
        self.connection_status_changed.emit("disconnected")

    def set_default_model(self, model: str) -> None:
        """
        Set the default model to use.

        Args:
            model: Model name (e.g., "llama3.2", "llama3.2:7b")
        """
        self._default_model = model
        logger.info(f"Set default model to {model}")

    def is_connected(self) -> bool:
        """
        Check if Ollama service is connected and ready.

        Returns:
            True if connected and ready
        """
        return self._is_connected and self._chat_ollama is not None

    def get_connection_status(self) -> str:
        """
        Get current connection status.

        Returns:
            Connection status: "connected", "disconnected", or "error"
        """
        if self.is_connected():
            return "connected"
        elif self._chat_ollama is None:
            return "error"
        else:
            return "disconnected"

    def test_connection(self) -> bool:
        """
        Test the Ollama connection by attempting a simple inference.

        Returns:
            True if connection test successful
        """
        if not self._chat_ollama:
            logger.error("ChatOllama client not initialized")
            return False

        try:
            logger.info("Testing Ollama connection")

            # Test with a minimal prompt to avoid long generation
            from langchain_core.messages import HumanMessage

            # Test with a minimal prompt - we don't need to store the response
            self._chat_ollama.invoke([HumanMessage(content="Hi")])

            self._is_connected = True
            self._current_model = self._default_model

            logger.info("Ollama connection successful.")
            self.connection_status_changed.emit("connected")
            return True

        except Exception as error:
            error_msg = f"Ollama connection failed: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.connection_status_changed.emit("error")
            return False

    def get_available_models(self) -> List[str]:
        """
        Get list of available models on the Ollama server.

        Note: With ChatOllama, we return common model names.
        In a production environment, this could query the Ollama API directly.

        Returns:
            List of model names
        """
        # Return common Ollama model names
        # This is a simplified approach for UI integration
        common_models = [
            "hf.co/unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF:latest",
            "deepseek-r1:8b",
            "llama3.2",
            "llama3.2:7b",
            "llama3.1",
            "mistral",
        ]

        if self.is_connected():
            self._available_models = common_models
            return self._available_models

        return []

    def is_model_available(self, model: str) -> bool:
        """
        Check if a specific model is available.

        Args:
            model: Model name to check

        Returns:
            True if model is available
        """
        if not self.is_connected():
            return False

        available_models = self.get_available_models()
        return model in available_models

    def pull_model(self, model: str) -> bool:
        """
        Pull/download a model to the Ollama server.

        Note: With ChatOllama, model pulling is handled by the Ollama service itself.
        This method simulates the operation for UI compatibility.

        Args:
            model: Model name to pull

        Returns:
            True if model pull simulation successful
        """
        if not self.is_connected():
            return False

        try:
            logger.info(f"Simulating model pull for {model}")

            # In a production environment, this could make direct HTTP calls
            # to the Ollama API for model pulling

            # For now, we simulate success if it's a known model
            available_models = self.get_available_models()
            if model in available_models:
                logger.info(f"Model {model} is available")
                return True
            else:
                logger.warning(f"Model {model} not in available list")
                return False

        except Exception as error:
            error_msg = f"Failed to pull model {model}: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate a response using the specified model.

        Args:
            prompt: Input prompt for the model
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text or None if failed
        """
        if not self.is_connected() or self._chat_ollama is None:
            logger.error("Ollama not connected")
            return None

        model_to_use = model or self._default_model

        # Check if model is available
        if not self.is_model_available(model_to_use):
            logger.warning(f"Model {model_to_use} not available")
            if not self.pull_model(model_to_use):
                return None

        try:
            logger.info(f"Generating response with model {model_to_use}")
            self.inference_started.emit()

            start_time = time.time()

            # Create a new ChatOllama instance with the specified parameters
            from langchain_core.messages import HumanMessage

            chat_model = ChatOllama(
                model=model_to_use,
                base_url=f"http://{self._host}:{self._port}",
                temperature=temperature,
            )

            if max_tokens:
                # Set max_tokens if specified
                bound_model = chat_model.bind(max_tokens=max_tokens)
                response = bound_model.invoke([HumanMessage(content=prompt)])
            else:
                response = chat_model.invoke([HumanMessage(content=prompt)])

            generated_text = str(response.content)

            end_time = time.time()

            logger.info(f"Generated response in {end_time - start_time:.2f}s")
            self.inference_completed.emit(generated_text)

            self._current_model = model_to_use
            return generated_text

        except Exception as error:
            error_msg = f"LLM generation failed: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Have a chat conversation using the specified model.

        Args:
            messages: List of messages in chat format
                     [{'role': 'user', 'content': 'Hello'}, ...]
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature (0.0 to 1.0)

        Returns:
            Generated response text or None if failed
        """
        if not self.is_connected() or self._chat_ollama is None:
            logger.error("Ollama not connected")
            return None

        model_to_use = model or self._default_model

        try:
            logger.info(f"Starting chat with model {model_to_use}")
            self.inference_started.emit()

            start_time = time.time()

            # Convert messages to LangChain format
            from langchain_core.messages import (
                AIMessage,
                BaseMessage,
                HumanMessage,
                SystemMessage,
            )

            langchain_messages: List[BaseMessage] = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                else:  # user or any other role
                    langchain_messages.append(HumanMessage(content=content))

            # Create ChatOllama with specified parameters
            chat_model = ChatOllama(
                model=model_to_use,
                base_url=f"http://{self._host}:{self._port}",
                temperature=temperature,
            )

            response = chat_model.invoke(langchain_messages)
            generated_text = str(response.content)

            end_time = time.time()

            logger.info(f"Chat response generated in {end_time - start_time:.2f}s")
            self.inference_completed.emit(generated_text)

            self._current_model = model_to_use
            return generated_text

        except Exception as error:
            error_msg = f"Chat generation failed: {error}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None

    def invoke_sync(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True,
    ) -> str:
        """
        Synchronously invoke the LLM with caching support.

        Args:
            messages: List of LangChain messages
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature (defaults to instance temperature)
            use_cache: Whether to use response caching

        Returns:
            Generated response text

        Raises:
            Exception: If LLM invocation fails
        """
        if not self.is_connected() or self._chat_ollama is None:
            raise Exception("Ollama not connected")

        model_to_use = model or self._default_model
        temperature_to_use = (
            temperature if temperature is not None else self._temperature
        )

        # Create cache key from messages
        prompt_text = "\n".join(
            str(msg.content) for msg in messages if hasattr(msg, "content")
        )
        model_config = {
            "model": model_to_use,
            "temperature": temperature_to_use,
        }

        # Check cache first
        if use_cache:
            cached_response = self._cache.get(prompt_text, model_config)
            if cached_response:
                logger.debug(f"Cache hit for prompt: {prompt_text[:50]}...")
                return cached_response

        # Generate response
        for attempt in range(self._max_retries):
            try:
                logger.info(
                    f"LLM invoke (attempt {attempt + 1}): "
                    f"model={model_to_use}, temp={temperature_to_use}"
                )

                # Create ChatOllama with specified parameters
                chat_model = ChatOllama(
                    model=model_to_use,
                    base_url=f"http://{self._host}:{self._port}",
                    temperature=temperature_to_use,
                )

                start_time = time.time()
                response = chat_model.invoke(messages)
                end_time = time.time()

                response_text = str(response.content)

                logger.info(f"LLM response generated in {end_time - start_time:.2f}s")

                # Cache the response
                if use_cache and response_text:
                    self._cache.set(prompt_text, response_text, model_config)

                return response_text

            except Exception as error:
                logger.warning(f"LLM invoke attempt {attempt + 1} failed: {error}")
                if attempt == self._max_retries - 1:
                    raise Exception(
                        f"LLM invocation failed after {self._max_retries} "
                        f"attempts: {error}"
                    )

                # Wait before retry (exponential backoff)
                wait_time = 2**attempt
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        raise Exception("Maximum retries exceeded")

    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Note: With ChatOllama, model info is simplified.
        In a production environment, this could query the Ollama API directly.

        Args:
            model: Model name (defaults to default_model)

        Returns:
            Model information dictionary
        """
        if not self.is_connected():
            return {}

        model_to_use = model or self._default_model

        # Return basic model information
        return {
            "name": model_to_use,
            "status": (
                "available" if self.is_model_available(model_to_use) else "unknown"
            ),
            "provider": "ollama",
            "temperature": 0.7,
            "max_tokens": None,
        }

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get Ollama server information.

        Returns:
            Server information dictionary
        """
        return {
            "host": self._host,
            "port": self._port,
            "base_url": f"http://{self._host}:{self._port}",
            "connected": self.is_connected(),
            "available_models": self._available_models,
            "current_model": self._current_model,
            "default_model": self._default_model,
        }

    def disconnect_service(self) -> None:
        """Disconnect from Ollama service."""
        self._is_connected = False
        self._current_model = None
        logger.info("Ollama service disconnected")
        self.connection_status_changed.emit("disconnected")

    def get_current_model(self) -> Optional[str]:
        """
        Get the currently loaded model.

        Returns:
            Current model name or None
        """
        return self._current_model


# Global LLM manager instance
_llm_manager: Optional[OllamaManager] = None


def get_llm_manager() -> Optional[OllamaManager]:
    """Get global LLM manager instance."""
    global _llm_manager

    if _llm_manager is None:
        # Load configuration from environment
        host = os.environ.get("RSPA_OLLAMA_HOST", "localhost")
        port = int(os.environ.get("RSPA_OLLAMA_PORT", "11434"))
        default_model = os.environ.get(
            "RSPA_OLLAMA_DEFAULT_MODEL",
            "hf.co/unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF:latest",
        )

        _llm_manager = OllamaManager(host=host, port=port, default_model=default_model)

    return _llm_manager
