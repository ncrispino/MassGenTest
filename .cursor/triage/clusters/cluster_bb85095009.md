# Cluster bb85095009

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'gpt-<num>-codex' == 'gpt-5'
  
  #x1B[0m#x1B[91m- gpt-5#x1B[39;49;00m#x1B[90m#x1B[39;49;00m
  #x1B[92m+ gpt-<num>-codex#x1B[39;49;00m#x1B[90m#x1B[39;49;00m`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_default
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_default
```

## Affected nodeids

- `massgen/tests/test_programmatic_api.py::TestBuildConfig::test_build_config_default`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

