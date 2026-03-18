# SignifyPy Integration Tests

This directory is the dedicated integration layer for SignifyPy.

Its job is to prove real client workflows that sit above mock-heavy unit tests
and below slow cross-repo doer/E2E coverage.

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
