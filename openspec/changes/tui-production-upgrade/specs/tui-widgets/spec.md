# TUI Widget Specifications

## Overview
This document specifies the API and behavior of new Textual widgets for the TUI production upgrade.

---

## 1. AgentTabBar

### Purpose
Horizontal tab bar for switching between agent panels.

### API
```python
class AgentTabBar(Widget):
    """Horizontal tab bar for agent switching."""

    # Reactive attributes
    active_agent: reactive[str]  # Currently selected agent ID

    def __init__(
        self,
        agent_ids: List[str],
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize tab bar.

        Args:
            agent_ids: List of agent IDs to display as tabs.
        """

    def update_agent_status(self, agent_id: str, status: str) -> None:
        """Update the status badge for an agent.

        Args:
            agent_id: Agent to update.
            status: One of "waiting", "working", "streaming", "completed", "error".
        """

    def set_active(self, agent_id: str) -> None:
        """Set the active (visible) agent.

        Args:
            agent_id: Agent to make active.
        """

    def action_next_tab(self) -> None:
        """Switch to next agent tab (Tab key)."""

    def action_previous_tab(self) -> None:
        """Switch to previous agent tab (Shift+Tab)."""

    def action_tab_1(self) -> None:
        """Switch to first agent (key 1)."""
        # ... action_tab_2 through action_tab_9
```

### Events
```python
class AgentTabChanged(Message):
    """Emitted when active tab changes."""
    agent_id: str  # Newly active agent
```

### CSS Classes
| Class | Description |
|-------|-------------|
| `.agent-tab` | Individual tab |
| `.agent-tab--active` | Currently selected tab |
| `.agent-tab--working` | Agent is working |
| `.agent-tab--completed` | Agent completed |
| `.agent-tab--error` | Agent errored |

### Bindings
| Key | Action |
|-----|--------|
| `tab` | `action_next_tab` |
| `shift+tab` | `action_previous_tab` |
| `1`-`9` | `action_tab_N` |

---

## 2. AgentContentPanel

### Purpose
Displays streaming content for a single agent with scrolling.

### API
```python
class AgentContentPanel(Widget):
    """Content panel for displaying agent output."""

    # Reactive attributes
    agent_id: reactive[str]
    status: reactive[str]
    auto_scroll: reactive[bool]

    def __init__(
        self,
        agent_id: str,
        model_name: Optional[str] = None,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize content panel.

        Args:
            agent_id: Agent ID to display.
            model_name: Model name for header display.
        """

    def append_content(
        self,
        content: str,
        content_type: str = "thinking",
    ) -> None:
        """Append streaming content.

        Args:
            content: Text content to append.
            content_type: Type of content for styling.
        """

    def add_tool_card(self, event: ToolCallEvent) -> None:
        """Add a tool call card.

        Args:
            event: Tool call event data.
        """

    def update_tool_card(
        self,
        call_id: str,
        status: Optional[str] = None,
        result: Optional[str] = None,
    ) -> None:
        """Update an existing tool card.

        Args:
            call_id: Tool call ID to update.
            status: New status.
            result: Tool result.
        """

    def clear(self) -> None:
        """Clear all content."""

    def scroll_to_bottom(self) -> None:
        """Scroll to bottom of content."""
```

### CSS Classes
| Class | Description |
|-------|-------------|
| `.agent-header` | Agent name/model header |
| `.agent-content` | Main scrollable area |
| `.content-thinking` | Thinking/reasoning text |
| `.content-tool` | Tool-related text |
| `.content-status` | Status messages |

---

## 3. ToolCallCard

### Purpose
Collapsible card for displaying tool call information.

### API
```python
@dataclass
class ToolCallEvent:
    """Data for a tool call."""
    call_id: str
    tool_name: str
    tool_type: str  # "mcp", "custom", "filesystem", "code", "web"
    status: str  # "pending", "running", "success", "error"
    params: Optional[Dict[str, Any]] = None
    result: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ToolCallCard(Widget):
    """Collapsible tool call display card."""

    # Reactive attributes
    expanded: reactive[bool]
    status: reactive[str]

    def __init__(
        self,
        event: ToolCallEvent,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize tool card.

        Args:
            event: Tool call event data.
        """

    def update(
        self,
        status: Optional[str] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update card with new data.

        Args:
            status: New status.
            result: Tool result.
            error: Error message.
        """

    def toggle_expand(self) -> None:
        """Toggle expanded/collapsed state."""

    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time for this tool call."""
```

### Visual States
| State | Collapsed View | Expanded View |
|-------|----------------|---------------|
| Pending | `🔧 tool_name ⏳ Pending` | + params |
| Running | `🔧 tool_name ⏳ Running` | + params |
| Success | `🔧 tool_name ✅ Done (1.2s)` | + params + result |
| Error | `🔧 tool_name ❌ Error` | + params + error |

### CSS Classes
| Class | Description |
|-------|-------------|
| `.tool-card` | Base card style |
| `.tool-card--collapsed` | Collapsed state |
| `.tool-card--expanded` | Expanded state |
| `.tool-card--running` | Currently executing |
| `.tool-card--success` | Completed successfully |
| `.tool-card--error` | Failed |
| `.tool-card--mcp` | MCP tool type |
| `.tool-card--custom` | Custom tool type |
| `.tool-card--filesystem` | Filesystem tool |
| `.tool-card--code` | Code execution |
| `.tool-card--web` | Web search |

### Bindings
| Key | Action |
|-----|--------|
| `enter` | `toggle_expand` |
| `space` | `toggle_expand` |

---

## 4. StatusBar

### Purpose
Persistent status display at bottom of screen.

### API
```python
class StatusBar(Widget):
    """Bottom status bar showing coordination status."""

    # Reactive attributes
    phase: reactive[str]
    event_count: reactive[int]
    elapsed_seconds: reactive[int]

    def __init__(
        self,
        agent_ids: List[str],
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize status bar.

        Args:
            agent_ids: List of agent IDs for vote display.
        """

    def update_votes(self, votes: Dict[str, int]) -> None:
        """Update vote counts.

        Args:
            votes: Dict of agent_id -> vote count.
        """

    def set_phase(self, phase: str) -> None:
        """Update current coordination phase.

        Args:
            phase: One of "initial_answer", "enforcement", "presentation", "completed".
        """

    def increment_events(self) -> None:
        """Increment event counter."""

    def start_timer(self) -> None:
        """Start/reset the elapsed timer."""

    def stop_timer(self) -> None:
        """Stop the elapsed timer."""
```

### Layout
```
┌─────────────────────────────────────────────────────────────────────────┐
│ 🗳️ Votes: A(2) B(1) C(0) │ 📝 Answering │ 📊 Events: 12 │ ⏱️ 1:23     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Phase Display
| Phase | Display |
|-------|---------|
| `initial_answer` | `📝 Answering` |
| `enforcement` | `🗳️ Voting` |
| `presentation` | `🎤 Presenting` |
| `completed` | `✅ Complete` |

### CSS Classes
| Class | Description |
|-------|-------------|
| `.status-bar` | Base style |
| `.status-votes` | Vote count section |
| `.status-phase` | Phase indicator |
| `.status-events` | Event counter |
| `.status-timer` | Elapsed timer |

---

## 5. ToastNotification

### Purpose
Auto-dismissing notification popup.

### API
```python
class ToastNotification(Widget):
    """Auto-dismissing notification toast."""

    # Class constants
    DISMISS_DELAY: float = 5.0  # seconds

    def __init__(
        self,
        title: str,
        message: str,
        toast_type: str = "info",
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize toast.

        Args:
            title: Toast title/headline.
            message: Toast body message.
            toast_type: One of "vote", "answer", "complete", "error", "info".
        """

    def dismiss(self) -> None:
        """Dismiss (remove) this toast immediately."""

    def reset_timer(self) -> None:
        """Reset the auto-dismiss timer."""
```

### Toast Types
| Type | Icon | Use Case |
|------|------|----------|
| `vote` | 🗳️ | Vote cast |
| `answer` | 📝 | Answer submitted |
| `complete` | ✅ | Agent completed |
| `error` | ❌ | Error occurred |
| `info` | ℹ️ | General info |

### CSS Classes
| Class | Description |
|-------|-------------|
| `.toast` | Base style |
| `.toast--vote` | Vote toast |
| `.toast--answer` | Answer toast |
| `.toast--complete` | Completion toast |
| `.toast--error` | Error toast |
| `.toast--info` | Info toast |

---

## 6. ToastContainer

### Purpose
Container for managing multiple toast notifications.

### API
```python
class ToastContainer(Widget):
    """Container for stacking toast notifications."""

    # Class constants
    MAX_VISIBLE: int = 3

    def __init__(
        self,
        *,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """Initialize toast container."""

    def add_toast(
        self,
        title: str,
        message: str,
        toast_type: str = "info",
    ) -> ToastNotification:
        """Add a new toast notification.

        Args:
            title: Toast title.
            message: Toast message.
            toast_type: Toast type.

        Returns:
            The created ToastNotification widget.
        """

    def clear_all(self) -> None:
        """Remove all toasts immediately."""
```

### Behavior
- Toasts stack from bottom (newest at bottom)
- When > MAX_VISIBLE, oldest are queued
- Queued toasts show when others dismiss

### CSS Classes
| Class | Description |
|-------|-------------|
| `.toast-container` | Container positioning |

---

## Widget Hierarchy

```
TextualApp
├── HeaderWidget
├── AgentTabBar
│   └── AgentTab × N
├── Container (main)
│   └── AgentContentPanel
│       ├── AgentHeader
│       └── ScrollableContainer
│           ├── RichLog (text content)
│           └── ToolCallCard × N
├── Input
├── StatusBar
│   ├── VoteDisplay
│   ├── PhaseIndicator
│   ├── EventCounter
│   └── Timer
└── ToastContainer (overlay)
    └── ToastNotification × N
```

---

## Event Flow

```
OrchestrationEvent
    │
    ▼
TextualTerminalDisplay.dispatch_event()
    │
    ├─► AgentTabBar.update_agent_status()
    │
    ├─► AgentContentPanel.append_content()
    │   └─► ToolCallCard (if tool event)
    │
    ├─► StatusBar.update_votes() / set_phase()
    │
    └─► ToastContainer.add_toast()
```

---

## Accessibility

### Keyboard Navigation
All widgets must be fully keyboard navigable:
- Tab bar: Tab/Shift+Tab, number keys
- Content panel: j/k scroll, Enter to expand tools
- Tool cards: Enter/Space to toggle
- Status bar: Click on events to open modal
- Toasts: Auto-dismiss or click to dismiss

### Screen Reader Support
- Proper ARIA roles where applicable
- Descriptive labels for status badges
- Announce toast notifications

### Color Contrast
- All text meets WCAG AA contrast ratio
- Status indicators have non-color indicators (icons)
- Theme-aware styling
