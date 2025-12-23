# Cluster 403c7f4eb0

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: Regex pattern did not match.
  Expected regex: 'Both llm_backend and embedding_backend'
  Actual message: "Either llm_config or llm_backend is required when mem0_config is not provided.\nRECOMMENDED: Use llm_config with mem0's native LLMs.\nExample: llm_config={'provider': 'openai', 'model': 'gpt-<num>-nano-<n>-04-14'}"`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_persistent_memory.py::TestPersistentMemoryInitialization::test_initialization_without_backends_fails
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_persistent_memory.py::TestPersistentMemoryInitialization::test_initialization_without_backends_fails
```

## Affected nodeids

- `massgen/tests/test_persistent_memory.py::TestPersistentMemoryInitialization::test_initialization_without_backends_fails`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

