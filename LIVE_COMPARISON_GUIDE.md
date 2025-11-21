# Live Design Comparison System - Complete Demo Guide

## Overview

The live comparison system provides a real-time web interface showing all 5 agent designers' work side-by-side. Instead of taking screenshots and posting to Discord, agents simply write their HTML designs to their workspace, and a Flask server automatically displays them in a 5-window grid that refreshes every 5 seconds.

**Key Features:**
- 🔄 **Auto-Discovery**: Server automatically finds the latest workspace on each request
- 🚫 **Cache-Busting**: No-cache headers ensure you always see the latest design
- 🌐 **Multi-Model Support**: Works with GPT, Claude, Gemini, Grok, and more
- 📊 **Real-Time Updates**: 5-second auto-refresh for live design evolution
- 🎯 **Zero Configuration**: Dynamic workspace detection - just start and go

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              http://localhost:5000                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Designer 1│ │Designer 2│ │Designer 3│ │Designer 4│ │Designer 5│ │
│  │  (Blue)  │ │  (Red)   │ │ (Purple) │ │ (Green)  │ │ (Orange) │ │
│  │          │ │          │ │          │ │          │ │          │ │
│  │ index.html│ │index.html│ │index.html│ │index.html│ │index.html│ │
│  │   from   │ │   from   │ │   from   │ │   from   │ │   from   │ │
│  │workspace1│ │workspace2│ │workspace3│ │workspace4│ │workspace5│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                                     │
│           Auto-refreshes every 5 seconds                           │
└─────────────────────────────────────────────────────────────────────┘
                               ▲
                               │
                               │ Reads from workspaces
                               │
┌──────────────────────────────┴────────────────────────────────────┐
│        .massgen/workspaces/designer_N_workspace_*/index.html      │
│                                                                    │
│  Designer agents write directly to their workspace index.html    │
│  No screenshots, no Discord posts, no external dependencies      │
└────────────────────────────────────────────────────────────────────┘
```

## Quick Start - Complete Demo Workflow

### Prerequisites

1. **Set API Keys** in `.env` file:
   ```bash
   # Required for all-Gemini version
   GOOGLE_API_KEY="your_gemini_key"
   
   # Required for multi-model version
   OPENAI_API_KEY="your_openai_key"
   ANTHROPIC_API_KEY="your_claude_key"
   XAI_API_KEY="your_grok_key"
   ```

2. **Install Dependencies**:
   ```bash
   pip install flask flask-cors watchdog
   ```

### Step 1: Start the Live Comparison Server

Open **Terminal 1** and run:

```bash
cd /home/zren/new_massgen/MassGen

# Kill any existing server on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Start the server
python3 massgen/configs/tools/live_comparison_server.py
```

**Expected Output:**
```
Designer 1: designer_1_workspace_1103dc89
Designer 2: designer_2_workspace_1103dc89
Designer 3: designer_3_workspace_1103dc89
Designer 4: designer_4_workspace_1103dc89
Designer 5: designer_5_workspace_1103dc89
============================================================
🎨 AI Frontend Design Collaboration Server
============================================================

📡 Server starting...
🌐 Open your browser to: http://localhost:5000

💡 The page will auto-refresh every 5 seconds
📁 Watching workspaces: /home/zren/new_massgen/MassGen/.massgen/workspaces

✨ Agents will update their designs in real-time!

Press Ctrl+C to stop the server
============================================================
 * Running on http://127.0.0.1:5000
 * Running on http://10.32.175.0:5000
```

**Key Points:**
- Server auto-discovers the **most recent** workspace for each designer
- Shows workspace IDs being used (e.g., `1103dc89`)
- Runs on port 5000 with debug mode enabled

### Step 2: Open the Comparison View

In your browser, navigate to:
```
http://localhost:5000
```

**What You'll See:**
- 5-window grid layout with color-coded headers
- Each window shows "⏳ Waiting for design to be created..." initially
- Designer names and specializations clearly labeled
- Auto-refresh countdown (updates every 5 seconds)

**Window Layout:**
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ Window #1   │ Window #2   │ Window #3   │ Window #4   │ Window #5   │
│ (Blue)      │ (Red)       │ (Purple)    │ (Green)     │ (Orange)    │
│ Minimalist  │ Bold Visual │ Storytelling│ Accessible  │ Experimental│
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### Step 3: Run MassGen with Configuration

Open **Terminal 2** and choose your configuration:

**Option A: All Gemini Agents (Recommended for Testing)**
```bash
cd /home/zren/new_massgen/MassGen

uv run python3 -m massgen.cli \
  --config massgen/configs/skills/gemini_frontend_design_collaboration_skills.yaml \
  "Design a modern landing page for a sustainable energy startup"
```

**Option B: Multi-Model (GPT, Gemini, Claude, Grok)**
```bash
cd /home/zren/new_massgen/MassGen

uv run python3 -m massgen.cli \
  --config massgen/configs/skills/multi_model_frontend_design_collaboration_skills.yaml \
  "Design a modern landing page for a sustainable energy startup"
```

**Expected MassGen Output:**
```
🤖 Multi-Agent Mode
Agents: gpt_designer_1, gemini_designer_2, claude_designer_3, grok_designer_4, gemini_designer_5
Question: Design a modern landing page for a sustainable energy startup

╔════════════════════════════════ Welcome ═══════════════════════════════╗
║ 🚀 MassGen Coordination Dashboard 🚀                                   ║
║ Multi-Agent System with 5 agents                                       ║
╚════════════════════════════════════════════════════════════════════════╝

╭─ ⏳ GPT_DESIGNER_1─╮ ╭─ ⏳ GEMINI_DESIGN─╮ ╭─ ⏳ CLAUDE_DESIGN─╮
│ Creating design... │ │ Creating design...│ │ Creating design...│
```

### Step 4: Watch the Live Design Process

As MassGen runs, **watch both terminals and your browser**:

**🔄 Round 1 - Initial Design Creation (0-5 minutes)**

**Terminal 2 (MassGen) Shows:**
```
├─ Round 1: Design Creation
│  ├─ gpt_designer_1: Writing HTML with minimalist approach...
│  ├─ gemini_designer_2: Creating bold visual design...
│  ├─ claude_designer_3: Crafting narrative flow...
│  ├─ grok_designer_4: Implementing accessible design...
│  └─ gemini_designer_5: Experimenting with layouts...
```

**Browser (http://localhost:5000) Shows:**
- Designs start appearing one by one in their windows
- Auto-refresh updates every 5 seconds
- Each design reflects the agent's specialty:
  - Window #1: Clean, spacious layout with subtle colors
  - Window #2: Vibrant hero section with bold typography
  - Window #3: Story-driven content with emotional imagery
  - Window #4: High contrast, semantic HTML, ARIA labels
  - Window #5: Unconventional grid, experimental interactions

**Terminal 1 (Server) Shows:**
```
127.0.0.1 - - [21/Nov/2025 01:30:00] "GET /design/1 HTTP/1.1" 200 -
127.0.0.1 - - [21/Nov/2025 01:30:05] "GET /design/2 HTTP/1.1" 200 -
127.0.0.1 - - [21/Nov/2025 01:30:10] "GET /design/3 HTTP/1.1" 200 -
```
- 200 status codes = designs successfully served
- Each request shows the auto-discovery working

**🔄 Round 2-5 - Iterative Refinement (5-20 minutes)**

**Terminal 2 (MassGen) Shows:**
```
├─ Round 2: Design Refinement
│  ├─ gpt_designer_1: Reading existing index.html...
│  │  └─ Refining typography spacing and color contrast
│  ├─ gemini_designer_2: Enhancing visual hierarchy...
│  │  └─ Adding scroll-triggered animations
│  └─ All agents viewing each other's work at http://localhost:5000
```

**Browser Shows:**
- Designs **evolve progressively** (not replaced)
- Subtle improvements appear with each refresh:
  - Better spacing and alignment
  - Enhanced color schemes
  - Smoother animations
  - Improved responsiveness
- Side-by-side comparison makes differences clear

**🗳️ Voting Phase (20-25 minutes)**

**Terminal 2 (MassGen) Shows:**
```
├─ Voting Phase
│  ├─ gpt_designer_1: Evaluating designs 2, 3, 4, 5...
│  │  └─ VOTE: agent3.4 (Claude's storytelling approach)
│  ├─ gemini_designer_2: Cannot vote for agent2.X...
│  │  └─ VOTE: agent4.3 (Grok's accessibility focus)
│  └─ Anti-self-voting rules enforced
```

**Browser Shows:**
- Final refined versions of all 5 designs
- You can see what each agent voted for
- All designs remain visible for comparison

### Step 5: Review Results

**Check the Winning Design:**
```bash
cd /home/zren/new_massgen/MassGen
cat .massgen/massgen_logs/log_*/turn_1/massgen.log | grep -A5 "FINAL DECISION"
```

**Explore Design Files:**
```bash
# List all workspaces created
ls -lt .massgen/workspaces/ | head -10

# View a specific design
cat .massgen/workspaces/designer_1_workspace_1103dc89/index.html

# Check file sizes
ls -lh .massgen/workspaces/designer_*_workspace_*/index.html
```

**Access Individual Designs:**
- Window #1: http://localhost:5000/design/1
- Window #2: http://localhost:5000/design/2
- Window #3: http://localhost:5000/design/3
- Window #4: http://localhost:5000/design/4
- Window #5: http://localhost:5000/design/5

**Check Server Status API:**
```bash
curl http://localhost:5000/api/status | python3 -m json.tool
```

### Step 6: Restart for New Run (Optional)

**To run another design task:**

1. **Keep server running** (Terminal 1) - it will auto-discover new workspaces
2. **Run MassGen again** (Terminal 2) with a new prompt:
   ```bash
   uv run python3 -m massgen.cli \
     --config massgen/configs/skills/gemini_frontend_design_collaboration_skills.yaml \
     "Design a landing page for an AI-powered fitness app"
   ```
3. **Hard refresh browser** (Ctrl+Shift+R) or **restart server** to see new designs:
   ```bash
   # In Terminal 1: Ctrl+C to stop, then:
   python3 massgen/configs/tools/live_comparison_server.py
   ```

**Server auto-updates workspace paths:**
```
Designer 1: designer_1_workspace_2a3b4c5d  # New workspace ID!
Designer 2: designer_2_workspace_2a3b4c5d
...
```

## Designer Window Mapping

### Configuration Options

**1. All-Gemini Version** (`gemini_frontend_design_collaboration_skills.yaml`)
| Window | Model | Designer | Color | Specialization |
|--------|-------|----------|-------|----------------|
| #1 | gemini-3-pro-preview | Minimalist Designer | Blue (#58a6ff) | Clean typography & whitespace |
| #2 | gemini-3-pro-preview | Bold Visual Designer | Red (#ff0000) | Vibrant colors & strong hierarchy |
| #3 | gemini-3-pro-preview | Storytelling Designer | Purple (#9b4dca) | Narrative flow & emotional engagement |
| #4 | gemini-3-pro-preview | Accessible Designer | Green (#2eb67d) | WCAG AA compliance & inclusivity |
| #5 | gemini-3-pro-preview | Experimental Designer | Orange (#e68a00) | Cutting-edge layouts & interactions |

**2. Multi-Model Version** (`multi_model_frontend_design_collaboration_skills.yaml`)
| Window | Model | Designer | Color | Specialization |
|--------|-------|----------|-------|----------------|
| #1 | gpt-4o-mini | Minimalist Designer | Blue (#58a6ff) | Clean typography & whitespace |
| #2 | gemini-3-pro-preview | Bold Visual Designer | Red (#ff0000) | Vibrant colors & strong hierarchy |
| #3 | claude-sonnet-4 | Storytelling Designer | Purple (#9b4dca) | Narrative flow & emotional engagement |
| #4 | grok-3-mini | Accessible Designer | Green (#2eb67d) | WCAG AA compliance & inclusivity |
| #5 | gemini-3-pro-preview | Experimental Designer | Orange (#e68a00) | Cutting-edge layouts & interactions |

**Workspace Pattern:**
- Dynamically discovered: `designer_N_workspace_<hash>`
- Example: `designer_1_workspace_1103dc89`
- Server finds **most recent** by modification time
- Changes automatically for each MassGen run

## Server Features

### Auto-Refresh
- **Frequency**: Every 5 seconds
- **What It Does**: Reloads all 5 design windows automatically
- **Why**: Ensures you always see the latest version as agents iterate

### Manual Refresh Controls
- **Individual Refresh**: Click "↻ Refresh" button on any window
- **Refresh All**: Click "Refresh All Designs" at the top
- **Use Case**: Force immediate update without waiting for auto-refresh

### Loading States
- **Waiting State**: "Waiting for design..." shown when no `index.html` exists
- **Loading Overlay**: Spinner shown when refreshing
- **Error State**: Message if file cannot be loaded

### Status API
Check which designs are ready:
```bash
curl http://localhost:5000/api/status
```

Response:
```json
{
  "designers": [
    {"id": 1, "name": "Minimalist Designer", "ready": true, "color": "#58a6ff"},
    {"id": 2, "name": "Bold Visual Designer", "ready": false, "color": "#ff0000"},
    ...
  ]
}
```

## Advantages Over Discord/Screenshot Approach

| Feature | Old (Discord) | New (Live Server) |
|---------|---------------|-------------------|
| **Setup** | Playwright, Discord bot, tokens | Just Flask server |
| **View Designs** | Check Discord channels manually | All 5 in one view |
| **Updates** | Manual screenshot + post each round | Automatic detection |
| **Comparison** | Switch between channels | Side-by-side in grid |
| **Agent Focus** | Complex bash commands | Simple file write |
| **Dependencies** | Playwright, Discord API, curl | Python, Flask |
| **Real-time** | No (must refresh Discord) | Yes (auto-refresh) |

## Agent Workflow Changes

### Before (Discord)
```python
# 1. Create design
echo '<html>...</html>' > index.html

# 2. Launch browser
playwright screenshot file://$(pwd)/index.html designer_1_design.png --full-page

# 3. Post to Discord
curl -X POST \
  -H "Authorization: Bot TOKEN" \
  -F "payload_json={...}" \
  -F "files[0]=@designer_1_design.png" \
  "https://discord.com/api/v10/channels/CHANNEL_ID/messages"
```

### After (Live Server)
```python
# 1. Create/update design
echo '<html>...</html>' > index.html

# That's it! Design appears at http://localhost:5000 automatically
```

## Troubleshooting

### Issue 1: Port 5000 Already in Use

**Error Message:**
```
Address already in use
Port 5000 is in use by another program.
```

**Solution:**
```bash
# Option 1: Force kill and restart (recommended)
lsof -ti:5000 | xargs kill -9 2>/dev/null
sleep 2
python3 massgen/configs/tools/live_comparison_server.py

# Option 2: Find and manually kill
lsof -i :5000  # Shows PID
kill -9 <PID>

# Option 3: Change port in live_comparison_server.py
# Edit the file and change: app.run(host='0.0.0.0', port=5001)
# Then update agent instructions to use http://localhost:5001
```

### Issue 2: Design Not Showing / 404 Errors

**Symptoms:**
- Browser shows "Not Found" or "Error code: 404"
- All windows show "File not found"
- Server logs show 404 status codes

**Root Cause:** Server is looking at old workspace, agents created new one

**Solution:**
```bash
# Step 1: Check which workspace has designs
ls -lt .massgen/workspaces/ | head -10

# Step 2: Restart server to auto-discover latest workspace
pkill -9 -f live_comparison_server.py
sleep 2
python3 massgen/configs/tools/live_comparison_server.py
```

**Server will show:**
```
Designer 1: designer_1_workspace_1103dc89  # Latest workspace!
Designer 2: designer_2_workspace_1103dc89
...
```

**Step 3: Hard refresh browser**
- Press `Ctrl+Shift+R` (Windows/Linux)
- Press `Cmd+Shift+R` (Mac)
- This bypasses browser cache

**Verification:**
```bash
# Check server logs for 200 status (not 404)
# Should see:
127.0.0.1 - - [date] "GET /design/1 HTTP/1.1" 200 -
127.0.0.1 - - [date] "GET /design/2 HTTP/1.1" 200 -
```

### Issue 3: Showing Old Designs (Browser Cache)

**Symptom:** Designs don't update even after agents iterate

**Solution:**
```bash
# Server already has cache-busting headers, but browser may persist cache

# Option 1: Hard refresh (best)
Ctrl+Shift+R (or Cmd+Shift+R on Mac)

# Option 2: Clear browser cache
# Chrome: Settings > Privacy > Clear browsing data > Cached images
# Firefox: Settings > Privacy > Clear Data > Cached Web Content

# Option 3: Use incognito/private mode
# Fresh session with no cache
```

### Issue 4: Server Not Starting

**Error: Missing Dependencies**
```bash
ModuleNotFoundError: No module named 'flask'
```

**Solution:**
```bash
pip install flask flask-cors watchdog

# Verify installation
python3 -c "import flask; print(flask.__version__)"
# Should print: 3.1.2 or similar
```

**Error: Python Version**
```bash
# Check Python version (requires 3.7+)
python3 --version

# If too old, use pyenv or conda to upgrade
```

### Issue 5: Designs Load Slowly / Blank Windows

**Cause:** Large HTML files or slow network

**What's Normal:**
- Initial load: 1-2 seconds per iframe
- Large files (>1MB): 3-5 seconds
- Auto-refresh: Brief flash when updating

**Solutions:**
```bash
# Check file sizes
ls -lh .massgen/workspaces/designer_*_workspace_*/index.html

# If files are huge (>5MB), agents may have embedded large images
# Consider optimizing or using external image links

# Force immediate refresh
# Click "Refresh All Designs" button at top of page
```

### Issue 6: Only Some Designs Show

**Symptom:** Windows 1-3 work, but 4-5 show "Waiting..."

**Root Cause:** Those agents haven't created index.html yet

**Check:**
```bash
# See which designers have files
for i in 1 2 3 4 5; do
  echo "=== Designer $i ==="
  latest=$(ls -td .massgen/workspaces/designer_${i}_workspace_* 2>/dev/null | head -1)
  if [ -n "$latest" ] && [ -f "$latest/index.html" ]; then
    echo "✓ Has design: $latest"
    ls -lh "$latest/index.html"
  else
    echo "✗ No design yet"
  fi
done
```

**Solution:** Wait for MassGen to continue, or check logs for errors:
```bash
tail -f .massgen/massgen_logs/log_*/turn_1/massgen.log
```

### Issue 7: MassGen Rate Limiting

**Error in MassGen logs:**
```
429 Resource has been exhausted (e.g. check quota)
```

**Cause:** Gemini API free tier limit (50 requests/minute)

**Solutions:**
```bash
# Option 1: Use multi-model config (spreads load across APIs)
# Uses: GPT-4o-mini, Claude Sonnet 4, Grok-3-mini, Gemini (x2)

# Option 2: Reduce max_new_answers_per_agent in YAML
# From: max_new_answers_per_agent: 5
# To:   max_new_answers_per_agent: 3

# Option 3: Add delays between rounds (advanced)
# Edit orchestrator settings to add coordination delays
```

### Issue 8: Anti-Self-Voting Not Working

**Symptom:** Agent logs show they voted for themselves

**Check:** Look for patterns like:
```
agent2: VOTE: agent2.3  # WRONG - voting for self
```

**Root Cause:** Agent misunderstood identity or instructions

**Solution:** Check system_message in YAML has:
```yaml
**CRITICAL VOTING RULE - YOU ARE DESIGNER #2, YOU CANNOT VOTE FOR agent2.X**
```

**Verify:** Check coordination logs:
```bash
grep -A2 "VOTE:" .massgen/massgen_logs/log_*/turn_1/coordination.json
```

## Advanced Configuration

### How Auto-Discovery Works

**Dynamic Workspace Detection:**
```python
# In live_comparison_server.py
def find_latest_workspace(designer_id):
    """Find the most recent workspace by checking modification time."""
    workspace_pattern = f"designer_{designer_id}_workspace_*"
    workspaces = list(WORKSPACE_BASE.glob(workspace_pattern))
    if not workspaces:
        return None
    # Sort by modification time, most recent first
    latest = max(workspaces, key=lambda p: p.stat().st_mtime)
    return latest.name
```

**On Each Request:**
```python
# Re-discover workspace to always get the latest
latest_workspace = find_latest_workspace(designer_id)
if latest_workspace:
    designer["workspace"] = latest_workspace
```

**Result:** No hardcoded workspace IDs - always serves the newest designs!

### Cache-Busting Implementation

```python
# In live_comparison_server.py
if html_file.exists():
    response = send_from_directory(workspace_path, "index.html")
    # Disable caching to always show the latest design
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
```

**Effect:** Browser never caches designs, always fetches fresh from server

### Customization Options

**1. Change Auto-Refresh Interval**

Edit `HTML_TEMPLATE` in `live_comparison_server.py`:
```javascript
// Change from 5000 (5 seconds) to 10000 (10 seconds)
setInterval(refreshAll, 10000);
```

**2. Change Server Port**

In `live_comparison_server.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # Use port 8080
```

Then update URLs in YAML agent instructions:
```yaml
**IMPORTANT: Your design is displayed LIVE at http://localhost:8080 window #1**
```

**3. Modify Designer Colors**

In `DESIGNERS` list:
```python
DESIGNERS = [
    {"id": 1, "name": "Minimalist Designer", "workspace": None, "color": "#00ff00"},  # Green
    {"id": 2, "name": "Bold Visual Designer", "workspace": None, "color": "#ff00ff"},  # Magenta
    # ... etc
]
```

**4. Change Grid Layout**

Edit CSS in `HTML_TEMPLATE`:
```css
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);  /* 3 columns instead of auto-fit */
    grid-gap: 20px;
}
```

**5. Add Custom Styling**

Inject custom CSS into `HTML_TEMPLATE`:
```css
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.designer-window {
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
```

## API Reference

### GET `/`
**Description**: Main comparison page with 5-window grid  
**Returns**: HTML page with embedded JavaScript  
**Example**: `curl http://localhost:5000/`

### GET `/design/<designer_id>`
**Description**: Serve specific designer's index.html  
**Parameters**: `designer_id` (1-5)  
**Returns**: HTML content from workspace  
**Example**: `curl http://localhost:5000/design/1`

### GET `/api/status`
**Description**: Check which designs are ready  
**Returns**: JSON with designer status  
**Example**: `curl http://localhost:5000/api/status | jq`

## Demo Checklist

### Before You Start
- [ ] API keys set in `.env` file
- [ ] Dependencies installed: `flask flask-cors watchdog`
- [ ] Port 5000 is free (or choose different port)
- [ ] Browser ready to open `http://localhost:5000`

### During Demo
- [ ] Terminal 1: Server running, showing workspace IDs
- [ ] Terminal 2: MassGen running, showing agent progress
- [ ] Browser: Comparison view open with 5 windows
- [ ] Designs appearing progressively (Round 1)
- [ ] Designs evolving iteratively (Rounds 2-5)
- [ ] Final voting and winner selection visible

### After Demo
- [ ] Review logs: `.massgen/massgen_logs/log_*/turn_1/massgen.log`
- [ ] Check individual designs: `http://localhost:5000/design/1` through `/design/5`
- [ ] Verify workspace files: `ls .massgen/workspaces/designer_*_workspace_*/index.html`
- [ ] Take screenshots or save designs for documentation

## Expected Timeline

**Total Duration:** ~20-30 minutes for full collaboration

| Phase | Time | Activity | What to Watch |
|-------|------|----------|---------------|
| **Setup** | 0-2 min | Start server, open browser, run MassGen | Server discovers workspaces, agents initialize |
| **Round 1** | 2-7 min | Initial design creation | Designs appear one by one, different styles emerge |
| **Round 2** | 7-12 min | First refinement | Agents read existing designs, make incremental improvements |
| **Round 3** | 12-17 min | Second refinement | Designs mature, styles solidify |
| **Round 4** | 17-22 min | Third refinement | Polishing, final touches |
| **Round 5** | 22-27 min | Final refinement | Best versions presented |
| **Voting** | 27-30 min | Evaluation & voting | Agents compare, discuss, vote (no self-voting) |
| **Results** | 30+ min | Winner announced | Check logs for final decision |

## Key Features Demonstrated

### 1. Auto-Discovery ✨
- Server automatically finds newest workspace
- No manual configuration needed
- Works across multiple MassGen runs

**Watch for:**
```
Designer 1: designer_1_workspace_1103dc89  # Latest workspace
```

### 2. Cache-Busting 🚫
- Browser never shows stale designs
- Hard refresh (Ctrl+Shift+R) optional but recommended
- Server headers prevent caching

**Check:** Designs update immediately on refresh

### 3. Multi-Model Support 🤖
- GPT-4o-mini: Efficient, balanced approach
- Claude Sonnet 4: Deep reasoning, narrative focus
- Grok-3-mini: Practical, accessible design
- Gemini: Creative, experimental styles

**Compare:** Different AI models produce distinctly different designs

### 4. Real-Time Iteration 🔄
- Designs evolve progressively
- Side-by-side comparison enables learning
- Agents reference each other's work

**Observe:** Design convergence or divergence over rounds

### 5. Anti-Self-Voting 🗳️
- Enforced in system prompts
- Agents must evaluate others
- Comprehensive criteria (not just specialty)

**Verify:** Check logs show agents voting for others, not themselves

## Success Metrics

**Successful Demo Shows:**
- ✅ All 5 designs created and visible
- ✅ Designs evolve across 5 rounds (not replaced)
- ✅ Server auto-discovers latest workspaces
- ✅ No 404 errors after server restart
- ✅ Auto-refresh updates designs every 5 seconds
- ✅ Voting phase completes without self-votes
- ✅ Winner declared with clear reasoning

## Next Steps

1. **First Run**: Start with all-Gemini config for consistency
2. **Multi-Model Run**: Try GPT+Claude+Grok mix for diversity
3. **Different Prompts**: Test with various design challenges
4. **Document Results**: Save designs, take screenshots, analyze approaches
5. **Customize**: Modify colors, layout, refresh interval to your needs

## Support & Resources

**Server Code:** `massgen/configs/tools/live_comparison_server.py`
**Configs:**
- All-Gemini: `massgen/configs/skills/gemini_frontend_design_collaboration_skills.yaml`
- Multi-Model: `massgen/configs/skills/multi_model_frontend_design_collaboration_skills.yaml`

**Logs Location:** `.massgen/massgen_logs/log_YYYYMMDD_HHMMSS_*/turn_1/`
**Designs Location:** `.massgen/workspaces/designer_N_workspace_*/index.html`

**Common Commands:**
```bash
# Restart server
lsof -ti:5000 | xargs kill -9 2>/dev/null && python3 massgen/configs/tools/live_comparison_server.py

# Check status
curl http://localhost:5000/api/status | python3 -m json.tool

# View specific design
curl http://localhost:5000/design/1 | head -50

# Find latest workspaces
ls -lt .massgen/workspaces/ | head -10
```

**Troubleshooting Quick Reference:**
- **404 errors** → Restart server (auto-discovers latest workspace)
- **Old designs** → Hard refresh browser (Ctrl+Shift+R)
- **Port in use** → `lsof -ti:5000 | xargs kill -9`
- **Slow loading** → Wait for auto-refresh or click "Refresh All"
- **Rate limits** → Use multi-model config or reduce rounds

---

**Ready to Demo?** Follow the [Quick Start](#quick-start---complete-demo-workflow) section above! 🚀
