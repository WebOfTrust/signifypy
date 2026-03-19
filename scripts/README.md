# SignifyPy Legacy Script Area

The old manual workflow scripts that used to live in this directory have been
retired.

Those scenarios now belong to the pytest-managed integration harness in
[`tests/integration`](/Users/kbull/code/keri/kentbull/signifypy/tests/integration),
which starts witnesses, KERIA, and `vlei-server` itself instead of requiring
multiple external terminal sessions.

## Run The Integration Layer

From the `signifypy` repo root:

```bash
./venv/bin/python -m pytest --run-integration tests/integration
```

To inspect the current live-scenario coverage:

```bash
./venv/bin/python -m pytest --run-integration --collect-only tests/integration
```

## What Remains Here

- `data/` keeps credential and rules fixtures that are still useful as source
  material for integration scenarios.
- `keri/` keeps legacy config assets that may still be useful for reference
  during future harness cleanup.

Verdict: do not add new integration workflows back under `scripts/`. New live
coverage belongs under `tests/integration`.
