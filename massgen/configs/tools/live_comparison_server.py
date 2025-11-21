#!/usr/bin/env python3
"""
Live Design Comparison Server
Displays all 5 agents' designs in real-time on a single webpage with 5 windows.
Each agent updates their design by copying their index.html to a specific location.
"""

from flask import Flask, render_template_string, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
CORS(app)

# Configuration
WORKSPACE_BASE = Path(".massgen/workspaces").resolve()

def find_latest_workspace(designer_id):
    """Find the most recent workspace for a designer by checking modification time."""
    workspace_pattern = f"designer_{designer_id}_workspace_*"
    workspaces = list(WORKSPACE_BASE.glob(workspace_pattern))
    if not workspaces:
        return None
    # Sort by modification time, most recent first
    latest = max(workspaces, key=lambda p: p.stat().st_mtime)
    return latest.name

DESIGNERS = [
    {"id": 1, "name": "Minimalist Designer", "workspace": None, "color": "#58a6ff"},
    {"id": 2, "name": "Bold Visual Designer", "workspace": None, "color": "#ff0000"},
    {"id": 3, "name": "Storytelling Designer", "workspace": None, "color": "#9b4dca"},
    {"id": 4, "name": "Accessible Designer", "workspace": None, "color": "#2eb67d"},
    {"id": 5, "name": "Experimental Designer", "workspace": None, "color": "#e68a00"},
]

# Auto-discover latest workspaces
for designer in DESIGNERS:
    workspace = find_latest_workspace(designer["id"])
    designer["workspace"] = workspace
    print(f"Designer {designer['id']}: {workspace}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Frontend Design Collaboration - Live Comparison</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            color: #ffffff;
            overflow-x: hidden;
        }

        .header {
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            text-align: center;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #58a6ff, #ff0000, #9b4dca, #2eb67d, #e68a00);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1rem;
        }

        .grid-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            padding: 20px;
            max-width: 2400px;
            margin: 0 auto;
        }

        .design-window {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            overflow: hidden;
            border: 2px solid rgba(255, 255, 255, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            flex-direction: column;
            height: 600px;
        }

        .design-window:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        .window-header {
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid;
        }

        .window-title {
            font-size: 1.1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .refresh-btn {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: white;
            padding: 5px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background 0.3s;
        }

        .refresh-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .iframe-container {
            flex: 1;
            background: white;
            position: relative;
            overflow: hidden;
        }

        .design-frame {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
        }

        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 20px;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-top-color: #333;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .no-design {
            color: #666;
            font-size: 1.2rem;
        }

        .controls {
            padding: 20px;
            text-align: center;
            background: rgba(0, 0, 0, 0.2);
        }

        .refresh-all-btn {
            background: linear-gradient(135deg, #58a6ff, #2eb67d);
            border: none;
            color: white;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .refresh-all-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(88, 166, 255, 0.5);
        }

        .last-update {
            margin-top: 10px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.9rem;
        }

        @media (max-width: 1200px) {
            .grid-container {
                grid-template-columns: 1fr;
            }
            
            .design-window {
                height: 500px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 AI Frontend Design Collaboration</h1>
        <p>Live comparison of 5 AI agents designing in real-time</p>
    </div>

    <div class="grid-container">
        {% for designer in designers %}
        <div class="design-window">
            <div class="window-header" style="border-bottom-color: {{ designer.color }};">
                <div class="window-title">
                    <div class="status-indicator" style="background-color: {{ designer.color }};"></div>
                    <span>Designer #{{ designer.id }}: {{ designer.name }}</span>
                </div>
                <button class="refresh-btn" onclick="refreshFrame({{ designer.id }})">🔄 Refresh</button>
            </div>
            <div class="iframe-container">
                <iframe 
                    id="frame-{{ designer.id }}"
                    class="design-frame" 
                    src="/design/{{ designer.id }}"
                    onload="hideLoading({{ designer.id }})"
                ></iframe>
                <div id="loading-{{ designer.id }}" class="loading-overlay">
                    <div class="spinner"></div>
                    <div class="no-design">Loading design...</div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="controls">
        <button class="refresh-all-btn" onclick="refreshAll()">🔄 Refresh All Designs</button>
        <div class="last-update" id="last-update">Auto-refreshing every 5 seconds...</div>
    </div>

    <script>
        function refreshFrame(designerId) {
            const frame = document.getElementById(`frame-${designerId}`);
            const loading = document.getElementById(`loading-${designerId}`);
            loading.style.display = 'flex';
            frame.src = frame.src.split('?')[0] + '?t=' + new Date().getTime();
        }

        function hideLoading(designerId) {
            const loading = document.getElementById(`loading-${designerId}`);
            setTimeout(() => {
                loading.style.display = 'none';
            }, 500);
        }

        function refreshAll() {
            {% for designer in designers %}
            refreshFrame({{ designer.id }});
            {% endfor %}
            updateLastUpdate();
        }

        function updateLastUpdate() {
            const now = new Date();
            document.getElementById('last-update').textContent = 
                `Last update: ${now.toLocaleTimeString()}`;
        }

        // Auto-refresh every 5 seconds
        setInterval(() => {
            refreshAll();
        }, 5000);

        // Initial update message
        updateLastUpdate();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main comparison page showing all 5 designs."""
    return render_template_string(HTML_TEMPLATE, designers=DESIGNERS)


@app.route('/design/<int:designer_id>')
def get_design(designer_id):
    """Serve the design HTML for a specific designer."""
    if designer_id < 1 or designer_id > 5:
        return "<html><body><h1>Invalid Designer ID</h1></body></html>", 404
    
    designer = DESIGNERS[designer_id - 1]
    
    # Re-discover workspace on each request to always get the latest
    latest_workspace = find_latest_workspace(designer_id)
    if not latest_workspace:
        designer["workspace"] = None
    else:
        designer["workspace"] = latest_workspace
    
    # Check if workspace exists
    if not designer["workspace"]:
        return f"""
        <html>
            <body style="display: flex; align-items: center; justify-content: center; 
                        height: 100vh; margin: 0; font-family: sans-serif; 
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);">
                <div style="text-align: center;">
                    <h1 style="color: {designer['color']}; font-size: 3rem; margin-bottom: 1rem;">
                        {designer['name']}
                    </h1>
                    <p style="color: #666; font-size: 1.2rem;">
                        ⏳ No workspace found yet...
                    </p>
                    <p style="color: #999; font-size: 1rem; margin-top: 1rem;">
                        Waiting for the AI agent to create their workspace
                    </p>
                </div>
            </body>
        </html>
        """, 200
    
    workspace_path = WORKSPACE_BASE / designer["workspace"]
    html_file = workspace_path / "index.html"
    
    if html_file.exists():
        response = send_from_directory(workspace_path, "index.html")
        # Disable caching to always show the latest design
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    else:
        return f"""
        <html>
            <body style="display: flex; align-items: center; justify-content: center; 
                        height: 100vh; margin: 0; font-family: sans-serif; 
                        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);">
                <div style="text-align: center;">
                    <h1 style="color: {designer['color']}; font-size: 3rem; margin-bottom: 1rem;">
                        {designer['name']}
                    </h1>
                    <p style="color: #666; font-size: 1.2rem;">
                        ⏳ Waiting for design to be created...
                    </p>
                    <p style="color: #999; font-size: 1rem; margin-top: 1rem;">
                        The AI agent is working on this design
                    </p>
                </div>
            </body>
        </html>
        """, 200


@app.route('/api/status')
def get_status():
    """API endpoint to check which designs are ready."""
    status = {}
    for designer in DESIGNERS:
        if not designer["workspace"]:
            status[f"designer_{designer['id']}"] = {
                "ready": False,
                "path": "No workspace found",
                "workspace": None
            }
            continue
        
        workspace_path = WORKSPACE_BASE / designer["workspace"]
        html_file = workspace_path / "index.html"
        status[f"designer_{designer['id']}"] = {
            "ready": html_file.exists(),
            "path": str(html_file),
            "last_modified": html_file.stat().st_mtime if html_file.exists() else None
        }
    return status


if __name__ == '__main__':
    print("=" * 60)
    print("🎨 AI Frontend Design Collaboration Server")
    print("=" * 60)
    print("\n📡 Server starting...")
    print(f"🌐 Open your browser to: http://localhost:5000")
    print("\n💡 The page will auto-refresh every 5 seconds")
    print("📁 Watching workspaces:", WORKSPACE_BASE.absolute())
    print("\n✨ Agents will update their designs in real-time!")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
