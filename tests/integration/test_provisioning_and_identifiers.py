"""
Phase 1 live smoke tests for SignifyPy integration coverage.
"""

from __future__ import annotations

import pytest
from .constants import QVI_SCHEMA_SAID, TEST_WITNESS_AIDS
from .helpers import (
    additional_schema_oobis,
    alias,
    contact_aliases,
    create_identifier,
    list_key_states,
    resolve_agent_oobi,
    resolve_oobi,
    resolve_schema_oobi,
    schema_oobi,
    rotate_identifier,
    wait_for_contact_alias,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_provision_agent_and_connect(client_factory):
    """Prove the default bootstrap path yields a usable delegated agent/client pair.

    This is the smallest believable live-stack contract for the SignifyPy
    client: boot the remote agent through KERIA, connect the local controller,
    and confirm the controller-to-agent delegation relationship is fully wired.
    """
    # This is the minimum believable client bootstrap: boot the remote agent,
    # connect, and verify the delegated agent/controller relationship is live.
    client = client_factory()

    assert client.controller == client.ctrl.pre
    assert client.agent.pre
    assert client.agent.pre != client.controller
    assert client.agent.delpre == client.controller
    assert client._integration_boot_response["i"] == client.agent.pre
    assert client._integration_boot_response["d"] == client.agent.said
    assert client.session is not None
    assert client.session.auth is not None


def test_manual_agent_boot_and_connect(client_factory):
    """Lock down the manual boot path used by the old `init_agent.py` workflow.

    The maintained contract here is not just "manual boot works", but "manual
    boot lands in the same connected delegated-agent state as the default
    client-managed boot path."
    """
    # This absorbs the old `init_agent.py` manual-boot path without requiring
    # an operator to paste an inception event into a terminal.
    client = client_factory(passcode="manualbootpath0000001", boot_mode="manual")

    assert client.controller == client.ctrl.pre
    assert client.agent.pre
    assert client.agent.delpre == client.controller
    assert client._integration_boot_response["i"] == client.agent.pre
    assert client._integration_boot_response["d"] == client.agent.said
    assert client.session is not None


def test_agent_config_read_path(client_factory):
    """Prove the client exposes the stack-local `/config` read path after connect."""
    client = client_factory()

    config = client.config().get()

    assert config == {"iurls": client._integration_live_stack["witness_config_iurls"]}


def test_single_sig_identifier_lifecycle_smoke(client_factory):
    """Prove one plain single-sig identifier can be created, listed, and read back.

    This test stays intentionally narrow so later failures in rotation, OOBI,
    or credential flows do not blur the contract for baseline identifier
    persistence and read-path behavior.
    """
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


def test_identifier_rename_update_compatibility(client_factory):
    """Prove TS-style identifier rename works without dropping the Python wrappers."""
    client = client_factory()
    name = alias("rename")
    renamed_name = alias("renamed")

    hab = create_identifier(client, name, wits=[], add_end_role=False)
    renamed = client.identifiers().update(name, {"name": renamed_name})
    fetched = client.identifiers().get(renamed_name)
    identifiers = client.identifiers().list()
    names = {aid["name"] for aid in identifiers["aids"]}

    assert hab["name"] == name
    assert renamed["name"] == renamed_name
    assert fetched["name"] == renamed_name
    assert fetched["prefix"] == hab["prefix"]
    assert renamed_name in names


def test_schema_oobi_resolution_smoke(client_factory):
    """Prove schema OOBI resolution works against the stack-local vLEI server.

    This is the first OOBI read-path contract because it avoids the extra
    moving parts of identifier endpoint publication while still proving that
    SignifyPy can resolve external schema metadata through the live stack.
    """
    # Use the vLEI schema OOBI as the first OOBI smoke case because it is
    # stable in the local stack and does not require extra endpoint wiring on a
    # newly created identifier.
    client = client_factory()

    result = resolve_schema_oobi(client, QVI_SCHEMA_SAID)
    schema = client.schemas().get(QVI_SCHEMA_SAID)
    schemas = client.schemas().list()
    schema_saids = {entry["$id"] for entry in schemas}

    assert result["done"] is True
    assert result["metadata"]["oobi"] == schema_oobi(client, QVI_SCHEMA_SAID)
    assert schema["$id"] == QVI_SCHEMA_SAID
    assert QVI_SCHEMA_SAID in schema_saids

    for alias_name, oobi in additional_schema_oobis(client).items():
        extra = resolve_oobi(client, oobi, alias=alias_name)
        assert extra["done"] is True
        assert extra["metadata"]["oobi"] == oobi


def test_witnessed_identifier_agent_oobi_resolution(client_factory):
    """Lock down the witness-backed agent OOBI publication sequence Phase 2 needs.

    The real contract is the ordering: witness-backed inception first, then
    group/agent end-role publication, then third-party OOBI resolution. This
    keeps later OOBI-heavy workflows honest about what has to exist before an
    agent OOBI becomes queryable and resolvable.
    """
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


def test_contact_and_key_state_read_paths(client_factory):
    """Replace the old contact/key-state listing scripts with live read assertions.

    After a real OOBI exchange, both participants should expose the peer in the
    contact list and should be able to read the peer's key state through the
    maintained SignifyPy wrapper surfaces.
    """
    # This replaces the old `list_contacts.py` and `list_kevers.py` scripts
    # with assertions on the same observable state after a real OOBI exchange.
    client_a = client_factory()
    client_b = client_factory()
    name_a = alias("contact-a")
    name_b = alias("contact-b")

    hab_a = create_identifier(client_a, name_a, wits=TEST_WITNESS_AIDS)
    hab_b = create_identifier(client_b, name_b, wits=TEST_WITNESS_AIDS)
    resolve_agent_oobi(client_a, name_a, client_b, alias=name_a)
    resolve_agent_oobi(client_b, name_b, client_a, alias=name_b)

    wait_for_contact_alias(client_a, name_b)
    wait_for_contact_alias(client_b, name_a)
    states_a = list_key_states(client_a, [hab_b["prefix"]])
    states_b = list_key_states(client_b, [hab_a["prefix"]])

    assert name_b in contact_aliases(client_a)
    assert name_a in contact_aliases(client_b)
    assert states_a[0]["i"] == hab_b["prefix"]
    assert states_b[0]["i"] == hab_a["prefix"]
    assert states_a[0]["b"] == TEST_WITNESS_AIDS
    assert states_b[0]["b"] == TEST_WITNESS_AIDS


def test_contact_management_read_and_update_paths(client_factory):
    """Prove the maintained contact CRUD read/update surfaces over a real contact.

    This test exists so maintainers can change contact wrapper internals
    without losing the observable contract for `list()`, `get(...)`, and
    `update(...)` after a real OOBI-backed contact relationship exists.
    """
    # This locks down the modern contact wrapper shape after OOBI exchange:
    # raw list(), get(prefix), and update(prefix, info).
    client_a = client_factory()
    client_b = client_factory()
    name_a = alias("contact-manage-a")
    name_b = alias("contact-manage-b")

    hab_a = create_identifier(client_a, name_a, wits=TEST_WITNESS_AIDS)
    hab_b = create_identifier(client_b, name_b, wits=TEST_WITNESS_AIDS)
    resolve_agent_oobi(client_a, name_a, client_b, alias=name_a)
    resolve_agent_oobi(client_b, name_b, client_a, alias=name_b)

    wait_for_contact_alias(client_a, name_b)
    wait_for_contact_alias(client_b, name_a)

    contacts = client_a.contacts().list()
    contact = client_a.contacts().get(hab_b["prefix"])
    assert any(entry["id"] == hab_b["prefix"] for entry in contacts)
    assert contact["id"] == hab_b["prefix"]
    assert contact["alias"] == name_b

    updated = client_a.contacts().update(
        hab_b["prefix"],
        {"company": "GLEIF", "location": "Denver"},
    )
    reread = client_a.contacts().get(hab_b["prefix"])

    assert updated["id"] == hab_b["prefix"]
    assert reread["company"] == "GLEIF"
    assert reread["location"] == "Denver"
    assert reread["alias"] == name_b


def test_single_sig_rotation_smoke(client_factory):
    """Keep one small rotation contract separate from the heavier OOBI workflows.

    The purpose is to prove sequence/digest advancement on the same identifier
    prefix without mixing in witness or multisig complexity.
    """
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
    """Prove the smallest useful self-issued credential flow against the live stack.

    This covers the minimum issuance contract for SignifyPy: create issuer,
    create registry, resolve schema, issue one credential, and verify the
    resulting record can be listed and exported through maintained read paths.
    """
    # This locks down the smallest useful credential workflow in SignifyPy:
    # identifier -> registry -> schema resolution -> issuance -> query/export.
    # It is intentionally self-issued so Phase 1 can verify the issuance path
    # without depending on IPEX exchange flows yet.
    client = client_factory()

    issuer_name = alias("issuer")
    registry_name = alias("registry")

    issuer_hab = create_identifier(client, issuer_name, wits=[])
    resolve_schema_oobi(client, QVI_SCHEMA_SAID)

    registry_result = client.registries().create(issuer_name, registry_name)
    wait_for_operation(client, registry_result.op())
    # Registry inception anchors itself with an interaction event, so the
    # identifier state must be reloaded before building the next credential
    # issuance anchor.
    issuer_hab = client.identifiers().get(issuer_name)
    registry = client.registries().get(issuer_name, registry_name)
    assert registry["name"] == registry_name

    data = {"LEI": "5493001KJTIIGC8Y1R17"}
    issue_result = client.credentials().issue(
        issuer_name,
        registry_name,
        data=data,
        schema=QVI_SCHEMA_SAID,
        recipient=issuer_hab["prefix"],
    )
    wait_for_operation(client, issue_result.op())
    creder = issue_result.acdc

    credentials = client.credentials().list()
    credential = next(entry for entry in credentials if entry["sad"]["d"] == creder.said)
    exported = client.credentials().export(creder.said)

    assert credential["sad"]["d"] == creder.said
    assert credential["sad"]["i"] == issuer_hab["prefix"]
    assert credential["sad"]["a"]["i"] == issuer_hab["prefix"]
    assert credential["sad"]["s"] == QVI_SCHEMA_SAID
    assert exported
