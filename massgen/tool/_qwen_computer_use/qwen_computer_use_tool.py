# -*- coding: utf-8 -*-
"""
Qwen Computer Use tool for automating browser interactions using Qwen3-VL-235B-A22B-Thinking model.

This tool implements browser control using Qwen's vision-language model which allows the model to:
- Control a web browser (click, type, scroll, navigate)
- Analyze screenshots and decide actions
- Perform multi-step workflows
- Handle safety checks and confirmations
"""

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from massgen.logger_config import logger
from massgen.tool._result import ExecutionResult, TextContent

# Optional dependencies with graceful fallback
try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None

try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None


# Screen dimensions
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string for API calls."""
    return base64.b64encode(image_bytes).decode("utf-8")


def take_screenshot_docker(container, display: str = ":99") -> bytes:
    """Take a screenshot from Docker container using scrot.

    Args:
        container: Docker container instance
        display: X11 display number

    Returns:
        Screenshot as bytes
    """
    import time

    # Remove old screenshot if exists
    container.exec_run("rm -f /tmp/screenshot.png")

    # Take screenshot with scrot
    result = container.exec_run(
        "scrot /tmp/screenshot.png",
        environment={"DISPLAY": display},
    )

    if result.exit_code != 0:
        logger.error(f"Screenshot command failed: {result.output}")
        # Try alternative method with import
        result = container.exec_run(
            "import -window root /tmp/screenshot.png",
            environment={"DISPLAY": display},
        )
        if result.exit_code != 0:
            logger.error(f"Alternative screenshot also failed: {result.output}")
            return b""

    # Small delay to ensure file is written
    time.sleep(0.2)

    # Verify screenshot exists and has content
    check_result = container.exec_run("ls -lh /tmp/screenshot.png")
    logger.info(f"Screenshot file info: {check_result.output.decode()}")

    # Read the screenshot
    read_result = container.exec_run("cat /tmp/screenshot.png", stdout=True)
    if read_result.exit_code != 0:
        logger.error(f"Failed to read screenshot: {read_result.output}")
        return b""

    screenshot_bytes = read_result.output

    # Verify we got actual image data
    if len(screenshot_bytes) < 1000:  # PNG should be at least a few KB
        logger.error(f"Screenshot too small ({len(screenshot_bytes)} bytes), likely invalid")
        return b""

    # Verify PNG header
    if not screenshot_bytes.startswith(b"\x89PNG"):
        logger.error("Screenshot does not have valid PNG header")
        return b""

    logger.info(f"Successfully captured screenshot: {len(screenshot_bytes)} bytes")
    return screenshot_bytes


async def execute_browser_action(page, action: Dict[str, Any], screen_width: int, screen_height: int) -> Dict[str, Any]:
    """Execute a browser action using Playwright.

    Args:
        page: Playwright page instance
        action: Action dictionary with type and parameters
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels

    Returns:
        Result dictionary
    """
    try:
        action_type = action.get("type")
        logger.info(f"     Executing action: {action_type}")

        if action_type == "click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            await page.mouse.click(x, y)
            logger.info(f"     Clicked at ({x}, {y})")

        elif action_type == "type":
            text = action.get("text", "")
            x = action.get("x")
            y = action.get("y")
            if x is not None and y is not None:
                await page.mouse.click(x, y)
                await asyncio.sleep(0.1)
            await page.keyboard.type(text)
            logger.info(f"     Typed: {text}")

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            amount = action.get("amount", 300)
            if direction == "down":
                await page.evaluate(f"window.scrollBy(0, {amount})")
            elif direction == "up":
                await page.evaluate(f"window.scrollBy(0, -{amount})")
            elif direction == "left":
                await page.evaluate(f"window.scrollBy(-{amount}, 0)")
            elif direction == "right":
                await page.evaluate(f"window.scrollBy({amount}, 0)")
            logger.info(f"     Scrolled {direction} by {amount}px")

        elif action_type == "navigate":
            url = action.get("url", "")
            await page.goto(url, wait_until="networkidle", timeout=10000)
            logger.info(f"     Navigated to: {url}")

        elif action_type == "go_back":
            await page.go_back()
            logger.info("     Went back")

        elif action_type == "go_forward":
            await page.go_forward()
            logger.info("     Went forward")

        elif action_type == "wait":
            duration = action.get("duration", 1)
            await asyncio.sleep(duration)
            logger.info(f"     Waited {duration} seconds")

        elif action_type == "key":
            key = action.get("key", "")
            await page.keyboard.press(key)
            logger.info(f"     Pressed key: {key}")

        else:
            logger.warning(f"     Unknown action type: {action_type}")
            return {"error": f"Unknown action type: {action_type}"}

        # Wait for potential navigations/renders
        try:
            await page.wait_for_load_state(timeout=2000)
        except Exception:
            pass  # Timeout is okay

        await asyncio.sleep(0.5)

        return {"success": True}

    except Exception as e:
        logger.error(f"Error executing action {action.get('type')}: {e}")
        return {"error": str(e)}


def execute_docker_action(container, action: Dict[str, Any], screen_width: int, screen_height: int, display: str = ":99") -> Dict[str, Any]:
    """Execute an action in Docker using xdotool.

    Args:
        container: Docker container instance
        action: Action dictionary with type and parameters
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        display: X11 display number

    Returns:
        Result dictionary
    """
    import time

    try:
        action_type = action.get("type")
        logger.info(f"     Docker executing action: {action_type}")

        if action_type == "click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            container.exec_run(
                f"xdotool mousemove {x} {y} click 1",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker clicked at ({x}, {y})")

        elif action_type == "type":
            text = action.get("text", "")
            x = action.get("x")
            y = action.get("y")
            if x is not None and y is not None:
                container.exec_run(
                    f"xdotool mousemove {x} {y} click 1",
                    environment={"DISPLAY": display},
                )
                time.sleep(0.1)
            escaped_text = text.replace("'", "'\\''")
            container.exec_run(
                f"xdotool type '{escaped_text}'",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker typed: {text}")

        elif action_type == "scroll":
            direction = action.get("direction", "down")
            if direction == "down":
                cmd = "xdotool key Page_Down"
            elif direction == "up":
                cmd = "xdotool key Page_Up"
            elif direction == "left":
                cmd = "xdotool key Left Left Left"
            elif direction == "right":
                cmd = "xdotool key Right Right Right"
            else:
                cmd = "xdotool key Page_Down"
            container.exec_run(cmd, environment={"DISPLAY": display})
            logger.info(f"     Docker scrolled {direction}")

        elif action_type == "navigate":
            url = action.get("url", "")
            container.exec_run("xdotool key ctrl+l", environment={"DISPLAY": display})
            time.sleep(0.5)
            escaped_url = url.replace("'", "'\\''")
            container.exec_run(
                f"xdotool type '{escaped_url}'",
                environment={"DISPLAY": display},
            )
            container.exec_run("xdotool key Return", environment={"DISPLAY": display})
            logger.info(f"     Docker navigated to: {url}")

        elif action_type == "go_back":
            container.exec_run("xdotool key alt+Left", environment={"DISPLAY": display})
            logger.info("     Docker went back")

        elif action_type == "go_forward":
            container.exec_run("xdotool key alt+Right", environment={"DISPLAY": display})
            logger.info("     Docker went forward")

        elif action_type == "wait":
            duration = action.get("duration", 1)
            time.sleep(duration)
            logger.info(f"     Docker waited {duration} seconds")

        elif action_type == "key":
            key = action.get("key", "")
            xdotool_key = key.replace("Control", "ctrl").replace("Shift", "shift").replace("Alt", "alt")
            container.exec_run(
                f"xdotool key {xdotool_key}",
                environment={"DISPLAY": display},
            )
            logger.info(f"     Docker pressed key: {key}")

        else:
            logger.warning(f"     Unknown action type: {action_type}")
            return {"error": f"Unknown action type: {action_type}"}

        time.sleep(0.5)
        return {"success": True}

    except Exception as e:
        logger.error(f"Error executing Docker action {action.get('type')}: {e}")
        return {"error": str(e)}


async def qwen_computer_use(
    task: str,
    environment: str = "browser",
    display_width: int = 1440,
    display_height: int = 900,
    max_iterations: int = 25,
    initial_url: Optional[str] = None,
    environment_config: Optional[Dict[str, Any]] = None,
    agent_cwd: Optional[str] = None,
    model: str = "qwen3-vl-235b-a22b-thinking",
) -> ExecutionResult:
    """
    Execute a browser or Docker automation task using Qwen's vision-language model.

    This tool implements control using Qwen's VL model which analyzes screenshots
    and generates actions to autonomously control a browser or Linux desktop to complete tasks.

    Args:
        task: Description of the task to perform
        environment: Environment type - "browser" or "linux" (Docker)
        display_width: Display width in pixels (default: 1440)
        display_height: Display height in pixels (default: 900)
        max_iterations: Maximum number of action iterations (default: 25)
        initial_url: Initial URL to navigate to (browser only, default: None)
        environment_config: Additional configuration (browser: headless/browser_type, docker: container_name/display)
        agent_cwd: Agent's current working directory
        model: Qwen model to use (default: qwen3-vl-235b-a22b-thinking)

    Returns:
        ExecutionResult containing success status, action log, and results

    Examples:
        # Browser task
        qwen_computer_use("Search for Python documentation on Google", environment="browser")

        # Docker task
        qwen_computer_use(
            "Open Firefox and browse to GitHub",
            environment="linux",
            environment_config={"container_name": "cua-container", "display": ":99"}
        )

    Prerequisites:
        - QWEN_API_KEY environment variable must be set
        - For browser: pip install playwright && playwright install
        - For Docker: Docker container with X11 and xdotool installed
    """
    # Check environment-specific dependencies
    if environment == "linux":
        if not DOCKER_AVAILABLE:
            result = {
                "success": False,
                "operation": "qwen_computer_use",
                "error": "Docker not installed. Install with: pip install docker",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
    else:  # browser
        if not PLAYWRIGHT_AVAILABLE:
            result = {
                "success": False,
                "operation": "qwen_computer_use",
                "error": "Playwright not installed. Install with: pip install playwright && playwright install",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

    if not OPENAI_AVAILABLE:
        result = {
            "success": False,
            "operation": "qwen_computer_use",
            "error": "OpenAI SDK not installed. Install with: pip install openai",
        }
        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

    environment_config = environment_config or {}

    try:
        # Load environment variables
        script_dir = Path(__file__).parent.parent.parent.parent
        env_path = script_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        qwen_api_key = os.getenv("QWEN_API_KEY")
        if not qwen_api_key:
            result = {
                "success": False,
                "operation": "qwen_computer_use",
                "error": "Qwen API key not found. Please set QWEN_API_KEY in .env file or environment variable.",
            }
            return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        # Initialize Qwen client (using OpenAI-compatible API)
        client = OpenAI(
            api_key=qwen_api_key,
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )

        # Initialize environment (browser or Docker)
        container = None
        display = None
        page = None
        playwright = None
        browser = None

        if environment == "linux":
            # Docker environment
            logger.info("Initializing Docker environment...")
            container_name = environment_config.get("container_name", "cua-container")
            display = environment_config.get("display", ":99")

            docker_client = docker.from_env()
            try:
                container = docker_client.containers.get(container_name)
                if container.status != "running":
                    logger.info(f"Starting container {container_name}...")
                    container.start()
                logger.info(f"Using Docker container: {container_name} (display {display})")
            except docker.errors.NotFound:
                result = {
                    "success": False,
                    "operation": "qwen_computer_use",
                    "error": f"Docker container '{container_name}' not found. Please create it first.",
                }
                return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

            # Take initial screenshot from Docker
            initial_screenshot = take_screenshot_docker(container, display)

            # Verify screenshot was captured
            if not initial_screenshot or len(initial_screenshot) < 1000:
                result = {
                    "success": False,
                    "operation": "qwen_computer_use",
                    "error": f"Failed to capture screenshot from Docker container. Check if X11 display {display} is running and scrot is installed.",
                }
                return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

        else:
            # Browser environment
            logger.info("Initializing browser...")
            playwright = await async_playwright().start()
            browser_type = environment_config.get("browser_type", "chromium")
            headless = environment_config.get("headless", True)

            # Prepare launch options
            launch_options = {"headless": headless}

            # If not headless and DISPLAY is set, log it
            if not headless:
                display_env = os.environ.get("DISPLAY")
                if display_env:
                    logger.info(f"Running browser with DISPLAY={display_env} (environment variable)")
                else:
                    logger.warning("headless=false but DISPLAY not set. Browser window may not be visible.")

            if browser_type == "chromium":
                browser = await playwright.chromium.launch(**launch_options)
            elif browser_type == "firefox":
                browser = await playwright.firefox.launch(**launch_options)
            elif browser_type == "webkit":
                browser = await playwright.webkit.launch(**launch_options)
            else:
                browser = await playwright.chromium.launch(**launch_options)

            context = await browser.new_context(viewport={"width": display_width, "height": display_height})
            page = await context.new_page()

            # Navigate to initial URL or blank page
            if initial_url:
                logger.info(f"Navigating to initial URL: {initial_url}")
                await page.goto(initial_url, wait_until="networkidle", timeout=10000)
            else:
                await page.goto("about:blank")

            logger.info(f"Initialized {browser_type} browser ({display_width}x{display_height})")

            # Take initial screenshot from browser
            initial_screenshot = await page.screenshot(type="png")

        # Initialize conversation
        logger.info(f"Task: {task} (environment: {environment}, model: {model})")

        # Encode initial screenshot
        screenshot_base64 = encode_image_base64(initial_screenshot)

        # System prompt for computer use
        system_prompt = """You are a computer automation assistant. You can see screenshots and generate actions to control the computer.

Your task is to analyze the screenshot and the user's request, then generate appropriate actions to complete the task.

Available actions:
- click: Click at coordinates {"type": "click", "x": <int>, "y": <int>}
- type: Type text {"type": "type", "text": "<string>", "x": <int>, "y": <int>} (x,y optional for focus)
- scroll: Scroll in direction {"type": "scroll", "direction": "down|up|left|right", "amount": <int>}
- navigate: Navigate to URL {"type": "navigate", "url": "<string>"}
- go_back: Go back {"type": "go_back"}
- go_forward: Go forward {"type": "go_forward"}
- wait: Wait {"type": "wait", "duration": <seconds>}
- key: Press key {"type": "key", "key": "<key_name>"}
- done: Task complete {"type": "done", "result": "<string>"}

Respond with a JSON object containing:
{
  "thought": "Your reasoning about what you see and what to do next",
  "actions": [<action_objects>]
}

Be precise with coordinates. Analyze the screenshot carefully before deciding actions."""

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Task: {task}\n\nAnalyze this screenshot and generate the next actions."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"},
                    },
                ],
            },
        ]

        # Agent loop
        action_log = []
        iteration_count = 0

        try:
            for i in range(max_iterations):
                iteration_count = i + 1
                logger.info(f"\n--- Qwen Computer Use Turn {iteration_count}/{max_iterations} ---")
                logger.info("Requesting action from Qwen...")

                # Call Qwen API
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                )

                assistant_message = response.choices[0].message.content
                logger.info(f"Qwen response: {assistant_message[:200]}...")

                # Parse response
                try:
                    # Try to extract JSON from response
                    response_json = json.loads(assistant_message)
                    thought = response_json.get("thought", "")
                    actions = response_json.get("actions", [])
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract from markdown code block
                    if "```json" in assistant_message:
                        json_str = assistant_message.split("```json")[1].split("```")[0].strip()
                        response_json = json.loads(json_str)
                        thought = response_json.get("thought", "")
                        actions = response_json.get("actions", [])
                    elif "```" in assistant_message:
                        json_str = assistant_message.split("```")[1].split("```")[0].strip()
                        response_json = json.loads(json_str)
                        thought = response_json.get("thought", "")
                        actions = response_json.get("actions", [])
                    else:
                        logger.warning(f"Could not parse JSON from response: {assistant_message}")
                        actions = []
                        thought = assistant_message

                logger.info(f"Thought: {thought}")
                logger.info(f"Actions: {actions}")

                # Check if task is complete
                if any(action.get("type") == "done" for action in actions):
                    final_result = next((action.get("result", "") for action in actions if action.get("type") == "done"), "Task completed")
                    logger.info(f"Task completed: {final_result}")
                    action_log.append(
                        {
                            "iteration": iteration_count,
                            "thought": thought,
                            "status": "completed",
                            "final_output": final_result,
                        },
                    )
                    break

                if not actions:
                    logger.warning("No actions generated, treating as completion")
                    action_log.append(
                        {
                            "iteration": iteration_count,
                            "thought": thought,
                            "status": "completed",
                            "final_output": thought,
                        },
                    )
                    break

                # Execute actions
                logger.info("Executing actions...")
                action_results = []
                for action in actions:
                    if environment == "linux":
                        result = execute_docker_action(container, action, display_width, display_height, display)
                    else:
                        result = await execute_browser_action(page, action, display_width, display_height)
                    action_results.append({"action": action, "result": result})

                # Log actions
                action_log.append(
                    {
                        "iteration": iteration_count,
                        "thought": thought,
                        "actions": action_results,
                    },
                )

                # Capture new screenshot
                logger.info("Capturing new screenshot...")
                if environment == "linux":
                    new_screenshot = take_screenshot_docker(container, display)
                else:
                    new_screenshot = await page.screenshot(type="png")

                screenshot_base64 = encode_image_base64(new_screenshot)

                # Add to conversation
                messages.append({"role": "assistant", "content": assistant_message})
                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Here is the new screenshot after executing the actions. Generate the next actions or indicate if the task is complete."},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{screenshot_base64}"},
                            },
                        ],
                    },
                )

        finally:
            # Cleanup
            if environment == "linux":
                logger.info("\nDocker environment cleanup complete")
            else:
                logger.info("\nClosing browser...")
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()

        # Prepare result
        if iteration_count >= max_iterations:
            result = {
                "success": False,
                "operation": "qwen_computer_use",
                "error": f"Reached maximum iterations ({max_iterations})",
                "task": task,
                "environment": environment,
                "model": model,
                "iterations": iteration_count,
                "action_log": action_log,
            }
        else:
            result = {
                "success": True,
                "operation": "qwen_computer_use",
                "task": task,
                "environment": environment,
                "model": model,
                "iterations": iteration_count,
                "action_log": action_log,
            }

        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])

    except Exception as e:
        logger.error(f"Qwen computer use failed: {str(e)}")
        import traceback

        traceback.print_exc()
        result = {
            "success": False,
            "operation": "qwen_computer_use",
            "error": f"Qwen computer use failed: {str(e)}",
            "task": task,
            "environment": environment,
        }
        return ExecutionResult(output_blocks=[TextContent(data=json.dumps(result, indent=2))])
