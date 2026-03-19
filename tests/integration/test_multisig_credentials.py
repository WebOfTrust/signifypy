"""Live multisig credential workflows that replace the legacy script demos."""

from __future__ import annotations

import pytest
from keri.core import coring
from keri.help import helping

from .constants import SCHEMA_OOBI, SCHEMA_SAID, TEST_WITNESS_AIDS
from .helpers import (
    alias,
    create_identifier,
    create_multisig_group,
    create_multisig_registry,
    create_registry,
    exchange_agent_oobis,
    expose_multisig_agent_oobi,
    issue_credential,
    issue_multisig_credential,
    resolve_oobi,
    wait_for_issued_credential,
    wait_for_multisig_registry_convergence,
    wait_for_multisig_request,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_single_sig_issuer_to_multisig_holder_credential_issue(client_factory):
    # This replaces the legacy single-issuer-to-multisig-holder scripts with
    # a truthful live contract: build the holder group, issue to the group
    # prefix, and assert the issuer can read the resulting issued credential.
    issuer_client = client_factory()
    holder_client_a = client_factory()
    holder_client_b = client_factory()

    issuer_name = alias("issuer")
    holder_member_a_name = alias("holder-a")
    holder_member_b_name = alias("holder-b")
    holder_group_name = alias("holder-group")
    registry_name = alias("registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder_member_a = create_identifier(holder_client_a, holder_member_a_name, wits=TEST_WITNESS_AIDS)
    holder_member_b = create_identifier(holder_client_b, holder_member_b_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(holder_client_a, holder_member_a_name, holder_client_b, holder_member_b_name)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client_a, holder_member_a_name)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client_b, holder_member_b_name)
    resolve_oobi(issuer_client, SCHEMA_OOBI, alias="schema")
    resolve_oobi(holder_client_a, SCHEMA_OOBI, alias="schema")
    resolve_oobi(holder_client_b, SCHEMA_OOBI, alias="schema")

    holder_group_a, holder_group_b = create_multisig_group(
        holder_client_a,
        holder_member_a_name,
        holder_client_b,
        holder_member_b_name,
        holder_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    holder_group_oobi = expose_multisig_agent_oobi(
        holder_client_a,
        holder_member_a_name,
        holder_client_b,
        holder_member_b_name,
        holder_group_name,
    )
    resolve_oobi(issuer_client, holder_group_oobi, alias=holder_group_name)

    _, registry = create_registry(issuer_client, issuer_name, registry_name)
    creder, iserder, _, _ = issue_credential(
        issuer_client,
        issuer_name=issuer_name,
        registry_name=registry_name,
        recipient=holder_group_a["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
    )
    issued = issuer_client.credentials().list(filtr={"-i": issuer["prefix"]})

    assert registry["name"] == registry_name
    assert holder_group_a["prefix"] == holder_group_b["prefix"]
    assert creder.sad["d"] == iserder.ked["i"]
    assert creder.sad["a"]["i"] == holder_group_a["prefix"]
    assert creder.sad["s"] == SCHEMA_SAID
    assert any(credential["sad"]["d"] == creder.said for credential in issued)


def test_multisig_issuer_to_multisig_holder_credential_issue(client_factory):
    # This replaces the old multisig issuer scripts with the stable contract we
    # can protect today: group registry inception plus converged credential
    # issuance from both issuer members to one holder-group recipient prefix.
    issuer_client_a = client_factory()
    issuer_client_b = client_factory()
    holder_client_a = client_factory()
    holder_client_b = client_factory()

    issuer_member_a_name = alias("issuer-a")
    issuer_member_b_name = alias("issuer-b")
    holder_member_a_name = alias("holder-a")
    holder_member_b_name = alias("holder-b")
    issuer_group_name = alias("issuer-group")
    holder_group_name = alias("holder-group")
    registry_name = alias("registry")

    issuer_member_a = create_identifier(issuer_client_a, issuer_member_a_name, wits=TEST_WITNESS_AIDS)
    issuer_member_b = create_identifier(issuer_client_b, issuer_member_b_name, wits=TEST_WITNESS_AIDS)
    holder_member_a = create_identifier(holder_client_a, holder_member_a_name, wits=TEST_WITNESS_AIDS)
    holder_member_b = create_identifier(holder_client_b, holder_member_b_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(issuer_client_a, issuer_member_a_name, issuer_client_b, issuer_member_b_name)
    exchange_agent_oobis(holder_client_a, holder_member_a_name, holder_client_b, holder_member_b_name)
    resolve_oobi(issuer_client_a, SCHEMA_OOBI, alias="schema")
    resolve_oobi(issuer_client_b, SCHEMA_OOBI, alias="schema")
    resolve_oobi(holder_client_a, SCHEMA_OOBI, alias="schema")
    resolve_oobi(holder_client_b, SCHEMA_OOBI, alias="schema")

    issuer_group_a, issuer_group_b = create_multisig_group(
        issuer_client_a,
        issuer_member_a_name,
        issuer_client_b,
        issuer_member_b_name,
        issuer_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    holder_group_a, holder_group_b = create_multisig_group(
        holder_client_a,
        holder_member_a_name,
        holder_client_b,
        holder_member_b_name,
        holder_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    issuer_group_oobi = expose_multisig_agent_oobi(
        issuer_client_a,
        issuer_member_a_name,
        issuer_client_b,
        issuer_member_b_name,
        issuer_group_name,
    )
    holder_group_oobi = expose_multisig_agent_oobi(
        holder_client_a,
        holder_member_a_name,
        holder_client_b,
        holder_member_b_name,
        holder_group_name,
    )
    resolve_oobi(issuer_client_a, holder_group_oobi, alias=holder_group_name)
    resolve_oobi(holder_client_a, issuer_group_oobi, alias=issuer_group_name)

    registry_nonce = coring.randomNonce()
    registry_operation_a, registry_meta_a = create_multisig_registry(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        registry_name=registry_name,
        nonce=registry_nonce,
        is_initiator=True,
    )
    _, registry_request_b = wait_for_multisig_request(issuer_client_b, "/multisig/vcp")
    registry_operation_b, registry_meta_b = create_multisig_registry(
        issuer_client_b,
        local_member_name=issuer_member_b_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_a["prefix"]],
        registry_name=registry_name,
        nonce=registry_nonce,
        request=registry_request_b,
    )
    wait_for_operation(issuer_client_a, registry_operation_a)
    wait_for_operation(issuer_client_b, registry_operation_b)
    registry_a, registry_b = wait_for_multisig_registry_convergence(
        issuer_client_a,
        issuer_client_b,
        group_name=issuer_group_name,
        registry_name=registry_name,
    )

    timestamp = helping.nowIso8601()
    creder_a, iserder_a, anc_a, sigs_a, credential_operation_a, _ = issue_multisig_credential(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        registry_name=registry_name,
        recipient=holder_group_a["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
        timestamp=timestamp,
        is_initiator=True,
    )
    _, issuance_request_b = wait_for_multisig_request(issuer_client_b, "/multisig/iss")
    creder_b, _, _, _, credential_operation_b, issuance_request_b = issue_multisig_credential(
        issuer_client_b,
        local_member_name=issuer_member_b_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_a["prefix"]],
        registry_name=registry_name,
        recipient=holder_group_a["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
        timestamp=timestamp,
        request=issuance_request_b,
    )
    wait_for_operation(issuer_client_a, credential_operation_a)
    wait_for_operation(issuer_client_b, credential_operation_b)
    issued_a = wait_for_issued_credential(issuer_client_a, issuer_group_a["prefix"], creder_a.said)
    issued_b = wait_for_issued_credential(issuer_client_b, issuer_group_b["prefix"], creder_a.said)

    assert registry_meta_a["name"] == registry_name
    assert registry_meta_b["name"] == registry_name
    assert registry_meta_a["group_prefix"] == issuer_group_a["prefix"]
    assert registry_meta_b["group_prefix"] == issuer_group_b["prefix"]
    assert registry_meta_a["vcp_said"] == registry_meta_b["vcp_said"]
    # Multisig registry join must reuse the initiator's exact embedded VCP and
    # anchoring interaction event so every member converges on one anchor SAID.
    assert registry_request_b[0]["exn"]["e"]["vcp"] == registry_meta_a["vcp"].ked
    assert registry_request_b[0]["exn"]["e"]["anc"] == registry_meta_a["anc"].ked
    assert issuer_group_a["prefix"] == issuer_group_b["prefix"]
    assert holder_group_a["prefix"] == holder_group_b["prefix"]
    assert registry_a["name"] == registry_name
    assert registry_b["name"] == registry_name
    assert registry_a["regk"] == registry_b["regk"]
    assert registry_a["state"] == registry_b["state"]
    # The same "mirror the initiator payload" rule applies to multisig
    # issuance: all members must join the same credential, issuance TEL event,
    # and anchoring interaction event.
    assert issuance_request_b[0]["exn"]["e"]["acdc"] == creder_a.sad
    assert issuance_request_b[0]["exn"]["e"]["iss"] == iserder_a.sad
    assert issuance_request_b[0]["exn"]["e"]["anc"] == anc_a.sad
    assert creder_a.said == creder_b.said
    assert creder_a.sad["d"] == iserder_a.ked["i"]
    assert creder_a.sad["i"] == issuer_group_a["prefix"]
    assert creder_a.sad["a"]["i"] == holder_group_a["prefix"]
    assert issued_a["sad"]["d"] == creder_a.said
    assert issued_b["sad"]["d"] == creder_a.said
