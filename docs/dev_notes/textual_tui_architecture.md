# Textual TUI Architecture Guide

This document provides a comprehensive overview of MassGen's Textual-based Terminal User Interface (TUI) for developers working on enhancements.

## Overview

The Textual TUI (`--display textual`) provides an interactive terminal interface for MassGen orchestration. It's built on the [Textual](https://textual.textualize.io/) framework and offers a richer experience than the Rich terminal display.

**Key File**: `massgen/frontend/displays/textual_terminal_display.py`

## Architecture

### Class Hierarchy

```
TextualTerminalDisplay (TerminalDisplay)
    │
    ├── TextualApp (textual.App)          # Main Textual application
    │   ├── WelcomeScreen (Container)     # Startup screen with logo
    │   ├── HeaderWidget (Static)         # Compact status header
    │   ├── AgentTabBar (Widget)          # Tab bar for agent switching
    │   ├── AgentPanel (ScrollableContainer)  # Per-agent content panel
    │   ├── PostEvaluationPanel           # Post-eval content
    │   └── FinalStreamPanel              # Final presentation stream
    │
    └── Nested Modal Classes
        ├── PresentationModal
        ├── AgentSelectorModal
        ├── TableModal
        ├── VoteResultsModal
        ├── SystemStatusModal
        ├── OrchestratorEventsModal
        └── TextContentModal
```

### Key Components

#### TextualTerminalDisplay

The main display class that bridges MassGen's display interface with Textual.

```python
class TextualTerminalDisplay(TerminalDisplay):
    def __init__(self, agent_ids: List[str], **kwargs):
        # Key attributes:
        self.agent_ids          # List of agent IDs
        self.agent_models       # Dict[str, str] - agent_id -> model name
        self.theme              # "dark" or "light"
        self._app               # TextualApp instance
        self._buffers           # Dict[str, List] - per-agent content buffers
        self.agent_widgets      # Dict[str, AgentPanel] - panel widgets
```

**Important**: `TextualTerminalDisplay` runs in a separate thread. The Textual app runs in the main thread, while orchestration happens in a background thread.

#### TextualApp

The Textual `App` subclass that manages the UI.

```python
class TextualApp(App):
    def __init__(self, display, question, buffers, buffer_lock, buffer_flush_interval):
        self.coordination_display = display  # Reference to TextualTerminalDisplay
        self.question = question
        self._buffers = buffers
        self._buffer_lock = buffer_lock

        # UI state
        self._showing_welcome = True         # Welcome screen visible?
        self._active_agent_id = None         # Currently visible agent
        self._tab_bar = None                 # AgentTabBar widget
        self.agent_widgets = {}              # Dict[str, AgentPanel]
```

#### AgentTabBar & AgentTab

Custom widgets for agent switching (in `textual_widgets/tab_bar.py`).

```python
class AgentTab(Static):
    """Individual tab showing agent ID and status badge."""
    # Status badges: ⏳ waiting, ⚙️ working, 📝 streaming, ✅ completed, ❌ error

class AgentTabBar(Widget):
    """Horizontal bar containing all agent tabs."""
    # Methods: set_active(), update_agent_status(), get_next_agent(), get_previous_agent()
    # Emits: AgentTabChanged message on tab click
```

#### AgentPanel

Per-agent content panel with RichLog for streaming content.

```python
class AgentPanel(ScrollableContainer):
    def __init__(self, agent_id, display, index):
        self.agent_id = agent_id
        self.status = "waiting"
        self._content_log = None  # RichLog widget

    def add_content(self, content, content_type, style):
        """Add content to the RichLog."""

    def update_status(self, status):
        """Update agent status and styling."""
```

## Data Flow

### Content Streaming

```
Backend API Response
    │
    ▼
orchestrator.py (processes chunks)
    │
    ▼
TextualTerminalDisplay.update_agent_content()
    │
    ▼
_buffers[agent_id].append(content)  # Thread-safe buffering
    │
    ▼
_flush_buffers() (periodic, runs in app thread)
    │
    ▼
AgentPanel.add_content() → RichLog.write()
```

### Tab Switching

```
User presses Tab / clicks tab / presses number key
    │
    ▼
TextualApp.action_next_agent() / on_agent_tab_changed() / on_key()
    │
    ▼
_switch_to_agent(new_agent_id)
    │
    ├── Hide current AgentPanel (add_class("hidden"))
    ├── Show new AgentPanel (remove_class("hidden"))
    ├── Update AgentTabBar.set_active()
    └── Update _active_agent_id
```

### Welcome Screen → Main UI Transition

```
App starts with _showing_welcome = True
    │
    ▼
User types question in input box
    │
    ▼
on_input_submitted() → _dismiss_welcome()
    │
    ├── Hide WelcomeScreen (add_class("hidden"))
    ├── Show HeaderWidget (remove_class("hidden"))
    ├── Show AgentTabBar (remove_class("hidden"))
    └── Show main_container (remove_class("hidden"))
```

## Styling (TCSS)

Themes are in `massgen/frontend/displays/textual_themes/`:
- `dark.tcss` - Dark theme (VS Code-inspired colors)
- `light.tcss` - Light theme

### Key Style Patterns

```css
/* Widget visibility */
.hidden {
    display: none;
}

/* Status-based styling */
AgentTab.status-working { border: solid #569cd6; }
AgentTab.status-streaming { border: solid #4ec9b0; }
AgentTab.status-completed { border: solid #4ec9b0; }
AgentTab.status-error { border: solid #f44747; }

/* Active state combines with status */
AgentTab.active.status-working { background: #569cd6; }
```

### Color Palette (Dark Theme)

| Purpose | Color | Usage |
|---------|-------|-------|
| Primary | `#007ACC` | Headers, active elements, buttons |
| Success | `#4ec9b0` | Completed, streaming |
| Working | `#569cd6` | In-progress states |
| Error | `#f44747` | Error states |
| Warning | `#ce9178` | Warnings, restart banner |
| Muted | `#858585` | Inactive, hints |
| Background | `#1e1e1e` | Main background |
| Surface | `#252526` | Panels, containers |

## Key Bindings

| Key | Action | Method |
|-----|--------|--------|
| `Tab` | Next agent | `action_next_agent()` |
| `Shift+Tab` | Previous agent | `action_prev_agent()` |
| `1-9` | Jump to agent N | `on_key()` |
| `q` / `Ctrl+Q` / `Escape` | Quit | `action_quit()` |
| `s` | System status modal | `action_open_system_status()` |
| `o` | Orchestrator events | `action_open_orchestrator()` |
| `v` | Vote results | `action_open_vote_results()` |

## Threading Model

```
Main Thread (Textual App)
├── UI rendering
├── Event handling
├── Buffer flushing (_flush_buffers)
└── Widget updates

Background Thread (Orchestration)
├── API calls to backends
├── Agent coordination
├── Content generation
└── Calls display.update_agent_content() → buffers
```

**Important**: All UI updates must happen on the main thread. Use `call_from_thread()` or buffer content for periodic flushing.

## Learnings from Phase 1

### What Worked Well

1. **Reusing AgentPanel**: Instead of creating a new `AgentContentPanel`, we reused the existing `AgentPanel` and just show/hide via CSS. This preserved:
   - Scroll position per agent
   - RichLog content history
   - Streaming state

2. **CSS-based visibility**: Using `.hidden { display: none; }` is simpler than managing widget lifecycle.

3. **Agent models at creation time**: Pass `agent_models` dict when creating the display, not relying on orchestrator being initialized.

4. **Container vs Static**: `WelcomeScreen` needed to be a `Container` (not `Static`) for `align: center middle` to work properly.

### Gotchas

1. **Config structure**: Model is nested in `backend.model`, not at top level of agent config.

2. **Compose timing**: `compose()` is called before orchestrator is set, so can't access `orchestrator.agents` there.

3. **Thread safety**: Always buffer content and flush periodically rather than updating widgets directly from background threads.

4. **TCSS specificity**: Status classes need to be combined properly (e.g., `AgentTab.active.status-working`).

5. **Height in Textual**: Use `height: 1fr` for flexible containers, `height: auto` for content-sized.

## Adding New Features

### Adding a New Widget

1. Create widget class (can be in `textual_terminal_display.py` or new file in `textual_widgets/`)
2. Add to `compose()` in `TextualApp`
3. Add styles to both `dark.tcss` and `light.tcss`
4. Wire up any event handlers

### Adding a New Modal

1. Inherit from `BaseModal` (handles ESC to close)
2. Implement `compose()` with content
3. Add action method in `TextualApp` to show it
4. Add key binding if needed

### Modifying Content Display

Content flows through `AgentPanel.add_content()`. To intercept/transform:
1. Modify `add_content()` method
2. Or modify `_flush_buffers()` in `TextualApp`
3. Or add preprocessing in `update_agent_content()` in `TextualTerminalDisplay`

## File Reference

| File | Purpose |
|------|---------|
| `textual_terminal_display.py` | Main display class, TextualApp, all widgets |
| `textual_widgets/__init__.py` | Widget exports |
| `textual_widgets/tab_bar.py` | AgentTabBar, AgentTab, AgentTabChanged |
| `textual_themes/dark.tcss` | Dark theme styles |
| `textual_themes/light.tcss` | Light theme styles |
| `coordination_ui.py` | Creates display, manages coordination |
| `cli.py` | Entry point, passes agent_models to display |

## Testing

### Manual Testing Script

```bash
# Test with different agent counts
uv run massgen --display textual --config massgen/configs/basic/multi/three_agents_default.yaml "test"

# Test tab bar widget standalone
uv run python scripts/test_tab_bar.py
```

### Key Test Scenarios

1. Single agent - tab bar still shows, no navigation needed
2. Multiple agents - tab switching, background streaming
3. Welcome screen - shows on startup, dismisses on input
4. Status updates - tabs and panels update colors
5. Terminal resize - layout adapts
6. Theme switching - both dark and light work
