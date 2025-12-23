# Cluster 286ae5317d

- **Count**: 1
- **Exception type**: `<unknown>`
- **Normalized message**: `AssertionError: assert 'too large' in 'openai api key not found. please set openai_api_key in .env file or environment variable.'
 +  where 'openai api key not found. please set openai_api_key in .env file or environment variable.' = <built-in method lower of str object at <hex>>()
 +    where <built-in method lower of str object at <hex>> = 'OpenAI API key not found. Please set OPENAI_API_KEY in .env file or environment variable.'.lower`

## Minimal repro

Single failing test:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_multimodal_size_limits.py::TestAudioSizeLimits::test_audio_exceeds_size_limit
```

Up to 25 tests from this cluster:

```bash
/Users/admin/src/MassGen/.venv/bin/python -m pytest -q massgen/tests/test_multimodal_size_limits.py::TestAudioSizeLimits::test_audio_exceeds_size_limit
```

## Affected nodeids

- `massgen/tests/test_multimodal_size_limits.py::TestAudioSizeLimits::test_audio_exceeds_size_limit`

## Resolution Steps

1. **Verify**: Run the 'Single failing test' command. It MUST fail.
2. **Fix**: Apply code changes or mark as integration/docker/expensive.
3. **Verify**: Run the command again. It MUST pass.
4. **Update**: Mark as `[x] Resolved` in `TRIAGE_DASHBOARD.md`.

