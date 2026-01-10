---
name: textual-ui-developer
description: Develop and improve the MassGen Textual TUI by running it in a browser via textual-serve and using Claude's browser tool for visual feedback.
---

# Textual UI Developer

This skill provides a workflow for developing and improving the MassGen Textual TUI with visual feedback.

## Purpose

Use this skill when you need to:
- Debug or improve the Textual TUI display
- Add new widgets or features to the TUI
- Fix styling or layout issues
- Test the TUI visually in a browser

## Setup

### Step 1: Install textual-serve

```bash
uv pip install textual-serve
```

### Step 2: Start Claude with Browser Access

In one terminal, start Claude Code with Chrome integration:

```bash
claude --chrome
```

### Step 3: Start the Textual TUI Server

In another terminal (or have Claude run it in background):

```bash
uv run massgen --textual-serve
```

Or with a specific config:

```bash
uv run massgen --textual-serve --config massgen/configs/basic/three_haiku_agents.yaml
```

Or on a different port:

```bash
uv run massgen --textual-serve --textual-serve-port 9000
```

## Workflow

### Visual Development Loop

1. **Start the server** in background:
   ```bash
   uv run massgen --textual-serve &
   ```

2. **Open in browser** and take screenshots:
   - Navigate to `http://localhost:8000`
   - Use Claude's browser tool to capture the current state

3. **Make changes** to the Textual code:
   - Widget files: `massgen/frontend/displays/textual_widgets/`
   - Main display: `massgen/frontend/displays/textual_terminal_display.py`
   - Themes: `massgen/frontend/displays/textual_themes/`

4. **Refresh and verify**:
   - The textual-serve auto-reloads on new connections
   - Open a new browser tab to see changes
   - Take another screenshot to compare

### Key Files

| File | Description |
|------|-------------|
| `massgen/frontend/displays/textual_terminal_display.py` | Main Textual app and display logic |
| `massgen/frontend/displays/textual_widgets/` | Custom widgets (tab bar, tool cards, etc.) |
| `massgen/frontend/displays/textual_themes/dark.tcss` | Dark theme CSS |
| `massgen/frontend/displays/textual_themes/light.tcss` | Light theme CSS |

### Commands Reference

```bash
# Start TUI server (default port 8000)
uv run massgen --textual-serve

# Start with specific config
uv run massgen --textual-serve --config path/to/config.yaml

# Start on different port
uv run massgen --textual-serve --textual-serve-port 9000

# Run TUI directly in terminal (no browser)
uv run massgen --display textual
```

## Tips

1. **Hot reload**: textual-serve spawns a new app instance per browser connection, so opening a new tab shows the latest code changes.

2. **Use --interactive**: Add `--interactive` flag to enable the input prompt for testing user interaction.

3. **Check the console**: The terminal running textual-serve shows any Python errors or exceptions.

4. **Browser DevTools**: Use browser dev tools to inspect the DOM-like structure that textual-serve renders.

5. **Multiple tabs**: Open multiple browser tabs to see how the UI handles concurrent sessions.

## Textual Resources

- **Textual Docs**: https://textual.textualize.io/
- **Widget Gallery**: https://textual.textualize.io/widget_gallery/
- **CSS Reference**: https://textual.textualize.io/css_types/
- **textual-serve Repo**: https://github.com/Textualize/textual-serve
