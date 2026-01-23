# TUI Redesign Phase 6 Handoff: Modals + Enhanced Previews

## Previous Phases Summary

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Input Bar + Mode Toggles | ✓ Complete |
| Phase 2 | Agent Tabs | ✓ Complete |
| Phase 3 | Tool Cards & Timeline | ✓ Complete |
| Phase 4 | Welcome Screen | ✓ Complete |
| Phase 5 | Task Lists + Progress | ✓ Complete |
| **Phase 6** | **Modals + Enhanced Previews** | **Next** |

## Phase 6 Tasks (from openspec)

Reference: `openspec/changes/update-tui-conversational-design/tasks.md`

### 6.1 Modal Visual Redesign
- [ ] 6.1.1 Update all modal containers to use rounded borders
- [ ] 6.1.2 Remove emoji from modal titles
- [ ] 6.1.3 Use bullet separators in modal headers
- [ ] 6.1.4 Soften border colors across all modals
- [ ] 6.1.5 Improve internal padding and margins
- [ ] 6.1.6 Unify button styling across modals
- [ ] 6.1.7 Polish close button with softer hover states

### 6.2 Diff View for File Edits
- [ ] 6.2.1 Create `DiffView` widget for displaying file changes
- [ ] 6.2.2 Implement colored diff rendering (green +, red -)
- [ ] 6.2.3 Add line numbers to diff display
- [ ] 6.2.4 Show context lines around changes
- [ ] 6.2.5 Add "+X -Y lines" summary header
- [ ] 6.2.6 Integrate diff view into tool result display for write_file/edit operations

### 6.3 Workspace Modal Improvements
- [ ] 6.3.1 Implement tree view for directory structure (replace flat list)
- [ ] 6.3.2 Add collapsible directory nodes
- [ ] 6.3.3 Show file statistics (number of files, +X -Y lines)
- [ ] 6.3.4 Add simple text-based file/folder icons
- [ ] 6.3.5 Show summary line (agents, turns, consensus status)

### 6.4 Better Tool Result Previews
- [ ] 6.4.1 Create formatted preview renderer for common result types
- [ ] 6.4.2 Replace raw dict display with readable formatting
- [ ] 6.4.3 Implement smart truncation with "show more" expansion
- [ ] 6.4.4 Add basic syntax highlighting for code in results
- [ ] **6.4.5 CHECKPOINT: User approval for modals + enhanced previews**

## Files to Modify

### Existing Modal Files
1. **`massgen/frontend/displays/textual_widgets/task_plan_modal.py`** - Task modal
2. **`massgen/frontend/displays/textual_widgets/tool_detail_modal.py`** - Tool detail modal
3. **`massgen/frontend/displays/textual_widgets/background_tasks_modal.py`** - Background tasks
4. **`massgen/frontend/displays/textual_widgets/plan_approval_modal.py`** - Plan approval
5. **`massgen/frontend/displays/textual_widgets/subagent_modal.py`** - Subagent modal

### New Files to Create
1. **`massgen/frontend/displays/textual_widgets/diff_view.py`** - New diff viewer widget
2. **`massgen/frontend/displays/textual_widgets/workspace_modal.py`** - If doesn't exist

### Theme Files
1. **`massgen/frontend/displays/textual_themes/dark.tcss`** - Dark theme
2. **`massgen/frontend/displays/textual_themes/light.tcss`** - Light theme

## Current Modal Styles

Looking at `task_plan_modal.py` as reference for current style:
- Border: `thick #a371f7`
- Background: `$surface`
- Header: styled with modal-specific colors
- Close button: `Button("✕", ...)`

## Suggested Implementation Order

### Step 1: Modal Visual Consistency (6.1)
Start by auditing all modal files and creating consistent patterns:
- Define standard border radius/style
- Remove emoji from titles (e.g., `📋 Task Plan` → `Task Plan`)
- Standardize button styling
- Create reusable modal CSS classes

### Step 2: Diff View Widget (6.2)
Create new `diff_view.py`:
```python
class DiffView(Static):
    """Widget for displaying file diffs with syntax highlighting."""

    def __init__(self, old_content: str, new_content: str, filename: str):
        ...

    def render(self) -> Text:
        # Show: +X -Y lines header
        # Colored diff: green for additions, red for deletions
        # Line numbers
        ...
```

### Step 3: Workspace Modal (6.3)
Implement tree view with collapsible nodes:
```
📁 src/
  ├─ 📄 main.py (+45 -12)
  ├─ 📁 utils/
  │   └─ 📄 helpers.py (+8 -2)
  └─ 📄 config.py (new)
```

### Step 4: Tool Result Previews (6.4)
Create smart formatters for common result types:
- JSON → formatted with syntax highlighting
- File paths → clickable/highlighted
- Errors → red with stack trace formatting
- Success messages → green checkmarks

## Design Guidelines

From previous phases:
- Use softer, less saturated colors
- Prefer text symbols over emoji
- Keep borders thin (`solid` not `thick`)
- Consistent spacing and padding
- Support both dark and light themes

## Testing

```bash
# Test with tool-heavy config
uv run massgen --display textual --config massgen/configs/tools/mcp/filesystem_demo.yaml "List files in the current directory and show their contents"

# Verify:
# - Modal styling is consistent
# - Tool results are formatted nicely
# - Diff view works for file edits
# - Ctrl+W opens workspace modal (if implemented)
```

## Phase 5 Context (Just Completed)

Key changes from Phase 5:
- Task card shows inline progress bar: `▸ Tasks (3/5)  ━━━━━━──────────`
- Click on task card opens modal (same as Ctrl+T)
- Removed redundant "Tasks: X/Y" badge from header
- Changed "← active" to "← current" for consistency
- Progress bar uses `━` for completed, `─` for remaining

## Approval Workflow

After completing Phase 6:
1. User tests modals across different scenarios
2. User approves or requests changes
3. Iterate if needed
4. Proceed to Phase 7: Header + Final Polish
