# MassGen v0.1.42 Release Announcement

<!--
This is the current release announcement. Copy this + feature-highlights.md to LinkedIn/X.
After posting, update the social links below.
-->

## Release Summary

We're excited to release MassGen v0.1.42, featuring Human Input Queue - inject messages to agents mid-stream while they're working! 🚀 This release also includes a comprehensive TUI Visual Redesign with a modern "Conversational AI" aesthetic - rounded corners, professional color palette, edge-to-edge layouts, and polished modals.

## Install

```bash
pip install massgen==0.1.42
```

## Links

- **Release notes:** https://github.com/massgen/MassGen/releases/tag/v0.1.42
- **X post:** [TO BE ADDED AFTER POSTING]
- **LinkedIn post:** [TO BE ADDED AFTER POSTING]

---

## Full Announcement (for LinkedIn)

Copy everything below this line, then append content from `feature-highlights.md`:

---

We're excited to release MassGen v0.1.42, featuring Human Input Queue!

**Human Input Queue**
- Inject messages to agents mid-stream while they work
- Thread-safe queue with per-agent tracking
- Visual indicators in TUI when input is pending

**TUI Visual Redesign**
The Textual terminal UI has been completely refreshed with a modern "Conversational AI" aesthetic:
- Rounded corners and softer borders throughout
- Professional desaturated color palette
- Edge-to-edge layouts with proper spacing
- Redesigned agent tabs, tool cards, and modals
- Scroll indicators and progress bars

**AG2 Single-Agent Fix**
- Fixed coordination issues for single-agent AG2 setups
- Proper vote handling when only one agent present

Try the new TUI: `massgen --display textual "your question"`

Release notes: https://github.com/massgen/MassGen/releases/tag/v0.1.42

<!-- Paste feature-highlights.md content here -->

---

## GitHub Release Highlights

# 🚀 Release Highlights — v0.1.42 (2026-01-23)

### 💬 [Human Input Queue](https://docs.massgen.ai/en/latest/user_guide/advanced/index.html)
- **Mid-Stream Injection**: Send messages to agents while they're working via new `HumanInputHook`
- **Thread-Safe Queue**: Per-agent tracking ensures each message is delivered once per agent, with visual indicators in TUI when input is pending

### 🎨 [TUI Visual Redesign](https://docs.massgen.ai/en/latest/quickstart/running-massgen.html#textual-tui)
- **Modern Aesthetic**: "Conversational AI" design with rounded corners, professional desaturated color palette, and edge-to-edge layouts
- **Redesigned Components**: Agent tabs with dot indicators (◉/○/✓), polished modals, adaptive tool cards, and scroll indicators

### 🔧 [AG2 Single-Agent Fix](https://docs.massgen.ai/en/latest/user_guide/integration/index.html)
- **Coordination Fix**: Single-agent AG2 setups now vote and coordinate correctly; properly clears `restart_pending` flag

---

### 📖 Getting Started
- [**Quick Start Guide**](https://github.com/massgen/MassGen?tab=readme-ov-file#1--installation): Try the new features today
- **Try These Examples**:
  - [three_agents_default.yaml](https://github.com/massgen/MassGen/blob/main/massgen/configs/basic/multi/three_agents_default.yaml) - Experience the redesigned TUI with multi-agent coordination

```bash
# Experience the redesigned TUI with interactive mode
uv run massgen --display textual \
  --config massgen/configs/basic/multi/three_agents_default.yaml \
  "Compare the pros and cons of React vs Vue for building a dashboard"
```
