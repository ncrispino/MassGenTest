# Cluster 9cac85ecd5

- **Count**: 2
- **Exception type**: `<unknown>`
- **Normalized message**: `ValueError: Claude Code backend requires 'cwd' configuration for workspace management`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_code.py::test_with_workflow_tools
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_code.py::test_with_workflow_tools massgen/tests/test_claude_code_orchestrator.py::test_claude_code_with_orchestrator
```

## Affected nodeids

- `massgen/tests/test_claude_code.py::test_with_workflow_tools`
- `massgen/tests/test_claude_code_orchestrator.py::test_claude_code_with_orchestrator`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

