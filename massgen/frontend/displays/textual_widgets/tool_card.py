# -*- coding: utf-8 -*-
"""
Tool Call Card Widget for MassGen TUI.

Provides collapsible cards for displaying tool calls with their
parameters, results, and status.
"""

from datetime import datetime
from typing import Optional

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

# Tool category detection - maps tool names to semantic categories
TOOL_CATEGORIES = {
    "filesystem": {
        "icon": "📁",
        "color": "#4ec9b0",
        "patterns": [
            "read_file",
            "write_file",
            "list_directory",
            "create_directory",
            "delete_file",
            "move_file",
            "copy_file",
            "file_exists",
            "get_file_info",
            "read_multiple_files",
            "edit_file",
            "directory_tree",
            "search_files",
            "find_files",
        ],
    },
    "web": {
        "icon": "🌐",
        "color": "#569cd6",
        "patterns": [
            "web_search",
            "search_web",
            "google_search",
            "fetch_url",
            "http_request",
            "browse",
            "scrape",
            "download",
        ],
    },
    "code": {
        "icon": "💻",
        "color": "#dcdcaa",
        "patterns": [
            "execute_command",
            "run_code",
            "bash",
            "python",
            "shell",
            "terminal",
            "exec",
            "run_script",
            "execute",
        ],
    },
    "database": {
        "icon": "🗄️",
        "color": "#c586c0",
        "patterns": [
            "query",
            "sql",
            "database",
            "db_",
            "select",
            "insert",
            "update",
            "delete_record",
        ],
    },
    "git": {
        "icon": "📦",
        "color": "#f14e32",
        "patterns": [
            "git_",
            "commit",
            "push",
            "pull",
            "clone",
            "branch",
            "merge",
            "checkout",
            "diff",
            "log",
            "status",
        ],
    },
    "api": {
        "icon": "🔌",
        "color": "#ce9178",
        "patterns": [
            "api_",
            "request",
            "post",
            "get",
            "put",
            "patch",
            "rest",
            "graphql",
            "endpoint",
        ],
    },
    "ai": {
        "icon": "🤖",
        "color": "#9cdcfe",
        "patterns": [
            "generate",
            "complete",
            "chat",
            "embed",
            "model",
            "inference",
            "predict",
            "classify",
        ],
    },
    "memory": {
        "icon": "🧠",
        "color": "#b5cea8",
        "patterns": [
            "memory",
            "remember",
            "recall",
            "store",
            "retrieve",
            "knowledge",
            "context",
        ],
    },
}


def get_tool_category(tool_name: str) -> dict:
    """Get category info for a tool name.

    Args:
        tool_name: The tool name to categorize.

    Returns:
        Dict with icon, color, and category name.
    """
    tool_lower = tool_name.lower()

    # Check MCP tools (format: mcp__server__tool)
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        if len(parts) >= 3:
            actual_tool = parts[-1]
            tool_lower = actual_tool.lower()

    # Check against category patterns
    for category_name, info in TOOL_CATEGORIES.items():
        for pattern in info["patterns"]:
            if pattern in tool_lower:
                return {
                    "icon": info["icon"],
                    "color": info["color"],
                    "category": category_name,
                }

    # Default to generic tool
    return {"icon": "🔧", "color": "#858585", "category": "tool"}


def format_tool_display_name(tool_name: str) -> str:
    """Format tool name for display.

    Args:
        tool_name: Raw tool name.

    Returns:
        Formatted display name.
    """
    # Handle MCP tools: mcp__server__tool -> server/tool
    if tool_name.startswith("mcp__"):
        parts = tool_name.split("__")
        if len(parts) >= 3:
            return f"{parts[1]}/{parts[2]}"
        elif len(parts) == 2:
            return parts[1]

    # Handle snake_case
    return tool_name.replace("_", " ").title()


class ToolCallCard(Static):
    """Collapsible card showing a tool call with status, params, and result.

    The card can be collapsed (showing just tool name and status) or
    expanded (showing full parameters and result).

    Attributes:
        tool_name: Name of the tool being called.
        tool_type: Type of tool (mcp, custom, etc.).
        status: Current status (running, success, error).
        is_expanded: Whether the card is expanded.
    """

    is_expanded = reactive(False)

    STATUS_ICONS = {
        "running": "⏳",
        "success": "✓",
        "error": "✗",
    }

    def __init__(
        self,
        tool_name: str,
        tool_type: str = "unknown",
        call_id: Optional[str] = None,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize the tool card.

        Args:
            tool_name: Name of the tool.
            tool_type: Type (mcp, custom, etc.).
            call_id: Optional unique call identifier.
            id: Optional DOM ID.
            classes: Optional CSS classes.
        """
        super().__init__(id=id, classes=classes)
        self.tool_name = tool_name
        self.tool_type = tool_type
        self.call_id = call_id
        self._status = "running"
        self._start_time = datetime.now()
        self._end_time: Optional[datetime] = None
        self._params: Optional[str] = None
        self._result: Optional[str] = None
        self._error: Optional[str] = None

        # Get category info for styling
        self._category = get_tool_category(tool_name)
        self._display_name = format_tool_display_name(tool_name)

        # Add type class for styling
        self.add_class(f"type-{self._category['category']}")
        self.add_class("status-running")

    def render(self) -> Text:
        """Render the card based on expanded state."""
        if self.is_expanded:
            return self._render_expanded()
        else:
            return self._render_collapsed()

    def _render_collapsed(self) -> Text:
        """Render collapsed view: icon + name + status + time."""
        icon = self._category["icon"]
        status_icon = self.STATUS_ICONS.get(self._status, "⏳")
        elapsed = self._get_elapsed_str()

        # Build the collapsed line
        text = Text()
        text.append("▶ ", style="dim")
        text.append(f"{icon} ", style=self._category["color"])
        text.append(self._display_name, style="bold")
        text.append("  ")

        # Status with color
        if self._status == "success":
            text.append(f"{status_icon}", style="bold green")
        elif self._status == "error":
            text.append(f"{status_icon}", style="bold red")
        else:
            text.append(f"{status_icon}", style="yellow")

        if elapsed:
            text.append(f" {elapsed}", style="dim")

        return text

    def _render_expanded(self) -> Text:
        """Render expanded view with params and result."""
        icon = self._category["icon"]
        status_icon = self.STATUS_ICONS.get(self._status, "⏳")
        elapsed = self._get_elapsed_str()
        color = self._category["color"]

        text = Text()

        # Header line
        text.append("▼ ", style="dim")
        text.append(f"{icon} ", style=color)
        text.append(self._display_name, style="bold")
        text.append("  ")

        if self._status == "success":
            text.append(f"{status_icon}", style="bold green")
        elif self._status == "error":
            text.append(f"{status_icon}", style="bold red")
        else:
            text.append(f"{status_icon}", style="yellow")

        if elapsed:
            text.append(f" {elapsed}", style="dim")

        # Parameters (if any)
        if self._params:
            text.append("\n  │ ", style="dim")
            text.append("Args: ", style="dim italic")
            params_display = self._params
            if len(params_display) > 100:
                params_display = params_display[:100] + "..."
            text.append(params_display, style="dim")

        # Result or error
        if self._error:
            text.append("\n  │ ", style="dim")
            text.append("Error: ", style="bold red")
            error_display = self._error
            if len(error_display) > 200:
                error_display = error_display[:200] + "..."
            text.append(error_display, style="red")
        elif self._result:
            text.append("\n  │ ", style="dim")
            text.append("Result: ", style="dim italic")
            result_lines = self._result.split("\n")
            if len(result_lines) > 5:
                result_display = "\n".join(result_lines[:5])
                text.append(result_display, style="dim")
                text.append(f"\n  │ ... [{len(result_lines) - 5} more lines]", style="dim italic")
            else:
                result_display = self._result
                if len(result_display) > 300:
                    result_display = result_display[:300] + "..."
                text.append(result_display, style="dim")
        elif self._status == "running":
            # Show waiting message when still running
            text.append("\n  │ ", style="dim")
            text.append("Waiting for result...", style="dim italic")

        return text

    def watch_is_expanded(self, expanded: bool) -> None:
        """React to expansion state changes."""
        self.refresh()

    def _get_elapsed_str(self) -> str:
        """Get elapsed time as formatted string."""
        end = self._end_time or datetime.now()
        elapsed = (end - self._start_time).total_seconds()

        if elapsed < 60:
            return f"({elapsed:.1f}s)"
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            return f"({mins}m{secs}s)"

    def on_click(self) -> None:
        """Handle click to toggle expanded state."""
        self.toggle_expanded()

    def toggle_expanded(self) -> None:
        """Toggle between collapsed and expanded view."""
        self.is_expanded = not self.is_expanded

    def set_params(self, params: str) -> None:
        """Set the tool parameters.

        Args:
            params: Parameters string to display.
        """
        self._params = params
        self.refresh()

    def set_result(self, result: str) -> None:
        """Set successful result.

        Args:
            result: Result string to display.
        """
        self._status = "success"
        self._result = result
        self._end_time = datetime.now()
        self.remove_class("status-running")
        self.add_class("status-success")
        self.refresh()

    def set_error(self, error: str) -> None:
        """Set error result.

        Args:
            error: Error message to display.
        """
        self._status = "error"
        self._error = error
        self._end_time = datetime.now()
        self.remove_class("status-running")
        self.add_class("status-error")
        self.refresh()

    @property
    def status(self) -> str:
        """Get current status."""
        return self._status

    @property
    def display_name(self) -> str:
        """Get display name."""
        return self._display_name
