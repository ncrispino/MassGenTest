# Cluster a582835a54

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'filesystem' not in ['filesystem', 'workspace_tools', 'command_line']`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_exclude_file_operation_mcps.py::TestExcludeFileOperationMCPs::test_inject_filesystem_mcp_keeps_workspace_tools_with_media
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_exclude_file_operation_mcps.py::TestExcludeFileOperationMCPs::test_inject_filesystem_mcp_keeps_workspace_tools_with_media
```

## Affected nodeids

- `massgen/tests/test_exclude_file_operation_mcps.py::TestExcludeFileOperationMCPs::test_inject_filesystem_mcp_keeps_workspace_tools_with_media`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

