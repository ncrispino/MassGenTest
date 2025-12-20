# Backend Model Listing Discovery (MAS-163)

## Overview
This document clarifies current backend model discovery behavior to inform
future UX improvements without introducing execution-time dependencies.

MassGen’s runtime model handling is **string-based and provider-agnostic**.

Model selection relies on:
- User-supplied model strings
- Provider prefixes (e.g. `groq/`, `together/`, `cerebras/`)
- LiteLLM backend routing

There are **no strict provider-specific model registries** used during execution.

As a result, automatic model listing primarily improves:
- CLI UX (interactive selection, suggestions)
- Documentation accuracy
- Example configurations

It does **not** affect core execution or routing.

---
## Model Discovery Tiers

Automatic model discovery is intentionally scoped to UX-facing components
and may vary by provider capability.

Three discovery tiers are supported conceptually:

1. **Live Unauthenticated Discovery**
   - Providers exposing public model registries
   - Example: OpenRouter
   - No API keys required

2. **Static Provider Manifests**
   - Curated model lists stored in-repo
   - Used for CLI UX, docs, and examples only
   - No runtime enforcement or dependencies
   - Suitable for providers without public APIs (e.g., Groq, OpenAI)

3. **Optional Authenticated Discovery (Future)**
   - Enabled only when user provides API keys
   - Strictly non-blocking and UX-only

## Non-Goals

- Introducing runtime dependencies on provider model registries
- Enforcing provider-specific model allowlists
- Blocking execution based on model availability checks

## Current Model Listing Status

| Provider     | Discovery Method        | Notes |
|-------------|-------------------------|-------|
| OpenRouter  | Live (unauthenticated)  | Public API |
| OpenAI      | Static manifest         | No public model registry |
| Anthropic   | Static manifest         | No public model registry |
| Groq        | Static manifest         | API key required for live listing |
| Nebius      | Static manifest         | Enterprise-gated |
| Together AI | Static manifest         | API key required |
| Cerebras    | Static manifest         | Limited availability |
| Qwen        | Static manifest         | Deployment-specific |
| Moonshot    | Static manifest         | Closed ecosystem |
---

## Findings

- Most providers do not expose unauthenticated model listing APIs
- Any automatic discovery beyond OpenRouter requires API keys
- Provider inference occurs via model name prefixes
- Tests confirm no hardcoded provider-specific model registries are enforced at runtime
- Model names primarily appear in:
  - Documentation
  - CLI examples
  - Presentation artifacts
---
These findings suggest that automatic model discovery should be treated as
a UX concern rather than a runtime requirement.

## Recommendations

1. Clearly document which providers support automatic model discovery
2. Mark providers requiring static manifests
3. Implement static provider model manifests for non-public providers
4. Treat authenticated API-based listing as an optional enhancement

## Follow-Up Work

This clarification enables safe exploration of automatic model listing
for providers such as Groq, OpenAI, Anthropic, and others without introducing
execution-time dependencies or requiring API keys at the initial stage.

Potential next steps include:
- Investigating which providers expose public or unauthenticated model listing APIs
- Leveraging LiteLLM or third-party wrappers for consolidated model discovery
- Implementing automatic listing exclusively in UX-facing components (e.g., CLI setup)
- Clearly documenting providers that must remain manually updated
- Define a standard provider manifest format for model metadata


