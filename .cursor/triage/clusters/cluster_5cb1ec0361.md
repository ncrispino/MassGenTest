# Cluster 5cb1ec0361

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `TypeError: build_config() got an unexpected keyword argument 'context_path'. Did you mean 'context_paths'?`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_with_context_path
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_with_context_path
```

## Affected nodeids

- `massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_with_context_path`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

