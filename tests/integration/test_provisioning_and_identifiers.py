"""
Phase 1 live smoke tests for SignifyPy integration coverage.
"""

from __future__ import annotations

import secrets
import string
import time

import pytest
from keri.core import serdering
from keri.core.coring import Tiers
from keri.help import helping

from signify.app.clienting import SignifyClient


pytestmark = pytest.mark.integration

SCHEMA_SAID = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
SCHEMA_OOBI = f"http://127.0.0.1:7723/oobi/{SCHEMA_SAID}"


def _random_passcode() -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(21))


def _alias(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(4)}"


def _connect_client(live_stack) -> SignifyClient:
    # Each scenario gets a fresh controller/agent pair so failures stay local
    # and the smoke tests do not accidentally depend on prior server state.
    client = SignifyClient(
        passcode=_random_passcode(),
        tier=Tiers.low,
        url=live_stack["keria_admin_url"],
        boot_url=live_stack["keria_boot_url"],
    )
    body = client.boot()
    assert isinstance(body, dict)
    client.connect()
    assert client.agent is not None
    return client


def _wait_for_operation(client: SignifyClient, operation: dict, *, timeout: float = 60.0) -> dict:
    # KERIA exposes long-running work uniformly through operations. Keeping the
    # poll loop here makes the scenario bodies read like workflows instead of
    # transport plumbing.
    deadline = time.time() + timeout
    current = operation
    while not current["done"]:
        if time.time() >= deadline:
            raise TimeoutError(f"timed out waiting for operation {current['name']}")
        time.sleep(0.5)
        current = client.operations().get(current["name"])
    return current


def _create_identifier(client: SignifyClient, name: str) -> dict:
    _, _, op = client.identifiers().create(name, toad="0", wits=[])
    result = _wait_for_operation(client, op)
    serder = serdering.SerderKERI(sad=result["response"])
    assert serder.pre
    client.identifiers().addEndRole(name=name, eid=client.agent.pre)
    return client.identifiers().get(name)


def _resolve_oobi(client: SignifyClient, oobi: str, alias: str | None = None) -> dict:
    op = client.oobis().resolve(oobi, alias=alias)
    return _wait_for_operation(client, op)


def test_provision_agent_and_connect(live_stack):
    # This is the minimum believable client bootstrap: boot the remote agent,
    # connect, and verify the delegated agent/controller relationship is live.
    client = _connect_client(live_stack)

    assert client.controller == client.ctrl.pre
    assert client.agent.pre
    assert client.agent.delpre == client.controller
    assert client.session is not None


def test_single_sig_identifier_lifecycle_smoke(live_stack):
    # Keep the first lifecycle check intentionally narrow: create a plain
    # single-sig identifier and prove it is persisted and queryable.
    client = _connect_client(live_stack)
    name = _alias("singlesig")

    hab = _create_identifier(client, name)

    identifiers = client.identifiers().list()
    names = {aid["name"] for aid in identifiers["aids"]}

    assert name in names
    assert hab["name"] == name
    assert hab["prefix"]
    assert hab["state"]["s"] == "0"


def test_schema_oobi_resolution_smoke(live_stack):
    # Use the vLEI schema OOBI as the first OOBI smoke case because it is
    # stable in the local stack and does not require extra endpoint wiring on a
    # newly created identifier.
    client = _connect_client(live_stack)

    result = _resolve_oobi(client, SCHEMA_OOBI, alias="schema")

    assert result["done"] is True
    assert result["metadata"]["oobi"] == SCHEMA_OOBI


def test_credential_issue_smoke(live_stack):
    # This locks down the smallest useful credential workflow in SignifyPy:
    # identifier -> registry -> schema resolution -> issuance -> query/export.
    # It is intentionally self-issued so Phase 1 can verify the issuance path
    # without depending on IPEX exchange flows yet.
    client = _connect_client(live_stack)

    issuer_name = _alias("issuer")
    registry_name = _alias("registry")

    issuer_hab = _create_identifier(client, issuer_name)
    _resolve_oobi(client, SCHEMA_OOBI, alias="schema")

    _, _, _, registry_op = client.registries().create(issuer_hab, registry_name)
    _wait_for_operation(client, registry_op)
    # Registry inception anchors itself with an interaction event, so the
    # identifier state must be reloaded before building the next credential
    # issuance anchor.
    issuer_hab = client.identifiers().get(issuer_name)
    registry = client.registries().get(issuer_name, registry_name)

    data = {"LEI": "5493001KJTIIGC8Y1R17"}
    creder, _, _, _, op = client.credentials().create(
        issuer_hab,
        registry=registry,
        data=data,
        schema=SCHEMA_SAID,
        recipient=issuer_hab["prefix"],
        timestamp=helping.nowIso8601(),
    )
    _wait_for_operation(client, op)

    credentials = client.credentials().list()
    exported = client.credentials().export(creder.said)

    saids = {entry["sad"]["d"] for entry in credentials}
    assert creder.said in saids
    assert exported
