# SignifyPy Integration Tests

This directory is the dedicated integration layer for SignifyPy.

Its job is to prove real client workflows that sit above mock-heavy unit tests
and below slow cross-repo doer/E2E coverage.

## Running

These tests are opt-in. A plain `pytest` run should only execute the local unit
and mocked suites.

To run this layer explicitly:

```bash
./venv/bin/python -m pytest --run-integration tests/integration
```

In CI, the same rule applies: the live layer should run from a dedicated
workflow job, not from the default fast-test invocation.

## Local Sources Required

The live integration fixture launches local services from sibling source repos,
so this workspace layout is part of the contract:

- `../keripy`
- `../keria`
- `../vLEI`

The current CI stack pins those sibling repos to explicit compatibility refs:

- `keripy`: `1.2.12`
- `keria`: `9e2461550f373ad7bdbe7eebeaceac689cb15397`
- `vLEI`: `1.0.2`

The CI runtime also constrains `hio` to `0.6.14` across the live stack.
`keripy` and `vLEI` both allow newer `hio` releases, but the pinned SignifyPy
integration stack currently relies on the older doer API shape used by KERIA
0.4.0-prep and vLEI 1.0.2.

It also expects repo-local virtualenv interpreters to exist at:

- `../signifypy/venv/bin/python`
- `../keria/venv/bin/python`
- `../vLEI/venv/bin/python`

That requirement is why the GitHub Actions workflow checks out the four repos
as siblings and creates one virtualenv per repo instead of trying to run the
whole stack from a single Python environment.

The CI job also caches those repo-local virtualenvs by dependency-manifest
hash. That keeps repeat runs fast without changing the local contract the
fixture depends on.

The fixture uses those runtimes to launch:

- local demo witnesses from KERIpy
- `keria` from the KERIA source tree
- `vlei-server` from the vLEI source tree

## Isolation Model

The live stack fixture points each spawned service at a pytest temp `HOME`
directory. That isolates fallback `~/.keri` state per run, avoids mutating a
developer's personal KERI state, and removes the need for destructive cleanup
between normal reruns.

The witness launcher also forces its local listeners onto `127.0.0.1` instead
of all interfaces. That keeps the harness aligned with the loopback OOBIs and
avoids hosted-runner socket-binding restrictions that can break all-interface
listeners in CI.

For the current pinned `keripy` stack, the harness also disables the witness
`/query` endpoint during startup. That endpoint opens a second LMDB-backed
registry handle for the same witness inside one process on Linux, which breaks
the live stack in CI. Current tests do not rely on witness `/query`, so the harness
keeps the rest of the witness HTTP surface while sidestepping that portability
bug. Eventually this needs to be fixed in the upstream WebOfTrust/keripy repo.

Initial target scenarios:

- provisioning and connect
- single-sig identifier lifecycle
- multisig lifecycle
- OOBI resolution
- challenge/response
- delegation
- credential issuance and presentation

The first concrete implementation slice should start in
`test_provisioning_and_identifiers.py`.
