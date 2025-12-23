# Cluster 3cf8378975

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'gemini-3-flash-preview' == 'gemini-<num>-flash'
  
  #x1B[0m#x1B[91m- gemini-<num>-flash#x1B[39;49;00m#x1B[90m#x1B[39;49;00m
  #x1B[92m+ gemini-3-flash-preview#x1B[39;49;00m#x1B[90m#x1B[39;49;00m`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_config_builder.py::TestCloneAgent::test_clone_openai_to_gemini_preserves_provider
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_config_builder.py::TestCloneAgent::test_clone_openai_to_gemini_preserves_provider
```

## Affected nodeids

- `massgen/tests/test_config_builder.py::TestCloneAgent::test_clone_openai_to_gemini_preserves_provider`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

