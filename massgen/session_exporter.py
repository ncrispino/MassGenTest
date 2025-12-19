# -*- coding: utf-8 -*-
"""Session export functionality for MassGen runs.

Generates self-contained HTML files for sharing MassGen sessions.
"""

import html
import json
import platform
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console

from .logs_analyzer import get_logs_dir


class SessionExporter:
    """Export MassGen sessions to shareable HTML."""

    def __init__(self, log_dir: Path):
        """Initialize exporter with a log directory.

        Args:
            log_dir: Path to the log attempt directory (e.g., log_XXX/turn_1/attempt_1)
        """
        self.log_dir = log_dir
        self.data: Dict[str, Any] = {}

    def load_session_data(self) -> Dict[str, Any]:
        """Load all relevant data from log directory.

        Returns:
            Consolidated session data dictionary
        """
        data: Dict[str, Any] = {
            "export_version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "massgen_version": self._get_massgen_version(),
        }

        # Load metrics_summary.json
        metrics_path = self.log_dir / "metrics_summary.json"
        if metrics_path.exists():
            metrics = json.loads(metrics_path.read_text())
            data["metrics"] = metrics
        else:
            data["metrics"] = {}

        # Load status.json
        status_path = self.log_dir / "status.json"
        if status_path.exists():
            status = json.loads(status_path.read_text())
            data["status"] = status
        else:
            data["status"] = {}

        # Load coordination_events.json
        events_path = self.log_dir / "coordination_events.json"
        if events_path.exists():
            events = json.loads(events_path.read_text())
            data["coordination"] = events
        else:
            data["coordination"] = {"events": [], "session_metadata": {}}

        # Load execution_metadata.yaml (from parent turn directory or log root)
        metadata_path = self._find_execution_metadata()
        if metadata_path and metadata_path.exists():
            with open(metadata_path) as f:
                execution_meta = yaml.safe_load(f)
            data["execution_metadata"] = self.sanitize_config(execution_meta or {})
        else:
            data["execution_metadata"] = {}

        # Load turn metadata
        turn_metadata_path = self.log_dir.parent / "metadata.json"
        if turn_metadata_path.exists():
            data["turn_metadata"] = json.loads(turn_metadata_path.read_text())
        else:
            data["turn_metadata"] = {}

        # Load final answer
        answer_path = self.log_dir.parent / "answer.txt"
        if answer_path.exists():
            data["final_answer"] = answer_path.read_text()
        else:
            data["final_answer"] = ""

        # Load agent outputs
        agent_outputs_dir = self.log_dir / "agent_outputs"
        data["agent_outputs"] = {}
        if agent_outputs_dir.exists():
            for output_file in agent_outputs_dir.glob("*.txt"):
                if output_file.name != "system_status.txt":
                    agent_id = output_file.stem
                    # Truncate very large output files to avoid huge HTML
                    content = output_file.read_text()
                    if len(content) > 100000:  # 100KB limit per agent
                        content = content[:100000] + "\n\n... [truncated - file too large] ..."
                    data["agent_outputs"][agent_id] = content

        # Load snapshot mappings and actual answer/vote content
        snapshot_mappings_path = self.log_dir / "snapshot_mappings.json"
        data["snapshot_mappings"] = {}
        data["answers"] = {}
        data["votes"] = {}
        if snapshot_mappings_path.exists():
            snapshot_mappings = json.loads(snapshot_mappings_path.read_text())
            data["snapshot_mappings"] = snapshot_mappings

            # Load actual answer/vote content from the mapped paths
            for label, mapping in snapshot_mappings.items():
                mapping_type = mapping.get("type", "")
                path = mapping.get("path", "")

                if path:
                    full_path = self.log_dir / path
                    if full_path.exists():
                        if mapping_type in ("answer", "final_answer"):
                            content = full_path.read_text()
                            if len(content) > 50000:  # Truncate long answers
                                content = content[:50000] + "\n\n... [truncated] ..."
                            data["answers"][label] = {
                                "label": label,
                                "agent_id": mapping.get("agent_id"),
                                "content": content,
                                "type": mapping_type,
                                "iteration": mapping.get("iteration"),
                                "round": mapping.get("round"),
                            }
                        elif mapping_type == "vote":
                            try:
                                vote_data = json.loads(full_path.read_text())
                                data["votes"][label] = {
                                    "label": label,
                                    "agent_id": mapping.get("agent_id"),
                                    "voted_for": mapping.get("voted_for"),
                                    "voted_for_label": mapping.get("voted_for_label"),
                                    "reason": vote_data.get("reason", ""),
                                    "iteration": mapping.get("iteration"),
                                    "round": mapping.get("round"),
                                }
                            except (json.JSONDecodeError, KeyError):
                                pass

        # Build session summary
        data["session"] = self._build_session_summary(data)

        self.data = data
        return data

    def _get_massgen_version(self) -> str:
        """Get MassGen version."""
        try:
            from . import __version__

            return __version__
        except ImportError:
            return "unknown"

    def _find_execution_metadata(self) -> Optional[Path]:
        """Find execution_metadata.yaml in the log hierarchy."""
        # Check in attempt directory
        path = self.log_dir / "execution_metadata.yaml"
        if path.exists():
            return path

        # Check in turn directory
        path = self.log_dir.parent / "execution_metadata.yaml"
        if path.exists():
            return path

        # Check in log root
        path = self.log_dir.parent.parent / "execution_metadata.yaml"
        if path.exists():
            return path

        return None

    def _build_session_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a summary section from loaded data."""
        metrics = data.get("metrics", {})
        status = data.get("status", {})
        coordination = data.get("coordination", {})
        meta = metrics.get("meta", {})
        status_meta = status.get("meta", {})

        # Get question from multiple sources
        question = meta.get("question") or status_meta.get("question") or coordination.get("session_metadata", {}).get("user_prompt") or "Unknown"

        # Get winner
        winner = meta.get("winner") or status.get("results", {}).get("winner") or coordination.get("session_metadata", {}).get("final_winner")

        # Get timestamps
        start_time = status_meta.get("start_time") or coordination.get("session_metadata", {}).get("start_time")
        end_time = coordination.get("session_metadata", {}).get("end_time")

        duration_seconds = None
        if start_time and end_time:
            duration_seconds = end_time - start_time
        elif status_meta.get("elapsed_seconds"):
            duration_seconds = status_meta.get("elapsed_seconds")

        # Get costs
        totals = metrics.get("totals", {})
        cost = totals.get("estimated_cost", 0)
        input_tokens = totals.get("input_tokens", 0)
        output_tokens = totals.get("output_tokens", 0)
        reasoning_tokens = totals.get("reasoning_tokens", 0)

        # Get agent info
        agents = metrics.get("agents", {})
        num_agents = meta.get("num_agents", len(agents))

        # Get tool info
        tools = metrics.get("tools", {})
        total_tool_calls = tools.get("total_calls", 0)
        total_tool_failures = tools.get("total_failures", 0)

        # Get rounds info
        rounds = metrics.get("rounds", {})
        total_rounds = rounds.get("total_rounds", 0)

        # Get log directory name
        log_name = self.log_dir.parent.parent.name if self.log_dir.parent.parent else "unknown"

        return {
            "question": question,
            "winner": winner,
            "start_time": start_time,
            "duration_seconds": duration_seconds,
            "log_directory": log_name,
            "cost": cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "num_agents": num_agents,
            "total_tool_calls": total_tool_calls,
            "total_tool_failures": total_tool_failures,
            "total_rounds": total_rounds,
        }

    def sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Remove API keys and sensitive data from config.

        Args:
            config: Configuration dictionary to sanitize

        Returns:
            Sanitized configuration dictionary
        """
        if not config:
            return config

        # Patterns for sensitive keys
        sensitive_patterns = [
            r"api_key",
            r"api-key",
            r"apikey",
            r"secret",
            r"password",
            r"credential",
            r"token",
            r"auth",
            r"private_key",
            r"private-key",
        ]
        pattern = re.compile("|".join(sensitive_patterns), re.IGNORECASE)

        def sanitize_value(key: str, value: Any) -> Any:
            if pattern.search(key):
                return "[REDACTED]"

            if isinstance(value, dict):
                return {k: sanitize_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(str(i), item) for i, item in enumerate(value)]
            elif isinstance(value, str):
                # Check if it looks like an API key or secret
                if re.match(r"^(sk-|key-|secret-|Bearer\s)", value):
                    return "[REDACTED]"
                # Remove home directory paths
                if "/Users/" in value or "/home/" in value:
                    value = re.sub(r"/Users/[^/]+/", "/~/", value)
                    value = re.sub(r"/home/[^/]+/", "/~/", value)
                return value
            return value

        return {k: sanitize_value(k, v) for k, v in config.items()}

    def generate_html(self, output_path: Path) -> None:
        """Generate self-contained HTML file.

        Args:
            output_path: Where to write the HTML file
        """
        if not self.data:
            self.load_session_data()

        html_content = self._render_html()
        output_path.write_text(html_content, encoding="utf-8")

    def _render_html(self) -> str:
        """Render complete HTML with embedded data and styling."""
        session = self.data.get("session", {})
        metrics = self.data.get("metrics", {})
        status = self.data.get("status", {})
        coordination = self.data.get("coordination", {})
        agent_outputs = self.data.get("agent_outputs", {})
        final_answer = self.data.get("final_answer", "")
        execution_metadata = self.data.get("execution_metadata", {})

        # Format values
        question = html.escape(session.get("question", "Unknown"))
        question_preview = question[:50] + "..." if len(question) > 50 else question
        winner = session.get("winner", "N/A")
        cost = session.get("cost", 0)
        duration = session.get("duration_seconds", 0)
        duration_str = self._format_duration(duration) if duration else "N/A"
        input_tokens = session.get("input_tokens", 0)
        output_tokens = session.get("output_tokens", 0)
        reasoning_tokens = session.get("reasoning_tokens", 0)
        total_tokens = input_tokens + output_tokens + reasoning_tokens
        total_tool_calls = session.get("total_tool_calls", 0)
        total_rounds = session.get("total_rounds", 0)
        num_agents = session.get("num_agents", 0)
        log_dir = session.get("log_directory", "")

        # Parse timestamp from log directory name
        timestamp_str = self._parse_timestamp_from_log_dir(log_dir)

        # Build agents HTML
        agents_html = self._build_agents_html(metrics, status)

        # Build tools HTML
        tools_html = self._build_tools_html(metrics)

        # Build timeline HTML
        timeline_html = self._build_timeline_html(coordination)

        # Build answers and votes HTML
        answers_votes_html = self._build_answers_votes_html(coordination, status)

        # Build agent outputs HTML
        agent_outputs_html = self._build_agent_outputs_html(agent_outputs)

        # Build config HTML
        config_html = self._build_config_html(execution_metadata)

        # Escape final answer for HTML
        final_answer_escaped = html.escape(final_answer)

        # Embed full data as JSON
        embedded_data = json.dumps(self.data, default=str)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MassGen Session: {question_preview}</title>
    <style>
        :root {{
            --bg-primary: #1a1b26;
            --bg-secondary: #24283b;
            --bg-tertiary: #292e42;
            --text-primary: #c0caf5;
            --text-secondary: #9aa5ce;
            --text-muted: #565f89;
            --accent-cyan: #7dcfff;
            --accent-green: #9ece6a;
            --accent-yellow: #e0af68;
            --accent-red: #f7768e;
            --accent-purple: #bb9af7;
            --border-color: #3b4261;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{ max-width: 1200px; margin: 0 auto; }}

        .session-header {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid var(--border-color);
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            color: var(--accent-cyan);
            font-weight: 600;
        }}

        .question-text {{
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 1rem;
            word-wrap: break-word;
        }}

        .meta-row {{
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            font-size: 0.9rem;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .meta-label {{ color: var(--text-muted); }}
        .meta-value {{ color: var(--accent-cyan); font-weight: 500; }}
        .winner-badge {{
            background: var(--accent-green);
            color: var(--bg-primary);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-weight: 600;
            font-size: 0.8rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1.25rem;
            border: 1px solid var(--border-color);
            text-align: center;
        }}

        .stat-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }}

        .stat-label {{
            color: var(--text-muted);
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }}

        .section {{
            margin-bottom: 2rem;
        }}

        .section-title {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .agent-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
        }}

        .agent-card {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1.25rem;
            border: 1px solid var(--border-color);
        }}

        .agent-card.winner {{
            border-color: var(--accent-green);
            box-shadow: 0 0 0 1px var(--accent-green);
        }}

        .agent-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}

        .agent-id {{
            font-weight: 600;
            font-size: 1rem;
        }}

        .agent-model {{
            color: var(--text-muted);
            font-size: 0.8rem;
        }}

        .agent-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
            font-size: 0.85rem;
        }}

        .agent-stat {{
            display: flex;
            justify-content: space-between;
        }}

        .agent-stat-label {{ color: var(--text-muted); }}
        .agent-stat-value {{ color: var(--text-secondary); }}

        .tools-list {{ }}

        .tool-bar {{
            display: flex;
            align-items: center;
            margin-bottom: 0.75rem;
            font-size: 0.85rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .tool-name {{
            min-width: 280px;
            max-width: 400px;
            color: var(--text-secondary);
            word-break: break-all;
            flex-shrink: 0;
            font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
            font-size: 0.8rem;
        }}

        .tool-bar-container {{
            flex: 1;
            min-width: 150px;
            height: 20px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
        }}

        .tool-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
            border-radius: 4px;
            transition: width 0.3s ease;
        }}

        .tool-stats {{
            min-width: 120px;
            text-align: right;
            color: var(--text-muted);
            flex-shrink: 0;
        }}

        /* Answers & Votes Section */
        .answers-section {{
            margin-bottom: 2rem;
        }}

        .answer-tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}

        .answer-tab {{
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            cursor: pointer;
            color: var(--text-secondary);
            font-size: 0.85rem;
            transition: all 0.2s;
        }}

        .answer-tab:hover {{
            background: var(--bg-tertiary);
        }}

        .answer-tab.active {{
            background: var(--accent-cyan);
            color: var(--bg-primary);
            border-color: var(--accent-cyan);
        }}

        .answer-tab.winner-tab {{
            border-color: var(--accent-green);
        }}

        .answer-tab.winner-tab.active {{
            background: var(--accent-green);
        }}

        .answer-content {{
            display: none;
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
        }}

        .answer-content.active {{
            display: block;
        }}

        .answer-meta {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            flex-wrap: wrap;
        }}

        .answer-meta-item {{
            color: var(--text-muted);
        }}

        .answer-meta-item span {{
            color: var(--text-secondary);
        }}

        .answer-text {{
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1.25rem;
            white-space: pre-wrap;
            font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
            font-size: 0.85rem;
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: 1rem;
        }}

        .vote-info {{
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1rem;
            border-left: 3px solid var(--accent-purple);
        }}

        .vote-info-header {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--accent-purple);
        }}

        .vote-reason {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-style: italic;
        }}

        .no-answer {{
            color: var(--text-muted);
            font-style: italic;
            padding: 2rem;
            text-align: center;
        }}

        .timeline {{
            position: relative;
            padding-left: 1.5rem;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 0.4rem;
            top: 0;
            bottom: 0;
            width: 2px;
            background: var(--border-color);
        }}

        .timeline-event {{
            position: relative;
            padding: 0.75rem 1rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            border: 1px solid var(--border-color);
        }}

        .timeline-event::before {{
            content: '';
            position: absolute;
            left: -1.4rem;
            top: 1rem;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-cyan);
        }}

        .timeline-event.answer::before {{ background: var(--accent-green); }}
        .timeline-event.vote::before {{ background: var(--accent-purple); }}
        .timeline-event.restart::before {{ background: var(--accent-yellow); }}
        .timeline-event.error::before {{ background: var(--accent-red); }}
        .timeline-event.final::before {{ background: var(--accent-green); }}

        .event-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 0.25rem;
        }}

        .event-type {{
            font-weight: 600;
            font-size: 0.9rem;
        }}

        .event-time {{
            color: var(--text-muted);
            font-size: 0.8rem;
        }}

        .event-details {{
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}

        .event-agent {{ color: var(--accent-cyan); }}

        .final-answer-section {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 2px solid var(--accent-green);
        }}

        .final-answer-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .final-answer-content {{
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1.25rem;
            white-space: pre-wrap;
            font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
            font-size: 0.85rem;
            max-height: 500px;
            overflow-y: auto;
        }}

        .collapsible {{
            background: var(--bg-secondary);
            border-radius: 8px;
            margin-bottom: 0.75rem;
            border: 1px solid var(--border-color);
            overflow: hidden;
        }}

        .collapsible-header {{
            padding: 1rem 1.25rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }}

        .collapsible-header:hover {{ background: var(--bg-tertiary); }}

        .collapsible-content {{
            display: none;
            padding: 1.25rem;
            border-top: 1px solid var(--border-color);
        }}

        .collapsible.open .collapsible-content {{ display: block; }}

        .collapsible-icon {{
            transition: transform 0.2s;
            color: var(--text-muted);
        }}

        .collapsible.open .collapsible-icon {{ transform: rotate(180deg); }}

        .agent-log {{
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1rem;
            font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
            font-size: 0.75rem;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
            word-break: break-word;
        }}

        .config-block {{
            background: var(--bg-tertiary);
            border-radius: 8px;
            padding: 1rem;
            font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
            font-size: 0.8rem;
            white-space: pre-wrap;
            overflow-x: auto;
        }}

        .export-footer {{
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border-color);
            margin-top: 2rem;
        }}

        .export-footer a {{
            color: var(--accent-cyan);
            text-decoration: none;
        }}

        .export-footer a:hover {{
            text-decoration: underline;
        }}

        .copy-btn {{
            background: var(--accent-cyan);
            color: var(--bg-primary);
            border: none;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.8rem;
        }}

        .copy-btn:hover {{ opacity: 0.9; }}
        .copy-btn.copied {{ background: var(--accent-green); }}

        .no-data {{
            color: var(--text-muted);
            font-style: italic;
            padding: 1rem;
            text-align: center;
        }}

        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            .meta-row {{ flex-direction: column; gap: 0.5rem; }}
            .tool-name {{ width: 120px; }}
            .tool-stats {{ width: 80px; }}
            .agent-stats {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="session-header">
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M8 12h8M12 8v8"/>
                </svg>
                MassGen Session Export
            </div>
            <div class="question-text">{question}</div>
            <div class="meta-row">
                <div class="meta-item">
                    <span class="meta-label">Date:</span>
                    <span class="meta-value">{timestamp_str}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Duration:</span>
                    <span class="meta-value">{duration_str}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Cost:</span>
                    <span class="meta-value">${cost:.4f}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Winner:</span>
                    <span class="winner-badge">{winner if winner else 'N/A'}</span>
                </div>
            </div>
        </header>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${cost:.2f}</div>
                <div class="stat-label">Estimated Cost</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_tokens:,}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_tool_calls}</div>
                <div class="stat-label">Tool Calls</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_rounds}</div>
                <div class="stat-label">Rounds</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{num_agents}</div>
                <div class="stat-label">Agents</div>
            </div>
        </div>

        <section class="section">
            <h2 class="section-title">Agents</h2>
            <div class="agent-grid">
                {agents_html}
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Tools Used</h2>
            <div class="tools-list">
                {tools_html}
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Coordination Timeline</h2>
            <div class="timeline">
                {timeline_html}
            </div>
        </section>

        <section class="section">
            <h2 class="section-title">Answers & Votes</h2>
            {answers_votes_html}
        </section>

        <section class="final-answer-section">
            <div class="final-answer-header">
                <h2 class="section-title" style="margin-bottom: 0;">Final Answer</h2>
                <button class="copy-btn" onclick="copyFinalAnswer()">Copy</button>
            </div>
            <div class="final-answer-content" id="final-answer">{final_answer_escaped if final_answer_escaped else '<span class="no-data">No final answer available</span>'}</div>
        </section>

        <section class="section">
            <h2 class="section-title">Agent Output Logs</h2>
            {agent_outputs_html}
        </section>

        <section class="section">
            <h2 class="section-title">Configuration</h2>
            {config_html}
        </section>

        <footer class="export-footer">
            <p>Generated by <a href="https://github.com/Leezekun/MassGen" target="_blank">MassGen</a> v{self.data.get('massgen_version', 'unknown')}</p>
            <p>Exported on {self.data.get('exported_at', 'unknown')}</p>
        </footer>
    </div>

    <script>
        // Toggle collapsible sections
        document.querySelectorAll('.collapsible-header').forEach(header => {{
            header.addEventListener('click', () => {{
                header.parentElement.classList.toggle('open');
            }});
        }});

        // Answer tab switching
        document.querySelectorAll('.answer-tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                const targetId = tab.getAttribute('data-target');

                // Remove active from all tabs and contents
                document.querySelectorAll('.answer-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.answer-content').forEach(c => c.classList.remove('active'));

                // Add active to clicked tab and corresponding content
                tab.classList.add('active');
                const targetContent = document.getElementById(targetId);
                if (targetContent) {{
                    targetContent.classList.add('active');
                }}
            }});
        }});

        // Copy final answer to clipboard
        function copyFinalAnswer() {{
            const content = document.getElementById('final-answer').innerText;
            navigator.clipboard.writeText(content).then(() => {{
                const btn = document.querySelector('.copy-btn');
                btn.textContent = 'Copied!';
                btn.classList.add('copied');
                setTimeout(() => {{
                    btn.textContent = 'Copy';
                    btn.classList.remove('copied');
                }}, 2000);
            }});
        }}

        // Embedded session data (for potential future use)
        const SESSION_DATA = {embedded_data};
    </script>
</body>
</html>"""

    def _format_duration(self, seconds: float) -> str:
        """Format seconds as human-readable duration."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def _parse_timestamp_from_log_dir(self, log_dir: str) -> str:
        """Parse timestamp from log directory name."""
        # Format: log_YYYYMMDD_HHMMSS_microseconds
        try:
            parts = log_dir.replace("log_", "").split("_")
            if len(parts) >= 2:
                date_part = parts[0]  # YYYYMMDD
                time_part = parts[1]  # HHMMSS
                return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        except (IndexError, ValueError):
            pass
        return log_dir

    def _build_agents_html(self, metrics: Dict, status: Dict) -> str:
        """Build HTML for agent cards."""
        agents = metrics.get("agents", {})
        status_agents = status.get("agents", {})
        winner = metrics.get("meta", {}).get("winner") or status.get("results", {}).get("winner")

        if not agents and not status_agents:
            return '<div class="no-data">No agent data available</div>'

        # Merge data from both sources
        all_agents = set(list(agents.keys()) + list(status_agents.keys()))

        html_parts = []
        for agent_id in sorted(all_agents):
            agent_metrics = agents.get(agent_id, {})
            agent_status = status_agents.get(agent_id, {})

            is_winner = agent_id == winner
            card_class = "agent-card winner" if is_winner else "agent-card"

            # Get token usage
            token_usage = agent_metrics.get("token_usage", agent_status.get("token_usage", {}))
            input_tokens = token_usage.get("input_tokens", 0)
            output_tokens = token_usage.get("output_tokens", 0)
            cost = token_usage.get("estimated_cost", 0)

            # Get status info
            agent_stat = agent_status.get("status", "unknown")
            answer_count = agent_status.get("answer_count", 0)
            vote_cast = agent_status.get("vote_cast")

            vote_info = ""
            if vote_cast:
                voted_for = vote_cast.get("voted_for_label", vote_cast.get("voted_for_agent", ""))
                vote_info = f"Voted for: {voted_for}"

            html_parts.append(
                f"""
                <div class="{card_class}">
                    <div class="agent-header">
                        <span class="agent-id">{html.escape(agent_id)}</span>
                        {"<span class='winner-badge'>Winner</span>" if is_winner else ""}
                    </div>
                    <div class="agent-stats">
                        <div class="agent-stat">
                            <span class="agent-stat-label">Status</span>
                            <span class="agent-stat-value">{html.escape(agent_stat)}</span>
                        </div>
                        <div class="agent-stat">
                            <span class="agent-stat-label">Answers</span>
                            <span class="agent-stat-value">{answer_count}</span>
                        </div>
                        <div class="agent-stat">
                            <span class="agent-stat-label">Input Tokens</span>
                            <span class="agent-stat-value">{input_tokens:,}</span>
                        </div>
                        <div class="agent-stat">
                            <span class="agent-stat-label">Output Tokens</span>
                            <span class="agent-stat-value">{output_tokens:,}</span>
                        </div>
                        <div class="agent-stat">
                            <span class="agent-stat-label">Cost</span>
                            <span class="agent-stat-value">${cost:.4f}</span>
                        </div>
                        <div class="agent-stat">
                            <span class="agent-stat-label">Vote</span>
                            <span class="agent-stat-value">{html.escape(vote_info) if vote_info else "N/A"}</span>
                        </div>
                    </div>
                </div>
            """,
            )

        return "\n".join(html_parts)

    def _build_tools_html(self, metrics: Dict) -> str:
        """Build HTML for tools breakdown."""
        tools = metrics.get("tools", {}).get("by_tool", {})

        if not tools:
            return '<div class="no-data">No tool data available</div>'

        # Sort by execution time
        sorted_tools = sorted(
            tools.items(),
            key=lambda x: x[1].get("total_execution_time_ms", 0),
            reverse=True,
        )

        # Find max time for bar scaling
        max_time = max((t[1].get("total_execution_time_ms", 0) for t in sorted_tools), default=1)

        html_parts = []
        for tool_name, data in sorted_tools[:10]:  # Top 10 tools
            calls = data.get("call_count", 0)
            time_ms = data.get("total_execution_time_ms", 0)
            bar_width = (time_ms / max_time * 100) if max_time > 0 else 0

            # Show full tool name (no truncation)
            display_name = tool_name

            time_str = f"{time_ms:.0f}ms" if time_ms < 1000 else f"{time_ms/1000:.1f}s"

            html_parts.append(
                f"""
                <div class="tool-bar">
                    <span class="tool-name">{html.escape(display_name)}</span>
                    <div class="tool-bar-container">
                        <div class="tool-bar-fill" style="width: {bar_width}%"></div>
                    </div>
                    <span class="tool-stats">{calls} calls, {time_str}</span>
                </div>
            """,
            )

        return "\n".join(html_parts)

    def _build_answers_votes_html(self, coordination: Dict, status: Dict) -> str:
        """Build HTML for interactive answers and votes viewer."""
        session_metadata = coordination.get("session_metadata", {})
        status_agents = status.get("agents", {})
        winner = session_metadata.get("final_winner") or status.get("results", {}).get("winner")

        # Get answers and votes from loaded data (from snapshot_mappings)
        loaded_answers = self.data.get("answers", {})
        loaded_votes = self.data.get("votes", {})

        if not loaded_answers and not loaded_votes:
            return '<div class="no-data">No answers or votes recorded</div>'

        # Build tabs and content
        tabs_html = []
        content_html = []

        # Sort answers by label (agent1.1, agent1.final, agent2.1, etc.)
        sorted_answers = sorted(loaded_answers.items(), key=lambda x: x[0])

        # Add answer tabs
        for i, (label, answer) in enumerate(sorted_answers):
            agent_id = answer.get("agent_id", "unknown")
            answer_type = answer.get("type", "answer")
            is_winner = agent_id == winner
            is_first = i == 0

            tab_class = "answer-tab"
            if is_winner:
                tab_class += " winner-tab"
            if is_first:
                tab_class += " active"

            # Determine display label
            if answer_type == "final_answer":
                display_label = f"{label} (Final)"
            else:
                display_label = label

            winner_indicator = " - Winner" if is_winner and answer_type == "final_answer" else ""
            tabs_html.append(
                f'<div class="{tab_class}" data-target="answer-{i}">' f"{html.escape(display_label)}{winner_indicator}</div>",
            )

            # Build content
            content_class = "answer-content active" if is_first else "answer-content"
            answer_content = answer.get("content", "No content available")
            round_num = answer.get("round", 0)
            answer.get("iteration", 0)

            # Get vote for this agent
            agent_vote = None
            for vote_label, vote in loaded_votes.items():
                if vote.get("agent_id") == agent_id:
                    agent_vote = vote
                    break

            # Also check status for vote info
            if not agent_vote and agent_id in status_agents:
                status_vote = status_agents[agent_id].get("vote_cast")
                if status_vote:
                    agent_vote = {
                        "voted_for_label": status_vote.get("voted_for_label", status_vote.get("voted_for_agent", "")),
                        "reason": status_vote.get("reason_preview", status_vote.get("reason", "")),
                    }

            vote_html = ""
            if agent_vote:
                voted_for_label = agent_vote.get("voted_for_label", agent_vote.get("voted_for", ""))
                vote_reason = agent_vote.get("reason", "")
                if vote_reason:
                    vote_html = f"""
                        <div class="vote-info">
                            <div class="vote-info-header">Vote: {html.escape(str(voted_for_label))}</div>
                            <div class="vote-reason">{html.escape(str(vote_reason)[:1000])}</div>
                        </div>
                    """

            content_html.append(
                f"""
                <div class="{content_class}" id="answer-{i}">
                    <div class="answer-meta">
                        <div class="answer-meta-item">Agent: <span>{html.escape(str(agent_id))}</span></div>
                        <div class="answer-meta-item">Label: <span>{html.escape(label)}</span></div>
                        <div class="answer-meta-item">Type: <span>{html.escape(answer_type)}</span></div>
                        <div class="answer-meta-item">Round: <span>{round_num}</span></div>
                    </div>
                    <div class="answer-text">{html.escape(answer_content)}</div>
                    {vote_html}
                </div>
            """,
            )

        # If no answers but we have votes, show vote summary
        if not sorted_answers and loaded_votes:
            tabs_html.append('<div class="answer-tab active" data-target="votes-summary">Votes Summary</div>')
            vote_items = []
            for vote_label, vote in loaded_votes.items():
                agent_id = vote.get("agent_id", "unknown")
                voted_for = vote.get("voted_for_label", vote.get("voted_for", ""))
                reason = vote.get("reason", "")
                vote_items.append(
                    f"""
                    <div class="vote-info" style="margin-bottom: 1rem;">
                        <div class="vote-info-header">{html.escape(str(agent_id))} voted for: {html.escape(str(voted_for))}</div>
                        <div class="vote-reason">{html.escape(str(reason)[:1000])}</div>
                    </div>
                """,
                )
            content_html.append(
                f"""
                <div class="answer-content active" id="votes-summary">
                    {"".join(vote_items)}
                </div>
            """,
            )

        return f"""
            <div class="answers-section">
                <div class="answer-tabs">
                    {"".join(tabs_html)}
                </div>
                {"".join(content_html)}
            </div>
        """

    def _build_timeline_html(self, coordination: Dict) -> str:
        """Build HTML for coordination timeline."""
        events = coordination.get("events", [])

        if not events:
            return '<div class="no-data">No timeline events available</div>'

        # Filter to key events
        key_event_types = {
            "session_start",
            "session_end",
            "new_answer",
            "vote_cast",
            "restart_triggered",
            "restart_completed",
            "final_agent_selected",
            "final_answer",
            "error",
        }

        filtered_events = [e for e in events if e.get("event_type") in key_event_types]

        # Limit to prevent huge HTML
        filtered_events = filtered_events[:50]

        if not filtered_events:
            return '<div class="no-data">No key timeline events available</div>'

        # Get start time for relative timestamps
        start_time = coordination.get("session_metadata", {}).get("start_time", 0)
        if not start_time and filtered_events:
            start_time = filtered_events[0].get("timestamp", 0)

        html_parts = []
        for event in filtered_events:
            event_type = event.get("event_type", "unknown")
            timestamp = event.get("timestamp", 0)
            agent_id = event.get("agent_id")
            details = event.get("details", "")

            # Calculate relative time
            relative_time = timestamp - start_time if start_time else 0
            time_str = f"+{relative_time:.1f}s"

            # Determine event class
            event_class = "timeline-event"
            if "answer" in event_type:
                event_class += " answer"
            elif "vote" in event_type:
                event_class += " vote"
            elif "restart" in event_type:
                event_class += " restart"
            elif "error" in event_type:
                event_class += " error"
            elif "final" in event_type:
                event_class += " final"

            # Format event type display
            event_type_display = event_type.replace("_", " ").title()

            agent_html = f'<span class="event-agent">{html.escape(agent_id)}</span>: ' if agent_id else ""

            html_parts.append(
                f"""
                <div class="{event_class}">
                    <div class="event-header">
                        <span class="event-type">{html.escape(event_type_display)}</span>
                        <span class="event-time">{time_str}</span>
                    </div>
                    <div class="event-details">{agent_html}{html.escape(details[:200])}</div>
                </div>
            """,
            )

        return "\n".join(html_parts)

    def _build_agent_outputs_html(self, agent_outputs: Dict[str, str]) -> str:
        """Build HTML for agent output logs."""
        if not agent_outputs:
            return '<div class="no-data">No agent output logs available</div>'

        html_parts = []
        for agent_id, output in sorted(agent_outputs.items()):
            escaped_output = html.escape(output)
            html_parts.append(
                f"""
                <div class="collapsible">
                    <div class="collapsible-header">
                        <span>{html.escape(agent_id)} Output Log</span>
                        <span class="collapsible-icon">&#x25BC;</span>
                    </div>
                    <div class="collapsible-content">
                        <div class="agent-log">{escaped_output}</div>
                    </div>
                </div>
            """,
            )

        return "\n".join(html_parts)

    def _build_config_html(self, execution_metadata: Dict) -> str:
        """Build HTML for configuration display."""
        if not execution_metadata:
            return '<div class="no-data">No configuration data available</div>'

        # Convert to YAML for display
        config_yaml = yaml.dump(execution_metadata, default_flow_style=False, allow_unicode=True)

        return f"""
            <div class="collapsible">
                <div class="collapsible-header">
                    <span>Execution Configuration (sanitized)</span>
                    <span class="collapsible-icon">&#x25BC;</span>
                </div>
                <div class="collapsible-content">
                    <div class="config-block">{html.escape(config_yaml)}</div>
                </div>
            </div>
        """


def find_latest_log() -> Path:
    """Find the most recent log directory with data."""
    logs_dir = get_logs_dir()
    logs = sorted(logs_dir.glob("log_*"), reverse=True)

    if not logs:
        raise FileNotFoundError(f"No logs found in {logs_dir}")

    # Search through logs to find one with metrics
    for log in logs:
        turns = sorted(log.glob("turn_*"), reverse=True)  # Check turns in reverse order
        for turn in turns:
            attempts = sorted(turn.glob("attempt_*"), reverse=True)
            for attempt in attempts:
                if (attempt / "metrics_summary.json").exists() or (attempt / "status.json").exists():
                    return attempt

    # Fallback to latest log even without metrics
    log = logs[0]
    turns = sorted(log.glob("turn_*"))
    if turns:
        attempts = sorted(turns[-1].glob("attempt_*"))
        if attempts:
            return attempts[-1]

    raise FileNotFoundError(f"No valid log attempt found in {logs_dir}")


def resolve_log_dir(log_dir_arg: Optional[str]) -> Path:
    """Resolve log directory from argument or find latest.

    Args:
        log_dir_arg: User-provided log directory path or name

    Returns:
        Path to the log attempt directory
    """
    if not log_dir_arg:
        return find_latest_log()

    path = Path(log_dir_arg)

    # If it's an absolute path, use it directly
    if path.is_absolute():
        if path.exists():
            # Check if this is already an attempt directory
            if (path / "metrics_summary.json").exists() or (path / "status.json").exists():
                return path
            # Check if it's a turn directory
            attempts = sorted(path.glob("attempt_*"))
            if attempts:
                return attempts[-1]
            # Check if it's a log directory
            turns = sorted(path.glob("turn_*"))
            if turns:
                attempts = sorted(turns[-1].glob("attempt_*"))
                if attempts:
                    return attempts[-1]
        raise FileNotFoundError(f"Log directory not found: {path}")

    # Try as a log directory name
    logs_dir = get_logs_dir()

    # Try exact name
    log_path = logs_dir / log_dir_arg
    if log_path.exists():
        turns = sorted(log_path.glob("turn_*"))
        if turns:
            attempts = sorted(turns[-1].glob("attempt_*"))
            if attempts:
                return attempts[-1]

    # Try with log_ prefix
    if not log_dir_arg.startswith("log_"):
        log_path = logs_dir / f"log_{log_dir_arg}"
        if log_path.exists():
            turns = sorted(log_path.glob("turn_*"))
            if turns:
                attempts = sorted(turns[-1].glob("attempt_*"))
                if attempts:
                    return attempts[-1]

    raise FileNotFoundError(f"Log directory not found: {log_dir_arg}")


def export_command(args) -> int:
    """Handle export subcommand.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    console = Console()

    try:
        # Resolve log directory
        log_dir_arg = getattr(args, "log_dir", None)
        log_dir = resolve_log_dir(log_dir_arg)

        # Handle --share flag
        if getattr(args, "share", False):
            from .share import ShareError, share_session

            console.print(f"[blue]Sharing session from: {log_dir}[/blue]")

            try:
                url = share_session(log_dir, console)
                console.print()
                console.print(f"[bold green]Share URL: {url}[/bold green]")
                console.print()
                console.print("[dim]Anyone with this link can view the session (no login required).[/dim]")
                return 0
            except ShareError as e:
                console.print(f"[red]Error:[/red] {e}")
                return 1

        console.print(f"[dim]Exporting session from: {log_dir}[/dim]")

        # Create exporter
        exporter = SessionExporter(log_dir)
        exporter.load_session_data()

        # Determine output path
        output_path = getattr(args, "output", None)
        if not output_path:
            # Generate default name
            log_name = log_dir.parent.parent.name if log_dir.parent.parent else "session"
            output_path = f"massgen_{log_name}.html"

        output_path = Path(output_path)

        # Generate HTML
        exporter.generate_html(output_path)

        console.print(f"[green]Exported to:[/green] {output_path.absolute()}")

        # Open in browser if requested
        if getattr(args, "open", False):
            open_in_browser(output_path, console)

        return 0

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1
    except json.JSONDecodeError as e:
        console.print(f"[red]Error parsing JSON file:[/red] {e}")
        return 1
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1


def open_in_browser(path: Path, console: Console) -> None:
    """Open file in default browser."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", str(path)], check=True)
        elif system == "Windows":
            subprocess.run(["start", str(path)], shell=True, check=True)
        else:  # Linux and others
            subprocess.run(["xdg-open", str(path)], check=True)
        console.print("[dim]Opened in browser[/dim]")
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[dim]Could not open browser automatically[/dim]")
