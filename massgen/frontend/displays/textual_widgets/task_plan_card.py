# -*- coding: utf-8 -*-
"""
Task Plan Card Widget for MassGen TUI.

Visual todo list display for Planning MCP integration.
Shows tasks from create_task_plan, update_task_status, etc.
"""

from typing import Any, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static


class TaskPlanCard(Static):
    """Card displaying a visual todo list from Planning MCP.

    Design:
    ```
    ┌─ Tasks ────────────────────────────────────┐
    │ ✓ Research OAuth providers                 │  ← completed (dimmed)
    │ ✓ Compare authentication methods           │  ← completed (dimmed)
    │ ● Implement OAuth flow                     │  ← in_progress (highlighted)
    │ ○ Write integration tests                  │  ← pending (ready)
    │ ○ Deploy to staging                        │  ← pending (blocked)
    └────────────────────────────────────────────┘
    ```

    Display Logic:
    - On create_task_plan: Show first 5 tasks
    - On update_task_status/edit_task: Show neighborhood around focused task
      (2 above, focused task, 2 below)
    """

    DEFAULT_CSS = """
    TaskPlanCard {
        width: 100%;
        height: auto;
        min-height: 3;
        padding: 0 1;
        margin: 1 0;
        background: #1a1f2e;
        border-left: thick #a371f7;
    }

    TaskPlanCard .task-header {
        text-style: bold;
        color: #a371f7;
        margin-bottom: 1;
    }

    TaskPlanCard .task-item {
        height: auto;
        padding: 0;
    }

    TaskPlanCard .task-completed {
        color: #6e7681;
    }

    TaskPlanCard .task-in-progress {
        color: #58a6ff;
        text-style: bold;
    }

    TaskPlanCard .task-pending {
        color: #8b949e;
    }

    TaskPlanCard .task-blocked {
        color: #6e7681;
        text-style: italic;
    }

    TaskPlanCard .task-focused {
        background: #21262d;
    }

    TaskPlanCard .task-count {
        color: #6e7681;
        text-style: italic;
    }
    """

    # Status indicators
    STATUS_ICONS = {
        "completed": "✓",
        "in_progress": "●",
        "pending": "○",
        "blocked": "◌",
    }

    # Maximum tasks to show
    MAX_VISIBLE = 5

    # Reactive properties
    tasks: reactive[List[Dict[str, Any]]] = reactive(list, always_update=True)
    focused_task_id: reactive[Optional[str]] = reactive(None)

    def __init__(
        self,
        tasks: Optional[List[Dict[str, Any]]] = None,
        focused_task_id: Optional[str] = None,
        operation: str = "create",
        id: Optional[str] = None,
    ) -> None:
        """Initialize the task plan card.

        Args:
            tasks: List of task dictionaries with id, description, status, priority
            focused_task_id: ID of the task to focus on (for update operations)
            operation: Type of operation (create, update, edit)
            id: Widget ID
        """
        super().__init__(id=id)
        self._tasks = tasks or []
        self._focused_task_id = focused_task_id
        self._operation = operation

    def compose(self) -> ComposeResult:
        yield Static(self._build_content())

    def _build_content(self) -> Text:
        """Build the card content as Rich Text."""
        text = Text()

        if not self._tasks:
            text.append("📋 No tasks", style="dim")
            return text

        # Header
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.get("status") == "completed")
        text.append(f"📋 Tasks ({completed}/{total})\n", style="bold #a371f7")

        # Get visible tasks based on operation
        visible_tasks, start_idx = self._get_visible_tasks()

        # Show "more above" indicator
        if start_idx > 0:
            text.append(f"  ↑ {start_idx} more above\n", style="dim italic")

        # Render each visible task
        for i, task in enumerate(visible_tasks):
            start_idx + i
            is_focused = task.get("id") == self._focused_task_id

            # Status icon
            status = task.get("status", "pending")
            icon = self.STATUS_ICONS.get(status, "○")

            # Description (truncate if needed)
            desc = task.get("description", "Untitled task")
            if len(desc) > 50:
                desc = desc[:47] + "..."

            # Style based on status
            if status == "completed":
                style = "dim #6e7681"
            elif status == "in_progress":
                style = "bold #58a6ff"
            elif status == "blocked":
                style = "italic #6e7681"
            else:
                style = "#8b949e"

            # Add focus highlight
            if is_focused:
                style = f"{style} on #21262d"

            # Priority indicator
            priority = task.get("priority", "medium")
            priority_marker = ""
            if priority == "high":
                priority_marker = " !"

            text.append(f"  {icon} {desc}{priority_marker}\n", style=style)

        # Show "more below" indicator
        remaining = total - (start_idx + len(visible_tasks))
        if remaining > 0:
            text.append(f"  ↓ {remaining} more below", style="dim italic")

        return text

    def _get_visible_tasks(self) -> tuple[List[Dict[str, Any]], int]:
        """Get the visible subset of tasks based on operation type.

        Returns:
            Tuple of (visible_tasks, start_index)
        """
        total = len(self._tasks)

        if total <= self.MAX_VISIBLE:
            return self._tasks, 0

        if self._operation == "create" or not self._focused_task_id:
            # Show first MAX_VISIBLE tasks
            return self._tasks[: self.MAX_VISIBLE], 0

        # Find focused task index
        focused_idx = 0
        for i, task in enumerate(self._tasks):
            if task.get("id") == self._focused_task_id:
                focused_idx = i
                break

        # Calculate window: 2 above, focused, 2 below
        context_above = 2
        context_below = 2

        start = max(0, focused_idx - context_above)
        end = min(total, focused_idx + context_below + 1)

        # Adjust if we're at the edges
        if end - start < self.MAX_VISIBLE:
            if start == 0:
                end = min(total, self.MAX_VISIBLE)
            elif end == total:
                start = max(0, total - self.MAX_VISIBLE)

        return self._tasks[start:end], start

    def update_tasks(self, tasks: List[Dict[str, Any]], focused_task_id: Optional[str] = None, operation: str = "update") -> None:
        """Update the displayed tasks.

        Args:
            tasks: New list of tasks
            focused_task_id: Task to focus on
            operation: Type of operation
        """
        self._tasks = tasks
        self._focused_task_id = focused_task_id
        self._operation = operation

        # Update display
        try:
            content_widget = self.query_one(Static)
            content_widget.update(self._build_content())
        except Exception:
            pass

    @classmethod
    def from_mcp_result(cls, result: Dict[str, Any], operation: str = "create") -> "TaskPlanCard":
        """Create a TaskPlanCard from MCP tool result.

        Args:
            result: Result dictionary from Planning MCP tool
            operation: Type of operation (create, update, add, edit)

        Returns:
            Configured TaskPlanCard instance
        """
        tasks = []
        focused_task_id = None

        # Extract tasks from result
        if "tasks" in result:
            tasks = result["tasks"]
        elif "plan" in result and "tasks" in result["plan"]:
            tasks = result["plan"]["tasks"]

        # Extract focused task from update operations
        if operation in ("update", "edit") and "task" in result:
            focused_task_id = result["task"].get("id")

        return cls(tasks=tasks, focused_task_id=focused_task_id, operation=operation)
