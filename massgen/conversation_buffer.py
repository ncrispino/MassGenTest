# -*- coding: utf-8 -*-
"""
AgentConversationBuffer - Single source of truth for agent conversation state.

This module provides a unified conversation buffer that captures ALL streaming
content during agent coordination, replacing the fragmented approach of multiple
separate storage mechanisms.

See docs/dev_notes/conversation_buffer_design.md for architecture details.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .token_manager.token_manager import TokenCostCalculator


class EntryType(Enum):
    """Types of entries in the conversation buffer."""

    USER = "user"  # User/orchestrator messages
    ASSISTANT = "assistant"  # Agent responses
    SYSTEM = "system"  # System messages
    TOOL_CALL = "tool_call"  # Tool invocation
    TOOL_RESULT = "tool_result"  # Tool execution result
    INJECTION = "injection"  # Injected updates from other agents
    REASONING = "reasoning"  # Agent thinking/reasoning content
    MEMORY_CONTEXT = "memory_context"  # Retrieved memories from persistent storage
    COMPRESSION_REQUEST = "compression_request"  # Request to compress context
    ENFORCEMENT = "enforcement"  # Orchestrator enforcement messages


@dataclass
class ConversationEntry:
    """
    Single entry in the conversation buffer.

    Attributes:
        timestamp: Unix timestamp when entry was created
        entry_type: Type of entry (user, assistant, tool_call, etc.)
        content: The actual content of the entry
        metadata: Additional context (tool_name, attempt, round, etc.)
    """

    timestamp: float
    entry_type: EntryType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dict."""
        return {
            "timestamp": self.timestamp,
            "entry_type": self.entry_type.value,
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationEntry":
        """Deserialize entry from dict."""
        return cls(
            timestamp=data["timestamp"],
            entry_type=EntryType(data["entry_type"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
        )


class AgentConversationBuffer:
    """
    Unified conversation buffer that captures ALL streaming content.

    This class serves as the single source of truth for agent conversation state,
    capturing everything that happens during streaming:
    - Content chunks (accumulated text)
    - Reasoning/thinking content
    - Tool calls (MCP, custom, workflow)
    - Tool results
    - Injected updates from other agents
    - System context

    This replaces the fragmented approach where content was split across:
    - conversation_history (incomplete, missing streamed content)
    - conversation_memory (separate system, not used for injection)
    - assistant_response (temporary accumulator, lost after streaming)

    Usage:
        buffer = AgentConversationBuffer(agent_id="agent_a")

        # During streaming:
        buffer.add_content("I'll analyze this...")
        buffer.add_tool_call("read_file", {"path": "foo.py"}, call_id="call_123")
        buffer.add_tool_result("read_file", "call_123", "file contents...")
        buffer.add_reasoning("Let me think about this...")

        # When turn completes:
        buffer.flush_turn()

        # For injection:
        buffer.inject_update({"agent_b": "Here's my answer..."})

        # Build LLM messages:
        messages = buffer.to_messages()

        # Persistence:
        buffer.save(Path("buffer.json"))
        buffer = AgentConversationBuffer.load(Path("buffer.json"))
    """

    def __init__(self, agent_id: str):
        """
        Initialize conversation buffer for an agent.

        Args:
            agent_id: Unique identifier for the agent
        """
        self.agent_id = agent_id
        self.entries: List[ConversationEntry] = []

        # Coordination tracking
        self.current_attempt = 0
        self.current_round = 0

        # Streaming accumulators (flushed on turn complete)
        self._pending_content = ""
        self._pending_reasoning = ""
        self._pending_tool_calls: List[Dict[str, Any]] = []

        # Track injection points for debugging
        self._injection_timestamps: List[float] = []

    # ─────────────────────────────────────────────────────────────────────
    # Recording during streaming
    # ─────────────────────────────────────────────────────────────────────

    def set_coordination_context(self, attempt: int, round_num: int) -> None:
        """
        Set current coordination context for metadata.

        Args:
            attempt: Current attempt number
            round_num: Current round number
        """
        self.current_attempt = attempt
        self.current_round = round_num

    def add_system_message(self, content: str) -> None:
        """
        Add system message to buffer.

        Args:
            content: System message content
        """
        self.entries.append(
            ConversationEntry(
                timestamp=time.time(),
                entry_type=EntryType.SYSTEM,
                content=content,
                metadata=self._base_metadata(),
            ),
        )

    def add_user_message(self, content: str) -> None:
        """
        Add user/orchestrator message to buffer.

        Args:
            content: User message content
        """
        self.entries.append(
            ConversationEntry(
                timestamp=time.time(),
                entry_type=EntryType.USER,
                content=content,
                metadata=self._base_metadata(),
            ),
        )

    def add_content(self, content: str) -> None:
        """
        Accumulate streaming content.

        Content is accumulated until flush_turn() is called, then
        stored as a single assistant entry.

        Args:
            content: Content chunk to accumulate
        """
        self._pending_content += content

    def add_reasoning(self, content: str) -> None:
        """
        Accumulate reasoning/thinking content.

        Args:
            content: Reasoning content chunk
        """
        self._pending_reasoning += content

    def add_tool_call(
        self,
        tool_name: str,
        args: Dict[str, Any],
        call_id: Optional[str] = None,
    ) -> None:
        """
        Record a tool call.

        Args:
            tool_name: Name of the tool being called
            args: Arguments passed to the tool
            call_id: Optional unique identifier for the call
        """
        self._pending_tool_calls.append(
            {
                "name": tool_name,
                "arguments": args,
                "call_id": call_id,
                "result": None,
                "timestamp": time.time(),
            },
        )

    def add_tool_result(
        self,
        tool_name: str,
        call_id: Optional[str],
        result: str,
    ) -> None:
        """
        Record tool result, matching to previous call if possible.

        Args:
            tool_name: Name of the tool
            call_id: Call ID to match (if available)
            result: Result from tool execution
        """
        # Try to find matching call and update result
        for call in reversed(self._pending_tool_calls):
            if call["name"] == tool_name:
                if call_id is None or call.get("call_id") == call_id:
                    if call["result"] is None:  # Don't overwrite existing result
                        call["result"] = result
                        return

        # No matching pending call found - add result directly to entries
        # This happens when tool results come in after flush (e.g., orchestrator tool execution)
        self.entries.append(
            ConversationEntry(
                timestamp=time.time(),
                entry_type=EntryType.TOOL_RESULT,
                content=result,
                metadata={
                    **self._base_metadata(),
                    "tool_name": tool_name,
                    "call_id": call_id,
                },
            ),
        )

    def add_memory_context(self, content: str, source: str = "persistent") -> None:
        """
        Add retrieved memory context to buffer.

        Args:
            content: The memory context content
            source: Source of memory ("persistent", "shared", "conversation")
        """
        self.entries.append(
            ConversationEntry(
                timestamp=time.time(),
                entry_type=EntryType.MEMORY_CONTEXT,
                content=content,
                metadata={**self._base_metadata(), "source": source},
            ),
        )

    def add_compression_request(self, content: str, usage_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Add compression request message to buffer.

        Args:
            content: The compression request content
            usage_info: Optional token usage info that triggered compression
        """
        metadata = self._base_metadata()
        if usage_info:
            metadata["usage_info"] = usage_info
        self.entries.append(
            ConversationEntry(
                timestamp=time.time(),
                entry_type=EntryType.COMPRESSION_REQUEST,
                content=content,
                metadata=metadata,
            ),
        )

    def add_enforcement(self, content: str, reason: str = "") -> None:
        """
        Add orchestrator enforcement message to buffer.

        Args:
            content: The enforcement message content
            reason: Why enforcement was needed (e.g., "no_workflow_tool", "invalid_vote")
        """
        self.entries.append(
            ConversationEntry(
                timestamp=time.time(),
                entry_type=EntryType.ENFORCEMENT,
                content=content,
                metadata={**self._base_metadata(), "reason": reason},
            ),
        )

    def flush_turn(self) -> None:
        """
        Flush accumulated content into entries.

        Called when agent turn completes (on "done" chunk). This converts
        all pending accumulators into permanent entries.
        """
        now = time.time()
        base_meta = self._base_metadata()

        # Add reasoning if present
        if self._pending_reasoning.strip():
            self.entries.append(
                ConversationEntry(
                    timestamp=now,
                    entry_type=EntryType.REASONING,
                    content=self._pending_reasoning.strip(),
                    metadata=base_meta,
                ),
            )

        # Add tool calls and results
        for call in self._pending_tool_calls:
            # Get arguments - may be dict or already JSON string
            args = call.get("arguments", {})
            if isinstance(args, str):
                # Already a JSON string, use as-is
                args_str = args
            else:
                # Convert dict to JSON string
                args_str = json.dumps(args, default=str)

            # Add tool call entry
            self.entries.append(
                ConversationEntry(
                    timestamp=call["timestamp"],
                    entry_type=EntryType.TOOL_CALL,
                    content=args_str,
                    metadata={
                        **base_meta,
                        "tool_name": call["name"],
                        "call_id": call.get("call_id"),
                    },
                ),
            )

            # Add tool result entry if present
            if call.get("result"):
                self.entries.append(
                    ConversationEntry(
                        timestamp=call["timestamp"] + 0.001,
                        entry_type=EntryType.TOOL_RESULT,
                        content=str(call["result"]),
                        metadata={
                            **base_meta,
                            "tool_name": call["name"],
                            "call_id": call.get("call_id"),
                        },
                    ),
                )

        # Add main content
        if self._pending_content.strip():
            self.entries.append(
                ConversationEntry(
                    timestamp=now,
                    entry_type=EntryType.ASSISTANT,
                    content=self._pending_content.strip(),
                    metadata=base_meta,
                ),
            )

        # Clear accumulators
        self._pending_content = ""
        self._pending_reasoning = ""
        self._pending_tool_calls = []

    def _base_metadata(self) -> Dict[str, Any]:
        """Get base metadata for entries."""
        return {
            "attempt": self.current_attempt,
            "round": self.current_round,
            "agent_id": self.agent_id,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Injection support
    # ─────────────────────────────────────────────────────────────────────

    def inject_update(
        self,
        new_answers: Dict[str, str],
        anonymize: bool = True,
    ) -> None:
        """
        Inject update from other agents into buffer.

        This is the canonical injection point - modifies the buffer directly
        with new answers from other agents.

        Args:
            new_answers: Dict mapping agent_id to their answer content
            anonymize: If True, use anonymous labels (agent1, agent2) instead of IDs
        """
        if not new_answers:
            return

        now = time.time()
        update_content = self._format_injection_message(new_answers, anonymize)

        self.entries.append(
            ConversationEntry(
                timestamp=now,
                entry_type=EntryType.INJECTION,
                content=update_content,
                metadata={
                    **self._base_metadata(),
                    "source_agents": list(new_answers.keys()),
                    "answer_count": len(new_answers),
                },
            ),
        )

        self._injection_timestamps.append(now)

    def _format_injection_message(
        self,
        new_answers: Dict[str, str],
        anonymize: bool = True,
    ) -> str:
        """
        Format the injection message content.

        Args:
            new_answers: Dict mapping agent_id to answer content
            anonymize: If True, use anonymous labels

        Returns:
            Formatted injection message string
        """
        parts = [
            "UPDATE: While you were working, new answers were provided.",
            "",
            "<NEW_ANSWERS>",
        ]

        for i, (agent_id, answer) in enumerate(sorted(new_answers.items()), 1):
            label = f"agent{i}" if anonymize else agent_id
            parts.append(f"<{label}>")
            parts.append(answer)
            parts.append(f"</{label}>")
            parts.append("")

        parts.append("</NEW_ANSWERS>")
        parts.append("")
        parts.append("You can now:")
        parts.append("1. Continue your current approach if you think it's better or different")
        parts.append("2. Build upon or refine the new answers")
        parts.append("3. Vote for an existing answer if you agree with it")
        parts.append("")
        parts.append("Proceed with your decision.")

        return "\n".join(parts)

    def get_last_injection_timestamp(self) -> Optional[float]:
        """Get timestamp of most recent injection, if any."""
        return self._injection_timestamps[-1] if self._injection_timestamps else None

    def get_entries_since_injection(self) -> List[ConversationEntry]:
        """Get all entries since the last injection."""
        last_injection = self.get_last_injection_timestamp()
        if last_injection is None:
            return self.entries.copy()
        return [e for e in self.entries if e.timestamp > last_injection]

    # ─────────────────────────────────────────────────────────────────────
    # Building LLM messages
    # ─────────────────────────────────────────────────────────────────────

    def to_messages(
        self,
        include_reasoning: bool = False,
        include_tool_details: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Convert buffer to generic LLM message format.

        This produces the message list that gets sent to the LLM API.
        For backend-specific formats, use to_openai_messages() or to_anthropic_messages().

        Args:
            include_reasoning: If True, include reasoning entries
            include_tool_details: If True, include tool call/result entries

        Returns:
            List of message dicts in LLM format
        """
        messages = []
        i = 0
        entries = self.entries

        while i < len(entries):
            entry = entries[i]

            if entry.entry_type == EntryType.SYSTEM:
                messages.append({"role": "system", "content": entry.content})

            elif entry.entry_type == EntryType.USER:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.ASSISTANT:
                messages.append({"role": "assistant", "content": entry.content})

            elif entry.entry_type == EntryType.REASONING:
                if include_reasoning:
                    messages.append(
                        {
                            "role": "assistant",
                            "content": f"[Reasoning]\n{entry.content}",
                        },
                    )

            elif entry.entry_type == EntryType.TOOL_CALL:
                if include_tool_details:
                    # Batch consecutive TOOL_CALL entries into a single assistant message
                    # OpenAI format requires all tool calls from one turn in one message
                    tool_calls = []
                    while i < len(entries) and entries[i].entry_type == EntryType.TOOL_CALL:
                        tc_entry = entries[i]
                        tool_name = tc_entry.metadata.get("tool_name", "unknown")
                        call_id = tc_entry.metadata.get("call_id", "")
                        tool_calls.append(
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": tool_name,
                                    "arguments": tc_entry.content,
                                },
                            },
                        )
                        i += 1
                    messages.append(
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": tool_calls,
                        },
                    )
                    continue  # Skip the i += 1 at the end since we already advanced

            elif entry.entry_type == EntryType.TOOL_RESULT:
                if include_tool_details:
                    messages.append(
                        {
                            "role": "tool",
                            "content": entry.content,
                            "tool_call_id": entry.metadata.get("call_id", ""),
                        },
                    )

            elif entry.entry_type == EntryType.INJECTION:
                # Injection appears as user message from orchestrator
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.MEMORY_CONTEXT:
                # Memory context injected as system message
                messages.append({"role": "system", "content": entry.content})

            elif entry.entry_type == EntryType.COMPRESSION_REQUEST:
                # Compression request as user message
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.ENFORCEMENT:
                # Enforcement as user message from orchestrator
                messages.append({"role": "user", "content": entry.content})

            i += 1

        return messages

    def to_openai_messages(self, include_reasoning: bool = False) -> List[Dict[str, Any]]:
        """
        Convert buffer to OpenAI-compatible message format.

        Handles tool calls properly:
        - Assistant messages with tool_calls can also have content
        - Consecutive tool calls from same turn are batched
        - Tool results use role="tool" with tool_call_id

        Args:
            include_reasoning: If True, include reasoning entries

        Returns:
            List of message dicts in OpenAI format
        """
        messages = []

        # Buffer for accumulating assistant turn content
        pending_content = None
        pending_tool_calls = []

        def flush_assistant_turn():
            """Flush accumulated assistant content + tool calls as one message."""
            nonlocal pending_content, pending_tool_calls
            if pending_content is not None or pending_tool_calls:
                msg = {"role": "assistant"}
                if pending_content:
                    msg["content"] = pending_content
                else:
                    msg["content"] = None
                if pending_tool_calls:
                    msg["tool_calls"] = pending_tool_calls
                messages.append(msg)
                pending_content = None
                pending_tool_calls = []

        for entry in self.entries:
            # These entry types end an assistant turn
            if entry.entry_type in (
                EntryType.SYSTEM,
                EntryType.USER,
                EntryType.TOOL_RESULT,
                EntryType.INJECTION,
                EntryType.MEMORY_CONTEXT,
                EntryType.COMPRESSION_REQUEST,
                EntryType.ENFORCEMENT,
            ):
                flush_assistant_turn()

            if entry.entry_type == EntryType.SYSTEM:
                messages.append({"role": "system", "content": entry.content})

            elif entry.entry_type == EntryType.USER:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.ASSISTANT:
                # Accumulate content for this turn
                if pending_content is None:
                    pending_content = entry.content
                else:
                    pending_content += "\n" + entry.content

            elif entry.entry_type == EntryType.REASONING:
                if include_reasoning:
                    # Accumulate reasoning as content
                    reasoning_text = f"[Reasoning]\n{entry.content}"
                    if pending_content is None:
                        pending_content = reasoning_text
                    else:
                        pending_content += "\n" + reasoning_text

            elif entry.entry_type == EntryType.TOOL_CALL:
                tool_name = entry.metadata.get("tool_name", "unknown")
                call_id = entry.metadata.get("call_id", f"call_{len(pending_tool_calls)}")
                pending_tool_calls.append(
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": entry.content,
                        },
                    },
                )

            elif entry.entry_type == EntryType.TOOL_RESULT:
                messages.append(
                    {
                        "role": "tool",
                        "content": entry.content,
                        "tool_call_id": entry.metadata.get("call_id", ""),
                    },
                )

            elif entry.entry_type == EntryType.INJECTION:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.MEMORY_CONTEXT:
                messages.append({"role": "system", "content": entry.content})

            elif entry.entry_type == EntryType.COMPRESSION_REQUEST:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.ENFORCEMENT:
                messages.append({"role": "user", "content": entry.content})

        # Flush any remaining assistant content/tool calls
        flush_assistant_turn()

        return messages

    def to_anthropic_messages(self, include_reasoning: bool = False) -> List[Dict[str, Any]]:
        """
        Convert buffer to Anthropic Claude-compatible message format.

        Handles tool calls properly:
        - Tool calls use content blocks with type="tool_use"
        - Tool results use content blocks with type="tool_result"
        - System messages should be extracted separately by caller

        Args:
            include_reasoning: If True, include reasoning/thinking entries

        Returns:
            List of message dicts in Anthropic format
        """
        messages = []
        pending_content_blocks = []  # Accumulate content blocks for assistant turn

        def flush_assistant_turn():
            """Flush accumulated content blocks as one assistant message."""
            nonlocal pending_content_blocks
            if pending_content_blocks:
                messages.append(
                    {
                        "role": "assistant",
                        "content": pending_content_blocks,
                    },
                )
                pending_content_blocks = []

        for entry in self.entries:
            # These entry types end an assistant turn
            if entry.entry_type in (
                EntryType.SYSTEM,
                EntryType.USER,
                EntryType.TOOL_RESULT,
                EntryType.INJECTION,
                EntryType.MEMORY_CONTEXT,
                EntryType.COMPRESSION_REQUEST,
                EntryType.ENFORCEMENT,
            ):
                flush_assistant_turn()

            if entry.entry_type == EntryType.SYSTEM:
                # Anthropic handles system separately via system parameter
                # Include as user message with prefix for compatibility
                messages.append({"role": "user", "content": f"[System]: {entry.content}"})

            elif entry.entry_type == EntryType.USER:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.ASSISTANT:
                pending_content_blocks.append(
                    {
                        "type": "text",
                        "text": entry.content,
                    },
                )

            elif entry.entry_type == EntryType.REASONING:
                if include_reasoning:
                    pending_content_blocks.append(
                        {
                            "type": "thinking",
                            "thinking": entry.content,
                        },
                    )

            elif entry.entry_type == EntryType.TOOL_CALL:
                tool_name = entry.metadata.get("tool_name", "unknown")
                call_id = entry.metadata.get("call_id", f"toolu_{len(pending_content_blocks)}")
                # Parse arguments from JSON string
                try:
                    args = json.loads(entry.content) if entry.content else {}
                except json.JSONDecodeError:
                    args = {"raw": entry.content}
                pending_content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": call_id,
                        "name": tool_name,
                        "input": args,
                    },
                )

            elif entry.entry_type == EntryType.TOOL_RESULT:
                # Tool result as user message with tool_result block
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": entry.metadata.get("call_id", ""),
                                "content": entry.content,
                            },
                        ],
                    },
                )

            elif entry.entry_type == EntryType.INJECTION:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.MEMORY_CONTEXT:
                messages.append({"role": "user", "content": f"[Memory Context]: {entry.content}"})

            elif entry.entry_type == EntryType.COMPRESSION_REQUEST:
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.ENFORCEMENT:
                messages.append({"role": "user", "content": entry.content})

        # Flush any remaining content blocks
        flush_assistant_turn()

        return messages

    def to_messages_for_backend(self, provider: str) -> List[Dict[str, Any]]:
        """
        Convert buffer to messages for a specific backend provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic", "google")

        Returns:
            List of message dicts in provider-specific format
        """
        provider_lower = provider.lower() if provider else ""

        if provider_lower in ("anthropic", "claude", "claude_code"):
            return self.to_anthropic_messages()
        elif provider_lower in ("openai", "azure", "azure openai"):
            return self.to_openai_messages()
        else:
            # Generic format works for most providers
            return self.to_messages()

    def to_simple_messages(self) -> List[Dict[str, str]]:
        """
        Convert buffer to simple message format (role + content only).

        Useful for backends that don't support tool message format.

        Returns:
            List of simple message dicts
        """
        messages = []

        for entry in self.entries:
            if entry.entry_type == EntryType.SYSTEM:
                messages.append({"role": "system", "content": entry.content})

            elif entry.entry_type in (EntryType.USER, EntryType.INJECTION, EntryType.ENFORCEMENT, EntryType.COMPRESSION_REQUEST):
                messages.append({"role": "user", "content": entry.content})

            elif entry.entry_type == EntryType.MEMORY_CONTEXT:
                messages.append({"role": "system", "content": entry.content})

            elif entry.entry_type in (EntryType.ASSISTANT, EntryType.REASONING):
                messages.append({"role": "assistant", "content": entry.content})

            elif entry.entry_type == EntryType.TOOL_CALL:
                tool_name = entry.metadata.get("tool_name", "unknown")
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"[Using tool: {tool_name}]\nArguments: {entry.content}",
                    },
                )

            elif entry.entry_type == EntryType.TOOL_RESULT:
                tool_name = entry.metadata.get("tool_name", "unknown")
                messages.append(
                    {
                        "role": "user",  # Tool results as user message in simple format
                        "content": f"[Result from {tool_name}]: {entry.content}",
                    },
                )

        return messages

    # ─────────────────────────────────────────────────────────────────────
    # Query methods
    # ─────────────────────────────────────────────────────────────────────

    def get_entries_since(self, timestamp: float) -> List[ConversationEntry]:
        """Get all entries since a given timestamp."""
        return [e for e in self.entries if e.timestamp > timestamp]

    def get_entries_by_type(self, entry_type: EntryType) -> List[ConversationEntry]:
        """Get all entries of a specific type."""
        return [e for e in self.entries if e.entry_type == entry_type]

    def get_tool_calls(self) -> List[ConversationEntry]:
        """Get all tool call entries."""
        return self.get_entries_by_type(EntryType.TOOL_CALL)

    def get_assistant_content(self) -> str:
        """Get concatenated assistant content."""
        entries = self.get_entries_by_type(EntryType.ASSISTANT)
        return "\n\n".join(e.content for e in entries)

    def entry_count(self) -> int:
        """Get total number of entries."""
        return len(self.entries)

    def has_pending_content(self) -> bool:
        """Check if there's unflushed pending content."""
        return bool(
            self._pending_content.strip() or self._pending_reasoning.strip() or self._pending_tool_calls,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Token counting
    # ─────────────────────────────────────────────────────────────────────

    def estimate_tokens(self, calculator: Optional["TokenCostCalculator"] = None) -> int:
        """
        Estimate total tokens in buffer including pending content.

        This provides an accurate view of context usage by counting ALL content
        in the buffer: entries, pending content, pending reasoning, and pending
        tool calls.

        Args:
            calculator: Optional TokenCostCalculator instance. If not provided,
                       creates a new one (slightly slower).

        Returns:
            Estimated total token count
        """
        if calculator is None:
            from .token_manager.token_manager import TokenCostCalculator

            calculator = TokenCostCalculator()

        # Build complete content from all entries
        all_content = []

        # Committed entries
        for entry in self.entries:
            all_content.append(entry.content)
            # Include tool metadata in token count
            if entry.entry_type in (EntryType.TOOL_CALL, EntryType.TOOL_RESULT):
                tool_name = entry.metadata.get("tool_name", "")
                if tool_name:
                    all_content.append(tool_name)

        # Pending content (not yet flushed)
        if self._pending_content.strip():
            all_content.append(self._pending_content)

        if self._pending_reasoning.strip():
            all_content.append(self._pending_reasoning)

        for call in self._pending_tool_calls:
            all_content.append(call.get("name", ""))
            all_content.append(json.dumps(call.get("arguments", {}), default=str))
            if call.get("result"):
                all_content.append(str(call["result"]))

        # Join and estimate
        combined = "\n".join(all_content)
        return calculator.estimate_tokens(combined)

    def get_token_stats(self, calculator: Optional["TokenCostCalculator"] = None) -> Dict[str, int]:
        """
        Get detailed token breakdown by entry type.

        Args:
            calculator: Optional TokenCostCalculator instance.

        Returns:
            Dict with token counts per entry type and totals
        """
        if calculator is None:
            from .token_manager.token_manager import TokenCostCalculator

            calculator = TokenCostCalculator()

        stats: Dict[str, int] = {
            "user": 0,
            "assistant": 0,
            "system": 0,
            "tool_call": 0,
            "tool_result": 0,
            "injection": 0,
            "reasoning": 0,
            "memory_context": 0,
            "compression_request": 0,
            "enforcement": 0,
            "pending": 0,
            "total": 0,
        }

        # Count committed entries by type
        for entry in self.entries:
            content = entry.content
            if entry.entry_type in (EntryType.TOOL_CALL, EntryType.TOOL_RESULT):
                tool_name = entry.metadata.get("tool_name", "")
                if tool_name:
                    content = f"{tool_name}\n{content}"

            tokens = calculator.estimate_tokens(content)
            stats[entry.entry_type.value] += tokens
            stats["total"] += tokens

        # Count pending content
        pending_tokens = 0
        if self._pending_content.strip():
            pending_tokens += calculator.estimate_tokens(self._pending_content)
        if self._pending_reasoning.strip():
            pending_tokens += calculator.estimate_tokens(self._pending_reasoning)
        for call in self._pending_tool_calls:
            pending_tokens += calculator.estimate_tokens(call.get("name", ""))
            pending_tokens += calculator.estimate_tokens(json.dumps(call.get("arguments", {}), default=str))
            if call.get("result"):
                pending_tokens += calculator.estimate_tokens(str(call["result"]))

        stats["pending"] = pending_tokens
        stats["total"] += pending_tokens

        return stats

    # ─────────────────────────────────────────────────────────────────────
    # Persistence
    # ─────────────────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize buffer to dict.

        Returns:
            Dict representation of the buffer
        """
        return {
            "agent_id": self.agent_id,
            "current_attempt": self.current_attempt,
            "current_round": self.current_round,
            "entries": [e.to_dict() for e in self.entries],
            "injection_timestamps": self._injection_timestamps,
            # Note: pending content is NOT serialized (should be flushed first)
        }

    def save(self, path: Path) -> None:
        """
        Save buffer to file.

        Args:
            path: Path to save to
        """
        # Warn if there's unflushed content
        if self.has_pending_content():
            import logging

            logging.warning(
                f"Saving buffer with unflushed content for agent {self.agent_id}. " "Call flush_turn() first to ensure all content is captured.",
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> "AgentConversationBuffer":
        """
        Load buffer from file.

        Args:
            path: Path to load from

        Returns:
            Loaded AgentConversationBuffer instance
        """
        data = json.loads(path.read_text())

        buffer = cls(data["agent_id"])
        buffer.current_attempt = data.get("current_attempt", 0)
        buffer.current_round = data.get("current_round", 0)
        buffer.entries = [ConversationEntry.from_dict(e) for e in data.get("entries", [])]
        buffer._injection_timestamps = data.get("injection_timestamps", [])

        return buffer

    def clear(self) -> None:
        """Clear all entries and pending content."""
        self.entries.clear()
        self._pending_content = ""
        self._pending_reasoning = ""
        self._pending_tool_calls = []
        self._injection_timestamps = []
        self.current_attempt = 0
        self.current_round = 0

    def clear_system_entries(self) -> int:
        """
        Clear all SYSTEM type entries from the buffer.

        This is used during phase transitions where system messages change
        (e.g., initial answer -> presentation -> post-evaluation).
        Each phase has its own system prompt, so old ones should be removed.

        Returns:
            Number of system entries removed
        """
        original_count = len(self.entries)
        self.entries = [e for e in self.entries if e.entry_type != EntryType.SYSTEM]
        removed = original_count - len(self.entries)
        return removed

    def save_to_text_file(self, path: Path) -> None:
        """
        Save buffer to grep-friendly text file.

        Each entry is formatted as a single line:
        [HH:MM:SS.ms] [TYPE] content...

        This format is optimized for grep/search rather than cat.

        Args:
            path: Path to save to (typically buffer.txt)
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        # Flush any pending content first
        if self.has_pending_content():
            self.flush_turn()

        lines = []
        for entry in self.entries:
            lines.append(self._format_entry_line(entry))

        path.write_text("\n".join(lines))

    def _format_entry_line(self, entry: "ConversationEntry") -> str:
        """
        Format entry as single grep-friendly line.

        Args:
            entry: The conversation entry to format

        Returns:
            Formatted line string
        """
        from datetime import datetime

        ts = datetime.fromtimestamp(entry.timestamp).strftime("%H:%M:%S.%f")[:-3]
        entry_type = entry.entry_type.value.upper()

        # Add tool name for tool entries
        if entry.entry_type in (EntryType.TOOL_CALL, EntryType.TOOL_RESULT):
            tool_name = entry.metadata.get("tool_name", "unknown")
            entry_type = f"{entry_type}:{tool_name}"

        # Replace newlines with spaces for grep-friendly single-line format
        content = entry.content.replace("\n", " ").replace("\r", "")

        return f"[{ts}] [{entry_type}] {content}"

    # ─────────────────────────────────────────────────────────────────────
    # String representation
    # ─────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"AgentConversationBuffer(" f"agent_id={self.agent_id!r}, " f"entries={len(self.entries)}, " f"attempt={self.current_attempt}, " f"round={self.current_round})"

    def __len__(self) -> int:
        return len(self.entries)
