# Backend Model Listing Discovery (MAS-163)

## Context

MassGen’s runtime model handling is **string-based and provider-agnostic**.
Model selection relies on:
- model name conventions
- provider prefixes (e.g., `groq/`, `together/`, `cerebras/`)
- LiteLLM backend routing

There are **no provider-specific model registries** used in core execution.

As a result, automatic model listing would primarily improve:
- CLI UX (interactive selection, suggestions)
- Documentation accuracy
- Example configurations

It would **not affect core execution or runtime behavior**.

---

## Current Backend Model Listing Status

| Provider      | Automatic Listing | Source | Notes |
|---------------|------------------|--------|-------|
| OpenRouter    | ✅ Yes            | OpenRouter API | Models dynamically fetched |
| OpenAI        | ❓ Unknown        |        | Likely available via API |
| Anthropic     | ❓ Unknown        |        | TBD |
| Groq          | ❓ Unknown        |        | TBD |
| Nebius        | ❓ Unknown        |        | TBD |
| Together AI   | ❓ Unknown        |        | TBD |
| Cerebras      | ❓ Unknown        |        | TBD |
| Qwen          | ❓ Unknown        |        | TBD |
| Moonshot      | ❓ Unknown        |        | TBD |

---

## Findings from Codebase Inspection

- Model handling is driven entirely by user-supplied strings
- Provider inference occurs via model name prefixes
- Tests confirm there are no hardcoded provider-specific model lists
- UX-facing model lists (CLI prompts, docs, examples) are the primary candidates for automation

---

## Next Steps

1. Identify all UX-facing model lists (CLI, interactive setup, documentation)
2. Investigate provider APIs and LiteLLM support for model discovery
3. Implement automatic listing for providers that support it
4. Clearly document providers that require manual model list updates
