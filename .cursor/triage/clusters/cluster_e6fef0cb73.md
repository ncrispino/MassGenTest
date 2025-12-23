# Cluster e6fef0cb73

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AttributeError: <massgen.backend.azure_openai.AzureOpenAIBackend object at <hex>> does not have the attribute 'client'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_stream_with_tools_with_model
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_stream_with_tools_with_model
```

## Affected nodeids

- `massgen/tests/test_azure_openai_backend.py::TestAzureOpenAIBackend::test_stream_with_tools_with_model`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

