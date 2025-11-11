# -*- coding: utf-8 -*-
"""
Broadcast toolkit for agent-to-agent and agent-to-human communication.
"""

from typing import Any, Dict, List, Optional

from .base import BaseToolkit, ToolType


class BroadcastToolkit(BaseToolkit):
    """Broadcast communication toolkit for agent coordination."""

    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        broadcast_mode: str = "agents",
        wait_by_default: bool = True,
    ):
        """
        Initialize the Broadcast toolkit.

        Args:
            orchestrator: Reference to orchestrator (for accessing BroadcastChannel)
            broadcast_mode: "agents" or "human"
            wait_by_default: Default waiting behavior for ask_others()
        """
        self.orchestrator = orchestrator
        self.broadcast_mode = broadcast_mode
        self.wait_by_default = wait_by_default

    @property
    def toolkit_id(self) -> str:
        """Unique identifier for broadcast toolkit."""
        return "broadcast"

    @property
    def toolkit_type(self) -> ToolType:
        """Type of this toolkit."""
        return ToolType.WORKFLOW

    def is_enabled(self, config: Dict[str, Any]) -> bool:
        """
        Check if broadcasts are enabled in configuration.

        Args:
            config: Configuration dictionary.

        Returns:
            True if broadcasts are enabled.
        """
        return config.get("broadcast_enabled", False)

    def set_orchestrator(self, orchestrator: Any):
        """
        Set the orchestrator reference.

        Args:
            orchestrator: Orchestrator instance
        """
        self.orchestrator = orchestrator

    def get_tools(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get broadcast tool definitions based on API format.

        Args:
            config: Configuration including api_format.

        Returns:
            List of broadcast tool definitions.
        """
        api_format = config.get("api_format", "chat_completions")

        tools = []

        # Tool 1: ask_others
        if api_format == "claude":
            ask_others_tool = {
                "name": "ask_others",
                "description": (
                    "Ask a question to other agents"
                    + (" and the human user" if self.broadcast_mode == "human" else "")
                    + " for collaborative problem-solving. Use this to coordinate, get input, or discuss approaches."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Your question for other agents (be specific and actionable)",
                        },
                        "wait": {
                            "type": "boolean",
                            "description": (
                                f"Whether to wait for responses (default: {self.wait_by_default}). " "If true, blocks until responses collected. If false, returns request_id for polling."
                            ),
                        },
                    },
                    "required": ["question"],
                },
            }
        else:
            # Chat completions format (OpenAI, etc.)
            ask_others_tool = {
                "type": "function",
                "function": {
                    "name": "ask_others",
                    "description": (
                        "Ask a question to other agents"
                        + (" and the human user" if self.broadcast_mode == "human" else "")
                        + " for collaborative problem-solving. Use this to coordinate, get input, or discuss approaches."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Your question for other agents (be specific and actionable)",
                            },
                            "wait": {
                                "type": "boolean",
                                "description": (
                                    f"Whether to wait for responses (default: {self.wait_by_default}). " "If true, blocks until responses collected. If false, returns request_id for polling."
                                ),
                            },
                        },
                        "required": ["question"],
                    },
                },
            }

        tools.append(ask_others_tool)

        # Tool 2: check_broadcast_status (only for polling mode)
        if not self.wait_by_default:
            if api_format == "claude":
                check_status_tool = {
                    "name": "check_broadcast_status",
                    "description": "Check the status of a broadcast request to see if responses are ready.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "request_id": {
                                "type": "string",
                                "description": "Request ID from ask_others()",
                            },
                        },
                        "required": ["request_id"],
                    },
                }
            else:
                check_status_tool = {
                    "type": "function",
                    "function": {
                        "name": "check_broadcast_status",
                        "description": "Check the status of a broadcast request to see if responses are ready.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "request_id": {
                                    "type": "string",
                                    "description": "Request ID from ask_others()",
                                },
                            },
                            "required": ["request_id"],
                        },
                    },
                }
            tools.append(check_status_tool)

        # Tool 3: get_broadcast_responses
        if api_format == "claude":
            get_responses_tool = {
                "name": "get_broadcast_responses",
                "description": "Get responses for a broadcast request (for polling mode).",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "request_id": {
                            "type": "string",
                            "description": "Request ID from ask_others()",
                        },
                    },
                    "required": ["request_id"],
                },
            }
        else:
            get_responses_tool = {
                "type": "function",
                "function": {
                    "name": "get_broadcast_responses",
                    "description": "Get responses for a broadcast request (for polling mode).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "request_id": {
                                "type": "string",
                                "description": "Request ID from ask_others()",
                            },
                        },
                        "required": ["request_id"],
                    },
                },
            }

        if not self.wait_by_default:
            tools.append(get_responses_tool)

        return tools
