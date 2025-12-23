# Cluster 692aca3f58

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert False
 +  where False = <function iscoroutinefunction at <hex>>(langgraph_lesson_planner)
 +    where <function iscoroutinefunction at <hex>> = <module 'inspect' from '<path>`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_langgraph_lesson_planner.py::TestLangGraphToolIntegration::test_tool_function_signature
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_langgraph_lesson_planner.py::TestLangGraphToolIntegration::test_tool_function_signature
```

## Affected nodeids

- `massgen/tests/test_langgraph_lesson_planner.py::TestLangGraphToolIntegration::test_tool_function_signature`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

