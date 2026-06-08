# Example: minimal Phase 0 output

These 11 files are the **actual, unedited** output of running the bootstrapper
against a small FastAPI repo (`tests/fixtures/python_fastapi_repo`):

```bash
phase0 scan --repo-path /path/to/python_fastapi_repo --output-dir ./.ai/phase0
```

It is what `<target-repo>/.ai/phase0/` looks like for a clean, well-equipped
Python service (tests + CI present, so the risk register is short). Only one
line was sanitized: `repo.root` in `manifest.yaml`, to avoid a machine path.

Use it as a shape reference for the pack a fresh repo should produce — not as
content to copy. Every claim here traces to `evidence-map.md`.
