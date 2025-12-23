# Cluster c93cc0fdf9

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AttributeError: 'ClaudeBackend' object has no attribute 'convert_messages_to_claude_format'`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_backend.py::test_claude_message_conversion
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_claude_backend.py::test_claude_message_conversion
```

## Affected nodeids

- `massgen/tests/test_claude_backend.py::test_claude_message_conversion`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

