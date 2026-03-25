"""Stable identities for the SignifyPy live integration harness.

Runtime ports, URLs, and OOBIs are generated per stack instance in
`tests/integration/topology.py`. This module only keeps the stable identifiers
that do not change when the harness runs in parallel.
"""

QVI_SCHEMA_SAID = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
ADDITIONAL_SCHEMA_OOBI_SAIDS = {
    "legal-entity": "ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY",
    "ecr-auth": "EH6ekLjSr8V32WyFbGe1zXjTzFs9PkTYmupJ9H65O14g",
    "ecr": "EEy9PkikFcANV1l7EHukCeXqrzT1hNZjGlUk7wuMO5jw",
}

WITNESS_AIDS = [
    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX",
]

# Use a single witness for most live scenarios so OOBI-heavy workflows stay
# cheaper and less fragile, while still keeping a witnessed path in coverage.
# Tests that care about witness-count-specific behavior should opt into the full
# `WITNESS_AIDS` list explicitly instead of assuming this reduced default.
TEST_WITNESS_AIDS = [WITNESS_AIDS[0]]
