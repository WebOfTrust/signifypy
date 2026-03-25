"""Live multisig credential workflows that replace the legacy script demos."""

from __future__ import annotations

import pytest
from keri.core import coring
from keri.help import helping

from .constants import QVI_SCHEMA_SAID, TEST_WITNESS_AIDS
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
    revoke_multisig_credential,
    resolve_oobi,
    resolve_schema_oobi,
    wait_for_issued_credential,
    wait_for_multisig_credential_state_convergence,
    wait_for_multisig_registry_convergence,
    wait_for_multisig_request,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def _normalized_registry_state(registry: dict) -> dict:
    """Strip timestamp-only churn before comparing registry state across members."""
    state = dict(registry["state"])
    state.pop("dt", None)
    return state


def _assert_credential_record(
    credential: dict,
    *,
    said: str,
    issuer_prefix: str,
    subject_prefix: str,
    expected_et: str,
    expected_sn: str,
) -> None:
    """Assert the stable credential fields that should match across members."""
    assert credential["sad"]["d"] == said
    assert credential["sad"]["i"] == issuer_prefix
    assert credential["sad"]["a"]["i"] == subject_prefix
    assert credential["sad"]["s"] == QVI_SCHEMA_SAID
    assert credential["status"]["et"] == expected_et
    assert credential["status"]["s"] == expected_sn


def _assert_issuer_query_surface(
    client,
    *,
    issuer_prefix: str,
    subject_prefix: str,
    registry_said: str,
    said: str,
    expected_et: str,
    expected_sn: str,
) -> None:
    """Assert the maintained issuer-side query/read surface for one credential."""
    all_credentials = client.credentials().list()
    issuer_filtered = client.credentials().list(filter={"-i": issuer_prefix})
    schema_filtered = client.credentials().list(filter={"-s": QVI_SCHEMA_SAID})
    subject_filtered = client.credentials().list(filter={"-a-i": subject_prefix})
    combined_filtered = client.credentials().list(
        filter={"-i": issuer_prefix, "-s": QVI_SCHEMA_SAID, "-a-i": subject_prefix}
    )
    fetched = client.credentials().get(said)
    fetched_cesr = client.credentials().get(said, includeCESR=True)
    exported = client.credentials().export(said)
    state = client.credentials().state(registry_said, said)

    assert len(all_credentials) == 1
    assert len(issuer_filtered) == 1
    assert len(schema_filtered) == 1
    assert len(subject_filtered) == 1
    assert len(combined_filtered) == 1
    _assert_credential_record(
        all_credentials[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
    )
    _assert_credential_record(
        issuer_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
    )
    _assert_credential_record(
        schema_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
    )
    _assert_credential_record(
        subject_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
    )
    _assert_credential_record(
        combined_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
    )
    _assert_credential_record(
        fetched,
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
    )
    assert fetched_cesr
    assert exported == fetched_cesr
    assert state["et"] == expected_et
    assert state["s"] == expected_sn


def _assert_holder_read_surface(
    client,
    *,
    issuer_prefix: str,
    holder_prefix: str,
    said: str,
) -> None:
    """Assert the maintained holder-side read surface for one received credential."""
    all_credentials = client.credentials().list()
    holder_filtered = client.credentials().list(filter={"-a-i": holder_prefix})
    fetched = client.credentials().get(said)
    fetched_cesr = client.credentials().get(said, includeCESR=True)
    exported = client.credentials().export(said)

    assert len(all_credentials) == 1
    assert len(holder_filtered) == 1
    _assert_credential_record(
        all_credentials[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=holder_prefix,
        expected_et="iss",
        expected_sn="0",
    )
    _assert_credential_record(
        holder_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=holder_prefix,
        expected_et="iss",
        expected_sn="0",
    )
    _assert_credential_record(
        fetched,
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=holder_prefix,
        expected_et="iss",
        expected_sn="0",
    )
    assert fetched_cesr
    assert exported == fetched_cesr


def test_single_sig_issuer_to_multisig_holder_credential_issue(client_factory):
    """Prove a single issuer can issue to one multisig holder group prefix.

    This is the smallest believable bridge between single-sig issuance and
    multisig receipt: build the holder group honestly, issue to the shared
    group prefix, and assert the issuer can read back the resulting issuance.
    """
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
    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client_a, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client_b, QVI_SCHEMA_SAID)

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
    issued = issuer_client.credentials().list(filter={"-i": issuer["prefix"]})

    assert registry["name"] == registry_name
    assert holder_group_a["prefix"] == holder_group_b["prefix"]
    assert creder.sad["d"] == iserder.ked["i"]
    assert creder.sad["a"]["i"] == holder_group_a["prefix"]
    assert creder.sad["s"] == QVI_SCHEMA_SAID
    assert any(credential["sad"]["d"] == creder.said for credential in issued)


def test_multisig_issuer_to_multisig_holder_credential_issue(client_factory):
    """Lock down the staged `/multisig/vcp` plus `/multisig/iss` follower replay contract.

    The non-obvious contract is that participant B must join the initiator's
    exact embedded proposal payloads rather than reconstructing "equivalent"
    local events. This test exists to make that invariant explicit.
    """
    # This is the canonical SignifyPy replay regression for `/multisig/vcp`
    # plus `/multisig/iss`.
    #
    # Participant A: `issuer_client_a` / `issuer_member_a_name`
    # Participant B: `issuer_client_b` / `issuer_member_b_name`
    #
    # Important mental model:
    # - follower B joins `/multisig/vcp` by reusing A's exact `vcp` and `anc`
    # - follower B joins `/multisig/iss` by reusing A's exact `acdc`, `iss`,
    #   and `anc`
    # - initiator A does not wait for echo notifications after local approval;
    #   the stable contract is operation completion plus semantic convergence
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
    resolve_schema_oobi(issuer_client_a, QVI_SCHEMA_SAID)
    resolve_schema_oobi(issuer_client_b, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client_a, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client_b, QVI_SCHEMA_SAID)

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
    # Both members have to use the same registry nonce or they are not even
    # attempting to converge on the same registry inception event.
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
    # Participant B joins the stored proposal, not a locally reconstructed one.
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
    # Operation completion is necessary but not sufficient; the real contract
    # is that both members can read the same converged registry view.
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
    # The follower must consume the initiator's stored issuance payload so the
    # two members prove they are approving the same credential and TEL anchor.
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
    assert _normalized_registry_state(registry_a) == _normalized_registry_state(registry_b)
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
    _assert_issuer_query_surface(
        issuer_client_a,
        issuer_prefix=issuer_group_a["prefix"],
        subject_prefix=holder_group_a["prefix"],
        registry_said=registry_a["regk"],
        said=creder_a.said,
        expected_et="iss",
        expected_sn="0",
    )
    _assert_issuer_query_surface(
        issuer_client_b,
        issuer_prefix=issuer_group_b["prefix"],
        subject_prefix=holder_group_b["prefix"],
        registry_said=registry_b["regk"],
        said=creder_a.said,
        expected_et="iss",
        expected_sn="0",
    )


def test_multisig_issuer_credential_revocation(client_factory):
    """Lock down the multisig follower replay contract for `/multisig/rev`.

    The holder stays single-sig on purpose: the thing under test is whether the
    second issuer member joins the same revocation proposal and anchor, not
    whether holder-side multisig changes the transport shape.
    """
    # This is the focused `/multisig/rev` replay regression for multisig
    # issuer credential revocation.
    #
    # Participant A: `issuer_client_a` / `issuer_member_a_name`
    # Participant B: `issuer_client_b` / `issuer_member_b_name`
    #
    # The holder is intentionally single-sig because holder-side multisig is
    # irrelevant to the follower replay contract on `/multisig/rev`.
    issuer_client_a = client_factory()
    issuer_client_b = client_factory()
    holder_client = client_factory()

    issuer_member_a_name = alias("issuer-a")
    issuer_member_b_name = alias("issuer-b")
    holder_name = alias("holder")
    issuer_group_name = alias("issuer-group")
    registry_name = alias("registry")

    issuer_member_a = create_identifier(issuer_client_a, issuer_member_a_name, wits=TEST_WITNESS_AIDS)
    issuer_member_b = create_identifier(issuer_client_b, issuer_member_b_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(issuer_client_a, issuer_member_a_name, issuer_client_b, issuer_member_b_name)
    exchange_agent_oobis(issuer_client_a, issuer_member_a_name, holder_client, holder_name)
    resolve_schema_oobi(issuer_client_a, QVI_SCHEMA_SAID)
    resolve_schema_oobi(issuer_client_b, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)

    issuer_group_a, issuer_group_b = create_multisig_group(
        issuer_client_a,
        issuer_member_a_name,
        issuer_client_b,
        issuer_member_b_name,
        issuer_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    issuer_group_oobi = expose_multisig_agent_oobi(
        issuer_client_a,
        issuer_member_a_name,
        issuer_client_b,
        issuer_member_b_name,
        issuer_group_name,
    )
    resolve_oobi(holder_client, issuer_group_oobi, alias=issuer_group_name)

    registry_nonce = coring.randomNonce()
    registry_operation_a, _ = create_multisig_registry(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        registry_name=registry_name,
        nonce=registry_nonce,
        is_initiator=True,
    )
    _, registry_request_b = wait_for_multisig_request(issuer_client_b, "/multisig/vcp")
    # As in the issuance test above, the follower registry creation path has to
    # join the stored proposal, or later revocation coverage becomes ambiguous.
    registry_operation_b, _ = create_multisig_registry(
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

    issue_timestamp = helping.nowIso8601()
    creder_a, _, _, _, credential_operation_a, _ = issue_multisig_credential(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        registry_name=registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
        timestamp=issue_timestamp,
        is_initiator=True,
    )
    _, issuance_request_b = wait_for_multisig_request(issuer_client_b, "/multisig/iss")
    # Stage the credential on both issuer members before attempting revocation
    # so the later `/multisig/rev` replay assertion has a real issued credential
    # to converge on.
    _, _, _, _, credential_operation_b, issuance_request_b = issue_multisig_credential(
        issuer_client_b,
        local_member_name=issuer_member_b_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_a["prefix"]],
        registry_name=registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
        timestamp=issue_timestamp,
        request=issuance_request_b,
    )
    wait_for_operation(issuer_client_a, credential_operation_a)
    wait_for_operation(issuer_client_b, credential_operation_b)
    issued_a = wait_for_issued_credential(issuer_client_a, issuer_group_a["prefix"], creder_a.said)
    issued_b = wait_for_issued_credential(issuer_client_b, issuer_group_b["prefix"], creder_a.said)

    revoke_timestamp = helping.nowIso8601()
    revoke_serder_a, revoke_anc_a, _, revoke_operation_a, _ = revoke_multisig_credential(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        credential_said=creder_a.said,
        timestamp=revoke_timestamp,
        is_initiator=True,
    )
    _, revoke_request_b = wait_for_multisig_request(issuer_client_b, "/multisig/rev")
    # The revocation follower path is the actual regression target: member B
    # must approve the same `rev` plus anchor payload that member A proposed.
    revoke_serder_b, revoke_anc_b, _, revoke_operation_b, revoke_request_b = revoke_multisig_credential(
        issuer_client_b,
        local_member_name=issuer_member_b_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_a["prefix"]],
        credential_said=creder_a.said,
        timestamp=revoke_timestamp,
        request=revoke_request_b,
    )
    wait_for_operation(issuer_client_a, revoke_operation_a)
    wait_for_operation(issuer_client_b, revoke_operation_b)
    revoke_state_a, revoke_state_b = wait_for_multisig_credential_state_convergence(
        issuer_client_a,
        issuer_client_b,
        registry_said=registry_a["regk"],
        credential_said=creder_a.said,
        expected_et="rev",
    )

    # The stored `/multisig/rev` request is the canonical proposal participant
    # B joins. Matching local reconstruction proves both members revoked the
    # same credential with the same anchoring event.
    assert revoke_request_b[0]["exn"]["e"]["rev"] == revoke_serder_a.ked
    assert revoke_request_b[0]["exn"]["e"]["anc"] == revoke_anc_a.ked
    assert revoke_serder_b.ked == revoke_serder_a.ked
    assert revoke_anc_b.ked == revoke_anc_a.ked
    assert issued_a["sad"]["d"] == creder_a.said
    assert issued_b["sad"]["d"] == creder_a.said
    assert registry_a["regk"] == registry_b["regk"]
    fetched_a = issuer_client_a.credentials().get(creder_a.said)
    fetched_b = issuer_client_b.credentials().get(creder_a.said)
    issuer_filtered_a = issuer_client_a.credentials().list(filter={"-i": issuer_group_a["prefix"]})
    issuer_filtered_b = issuer_client_b.credentials().list(filter={"-i": issuer_group_b["prefix"]})
    fetched_cesr_a = issuer_client_a.credentials().get(creder_a.said, includeCESR=True)
    fetched_cesr_b = issuer_client_b.credentials().get(creder_a.said, includeCESR=True)
    exported_a = issuer_client_a.credentials().export(creder_a.said)
    exported_b = issuer_client_b.credentials().export(creder_a.said)
    assert revoke_state_a["et"] == "rev"
    assert revoke_state_b["et"] == "rev"
    _assert_credential_record(
        fetched_a,
        said=creder_a.said,
        issuer_prefix=issuer_group_a["prefix"],
        subject_prefix=holder["prefix"],
        expected_et="rev",
        expected_sn="1",
    )
    _assert_credential_record(
        fetched_b,
        said=creder_a.said,
        issuer_prefix=issuer_group_b["prefix"],
        subject_prefix=holder["prefix"],
        expected_et="rev",
        expected_sn="1",
    )
    assert len(issuer_filtered_a) == 1
    assert len(issuer_filtered_b) == 1
    _assert_credential_record(
        issuer_filtered_a[0],
        said=creder_a.said,
        issuer_prefix=issuer_group_a["prefix"],
        subject_prefix=holder["prefix"],
        expected_et="rev",
        expected_sn="1",
    )
    _assert_credential_record(
        issuer_filtered_b[0],
        said=creder_a.said,
        issuer_prefix=issuer_group_b["prefix"],
        subject_prefix=holder["prefix"],
        expected_et="rev",
        expected_sn="1",
    )
    assert fetched_cesr_a
    assert fetched_cesr_b
    assert exported_a == fetched_cesr_a
    assert exported_b == fetched_cesr_b
