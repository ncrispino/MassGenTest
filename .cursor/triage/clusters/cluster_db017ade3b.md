# Cluster db017ade3b

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `TypeError: Can't instantiate abstract class MockClaudeCodeAgent without an implementation for abstract methods 'get_configurable_system_message', 'get_status', 'reset'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_code_context_sharing.py::test_non_claude_code_agents_ignored
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_code_context_sharing.py::test_non_claude_code_agents_ignored
```

## Affected nodeids

- `massgen/tests/test_claude_code_context_sharing.py::test_non_claude_code_agents_ignored`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

