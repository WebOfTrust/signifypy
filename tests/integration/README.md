# SignifyPy Integration Tests

This directory is the dedicated integration layer for SignifyPy.

Its job is to prove real client workflows that sit above mock-heavy unit tests
and below slow cross-repo doer/E2E coverage.

It is also the replacement for the old manual `scripts/*.py` workflow demos.
Those script entrypoints have been retired so the repo has one live-stack
contract layer instead of a second, terminal-driven harness.

## Running

These tests are opt-in. A plain `pytest` run should only execute the local unit
and mocked suites.

To run this layer explicitly:

```bash
./venv/bin/python -m pytest --run-integration tests/integration
```

Maintainer shortcuts:

```bash
make test-integration
make test-integration-parallel
```

Local live-stack dependencies are explicit. Before running this layer on a
fresh checkout, sync the pinned source repos and their service virtualenvs:

```bash
make sync-integration-deps
```

This creates `.integration-deps/keripy`, `.integration-deps/keria`, and
`.integration-deps/vLEI`, checks each repo out at the pinned SHA below, and
builds the KERIA and vLEI repo-local virtualenvs used by the harness. The
directory is ignored by Git.

In CI, the same rule applies: the live layer should run from a dedicated
workflow job, not from the default fast-test invocation.

## Source Dependencies Required

The live integration fixture launches local services from pinned source repos.
For local runs, `make sync-integration-deps` installs them under
`.integration-deps/`. CI may provide the same repos as siblings instead:

- `../keripy`
- `../keria`
- `../vLEI`

The current stack pins those source dependencies to explicit compatibility
SHAs:

- `keripy`: `4ee02c0213770d25a0114fe7ebd7ab4ab5500cde` (tag `1.2.12`)
- `keria`: `5b703bd8a60fab68a6476819626b22784317bf14` from `kentbull/keria`
- `vLEI`: `f514b9431c5f965b5f7f64a8693e19df2f181564` (tag `1.0.2`)

The CI runtime also constrains `hio` to `0.6.14` across the live stack.
`keripy` and `vLEI` both allow newer `hio` releases, but the pinned SignifyPy
integration stack currently relies on the older doer API shape used by KERIA
0.4.0-prep and vLEI 1.0.2.

The local default expects repo-local virtualenv interpreters to exist at:

- `./venv/bin/python`
- `.integration-deps/keria/venv/bin/python`
- `.integration-deps/vLEI/venv/bin/python`

CI may still check out the four repos as siblings and create one virtualenv per
repo. When it does, it points the harness at those sibling roots with
`SIGNIFYPY_INTEGRATION_*_ROOT` environment variables. Either way, missing repos,
wrong SHAs, or missing service virtualenvs are integration-test failures when
`--run-integration` is requested.

The CI job also caches those repo-local virtualenvs by dependency-manifest
hash. That keeps repeat runs fast without changing the local contract the
fixture depends on.

The fixture uses those runtimes to launch:

- local demo witnesses from KERIpy
- `keria` from the KERIA source tree
- `vlei-server` from the vLEI source tree

## Isolation Model

The live harness now builds a runtime-generated stack topology instead of
assuming fixed localhost ports.

Every stack instance gets its own:

- `HOME`
- runtime root
- config root
- log root
- loopback ports for witnesses, KERIA, and vLEI
- derived witness and schema OOBIs

This keeps parallel runs from colliding on the old fixed `3901/3902/3903`,
`5642/5643/5644`, and `7723` layout.

The fixture surface is now:

- `shared_live_stack`: one stack per xdist worker session
- `isolated_live_stack`: one stack per test function
- `live_stack`: compatibility alias for `shared_live_stack`
- `client_factory`: clients bound to the shared-per-worker stack
- `isolated_client_factory`: clients bound to a per-test isolated stack

The default model is still the shared stack, but tests that need stronger
runtime/process separation can opt into the isolated fixture explicitly.

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

Current Phase 2 shape:

- `test_provisioning_and_identifiers.py`
  - provisioning/connect
  - single-sig lifecycle
  - schema OOBI resolution
  - witnessed identifier OOBI coverage
  - single-sig rotation
  - self-issued credential smoke
- `test_multisig.py`
  - 2-of-2 multisig lifecycle
- `test_multisig_interactions.py`
  - existing-group multisig interaction path
  - `icp -> ixn -> rot -> ixn -> ixn` sequence and anchor assertions
- `test_challenges.py`
  - challenge/response workflow
- `test_delegation.py`
  - single-sig to single-sig delegation
  - single-sig to multisig delegation
  - multisig to single-sig delegation
  - multisig to multisig delegation
- `test_credentials.py`
  - single-sig grant/admit presentation path
- `test_multisig_join.py`
  - 4-party multisig join/inception and rotation path
- `test_multisig_credentials.py`
  - single-sig issuer to multisig holder issuance path
  - multisig issuer to multisig holder remains staged behind one skipped test
    while the pinned stack still stalls on second-member `/multisig/vcp`
    anchor convergence

The shared helper module in `tests/integration/helpers.py` intentionally mirrors
the workflow substance used in the SignifyTS integration utilities: witness-backed
identifiers by default for OOBI-dependent scenarios, explicit waits around
`addEndRole` before querying OOBIs, exact role-specific OOBI usage instead of
"best available" fallbacks, and reusable multisig choreography helpers instead
of per-test ad hoc polling.

Another subtle harness rule lives in `tests/integration/conftest.py`: witness
config and KERIA config are intentionally written into different `Configer`
paths because the underlying services read different bases. If that pathing
drifts, the stack may still boot while silently publishing broken endpoint
metadata, which then shows up later as empty agent OOBIs or stalled multistep
workflows.
