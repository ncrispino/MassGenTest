# Cluster 0417872da1

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'custom_function' in {'custom_tool__custom_function': RegisteredToolEntry(tool_name='custom_tool__custom_function', category='default', ori...bject'}}}, preset_params={}, context_param_names=set(), extension_model=None, mcp_server_id=None, post_processor=None)}
 +  where {'custom_tool__custom_function': RegisteredToolEntry(tool_name='custom_tool__custom_function', category='default', ori...bject'}}}, preset_params={}, context_param_names=set(), extension_model=None, mcp_server_id=None, post_processor=None)} = <massgen.tool._manager.ToolManager object at <hex>>.registered_tools
 +    where <massgen.tool._manager.ToolManager object at <hex>> = <massgen.tests.test_custom_tools.TestToolManager object at <hex>>.tool_manager`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_custom_tools.py::TestToolManager::test_add_tool_with_path
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_custom_tools.py::TestToolManager::test_add_tool_with_path
```

## Affected nodeids

- `massgen/tests/test_custom_tools.py::TestToolManager::test_add_tool_with_path`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

