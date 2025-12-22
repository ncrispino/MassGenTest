# -*- coding: utf-8 -*-
"""
Gemini Interactions API parameters handler.
"""

from typing import Any, Dict, List, Set

from ._api_params_handler_base import APIParamsHandlerBase


class GeminiInteractionsAPIParamsHandler(APIParamsHandlerBase):
    """API params handler for Gemini Interactions API."""

    def get_excluded_params(self) -> Set[str]:
        base = self.get_base_excluded_params()
        extra = {
            "enable_web_search",
            "enable_google_search",
            "enable_code_execution",
            "enable_url_context",
            "use_interactions_api",
            "interactions_polling_interval",
            "interactions_stream_mode",
            "interactions_store",
            "function_calling_mode",
            "use_multi_mcp",
            "mcp_sdk_auto",
            "allowed_tools",
            "exclude_tools",
            "custom_tools",
            "enable_file_generation",
            "enable_image_generation",
            "enable_audio_generation",
            "enable_video_generation",
            "gemini_backoff_max_attempts",
            "gemini_backoff_initial_delay",
            "gemini_backoff_multiplier",
            "gemini_backoff_max_delay",
            "gemini_backoff_jitter",
            "thinking_level",
            "thinking_budget",
            "include_thoughts",
            "response_format",
            "response_modalities",
        }
        return set(base) | extra

    def get_provider_tools(self, all_params: Dict[str, Any]) -> List[Any]:
        """Get provider-specific builtin tools."""
        tools: List[Any] = []

        if all_params.get("enable_web_search", False):
            try:
                from google.genai.types import GoogleSearch, Tool

                tools.append(Tool(google_search=GoogleSearch()))
            except Exception:
                pass

        if all_params.get("enable_code_execution", False):
            try:
                from google.genai.types import Tool, ToolCodeExecution

                tools.append(Tool(code_execution=ToolCodeExecution()))
            except Exception:
                pass

        if all_params.get("enable_url_context", False):
            tools.append({"type": "url_context"})

        return tools

    async def build_api_params(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        all_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build config dict for client.interactions.create()."""
        excluded = self.get_excluded_params()
        config: Dict[str, Any] = {}

        for key, value in all_params.items():
            if key in excluded or value is None:
                continue
            if key == "max_tokens":
                config["max_output_tokens"] = value
            elif key == "model":
                continue
            else:
                config[key] = value

        function_calling_mode = all_params.get("function_calling_mode")
        if function_calling_mode:
            from ..logger_config import logger

            try:
                from google.genai.types import FunctionCallingConfig, ToolConfig

                valid_modes = {"AUTO", "ANY", "NONE"}
                mode = function_calling_mode.upper()
                if mode not in valid_modes:
                    logger.warning(
                        f"[GeminiInteractions] Invalid function_calling_mode '{function_calling_mode}'. " f"Valid modes: {valid_modes}. Ignoring.",
                    )
                else:
                    config["tool_config"] = ToolConfig(
                        function_calling_config=FunctionCallingConfig(mode=mode),
                    )
            except ImportError:
                logger.warning(
                    "[GeminiInteractions] google.genai.types not available. Ignoring function_calling_mode.",
                )

        return config
