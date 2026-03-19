"""
Phase 1 live smoke tests for SignifyPy integration coverage.
"""

from __future__ import annotations

import pytest
from keri.help import helping

from .constants import SCHEMA_OOBI, SCHEMA_SAID, TEST_WITNESS_AIDS
from .helpers import (
    alias,
    create_identifier,
    resolve_agent_oobi,
    resolve_oobi,
    rotate_identifier,
    wait_for_contact_alias,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_provision_agent_and_connect(client_factory):
    # This is the minimum believable client bootstrap: boot the remote agent,
    # connect, and verify the delegated agent/controller relationship is live.
    client = client_factory()

    assert client.controller == client.ctrl.pre
    assert client.agent.pre
    assert client.agent.pre != client.controller
    assert client.agent.delpre == client.controller
    assert client.session is not None
    assert client.session.auth is not None


def test_single_sig_identifier_lifecycle_smoke(client_factory):
    # Keep the first lifecycle check intentionally narrow: create a plain
    # single-sig identifier and prove it is persisted and queryable.
    client = client_factory()
    name = alias("singlesig")

    hab = create_identifier(client, name, wits=[])
    fetched = client.identifiers().get(name)

    identifiers = client.identifiers().list()
    names = {aid["name"] for aid in identifiers["aids"]}

    assert name in names
    assert hab["name"] == name
    assert hab["prefix"]
    assert hab["state"]["s"] == "0"
    assert hab["state"]["b"] == []
    assert fetched["prefix"] == hab["prefix"]


def test_schema_oobi_resolution_smoke(client_factory):
    # Use the vLEI schema OOBI as the first OOBI smoke case because it is
    # stable in the local stack and does not require extra endpoint wiring on a
    # newly created identifier.
    client = client_factory()

    result = resolve_oobi(client, SCHEMA_OOBI, alias="schema")

    assert result["done"] is True
    assert result["metadata"]["oobi"] == SCHEMA_OOBI


def test_witnessed_identifier_agent_oobi_resolution(client_factory):
    # This scenario exists to lock down the exact OOBI publication sequence the
    # rest of Phase 2 depends on:
    # 1. witness-backed identifier inception
    # 2. agent end-role publication
    # 3. agent OOBI resolution from another client
    client_a = client_factory()
    client_b = client_factory()
    name_a = alias("wit-a")
    name_b = alias("wit-b")

    hab_a = create_identifier(client_a, name_a, wits=TEST_WITNESS_AIDS)
    hab_b = create_identifier(client_b, name_b, wits=TEST_WITNESS_AIDS)
    resolved_a = resolve_agent_oobi(client_a, name_a, client_b, alias=name_a)
    resolved_b = resolve_agent_oobi(client_b, name_b, client_a, alias=name_b)
    oobis_a = client_a.oobis().get(name_a, role="agent")["oobis"]
    oobis_b = client_b.oobis().get(name_b, role="agent")["oobis"]
    contact_a = wait_for_contact_alias(client_a, name_b)
    contact_b = wait_for_contact_alias(client_b, name_a)

    assert resolved_a["done"] is True
    assert resolved_b["done"] is True
    assert hab_a["prefix"]
    assert hab_b["prefix"]
    assert hab_a["state"]["b"] == TEST_WITNESS_AIDS
    assert hab_b["state"]["b"] == TEST_WITNESS_AIDS
    assert oobis_a
    assert oobis_b
    assert contact_a["alias"] == name_b
    assert contact_a["id"] == hab_b["prefix"]
    assert contact_b["alias"] == name_a
    assert contact_b["id"] == hab_a["prefix"]


def test_single_sig_rotation_smoke(client_factory):
    # Keep rotation coverage intentionally small here: one create, one rotate,
    # then assert sequence-number advancement on the same prefix.
    client = client_factory()
    name = alias("rot")

    created = create_identifier(client, name, wits=[])
    rotated = rotate_identifier(client, name)

    assert created["prefix"] == rotated["prefix"]
    assert int(rotated["state"]["s"], 16) == 1
    assert rotated["state"]["d"] != created["state"]["d"]


def test_credential_issue_smoke(client_factory):
    # This locks down the smallest useful credential workflow in SignifyPy:
    # identifier -> registry -> schema resolution -> issuance -> query/export.
    # It is intentionally self-issued so Phase 1 can verify the issuance path
    # without depending on IPEX exchange flows yet.
    client = client_factory()

    issuer_name = alias("issuer")
    registry_name = alias("registry")

    issuer_hab = create_identifier(client, issuer_name, wits=[])
    resolve_oobi(client, SCHEMA_OOBI, alias="schema")

    _, _, _, registry_op = client.registries().create(issuer_hab, registry_name)
    wait_for_operation(client, registry_op)
    # Registry inception anchors itself with an interaction event, so the
    # identifier state must be reloaded before building the next credential
    # issuance anchor.
    issuer_hab = client.identifiers().get(issuer_name)
    registry = client.registries().get(issuer_name, registry_name)
    assert registry["name"] == registry_name

    data = {"LEI": "5493001KJTIIGC8Y1R17"}
    creder, _, _, _, op = client.credentials().create(
        issuer_hab,
        registry=registry,
        data=data,
        schema=SCHEMA_SAID,
        recipient=issuer_hab["prefix"],
        timestamp=helping.nowIso8601(),
    )
    wait_for_operation(client, op)

    credentials = client.credentials().list()
    credential = next(entry for entry in credentials if entry["sad"]["d"] == creder.said)
    exported = client.credentials().export(creder.said)

    assert credential["sad"]["d"] == creder.said
    assert credential["sad"]["i"] == issuer_hab["prefix"]
    assert credential["sad"]["a"]["i"] == issuer_hab["prefix"]
    assert credential["sad"]["s"] == SCHEMA_SAID
    assert exported
