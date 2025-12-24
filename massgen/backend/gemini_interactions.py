# -*- coding: utf-8 -*-
"""
Gemini Interactions API backend with stateful conversations and agent support.
"""

import asyncio
import json
import logging
import os
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Dict, List, Optional, Set

from ..formatter._gemini_formatter import GeminiFormatter
from ..logger_config import (
    log_backend_activity,
    log_backend_agent_message,
    log_stream_chunk,
    log_tool_call,
    logger,
)
from .base import FilesystemSupport, StreamChunk
from .base_with_custom_tool_and_mcp import (
    CustomToolAndMCPBackend,
    ExecutionContext,
    ToolExecutionConfig,
)

# Google GenAI SDK imports
try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]
    GENAI_AVAILABLE = False


# Suppress Gemini SDK logger warning about non-text parts in response
class NoFunctionCallWarning(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "there are non-text parts in the response:" in message:
            return False
        return True


logging.getLogger("google_genai.types").addFilter(NoFunctionCallWarning())


@dataclass
class BackoffConfig:
    """Configuration for exponential backoff on rate limit errors."""

    max_attempts: int = 5
    initial_delay: float = 2.0
    multiplier: float = 3.0
    max_delay: float = 60.0
    jitter: float = 0.2
    retry_statuses: Set[int] = field(default_factory=lambda: {429, 503})


def _is_retryable_gemini_error(exc: Exception, retry_statuses: Set[int]) -> tuple:
    """
    Check if exception is a retryable Gemini API error.

    Returns:
        (is_retryable, status_code, error_message)
    """
    status_code = None
    error_msg = str(exc).lower()

    # Check for status_code attribute
    if hasattr(exc, "status_code"):
        status_code = exc.status_code
    elif hasattr(exc, "code"):
        code = exc.code
        if callable(code):
            code = code()
        if code == 8:
            status_code = 429
        elif code == 14:
            status_code = 503

    # Check exception type name
    exc_type = type(exc).__name__
    if exc_type in ("ResourceExhausted", "TooManyRequests"):
        status_code = 429
    elif exc_type == "ServiceUnavailable":
        status_code = 503

    # Check error message patterns
    retryable_patterns = [
        "resource exhausted",
        "resource has been exhausted",
        "quota exceeded",
        "rate limit",
        "too many requests",
        "429",
        "503",
    ]
    pattern_suggests_rate_limit = any(pattern in error_msg for pattern in retryable_patterns)

    if status_code is not None:
        is_retryable = status_code in retry_statuses
    elif pattern_suggests_rate_limit and 429 in retry_statuses:
        is_retryable = True
    else:
        is_retryable = False
    return (is_retryable, status_code, str(exc))


def _extract_retry_after(exc: Exception) -> Optional[float]:
    """Extract Retry-After value from exception if available."""
    # Check for response headers
    if hasattr(exc, "response") and hasattr(exc.response, "headers"):
        headers = exc.response.headers
        if "retry-after-ms" in headers:
            try:
                return float(headers["retry-after-ms"]) / 1000.0
            except (ValueError, TypeError):
                pass
        if "retry-after" in headers:
            try:
                return float(headers["retry-after"])
            except (ValueError, TypeError):
                pass

    if hasattr(exc, "metadata") and exc.metadata is not None:
        metadata = exc.metadata
        try:
            # Handle dict-like metadata
            if hasattr(metadata, "items"):
                items = metadata.items()
            # Handle tuple/list of pairs
            elif hasattr(metadata, "__iter__"):
                items = metadata
            else:
                items = []

            for key, value in items:
                if str(key).lower() == "retry-after":
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        pass
        except (ValueError, TypeError):
            pass

    return None


# MCP integration imports
try:
    from ..mcp_tools import (
        MCPConnectionError,
        MCPError,
        MCPServerError,
        MCPTimeoutError,
    )
except ImportError:
    MCPError = ImportError  # type: ignore[assignment]
    MCPConnectionError = ImportError  # type: ignore[assignment]
    MCPTimeoutError = ImportError  # type: ignore[assignment]
    MCPServerError = ImportError  # type: ignore[assignment]


class GeminiInteractionsBackend(CustomToolAndMCPBackend):
    """Google Gemini Interactions API backend with stateful conversation support."""

    # Agent model patterns for auto-detection
    AGENT_PATTERNS = ["deep-research", "deep-research-pro", "deep-research-pro-preview"]

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Gemini Interactions backend.

        Args:
            api_key: Gemini API key (or use GOOGLE_API_KEY/GEMINI_API_KEY env vars)
            **kwargs: Additional configuration including:
                - interactions_stream_mode: Override auto-detection (bool, optional)
                - interactions_polling_interval: Polling frequency in seconds (float, default 2.0)
                - interactions_store: State pe
                rsistence for stateful conversations (bool, default True)
                - gemini_backoff_*: Backoff configuration parameters
        """
        # Store Gemini-specific API key before calling parent init
        gemini_api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

        # Extract backoff configuration parameters
        backoff_max_attempts = kwargs.pop("gemini_backoff_max_attempts", 5)
        backoff_initial_delay = kwargs.pop("gemini_backoff_initial_delay", 2.0)
        backoff_multiplier = kwargs.pop("gemini_backoff_multiplier", 3.0)
        backoff_max_delay = kwargs.pop("gemini_backoff_max_delay", 60.0)
        backoff_jitter = kwargs.pop("gemini_backoff_jitter", 0.2)

        # Extract Interactions API specific parameters
        self._stream_mode_override = kwargs.pop("interactions_stream_mode", None)
        self._polling_interval = kwargs.pop("interactions_polling_interval", 2.0)
        self._store_interactions = kwargs.pop("interactions_store", True)

        # Call parent class __init__
        super().__init__(gemini_api_key, **kwargs)

        # Override API key with Gemini-specific value
        self.api_key = gemini_api_key

        # Gemini-specific counters for builtin tools
        self.search_count = 0
        self.code_execution_count = 0

        # Formatter for message and tool formatting
        self.formatter = GeminiFormatter()

        # API params handler for building SDK config
        from ..api_params_handler import GeminiInteractionsAPIParamsHandler

        self.api_params_handler = GeminiInteractionsAPIParamsHandler(self)

        # Exponential backoff configuration
        self.backoff_config = BackoffConfig(
            max_attempts=int(backoff_max_attempts),
            initial_delay=float(backoff_initial_delay),
            multiplier=float(backoff_multiplier),
            max_delay=float(backoff_max_delay),
            jitter=float(backoff_jitter),
        )

        # Backoff telemetry counters
        self.backoff_retry_count = 0
        self.backoff_total_delay = 0.0

        # Stateful conversation tracking
        self._previous_interaction_id: Optional[str] = None

        # Execution context for tools
        self._execution_context: Optional[ExecutionContext] = None

        # Active tool result capture during manual tool execution
        self._active_tool_result_store: Optional[Dict[str, str]] = None

        # Agent type detection (set during stream_with_tools)
        self._is_agent: bool = False
        self._use_streaming: bool = True

    def _detect_agent_type(self, model_name: str) -> bool:
        """Detect if model is an agent (deep-research) or regular model."""
        if not model_name:
            return False
        model_lower = model_name.lower()
        return any(pattern in model_lower for pattern in self.AGENT_PATTERNS)

    def _create_genai_client(self):
        """Create and return a Gemini API client."""
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai SDK is required for GeminiInteractionsBackend. " "Install with: pip install google-genai",
            )
        return genai.Client(api_key=self.api_key)

    # Stateful conversation methods
    def is_stateful(self) -> bool:
        """Return True - Interactions API is stateful."""
        return True

    async def clear_history(self) -> None:
        """Clear conversation history by resetting interaction ID."""
        self._previous_interaction_id = None
        logger.info("[GeminiInteractions] Conversation history cleared")

    async def reset_state(self) -> None:
        """Reset all state including history and counters."""
        await self.clear_history()
        self.backoff_retry_count = 0
        self.backoff_total_delay = 0.0
        self.search_count = 0
        self.code_execution_count = 0
        logger.info("[GeminiInteractions] State reset complete")

    def _setup_permission_hooks(self):
        """Override base class - Gemini uses session-based permissions."""
        logger.debug("[GeminiInteractions] Using session-based permissions, skipping function hook setup")

    async def _process_stream(self, stream, all_params, agent_id: Optional[str] = None) -> AsyncGenerator[StreamChunk, None]:
        """Required by CustomToolAndMCPBackend - not used by Interactions API."""
        if False:
            yield  # Make this an async generator
        raise NotImplementedError("GeminiInteractions uses custom streaming logic in stream_with_tools()")

    async def _setup_mcp_tools(self) -> None:
        """Override parent class - Use base class MCP setup."""
        await super()._setup_mcp_tools()

    def supports_upload_files(self) -> bool:
        """Gemini Interactions does not support upload_files preprocessing."""
        return False

    def _create_client(self, **kwargs):
        """Not used - client created inline."""

    async def _stream_with_custom_and_mcp_tools(
        self,
        current_messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        client,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Not used - custom logic in stream_with_tools."""
        yield StreamChunk(type="error", error="Not implemented")

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return "gemini_interactions"

    def get_filesystem_support(self) -> FilesystemSupport:
        """Get filesystem support type."""
        return FilesystemSupport.MCP

    def get_supported_builtin_tools(self) -> List[str]:
        """Get list of builtin tools supported by this provider."""
        return ["google_search", "code_execution"]

    async def _interactions_create_with_backoff(
        self,
        client,
        create_params: Dict[str, Any],
        op_name: str,
        agent_id: Optional[str] = None,
    ):
        """Execute interactions.create with exponential backoff on rate limit errors."""
        last_exc = None
        cfg = self.backoff_config

        for attempt in range(1, cfg.max_attempts + 1):
            try:
                return await client.aio.interactions.create(**create_params)

            except Exception as exc:
                is_retryable, status_code, error_msg = _is_retryable_gemini_error(exc, cfg.retry_statuses)
                last_exc = exc

                if not is_retryable:
                    logger.error(f"[GeminiInteractions] Non-retryable error in {op_name}: {error_msg}")
                    raise

                if attempt >= cfg.max_attempts:
                    logger.error(
                        f"[GeminiInteractions] Max retries ({cfg.max_attempts}) exhausted for {op_name}. " f"Last error: {error_msg}",
                    )
                    raise

                retry_after = _extract_retry_after(exc)
                if retry_after is not None:
                    delay = min(retry_after, cfg.max_delay)
                else:
                    delay = min(cfg.initial_delay * (cfg.multiplier ** (attempt - 1)), cfg.max_delay)

                # Apply jitter
                if cfg.jitter > 0:
                    delay *= random.uniform(1 - cfg.jitter, 1 + cfg.jitter)

                # Update telemetry
                self.backoff_retry_count += 1
                self.backoff_total_delay += delay

                log_backend_activity(
                    "gemini_interactions",
                    "Rate limited, backing off",
                    {
                        "op_name": op_name,
                        "attempt": attempt,
                        "max_attempts": cfg.max_attempts,
                        "delay_seconds": round(delay, 2),
                        "status_code": status_code,
                        "error": error_msg[:200],
                    },
                    agent_id=agent_id,
                )

                logger.warning(
                    f"[GeminiInteractions] Rate limited (HTTP {status_code}) in {op_name}. " f"Retry {attempt}/{cfg.max_attempts} in {delay:.1f}s",
                )

                await asyncio.sleep(delay)

        if last_exc:
            raise last_exc

    async def _interactions_get_with_backoff(
        self,
        client,
        interaction_id: str,
        op_name: str,
        agent_id: Optional[str] = None,
    ):
        """Execute interactions.get with exponential backoff on rate limit errors."""
        last_exc = None
        cfg = self.backoff_config

        for attempt in range(1, cfg.max_attempts + 1):
            try:
                return await client.aio.interactions.get(id=interaction_id)

            except Exception as exc:
                is_retryable, status_code, error_msg = _is_retryable_gemini_error(exc, cfg.retry_statuses)
                last_exc = exc

                if not is_retryable:
                    logger.error(f"[GeminiInteractions] Non-retryable error in {op_name}: {error_msg}")
                    raise

                if attempt >= cfg.max_attempts:
                    logger.error(
                        f"[GeminiInteractions] Max retries ({cfg.max_attempts}) exhausted for {op_name}. " f"Last error: {error_msg}",
                    )
                    raise

                retry_after = _extract_retry_after(exc)
                if retry_after is not None:
                    delay = min(retry_after, cfg.max_delay)
                else:
                    delay = min(cfg.initial_delay * (cfg.multiplier ** (attempt - 1)), cfg.max_delay)

                if cfg.jitter > 0:
                    delay *= random.uniform(1 - cfg.jitter, 1 + cfg.jitter)

                self.backoff_retry_count += 1
                self.backoff_total_delay += delay

                log_backend_activity(
                    "gemini_interactions",
                    "Rate limited on get, backing off",
                    {
                        "op_name": op_name,
                        "interaction_id": interaction_id,
                        "attempt": attempt,
                        "delay_seconds": round(delay, 2),
                    },
                    agent_id=agent_id,
                )

                await asyncio.sleep(delay)

        if last_exc:
            raise last_exc

    def _convert_interaction_output_to_tool_call(self, output: Any, index: int) -> Optional[Dict[str, Any]]:
        """Convert Interactions API output to tool call format."""
        if not hasattr(output, "type"):
            return None

        output_type = getattr(output, "type", None)
        if output_type != "function_call":
            return None

        name = getattr(output, "name", "")
        if not name:
            logger.warning(f"[GeminiInteractions] Skipping function call with missing name: {output}")
            return None

        args = getattr(output, "arguments", {})
        if hasattr(args, "items"):
            args = dict(args)
        elif not isinstance(args, dict):
            args = {}

        call_id = getattr(output, "id", None)
        if not call_id:
            call_id = f"call_{index}_{uuid.uuid4().hex[:8]}"

        thought_signature = getattr(output, "thought_signature", None)

        result = {
            "call_id": call_id,
            "name": name,
            "arguments": json.dumps(args),
        }

        if thought_signature:
            result["thought_signature"] = thought_signature

        return result

    def _build_tool_response_input(self, tool_calls: List[Dict[str, Any]], tool_results: Dict[str, str]) -> List[Dict[str, Any]]:
        """Build input for continuation with tool responses."""
        function_results = []
        for call in tool_calls:
            call_id = call.get("call_id", "")
            name = call.get("name", "")

            if not name:
                logger.warning(f"[GeminiInteractions] Skipping tool response with missing name: {call}")
                continue

            result = tool_results.get(call_id, "No result")
            if not isinstance(result, str):
                try:
                    result = json.dumps(result)
                except (TypeError, ValueError):
                    result = str(result)

            function_result_entry = {
                "type": "function_result",
                "name": name,
                "call_id": call_id if call_id else None,
                "result": result,
            }

            if "thought_signature" in call:
                function_result_entry["thought_signature"] = call["thought_signature"]

            function_results.append(function_result_entry)

        return function_results

    def _extract_text_from_outputs(self, outputs: List[Any]) -> str:
        """Extract text content from Interaction outputs."""
        text_parts = []
        for output in outputs:
            output_type = getattr(output, "type", None)
            if output_type == "text":
                text = getattr(output, "text", "")
                if text:
                    text_parts.append(text)
        return "".join(text_parts)

    def _extract_function_calls_from_outputs(self, outputs: List[Any]) -> List[Dict[str, Any]]:
        """Extract function calls from Interaction outputs."""
        function_calls = []
        for i, output in enumerate(outputs):
            call = self._convert_interaction_output_to_tool_call(output, i)
            if call:
                function_calls.append(call)
        return function_calls

    def _update_token_usage_from_interaction(self, interaction: Any, model_name: str) -> None:
        """Update token usage from Interaction response."""
        usage = getattr(interaction, "usage", None)
        if not usage:
            return

        usage_dict = {
            "prompt_token_count": getattr(usage, "prompt_token_count", 0) or 0,
            "candidates_token_count": getattr(usage, "candidates_token_count", 0) or 0,
            "thoughts_token_count": getattr(usage, "thoughts_token_count", 0) or 0,
            "cached_content_token_count": getattr(usage, "cached_content_token_count", 0) or 0,
        }

        if usage_dict["prompt_token_count"] > 0 or usage_dict["candidates_token_count"] > 0:
            self._update_token_usage_from_api_response(usage_dict, model_name)
            logger.info(
                f"[GeminiInteractions] Token usage tracked: "
                f"input={usage_dict['prompt_token_count']}, "
                f"output={usage_dict['candidates_token_count']}, "
                f"thinking={usage_dict['thoughts_token_count']}, "
                f"cached={usage_dict['cached_content_token_count']}",
            )

    async def _stream_interaction(
        self,
        client,
        interaction_params: Dict[str, Any],
        model_name: str,
        agent_id: Optional[str] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Execute interaction in streaming mode."""
        logger.info("[GeminiInteractions] Using streaming mode")

        params = {**interaction_params, "stream": True}
        if self._is_agent:
            params["background"] = True

        try:
            stream = await self._interactions_create_with_backoff(
                client,
                params,
                "stream_interaction",
                agent_id,
            )

            full_text = ""
            captured_function_calls = []
            last_interaction = None
            chunk_count = 0

            async for chunk in stream:
                chunk_count += 1
                last_interaction = chunk

                # Check for event_type (Interactions API streaming format)
                event_type = getattr(chunk, "event_type", None)

                if event_type == "content.delta":
                    delta = getattr(chunk, "delta", None)
                    if delta:
                        delta_type = getattr(delta, "type", None)

                        if delta_type == "text":
                            text_delta = getattr(delta, "text", "")
                            if text_delta:
                                full_text += text_delta
                                log_backend_agent_message(
                                    agent_id,
                                    "RECV",
                                    {"content": text_delta},
                                    backend_name="gemini_interactions",
                                )
                                log_stream_chunk("backend.gemini_interactions", "content", text_delta, agent_id)
                                yield StreamChunk(type="content", content=text_delta)

                        elif delta_type == "function_call":
                            # Native function call from Gemini Interactions API
                            func_name = getattr(delta, "name", "")
                            func_id = getattr(delta, "id", f"call_{len(captured_function_calls)}")
                            func_args = getattr(delta, "arguments", {})
                            if func_name:
                                call = {
                                    "name": func_name,
                                    "call_id": func_id,
                                    "arguments": json.dumps(func_args) if isinstance(func_args, dict) else func_args,
                                }
                                captured_function_calls.append(call)
                                logger.info(f"[GeminiInteractions] Native function call: {func_name}")

                        elif delta_type == "thought":
                            thought_delta = getattr(delta, "thought", "")
                            if thought_delta:
                                logger.debug(f"[GeminiInteractions] Thought: {thought_delta[:100]}...")
                                yield StreamChunk(
                                    type="thought",
                                    content=thought_delta,
                                    source="gemini_interactions",
                                )

                        elif delta_type == "thought_signature":
                            # Thinking signatures - just log for debugging
                            logger.debug("[GeminiInteractions] Received thought signature")

                elif event_type == "interaction.complete":
                    interaction = getattr(chunk, "interaction", None)
                    if interaction:
                        last_interaction = interaction

                elif hasattr(chunk, "outputs") and chunk.outputs:
                    for output in chunk.outputs:
                        output_type = getattr(output, "type", None)

                        if output_type == "text":
                            text_delta = getattr(output, "text", "")
                            if text_delta:
                                full_text += text_delta
                                log_backend_agent_message(
                                    agent_id,
                                    "RECV",
                                    {"content": text_delta},
                                    backend_name="gemini_interactions",
                                )
                                log_stream_chunk("backend.gemini_interactions", "content", text_delta, agent_id)
                                yield StreamChunk(type="content", content=text_delta)

                        elif output_type == "thought":
                            thought_text = getattr(output, "text", "") or getattr(output, "thought", "")
                            if thought_text:
                                logger.debug(f"[GeminiInteractions] Thought: {thought_text[:100]}...")
                                yield StreamChunk(
                                    type="thought",
                                    content=thought_text,
                                    source="gemini_interactions",
                                )

                        elif output_type == "function_call":
                            call = self._convert_interaction_output_to_tool_call(output, len(captured_function_calls))
                            if call:
                                captured_function_calls.append(call)
                                logger.info(f"[GeminiInteractions] Function call detected: {call['name']}")

            # Log summary of what we received
            logger.info(f"[GeminiInteractions] Stream complete: {chunk_count} chunks, text_len={len(full_text)}, func_calls={len(captured_function_calls)}")

            if last_interaction and hasattr(last_interaction, "id") and self._store_interactions:
                self._previous_interaction_id = last_interaction.id
                logger.info(f"[GeminiInteractions] Stored interaction ID: {self._previous_interaction_id}")

            if last_interaction:
                self._update_token_usage_from_interaction(last_interaction, model_name)

            if captured_function_calls:
                yield StreamChunk(
                    type="tool_calls",
                    tool_calls=captured_function_calls,
                    source="gemini_interactions",
                )

            return

        except Exception as e:
            logger.error(f"[GeminiInteractions] Streaming error: {e}")
            yield StreamChunk(type="error", error=f"Streaming error: {str(e)}")
            raise

    async def _poll_interaction(
        self,
        client,
        interaction_params: Dict[str, Any],
        model_name: str,
        agent_id: Optional[str] = None,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Execute interaction in polling mode."""
        logger.info("[GeminiInteractions] Using polling mode (background execution)")

        params = {**interaction_params, "background": True}

        try:
            interaction = await self._interactions_create_with_backoff(
                client,
                params,
                "poll_interaction_create",
                agent_id,
            )

            interaction_id = getattr(interaction, "id", None)
            if not interaction_id:
                yield StreamChunk(type="error", error="No interaction ID returned")
                return

            logger.info(f"[GeminiInteractions] Interaction {interaction_id} started")

            poll_count = 0
            max_polls = 300  # Safety limit

            while poll_count < max_polls:
                await asyncio.sleep(self._polling_interval)
                poll_count += 1

                interaction = await self._interactions_get_with_backoff(
                    client,
                    interaction_id,
                    f"poll_status_{poll_count}",
                    agent_id,
                )

                status = getattr(interaction, "status", "unknown")

                if status == "working":
                    if poll_count % 5 == 0:  # Log every 5th poll
                        logger.info(f"[GeminiInteractions] Processing... (poll {poll_count})")
                    continue

                elif status == "completed":
                    logger.info(f"[GeminiInteractions] Interaction completed after {poll_count} polls")
                    break

                elif status == "failed":
                    error_msg = getattr(interaction, "error", "Unknown error")
                    yield StreamChunk(type="error", error=f"Interaction failed: {error_msg}")
                    raise Exception(f"Interaction failed: {error_msg}")

                elif status == "requires_action":
                    logger.info("[GeminiInteractions] Interaction requires action (tool calls)")
                    break

                else:
                    logger.warning(f"[GeminiInteractions] Unknown status: {status}")

            if poll_count >= max_polls:
                yield StreamChunk(type="error", error="Polling timeout exceeded")
                raise Exception("Polling timeout exceeded")

            if self._store_interactions:
                self._previous_interaction_id = interaction_id
                logger.info(f"[GeminiInteractions] Stored interaction ID: {self._previous_interaction_id}")

            outputs = getattr(interaction, "outputs", []) or []

            text_content = self._extract_text_from_outputs(outputs)
            if text_content:
                log_backend_agent_message(
                    agent_id,
                    "RECV",
                    {"content": text_content},
                    backend_name="gemini_interactions",
                )
                log_stream_chunk("backend.gemini_interactions", "content", text_content, agent_id)
                yield StreamChunk(type="content", content=text_content)

            # Extract function calls
            function_calls = self._extract_function_calls_from_outputs(outputs)
            if function_calls:
                yield StreamChunk(
                    type="tool_calls",
                    tool_calls=function_calls,
                    source="gemini_interactions",
                )

            # Update token usage
            self._update_token_usage_from_interaction(interaction, model_name)

        except Exception as e:
            logger.error(f"[GeminiInteractions] Polling error: {e}")
            yield StreamChunk(type="error", error=f"Polling error: {str(e)}")
            raise

    async def stream_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream response using Gemini Interactions API with tool support.

        This method implements the main streaming logic for the Interactions API:
        1. Setup phase: Initialize client, MCP tools, detect coordination mode
        2. Agent/Model detection: Determine if using agent or model field
        3. Execution mode selection: Choose streaming or polling based on detection
        4. Tool execution: Handle custom, MCP, builtin, and coordination tools

        Args:
            messages: Conversation messages
            tools: Available tools schema
            **kwargs: Additional parameters including model

        Yields:
            StreamChunk: Standardized response chunks
        """
        # Use instance agent_id or get from kwargs
        agent_id = self.agent_id or kwargs.get("agent_id", None)

        # Build execution context for tools
        self._execution_context = ExecutionContext(
            messages=messages,
            agent_system_message=kwargs.get("system_message", None),
            agent_id=self.agent_id,
            backend_name="gemini_interactions",
            current_stage=self.coordination_stage,
        )

        log_backend_activity(
            "gemini_interactions",
            "Starting stream_with_tools",
            {"num_messages": len(messages), "num_tools": len(tools) if tools else 0},
            agent_id=agent_id,
        )

        # Track whether MCP tools were used
        mcp_used = False

        try:
            if not GENAI_AVAILABLE:
                raise ImportError(
                    "google-genai SDK is required for GeminiInteractionsBackend. " "Install with: pip install google-genai",
                )

            # Setup MCP using base class if not already initialized
            if not self._mcp_initialized and self.mcp_servers:
                await self._setup_mcp_tools()
                if self._mcp_initialized:
                    yield StreamChunk(
                        type="mcp_status",
                        status="mcp_initialized",
                        content="✅ [MCP] Tools initialized",
                        source="mcp_tools",
                    )

            # Merge constructor config with stream kwargs
            all_params = {**self.config, **kwargs}

            # Detect custom tools
            using_custom_tools = bool(self.custom_tool_manager and len(self._custom_tool_names) > 0)

            # Detect coordination mode
            is_coordination = self.formatter.has_coordination_tools(tools)
            is_post_evaluation = self.formatter.has_post_evaluation_tools(tools)

            # Extract model name
            model_name = all_params.get("model", "")

            # ====================================================================
            # BLOCK 1: Agent vs Model Detection
            # ====================================================================
            self._is_agent = self._detect_agent_type(model_name)

            # Determine execution mode
            # Per Google docs: Deep Research agents support and benefit from streaming
            # with background=True + stream=True for real-time progress updates
            if self._stream_mode_override is not None:
                self._use_streaming = self._stream_mode_override
                mode_source = "user override"
            else:
                # Both agents and models default to streaming
                # Agents use background=True + stream=True per Google docs
                self._use_streaming = True
                mode_source = "auto-detect (streaming recommended)"

            # Log detection results
            entity_type = "agent" if self._is_agent else "model"
            exec_mode = "streaming" if self._use_streaming else "polling"
            logger.info(
                f"[GeminiInteractions] Detected {entity_type} '{model_name}', " f"using {exec_mode} mode ({mode_source})",
            )

            # ====================================================================
            # BLOCK 2: Build Interaction Parameters
            # ====================================================================
            # Create Gemini client
            client = self._create_genai_client()

            # Build content string from messages
            full_content = self.formatter.format_messages(messages)

            # For coordination requests, modify prompt for structured output
            valid_agent_ids = None
            broadcast_enabled = False

            if is_coordination:
                for tool in tools:
                    if tool.get("type") == "function":
                        func_def = tool.get("function", {})
                        tool_name = func_def.get("name")
                        if tool_name == "vote":
                            agent_id_param = func_def.get("parameters", {}).get("properties", {}).get("agent_id", {})
                            if "enum" in agent_id_param:
                                valid_agent_ids = agent_id_param["enum"]
                        elif tool_name == "ask_others":
                            broadcast_enabled = True

                full_content = self.formatter.build_structured_output_prompt(
                    full_content,
                    valid_agent_ids,
                    broadcast_enabled=broadcast_enabled,
                )
            elif is_post_evaluation:
                full_content = self.formatter.build_post_evaluation_prompt(full_content)

            # Build base interaction parameters
            interaction_params: Dict[str, Any] = {
                "input": full_content,
                "store": self._store_interactions,
            }

            # CRITICAL: Use EITHER agent OR model field (mutually exclusive)
            if self._is_agent:
                interaction_params["agent"] = model_name
                logger.info(f"[GeminiInteractions] Using agent field: {model_name}")
            else:
                interaction_params["model"] = model_name
                logger.info(f"[GeminiInteractions] Using model field: {model_name}")

            # Add previous_interaction_id for multi-turn conversations
            if self._previous_interaction_id and self._store_interactions:
                interaction_params["previous_interaction_id"] = self._previous_interaction_id
                logger.info(f"[GeminiInteractions] Continuing conversation: {self._previous_interaction_id}")

            # ====================================================================
            # Tool Registration Phase (Interactions API format)
            # ====================================================================
            # Interactions API expects tools in flat format:
            # {"type": "function", "name": ..., "description": ..., "parameters": {...}}
            tools_to_apply = []

            # Collect custom tools schemas for Interactions API format
            custom_tools_schemas = None
            if using_custom_tools:
                try:
                    custom_tools_schemas = self._get_custom_tools_schemas()
                    if custom_tools_schemas:
                        logger.debug(f"[GeminiInteractions] Found {len(custom_tools_schemas)} custom tools")
                        yield StreamChunk(
                            type="custom_tool_status",
                            status="custom_tools_registered",
                            content=f"🔧 [Custom Tools] Registered {len(custom_tools_schemas)} tools",
                            source="custom_tools",
                        )
                except Exception as e:
                    logger.warning(f"[GeminiInteractions] Failed to get custom tools: {e}")

            # Collect MCP functions for Interactions API format
            mcp_functions_to_use = None
            if self._mcp_initialized and self._mcp_functions:
                if self.is_planning_mode_enabled():
                    blocked_tools = self.get_planning_mode_blocked_tools()
                    if not blocked_tools:
                        logger.info("[GeminiInteractions] Planning mode - blocking ALL MCP tools")
                        yield StreamChunk(
                            type="mcp_status",
                            status="planning_mode_blocked",
                            content="🚫 [MCP] Planning mode active - all MCP tools blocked",
                            source="planning_mode",
                        )
                    else:
                        mcp_functions_to_use = self._mcp_functions
                        mcp_used = True
                        yield StreamChunk(
                            type="mcp_status",
                            status="mcp_tools_registered",
                            content=f"🔧 [MCP] Registered {len(self._mcp_functions)} tools (selective blocking)",
                            source="mcp_tools",
                        )
                else:
                    mcp_functions_to_use = self._mcp_functions
                    mcp_used = True
                    logger.debug(f"[GeminiInteractions] Found {len(self._mcp_functions)} MCP tools")
                    yield StreamChunk(
                        type="mcp_status",
                        status="mcp_tools_registered",
                        content=f"🔧 [MCP] Registered {len(self._mcp_functions)} tools",
                        source="mcp_tools",
                    )

            # Convert all tools to Interactions API format using formatter
            # Include workflow tools (new_answer, vote) from the tools parameter
            workflow_tools = [t for t in (tools or []) if t.get("type") == "function" and t.get("function", {}).get("name") in ("new_answer", "vote", "ask_others")]

            if custom_tools_schemas or mcp_functions_to_use or workflow_tools:
                try:
                    tools_to_apply = self.formatter.format_tools_for_interactions_api(
                        custom_tools=custom_tools_schemas,
                        mcp_functions=mcp_functions_to_use,
                        workflow_tools=workflow_tools,
                    )
                    logger.info(f"[GeminiInteractions] Formatted {len(tools_to_apply)} tools for Interactions API")
                except Exception as e:
                    logger.warning(f"[GeminiInteractions] Failed to format tools: {e}")

            # Add builtin tools (GoogleSearch, CodeExecution, UrlContext)
            if all_params.get("enable_web_search") or all_params.get("enable_google_search"):
                tools_to_apply.append({"type": "google_search"})
                logger.info("[GeminiInteractions] Registered GoogleSearch builtin tool (executed by API)")

            if all_params.get("enable_code_execution"):
                tools_to_apply.append({"type": "code_execution"})
                logger.info("[GeminiInteractions] Registered CodeExecution builtin tool (executed by API)")

            if all_params.get("enable_url_context"):
                tools_to_apply.append({"type": "url_context"})
                logger.info("[GeminiInteractions] Registered UrlContext builtin tool (executed by API)")

            # Apply tools to interaction params
            if tools_to_apply:
                interaction_params["tools"] = tools_to_apply
                # Debug: Log what tools are being sent
                tool_names = [t.get("name", t.get("type", "unknown")) for t in tools_to_apply]
                logger.info(f"[GeminiInteractions] Tools being sent to API: {tool_names}")

            # Build generation config
            generation_config = {}
            if "temperature" in all_params:
                generation_config["temperature"] = all_params["temperature"]
            if "top_p" in all_params:
                generation_config["top_p"] = all_params["top_p"]
            if "max_output_tokens" in all_params or "max_tokens" in all_params:
                generation_config["max_output_tokens"] = all_params.get("max_output_tokens") or all_params.get("max_tokens")

            # Thinking config for Gemini 2.5/3 models
            thinking_config = {}
            if "thinking_level" in all_params:
                thinking_config["thinking_level"] = all_params["thinking_level"]
                logger.info(f"[GeminiInteractions] Thinking level: {all_params['thinking_level']}")
            if "thinking_budget" in all_params:
                thinking_config["thinking_budget"] = all_params["thinking_budget"]
                logger.info(f"[GeminiInteractions] Thinking budget: {all_params['thinking_budget']}")
            if all_params.get("include_thoughts"):
                thinking_config["include_thoughts"] = True
                logger.info("[GeminiInteractions] Thought summaries enabled")
            if thinking_config:
                generation_config["thinking_config"] = thinking_config

            if generation_config:
                interaction_params["generation_config"] = generation_config

            # Add response_format for structured JSON output (JSON schema)
            if "response_format" in all_params and all_params["response_format"]:
                interaction_params["response_format"] = all_params["response_format"]
                logger.info("[GeminiInteractions] Response format (JSON schema) configured")

            # Add response_modalities for multimodal generation (e.g., ["IMAGE"], ["TEXT"])
            if "response_modalities" in all_params and all_params["response_modalities"]:
                interaction_params["response_modalities"] = all_params["response_modalities"]
                logger.info(f"[GeminiInteractions] Response modalities: {all_params['response_modalities']}")

            # Add system instruction if present
            system_message = None
            for msg in messages:
                if msg.get("role") == "system":
                    system_message = msg.get("content", "")
                    break

            if system_message:
                interaction_params["system_instruction"] = system_message

            # Log messages being sent
            log_backend_agent_message(
                agent_id or "default",
                "SEND",
                {
                    "content": full_content[:500] + "..." if len(full_content) > 500 else full_content,
                    "tools_count": len(tools_to_apply),
                },
                backend_name="gemini_interactions",
            )

            # ====================================================================
            # BLOCK 3: Execution Mode Selection
            # ====================================================================
            captured_function_calls = []
            full_content_text = ""

            if self._use_streaming:
                # Streaming mode
                async for chunk in self._stream_interaction(
                    client,
                    interaction_params,
                    model_name,
                    agent_id,
                ):
                    if chunk.type == "content":
                        full_content_text += chunk.content or ""
                        yield chunk
                    elif chunk.type == "tool_calls":
                        # Don't yield tool_calls here - we'll handle them after categorization
                        # to avoid double-emitting workflow tools (vote, new_answer, ask_others)
                        captured_function_calls.extend(chunk.tool_calls or [])
                    else:
                        # Yield other chunk types (thought, error, etc.)
                        yield chunk
            else:
                # Polling mode
                async for chunk in self._poll_interaction(
                    client,
                    interaction_params,
                    model_name,
                    agent_id,
                ):
                    if chunk.type == "content":
                        full_content_text += chunk.content or ""
                        yield chunk
                    elif chunk.type == "tool_calls":
                        # Don't yield tool_calls here - we'll handle them after categorization
                        # to avoid double-emitting workflow tools (vote, new_answer, ask_others)
                        captured_function_calls.extend(chunk.tool_calls or [])
                    else:
                        # Yield other chunk types (thought, error, etc.)
                        yield chunk

            # ====================================================================
            # Structured Coordination Output Parsing
            # ====================================================================
            if is_coordination and full_content_text:
                parsed = self.formatter.extract_structured_response(full_content_text)

                if parsed and isinstance(parsed, dict):
                    tool_calls = self.formatter.convert_structured_to_tool_calls(parsed)

                    if tool_calls:
                        if captured_function_calls:
                            logger.warning(
                                f"[GeminiInteractions] Structured output found, clearing {len(captured_function_calls)} " "spurious function calls",
                            )
                            captured_function_calls.clear()

                        mcp_calls, custom_calls, provider_calls = self._categorize_tool_calls(tool_calls)

                        if custom_calls:
                            for call in custom_calls:
                                call["_from_structured_output"] = True
                            captured_function_calls.extend(custom_calls)

                        if provider_calls:
                            workflow_tool_calls = []
                            for call in provider_calls:
                                tool_name = call.get("name", "")
                                tool_args_str = call.get("arguments", "{}")

                                if isinstance(tool_args_str, str):
                                    try:
                                        tool_args = json.loads(tool_args_str)
                                    except json.JSONDecodeError:
                                        tool_args = {}
                                else:
                                    tool_args = tool_args_str

                                logger.info(f"[GeminiInteractions] Structured coordination action: {tool_name}")
                                log_tool_call(agent_id, tool_name, tool_args, None, backend_name="gemini_interactions")

                                workflow_tool_calls.append(
                                    {
                                        "id": call.get("call_id", f"call_{len(workflow_tool_calls)}"),
                                        "type": "function",
                                        "function": {
                                            "name": tool_name,
                                            "arguments": tool_args,
                                        },
                                    },
                                )

                            if workflow_tool_calls:
                                log_stream_chunk("backend.gemini_interactions", "tool_calls", workflow_tool_calls, agent_id)
                                yield StreamChunk(
                                    type="tool_calls",
                                    tool_calls=workflow_tool_calls,
                                    source="gemini_interactions",
                                )

                            if provider_calls and not captured_function_calls:
                                if mcp_used:
                                    yield StreamChunk(
                                        type="mcp_status",
                                        status="mcp_session_complete",
                                        content="✅ [MCP] Session completed",
                                        source="mcp_tools",
                                    )
                                yield StreamChunk(type="done")
                                return

            # ====================================================================
            # Tool Execution Phase
            # ====================================================================
            if captured_function_calls:
                # Filter out tool calls with missing names before categorization
                valid_function_calls = []
                for call in captured_function_calls:
                    if not call.get("name"):
                        logger.warning(f"[GeminiInteractions] Skipping tool call with missing name: {call}")
                        continue
                    valid_function_calls.append(call)

                if not valid_function_calls:
                    logger.info("[GeminiInteractions] No valid tool calls after filtering")
                    captured_function_calls = []
                else:
                    captured_function_calls = valid_function_calls

                mcp_calls, custom_calls, provider_calls = self._categorize_tool_calls(captured_function_calls)

                # Handle provider (workflow) calls - emit but don't execute
                if provider_calls:
                    workflow_tool_calls = []
                    for call in provider_calls:
                        tool_name = call.get("name", "")
                        tool_args_str = call.get("arguments", "{}")

                        if isinstance(tool_args_str, str):
                            try:
                                tool_args = json.loads(tool_args_str)
                            except json.JSONDecodeError:
                                tool_args = {}
                        else:
                            tool_args = tool_args_str

                        logger.info(f"[GeminiInteractions] Function call coordination action: {tool_name}")
                        log_tool_call(agent_id, tool_name, tool_args, None, backend_name="gemini_interactions")

                        workflow_tool_calls.append(
                            {
                                "id": call.get("call_id", f"call_{len(workflow_tool_calls)}"),
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tool_args,
                                },
                            },
                        )

                    if workflow_tool_calls:
                        log_stream_chunk("backend.gemini_interactions", "tool_calls", workflow_tool_calls, agent_id)
                        yield StreamChunk(
                            type="tool_calls",
                            tool_calls=workflow_tool_calls,
                            source="gemini_interactions",
                        )

                    if mcp_used:
                        yield StreamChunk(
                            type="mcp_status",
                            status="mcp_session_complete",
                            content="✅ [MCP] Session completed",
                            source="mcp_tools",
                        )

                    yield StreamChunk(type="done")
                    return

                # Execute custom and MCP tools
                updated_messages = messages.copy()
                processed_call_ids = set()

                CUSTOM_TOOL_CONFIG = ToolExecutionConfig(
                    tool_type="custom",
                    chunk_type="custom_tool_status",
                    emoji_prefix="🔧 [Custom Tool]",
                    success_emoji="✅ [Custom Tool]",
                    error_emoji="❌ [Custom Tool Error]",
                    source_prefix="custom_",
                    status_called="custom_tool_called",
                    status_response="custom_tool_response",
                    status_error="custom_tool_error",
                    execution_callback=self._execute_custom_tool,
                )

                MCP_TOOL_CONFIG = ToolExecutionConfig(
                    tool_type="mcp",
                    chunk_type="mcp_status",
                    emoji_prefix="🔧 [MCP Tool]",
                    success_emoji="✅ [MCP Tool]",
                    error_emoji="❌ [MCP Tool Error]",
                    source_prefix="mcp_",
                    status_called="mcp_tool_called",
                    status_response="mcp_tool_response",
                    status_error="mcp_tool_error",
                    execution_callback=self._execute_mcp_function_with_retry,
                )

                tool_results: Dict[str, str] = {}
                self._active_tool_result_store = tool_results

                try:
                    if mcp_calls and not await self._check_circuit_breaker_before_execution():
                        logger.warning("[GeminiInteractions] All MCP servers blocked by circuit breaker")
                        yield StreamChunk(
                            type="mcp_status",
                            status="mcp_blocked",
                            content="⚠️ [MCP] All servers blocked by circuit breaker",
                            source="circuit_breaker",
                        )
                        mcp_calls = []

                    all_calls = custom_calls + mcp_calls

                    def tool_config_for_call(call: Dict[str, Any]) -> ToolExecutionConfig:
                        tool_name = call.get("name", "")
                        return CUSTOM_TOOL_CONFIG if tool_name in (self._custom_tool_names or set()) else MCP_TOOL_CONFIG

                    if all_calls:
                        if mcp_calls:
                            mcp_used = True

                        async for chunk in self._execute_tool_calls(
                            all_calls=all_calls,
                            tool_config_for_call=tool_config_for_call,
                            all_params=all_params,
                            updated_messages=updated_messages,
                            processed_call_ids=processed_call_ids,
                            log_prefix="[GeminiInteractions]",
                            chunk_adapter=lambda c: c,
                        ):
                            yield chunk

                finally:
                    self._active_tool_result_store = None

                # ====================================================================
                # Tool-Call Continuation Loop
                # Continue conversation with tool results until no more function calls
                # ====================================================================
                max_continuation_turns = 10  # Safety limit
                continuation_turn = 0

                while tool_results and continuation_turn < max_continuation_turns:
                    continuation_turn += 1
                    logger.info(
                        f"[GeminiInteractions] Continuation turn {continuation_turn}: " f"sending {len(tool_results)} tool results",
                    )

                    # Build function responses for Interactions API using native format
                    # Format: [{"type": "function_result", "name": ..., "call_id": ..., "result": ...}]
                    function_response_input = self._build_tool_response_input(
                        all_calls,
                        tool_results,
                    )

                    # Handle empty tool results
                    if not function_response_input:
                        logger.info("[GeminiInteractions] No tool results to send, skipping continuation")
                        break

                    logger.debug(
                        f"[GeminiInteractions] Sending {len(function_response_input)} function results with call_ids",
                    )

                    # Build continuation parameters
                    # Input is a list of function_result dicts (native Interactions API format)
                    continuation_params: Dict[str, Any] = {
                        "input": function_response_input,
                        "store": self._store_interactions,
                    }

                    # Use agent or model field (mutually exclusive)
                    if self._is_agent:
                        continuation_params["agent"] = model_name
                    else:
                        continuation_params["model"] = model_name

                    # Include previous_interaction_id for stateful continuation
                    if self._previous_interaction_id and self._store_interactions:
                        continuation_params["previous_interaction_id"] = self._previous_interaction_id

                    # Add tools for potential further calls
                    if tools_to_apply:
                        continuation_params["tools"] = tools_to_apply

                    # Add streaming/background flags
                    if self._use_streaming:
                        continuation_params["stream"] = True
                        if self._is_agent:
                            continuation_params["background"] = True

                    logger.info(f"[GeminiInteractions] Continuing with tool results (turn {continuation_turn})")

                    # Execute continuation request
                    continuation_text = ""
                    continuation_function_calls = []

                    try:
                        if self._use_streaming:
                            # Streaming continuation
                            stream = await self._interactions_create_with_backoff(
                                client,
                                continuation_params,
                                f"continuation_{continuation_turn}",
                                agent_id,
                            )

                            last_interaction = None
                            async for chunk in stream:
                                last_interaction = chunk

                                # Handle event_type streaming format (same as first stream)
                                event_type = getattr(chunk, "event_type", None)

                                if event_type == "content.delta":
                                    delta = getattr(chunk, "delta", None)
                                    if delta:
                                        delta_type = getattr(delta, "type", None)

                                        if delta_type == "text":
                                            text_delta = getattr(delta, "text", "")
                                            if text_delta:
                                                continuation_text += text_delta
                                                log_stream_chunk(
                                                    "backend.gemini_interactions",
                                                    "content",
                                                    text_delta,
                                                    agent_id,
                                                )
                                                yield StreamChunk(type="content", content=text_delta)

                                        elif delta_type == "function_call":
                                            # Native function call from continuation
                                            func_name = getattr(delta, "name", "")
                                            func_id = getattr(delta, "id", f"cont_call_{len(continuation_function_calls)}")
                                            func_args = getattr(delta, "arguments", {})
                                            if func_name:
                                                call = {
                                                    "name": func_name,
                                                    "call_id": func_id,
                                                    "arguments": json.dumps(func_args) if isinstance(func_args, dict) else func_args,
                                                }
                                                continuation_function_calls.append(call)
                                                logger.info(f"[GeminiInteractions] Continuation function call: {func_name}")

                                # Also handle outputs format (fallback)
                                elif hasattr(chunk, "outputs") and chunk.outputs:
                                    for output in chunk.outputs:
                                        output_type = getattr(output, "type", None)

                                        if output_type == "text":
                                            text_delta = getattr(output, "text", "")
                                            if text_delta:
                                                continuation_text += text_delta
                                                log_stream_chunk(
                                                    "backend.gemini_interactions",
                                                    "content",
                                                    text_delta,
                                                    agent_id,
                                                )
                                                yield StreamChunk(type="content", content=text_delta)

                                        elif output_type == "function_call":
                                            call = self._convert_interaction_output_to_tool_call(
                                                output,
                                                len(continuation_function_calls),
                                            )
                                            if call:
                                                continuation_function_calls.append(call)

                            # Update interaction ID
                            if last_interaction and hasattr(last_interaction, "id") and self._store_interactions:
                                self._previous_interaction_id = last_interaction.id

                            # Update token usage
                            if last_interaction:
                                self._update_token_usage_from_interaction(last_interaction, model_name)

                        else:
                            # Polling continuation
                            continuation_params["background"] = True
                            continuation_params.pop("stream", None)

                            interaction = await self._interactions_create_with_backoff(
                                client,
                                continuation_params,
                                f"continuation_poll_{continuation_turn}",
                                agent_id,
                            )

                            interaction_id = getattr(interaction, "id", None)
                            if interaction_id:
                                # Poll until completion
                                poll_count = 0
                                max_polls = 300

                                while poll_count < max_polls:
                                    await asyncio.sleep(self._polling_interval)
                                    poll_count += 1

                                    interaction = await self._interactions_get_with_backoff(
                                        client,
                                        interaction_id,
                                        f"continuation_poll_status_{poll_count}",
                                        agent_id,
                                    )

                                    status = getattr(interaction, "status", "unknown")
                                    if status in ("completed", "requires_action"):
                                        break
                                    elif status == "failed":
                                        error_msg = getattr(interaction, "error", "Unknown error")
                                        raise Exception(f"Continuation failed: {error_msg}")

                                # Update interaction ID
                                if self._store_interactions:
                                    self._previous_interaction_id = interaction_id

                                # Extract outputs
                                outputs = getattr(interaction, "outputs", []) or []
                                continuation_text = self._extract_text_from_outputs(outputs)
                                continuation_function_calls = self._extract_function_calls_from_outputs(outputs)

                                if continuation_text:
                                    log_stream_chunk(
                                        "backend.gemini_interactions",
                                        "content",
                                        continuation_text,
                                        agent_id,
                                    )
                                    yield StreamChunk(type="content", content=continuation_text)

                                # Update token usage
                                self._update_token_usage_from_interaction(interaction, model_name)

                    except Exception as e:
                        logger.error(f"[GeminiInteractions] Continuation error: {e}")
                        yield StreamChunk(type="error", error=f"Continuation error: {str(e)}")
                        break

                    # Check if there are more function calls to execute
                    if not continuation_function_calls:
                        logger.info("[GeminiInteractions] No more function calls, continuation complete")
                        break

                    # Categorize tool calls FIRST before yielding
                    mcp_calls, custom_calls, provider_calls = self._categorize_tool_calls(
                        continuation_function_calls,
                    )

                    # If provider calls, emit only workflow tools and exit (handled by orchestrator)
                    if provider_calls:
                        workflow_tool_calls = []
                        for call in provider_calls:
                            tool_name = call.get("name", "")
                            tool_args_str = call.get("arguments", "{}")
                            if isinstance(tool_args_str, str):
                                try:
                                    tool_args = json.loads(tool_args_str)
                                except json.JSONDecodeError:
                                    tool_args = {}
                            else:
                                tool_args = tool_args_str

                            log_tool_call(agent_id, tool_name, tool_args, None, backend_name="gemini_interactions")
                            workflow_tool_calls.append(
                                {
                                    "id": call.get("call_id", f"call_{len(workflow_tool_calls)}"),
                                    "type": "function",
                                    "function": {"name": tool_name, "arguments": tool_args},
                                },
                            )

                        if workflow_tool_calls:
                            yield StreamChunk(
                                type="tool_calls",
                                tool_calls=workflow_tool_calls,
                                source="gemini_interactions",
                            )
                        break

                    # For non-workflow calls, yield the tool_calls chunk for custom/MCP tools
                    non_workflow_calls = custom_calls + mcp_calls
                    if non_workflow_calls:
                        yield StreamChunk(
                            type="tool_calls",
                            tool_calls=non_workflow_calls,
                            source="gemini_interactions",
                        )

                    # Execute custom and MCP tools
                    all_calls = custom_calls + mcp_calls
                    if not all_calls:
                        break

                    tool_results = {}
                    self._active_tool_result_store = tool_results

                    try:
                        if mcp_calls and not await self._check_circuit_breaker_before_execution():
                            logger.warning("[GeminiInteractions] Circuit breaker blocking MCP calls")
                            mcp_calls = []
                            all_calls = custom_calls

                        if all_calls:
                            if mcp_calls:
                                mcp_used = True

                            async for chunk in self._execute_tool_calls(
                                all_calls=all_calls,
                                tool_config_for_call=tool_config_for_call,
                                all_params=all_params,
                                updated_messages=updated_messages,
                                processed_call_ids=processed_call_ids,
                                log_prefix="[GeminiInteractions]",
                                chunk_adapter=lambda c: c,
                            ):
                                yield chunk
                        else:
                            tool_results = {}  # No tools to execute, exit loop

                    finally:
                        self._active_tool_result_store = None

                if continuation_turn >= max_continuation_turns:
                    logger.warning(
                        f"[GeminiInteractions] Max continuation turns ({max_continuation_turns}) reached",
                    )

            # Emit completion status
            if mcp_used:
                yield StreamChunk(
                    type="mcp_status",
                    status="mcp_session_complete",
                    content="✅ [MCP] Session completed",
                    source="mcp_tools",
                )

            yield StreamChunk(type="done")

        except Exception as e:
            logger.error(f"[GeminiInteractions] Error in stream_with_tools: {e}", exc_info=True)
            yield StreamChunk(type="error", error=str(e))
            raise

    def _append_tool_result_message(
        self,
        updated_messages: List[Dict[str, Any]],
        call: Dict[str, Any],
        result: Any,
        tool_type: str,
    ) -> None:
        """Append tool result to messages.

        For Interactions API, we store results in the active tool result store
        for use in continuation requests.
        """
        call_id = call.get("call_id", "")
        result_str = str(result) if result else "No result"

        if self._active_tool_result_store is not None:
            self._active_tool_result_store[call_id] = result_str

        # Also append to messages for compatibility
        updated_messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "name": call.get("name", ""),
                "content": result_str,
            },
        )

    def _append_tool_error_message(
        self,
        updated_messages: List[Dict[str, Any]],
        call: Dict[str, Any],
        error_msg: str,
        tool_type: str,
    ) -> None:
        """Append tool error to messages."""
        call_id = call.get("call_id", "")

        if self._active_tool_result_store is not None:
            self._active_tool_result_store[call_id] = f"Error: {error_msg}"

        updated_messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "name": call.get("name", ""),
                "content": f"Error: {error_msg}",
            },
        )

    async def _execute_custom_tool(self, call: Dict[str, Any]) -> AsyncGenerator:
        """Execute a custom tool and stream results.

        Args:
            call: Tool call dictionary

        Yields:
            CustomToolChunk objects
        """
        async for chunk in self.stream_custom_tool_execution(call):
            yield chunk

    async def _try_close_resource(
        self,
        resource: Any,
        method_names: tuple,
        resource_label: str,
    ) -> bool:
        """Try to close a resource using one of the provided method names.

        Args:
            resource: Object to close
            method_names: Method names to try (e.g., ("aclose", "close"))
            resource_label: Label for error logging

        Returns:
            True if closed successfully, False otherwise
        """
        if resource is None:
            return False

        for method_name in method_names:
            close_method = getattr(resource, method_name, None)
            if close_method is not None:
                try:
                    result = close_method()
                    if hasattr(result, "__await__"):
                        await result
                    return True
                except Exception as e:
                    log_backend_activity(
                        "gemini_interactions",
                        f"{resource_label} cleanup failed",
                        {"error": str(e), "method": method_name},
                        agent_id=self.agent_id,
                    )
                    return False
        return False

    async def _cleanup_genai_resources(self, stream: Any = None, client: Any = None) -> None:
        """Cleanup google-genai resources to avoid unclosed aiohttp sessions.

        Cleanup order is critical: stream → session → transport → client → MCP.
        Each resource is cleaned independently with error isolation.
        """
        # 1. Close stream
        await self._try_close_resource(stream, ("aclose", "close"), "Stream")

        # 2. Close internal aiohttp session (requires special handling)
        if client is not None:
            base_client = getattr(client, "_api_client", None)
            if base_client is not None:
                session = getattr(base_client, "_aiohttp_session", None)
                if session is not None and not getattr(session, "closed", True):
                    try:
                        await session.close()
                        log_backend_activity(
                            "gemini_interactions",
                            "Closed google-genai aiohttp session",
                            {},
                            agent_id=self.agent_id,
                        )
                        base_client._aiohttp_session = None
                        # Yield control to allow connector cleanup
                        await asyncio.sleep(0)
                    except Exception as e:
                        log_backend_activity(
                            "gemini_interactions",
                            "Failed to close google-genai aiohttp session",
                            {"error": str(e)},
                            agent_id=self.agent_id,
                        )

        # 3. Close internal async transport
        if client is not None:
            aio_obj = getattr(client, "aio", None)
            await self._try_close_resource(aio_obj, ("close", "stop"), "Client AIO")

        # 4. Close client
        await self._try_close_resource(client, ("aclose", "close"), "Client")

        # 5. Cleanup MCP connections
        await self.cleanup_mcp()

    async def __aenter__(self):
        """Async context manager entry."""
        if self.mcp_servers:
            await self._setup_mcp_tools()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_genai_resources()
        return False
