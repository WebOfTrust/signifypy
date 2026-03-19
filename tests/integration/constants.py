"""Shared constants for the live SignifyPy integration harness.

These values intentionally track the local sibling-repo demo topology rather
than abstract "some witnesses somewhere." When one of these constants changes,
the harness config written in `conftest.py` and the OOBI expectations in the
tests need to stay in sync.
"""

KERIA_ADMIN_URL = "http://127.0.0.1:3901"
KERIA_AGENT_URL = "http://127.0.0.1:3902"
KERIA_BOOT_URL = "http://127.0.0.1:3903"
VLEI_SCHEMA_URL = "http://127.0.0.1:7723"

SCHEMA_SAID = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
SCHEMA_OOBI = f"{VLEI_SCHEMA_URL}/oobi/{SCHEMA_SAID}"

WITNESS_AIDS = [
    "BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha",
    "BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM",
    "BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX",
]

# These witness identities are the canonical SignifyTS / witness-demo fixture.
# The live SignifyPy harness must launch witnesses that match these AIDs or the
# published witness OOBIs will describe a different topology than the tests.
WITNESS_CONFIG_IURLS = [
    f"http://127.0.0.1:5642/oobi/{WITNESS_AIDS[0]}/controller?name=Wan&tag=witness",
    f"http://127.0.0.1:5643/oobi/{WITNESS_AIDS[1]}/controller?name=Wil&tag=witness",
    f"http://127.0.0.1:5644/oobi/{WITNESS_AIDS[2]}/controller?name=Wes&tag=witness",
]

WITNESS_OOBIS = list(WITNESS_CONFIG_IURLS)

# Use a single witness for most live scenarios so OOBI-heavy workflows stay
# cheaper and less fragile, while still keeping a witnessed path in coverage.
# Tests that care about witness-count-specific behavior should opt into the full
# `WITNESS_AIDS` list explicitly instead of assuming this reduced default.
TEST_WITNESS_AIDS = [WITNESS_AIDS[0]]
