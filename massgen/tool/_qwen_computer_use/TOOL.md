---
name: qwen-computer-use
description: Browser and desktop automation using Qwen's vision-language model (qwen3-vl-235b-a22b-thinking)
category: automation
requires_api_keys: [QWEN_API_KEY]
tasks:
  - "Automate browser interactions using Qwen's VL model with vision capabilities"
  - "Control desktop applications with Qwen's action system"
  - "Perform multi-step workflows with Qwen vision-guided automation"
  - "Execute browser automation with Qwen's vision-language model"
keywords: [qwen, alibaba, computer-use, browser, automation, playwright, desktop-control, vision-language, vl-model]
---

# Qwen Computer Use

Browser and desktop automation tool using Qwen's vision-language model (qwen3-vl-235b-a22b-thinking), which provides computer control capabilities through vision-guided action generation with thinking process.

## Purpose

Enable Qwen models to control computers through vision-language understanding:
- **Vision-guided control**: Qwen analyzes screenshots and generates actions
- **OpenAI-compatible API**: Uses Qwen's OpenAI-compatible endpoint
- **Natural language tasks**: Describe what to do in plain English
- **Multi-step automation**: Qwen chains actions automatically
- **Cost-effective**: Leveraging Qwen's efficient VL model

## When to Use This Tool

**Use Qwen Computer Use when:**
- Working with Qwen's vision-language models
- Want cost-effective computer use capabilities
- Prefer Alibaba Cloud's AI ecosystem
- Need fast vision-guided automation
- Task benefits from Qwen's VL reasoning

**Use Gemini Computer Use instead when:**
- Working with Google's Gemini models
- Need Google's specific API features
- Prefer Google AI ecosystem

**Use Claude Computer Use instead when:**
- Working with Anthropic's Claude models
- Need Claude's specific safety features
- Prefer Anthropic's API

**Use Browser Automation instead when:**
- Need simple, predefined actions
- Don't require AI-guided decision making
- Want lower cost/faster execution

## Available Functions

### `qwen_computer_use(task: str, environment: str, ...) -> ExecutionResult`

Main function for Qwen-powered computer automation.

**Example - Browser Automation:**
```python
result = await qwen_computer_use(
    task="Go to example.com and find the main heading",
    environment="browser",
    initial_url="https://example.com"
)
# Qwen navigates, reads page, extracts heading
```

**Example - Multi-step Workflow:**
```python
result = await qwen_computer_use(
    task="""
    1. Navigate to wikipedia.org
    2. Search for 'Artificial Intelligence'
    3. Scroll down to the history section
    4. Summarize the first paragraph
    """,
    environment="browser"
)
# Qwen performs all steps and provides summary
```

**Parameters:**
- `task` (str): Natural language description of what to do
- `environment` (str): "browser" or "linux" (Docker)
- `display_width` (int): Display width in pixels (default: 1440)
- `display_height` (int): Display height in pixels (default: 900)
- `max_iterations` (int): Maximum actions Qwen can take (default: 25)
- `initial_url` (str, optional): Starting URL for browser tasks
- `environment_config` (dict, optional): Additional configuration (headless, browser_type, etc.)
- `model` (str): Qwen model to use (default: "qwen3-vl-235b-a22b-thinking")

**Returns:**
- Success/failure status
- Action log showing Qwen's steps
- Thought process at each step
- Final result/answer

## How It Works

1. **Task submission**: You describe the task in natural language
2. **Screen capture**: Qwen sees current screen state via screenshot
3. **Vision analysis**: Qwen VL model analyzes the screenshot
4. **Action planning**: Qwen decides next actions based on visual understanding
5. **Action execution**: Playwright/Docker executes the actions
6. **Verification**: Qwen sees result on new screenshot
7. **Repeat**: Loop until task complete or max iterations reached

**Qwen's actions:**
- `click`: Click at pixel coordinates `{"type": "click", "x": <int>, "y": <int>}`
- `type`: Type text `{"type": "type", "text": "<string>", "x": <int>, "y": <int>}`
- `scroll`: Scroll in direction `{"type": "scroll", "direction": "down|up|left|right", "amount": <int>}`
- `navigate`: Navigate to URL `{"type": "navigate", "url": "<string>"}`
- `go_back`: Go back `{"type": "go_back"}`
- `go_forward`: Go forward `{"type": "go_forward"}`
- `wait`: Wait `{"type": "wait", "duration": <seconds>}`
- `key`: Press key `{"type": "key", "key": "<key_name>"}`
- `done`: Task complete `{"type": "done", "result": "<string>"}`

**Response format:**
Qwen responds with JSON containing:
```json
{
  "thought": "Reasoning about what to do next",
  "actions": [<action_objects>]
}
```

## Configuration

### Prerequisites

**Qwen API key:**
```bash
export QWEN_API_KEY="your-api-key"
```

**Install dependencies:**
```bash
pip install playwright openai
playwright install chromium
```

**For Docker automation (optional):**
```bash
pip install docker
```

### Supported Models

Qwen Computer Use works with:
- **qwen3-vl-235b-a22b-thinking** (recommended): Large vision-language model with thinking process
- **qwen3-vl-30b-a3b-thinking**: Smaller VL model with thinking
- Other Qwen VL models with vision capabilities

### YAML Config

Enable Qwen Computer Use in your config:

```yaml
agents:
  - id: "qwen_automation_agent"
    backend:
      type: "openai"  # Orchestration backend
      model: "gpt-4.1"
      custom_tools:
        - name: ["qwen_computer_use"]
          category: "automation"
          path: "massgen/tool/_qwen_computer_use/qwen_computer_use_tool.py"
          function: ["qwen_computer_use"]
          preset_args:
            environment: "browser"
            display_width: 1440
            display_height: 900
            max_iterations: 25
            model: "qwen3-vl-235b-a22b-thinking"
```

## Environment Types

### Browser Environment
Uses Playwright to control Chromium browser.

**Features:**
- Full web browser control
- JavaScript execution
- Cookies/session management
- Headless mode support

**Screen dimensions:** 1440x900 (default, configurable)

### Docker Environment (Linux)
Runs automation in isolated Docker container.

**Features:**
- Desktop application control
- X11 GUI support
- Complete isolation
- Linux environment

**Requires:** Docker with X11 setup and xdotool installed

## Qwen-Specific Features

**Vision-language understanding:**
- Analyzes screenshots with VL model
- Generates actions based on visual understanding
- Provides reasoning about what it sees

**OpenAI-compatible API:**
- Uses familiar OpenAI SDK
- Easy integration with existing code
- Consistent API patterns

**Cost-effective:**
- Efficient VL model
- Competitive pricing
- Good performance/cost ratio

**Alibaba Cloud integration:**
- Works with Alibaba Cloud services
- Consistent API across Qwen products
- Regional deployment options

## Differences from Other Computer Use Tools

| Feature | Qwen Computer Use | Gemini Computer Use | Claude Computer Use |
|---------|------------------|---------------------|---------------------|
| **Model** | Qwen3-VL-235B | Gemini 2.5 | Claude 3.5+ |
| **Coordinates** | Pixel-based | Normalized (0-1000) | Pixel-based |
| **Screen size** | 1440x900 (default) | 1440x900 | 1024x768 |
| **API** | OpenAI-compatible | Google GenAI | Anthropic |
| **Provider** | Alibaba Cloud | Google | Anthropic |
| **Implementation** | Vision → JSON actions | Native computer use | Native computer use |

## Cost Considerations

**Qwen API pricing:**
- VL model calls (qwen3-vl-235b-a22b-thinking with reasoning)
- Vision processing (screenshots)
- Action generation

**Typical costs:**
- Simple task (5 steps): $0.05-0.20
- Complex task (20 steps): $0.20-0.80
- Per screenshot + response: ~$0.005-0.02

**Cost varies by:**
- Number of iterations
- Screenshot frequency
- Model used
- Task complexity

**Generally competitive with other providers.**

## Limitations

- **Vision model dependency**: Requires Qwen VL model access
- **API-dependent**: Subject to Alibaba Cloud API availability
- **JSON parsing**: Requires proper JSON formatting in responses
- **Beta features**: Computer use implementation may evolve
- **Rate limits**: Subject to Alibaba Cloud rate limits
- **Coordinate precision**: Pixel-based coordinates require accurate screen size
- **Regional availability**: May vary by region

## Best Practices

**1. Clear, specific tasks:**
```python
# Good
task = "Navigate to news.ycombinator.com and extract the top 5 story titles"

# Bad
task = "Check Hacker News"
```

**2. Reasonable iteration limits:**
```python
# Most tasks complete in < 20 iterations
max_iterations=20

# Complex tasks
max_iterations=30
```

**3. Handle JSON parsing:**
The implementation handles various JSON formats including markdown code blocks.

**4. Error handling:**
```python
try:
    result = await qwen_computer_use(task=task, environment="browser")
    if result.output_blocks:
        output_data = json.loads(result.output_blocks[0].data)
        if output_data.get("success"):
            print("Task completed successfully")
except Exception as e:
    logger.error(f"Qwen computer use failed: {e}")
```

**5. Monitor performance:**
```python
result = await qwen_computer_use(...)
output_data = json.loads(result.output_blocks[0].data)
print(f"Completed in {output_data.get('iterations')} iterations")
```

## Common Use Cases

1. **Web scraping**: Extract data from dynamic websites
2. **Form automation**: Fill out web forms automatically
3. **Testing**: Automated UI testing with natural language
4. **Research**: Browse and synthesize information from multiple pages
5. **Monitoring**: Check website status or content changes
6. **Data entry**: Automate repetitive web data entry tasks

## Example Workflows

**Research task:**
```python
task = """
Go to scholar.google.com
Search for 'machine learning computer vision'
Find the most cited paper from 2024
Extract the title, authors, and citation count
"""
result = await qwen_computer_use(
    task=task,
    environment="browser",
    model="qwen3-vl-235b-a22b-thinking"
)
```

**E-commerce interaction:**
```python
task = """
Navigate to example-shop.com
Search for 'wireless headphones'
Sort by price: low to high
Extract the name and price of the cheapest option
"""
result = await qwen_computer_use(
    task=task,
    environment="browser",
    initial_url="https://example-shop.com"
)
```

**Form submission:**
```python
task = """
Go to contact-form.example.com
Fill in:
  Name: Alice Smith
  Email: alice@example.com
  Subject: Product inquiry
  Message: What are your business hours?
Click Submit
Confirm success message appears
"""
result = await qwen_computer_use(task=task, environment="browser")
```

## Debugging

**Check result:**
```python
result = await qwen_computer_use(...)
output_data = json.loads(result.output_blocks[0].data)
print(json.dumps(output_data, indent=2))
```

**Review action log:**
```python
for iteration in output_data.get("action_log", []):
    print(f"Iteration {iteration.get('iteration')}:")
    print(f"  Thought: {iteration.get('thought', 'N/A')}")
    print(f"  Actions: {iteration.get('actions', [])}")
```

**Common issues:**
- **Max iterations exceeded**: Task too complex, break into smaller tasks or increase limit
- **JSON parsing errors**: Model may not format JSON correctly, implementation handles common formats
- **Action failed**: Page changed unexpectedly, try again or adjust task description
- **Coordinate issues**: Ensure screen size matches display_width/display_height
- **Rate limit**: Reduce automation frequency or use backoff

## Performance Tips

**1. Use capable model:**
qwen3-vl-235b-a22b-thinking provides strong reasoning with thinking process.

**2. Headless mode:**
```python
environment_config={"headless": True}  # Faster execution
```

**3. Clear task descriptions:**
Write specific, actionable tasks to reduce unnecessary iterations.

**4. Set appropriate iteration limits:**
```python
max_iterations=15  # Adjust based on task complexity
```

**5. Minimize unnecessary actions:**
Be specific about what information you need to avoid exploration.

## Comparison with Other Approaches

**When to use Qwen Computer Use:**
- ✅ Complex web interactions requiring vision understanding
- ✅ Natural language task descriptions
- ✅ Tasks requiring visual analysis
- ✅ Multi-step workflows with decision points
- ✅ Cost-effective automation

**When to use alternatives:**
- ❌ Simple, predefined actions → Use Browser Automation
- ❌ API-accessible data → Use direct API calls
- ❌ Provider-specific features → Use Gemini/Claude Computer Use
- ❌ Non-vision tasks → Use traditional automation

## Migration from Other Tools

**From Gemini Computer Use:**
```python
# Before (Gemini)
result = await gemini_computer_use(
    task="...",
    environment="browser"
)

# After (Qwen)
result = await qwen_computer_use(
    task="...",
    environment="browser",
    model="qwen3-vl-235b-a22b-thinking"
)
```

Main differences:
- Different API (OpenAI-compatible vs Google GenAI)
- Pixel coordinates instead of normalized
- JSON-based action format
- Different response structure

## Security Considerations

**API Key protection:**
- Store QWEN_API_KEY securely
- Use environment variables, not code
- Rotate keys regularly

**Sandbox execution:**
- Use Docker for isolation
- Limit browser access in production
- Monitor automation activities

**Input validation:**
- Sanitize task descriptions
- Validate action parameters
- Handle errors gracefully
