# Cluster a6331c8a4f

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: Error during normal content test: object Mock can't be used in 'await' expression
assert False`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_final_presentation_fallback.py::test_final_presentation_with_content
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_final_presentation_fallback.py::test_final_presentation_with_content
```

## Affected nodeids

- `massgen/tests/test_final_presentation_fallback.py::test_final_presentation_with_content`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

