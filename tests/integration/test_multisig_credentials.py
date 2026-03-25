"""Live multisig credential and IPEX workflow coverage.

These tests are intentionally more narrative than most unit tests because the
main failure modes are protocol-shape mistakes: wrong OOBIs, wrong proposal
replay payloads, wrong grant/admit ordering, or asserting on notifications
instead of the stored exchanges and credentials they point to.
"""

from __future__ import annotations

import pytest
from keri.core import coring
from keri.help import helping

from .constants import ADDITIONAL_SCHEMA_OOBI_SAIDS, QVI_SCHEMA_SAID, TEST_WITNESS_AIDS
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
    send_credential_grant,
    send_multisig_credential_grant,
    submit_admit,
    submit_multisig_admit,
    wait_for_credential,
    wait_for_exchange,
    wait_for_filtered_credential,
    wait_for_issued_credential,
    wait_for_multisig_credential_state_convergence,
    wait_for_multisig_received_credential,
    wait_for_multisig_registry_convergence,
    wait_for_multisig_request,
    wait_for_notification,
    wait_for_notification_any,
    wait_for_operation,
)


pytestmark = pytest.mark.integration

LE_USAGE_DISCLAIMER = (
    "Usage of a valid, unexpired, and non-revoked vLEI Credential, as defined "
    "in the associated Ecosystem Governance Framework, does not assert that "
    "the Legal Entity is trustworthy, honest, reputable in its business "
    "dealings, safe to do business with, or compliant with any laws or that "
    "an implied or expressly intended purpose will be fulfilled."
)

LE_ISSUANCE_DISCLAIMER = (
    "All information in a valid, unexpired, and non-revoked vLEI Credential, "
    "as defined in the associated Ecosystem Governance Framework, is accurate "
    "as of the date the validation process was complete. The vLEI Credential "
    "has been issued to the legal entity or person named in the vLEI "
    "Credential as the subject; and the qualified vLEI Issuer exercised "
    "reasonable care to perform the validation process set forth in the vLEI "
    "Ecosystem Governance Framework."
)

LE_DATA = {"LEI": "875500ELOZEL05BVXV37"}
OOR_DATA = {
    "LEI": LE_DATA["LEI"],
    "personLegalName": "John Doe",
    "officialRole": "HR Manager",
}


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
    schema_said: str = QVI_SCHEMA_SAID,
) -> None:
    """Assert the stable credential fields that should match across members."""
    assert credential["sad"]["d"] == said
    assert credential["sad"]["i"] == issuer_prefix
    assert credential["sad"]["a"]["i"] == subject_prefix
    assert credential["sad"]["s"] == schema_said
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
    schema_said: str = QVI_SCHEMA_SAID,
) -> None:
    """Assert the maintained issuer-side query/read surface for one credential."""
    all_credentials = client.credentials().list()
    issuer_filtered = client.credentials().list(filter={"-i": issuer_prefix})
    schema_filtered = client.credentials().list(filter={"-s": schema_said})
    subject_filtered = client.credentials().list(filter={"-a-i": subject_prefix})
    combined_filtered = client.credentials().list(
        filter={"-i": issuer_prefix, "-s": schema_said, "-a-i": subject_prefix}
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
        schema_said=schema_said,
    )
    _assert_credential_record(
        issuer_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
        schema_said=schema_said,
    )
    _assert_credential_record(
        schema_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
        schema_said=schema_said,
    )
    _assert_credential_record(
        subject_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
        schema_said=schema_said,
    )
    _assert_credential_record(
        combined_filtered[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
        schema_said=schema_said,
    )
    _assert_credential_record(
        fetched,
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=subject_prefix,
        expected_et=expected_et,
        expected_sn=expected_sn,
        schema_said=schema_said,
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
    schema_said: str = QVI_SCHEMA_SAID,
    assert_subject_filter: bool = True,
) -> None:
    """Assert the maintained holder-side read surface for one received credential."""
    all_credentials = client.credentials().list()
    fetched = client.credentials().get(said)
    fetched_cesr = client.credentials().get(said, includeCESR=True)
    exported = client.credentials().export(said)
    matching_all = [
        credential for credential in all_credentials if credential["sad"]["d"] == said
    ]
    matching_holder = (
        wait_for_filtered_credential(client, said, filter={"-a-i": holder_prefix})
        if assert_subject_filter
        else None
    )

    assert len(matching_all) == 1
    _assert_credential_record(
        matching_all[0],
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=holder_prefix,
        expected_et="iss",
        expected_sn="0",
        schema_said=schema_said,
    )
    if assert_subject_filter:
        _assert_credential_record(
            matching_holder,
            said=said,
            issuer_prefix=issuer_prefix,
            subject_prefix=holder_prefix,
            expected_et="iss",
            expected_sn="0",
            schema_said=schema_said,
        )
    _assert_credential_record(
        fetched,
        said=said,
        issuer_prefix=issuer_prefix,
        subject_prefix=holder_prefix,
        expected_et="iss",
        expected_sn="0",
        schema_said=schema_said,
    )
    assert fetched_cesr
    assert exported == fetched_cesr


def _resolve_schema_set(client, *schema_saids: str) -> None:
    """Resolve a small explicit set of schema OOBIs for one participant."""
    for schema_said in schema_saids:
        resolve_schema_oobi(client, schema_said)


def _le_rules() -> dict:
    """Build the shared rules payload used by LE/OOR-family credentials."""
    return coring.Saider.saidify(
        sad={
            "d": "",
            "usageDisclaimer": {"l": LE_USAGE_DISCLAIMER},
            "issuanceDisclaimer": {"l": LE_ISSUANCE_DISCLAIMER},
        }
    )[1]


def _source_edges(label: str, credential, *, operator: str | None = None) -> dict:
    """Build a saidified source-edge payload for one parent credential."""
    sad = credential["sad"] if isinstance(credential, dict) else credential.sad
    edge = {"n": sad["d"], "s": sad["s"]}
    if operator is not None:
        edge["o"] = operator
    return coring.Saider.saidify(sad={"d": "", label: edge})[1]


def _assert_filtered_contains(client, *, schema_said: str, subject_prefix: str, said: str) -> None:
    """Assert one issuer-side filtered list contains the expected credential SAID."""
    filtered = client.credentials().list(filter={"-s": schema_said, "-a-i": subject_prefix})
    assert any(credential["sad"]["d"] == said for credential in filtered)


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


def test_multisig_issuer_to_multisig_holder_credential_presentation(client_factory):
    """Prove multisig grant/admit stores the credential on both holder members.

    This is the core holder-side parity test for multisig IPEX. The important
    contract is:
    - both issuer members send the same grant wave
    - both grant operations finish before either holder admits
    - both holder members converge on one admit wave
    - only then should stored-credential reads succeed on both holder members
    """
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
    _resolve_schema_set(issuer_client_a, QVI_SCHEMA_SAID)
    _resolve_schema_set(issuer_client_b, QVI_SCHEMA_SAID)
    _resolve_schema_set(holder_client_a, QVI_SCHEMA_SAID)
    _resolve_schema_set(holder_client_b, QVI_SCHEMA_SAID)

    # Stage 1: build issuer and holder multisig groups and exchange the base
    # multisig OOBIs, not member-specific `/agent/...` OOBIs.
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
    resolve_oobi(issuer_client_b, holder_group_oobi, alias=holder_group_name)
    resolve_oobi(holder_client_a, issuer_group_oobi, alias=issuer_group_name)
    resolve_oobi(holder_client_b, issuer_group_oobi, alias=issuer_group_name)

    # Stage 2: converge the issuer registry on both issuer members before
    # attempting any credential issuance.
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

    # Stage 3: issue the credential through `/multisig/iss` using one shared
    # timestamp so both members sign the same issuance payload.
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
    creder_b, iserder_b, anc_b, sigs_b, credential_operation_b, _ = issue_multisig_credential(
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
    wait_for_issued_credential(issuer_client_a, issuer_group_a["prefix"], creder_a.said)
    wait_for_issued_credential(issuer_client_b, issuer_group_b["prefix"], creder_a.said)

    # Stage 4: complete the full grant wave before either holder starts the
    # admit wave. This mirrors the working TS/KLI contract.
    grant_timestamp = helping.nowIso8601()
    grant_operation_a = send_multisig_credential_grant(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        recipient=holder_group_a["prefix"],
        creder=creder_a,
        iserder=iserder_a,
        anc=anc_a,
        sigs=sigs_a,
        timestamp=grant_timestamp,
        is_initiator=True,
    )
    grant_operation_b = send_multisig_credential_grant(
        issuer_client_b,
        local_member_name=issuer_member_b_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_a["prefix"]],
        recipient=holder_group_a["prefix"],
        creder=creder_b,
        iserder=iserder_b,
        anc=anc_b,
        sigs=sigs_b,
        timestamp=grant_timestamp,
    )
    wait_for_operation(issuer_client_a, grant_operation_a)
    wait_for_operation(issuer_client_b, grant_operation_b)

    # Stage 5: admit from both holder members using the same stored grant SAID
    # and one shared admit timestamp.
    grant_client_index, grant_note = wait_for_notification_any(
        [holder_client_a, holder_client_b],
        "/exn/ipex/grant",
    )
    grant_said = grant_note["a"]["d"]
    admit_timestamp = helping.nowIso8601()
    if grant_client_index == 0:
        first_holder_client, first_holder_name, first_peer_prefixes = (
            holder_client_a,
            holder_member_a_name,
            [holder_member_b["prefix"]],
        )
        second_holder_client, second_holder_name, second_peer_prefixes = (
            holder_client_b,
            holder_member_b_name,
            [holder_member_a["prefix"]],
        )
    else:
        first_holder_client, first_holder_name, first_peer_prefixes = (
            holder_client_b,
            holder_member_b_name,
            [holder_member_a["prefix"]],
        )
        second_holder_client, second_holder_name, second_peer_prefixes = (
            holder_client_a,
            holder_member_a_name,
            [holder_member_b["prefix"]],
        )
    first_admit_operation = submit_multisig_admit(
        first_holder_client,
        local_member_name=first_holder_name,
        group_name=holder_group_name,
        other_member_prefixes=first_peer_prefixes,
        issuer_prefix=issuer_group_a["prefix"],
        grant_said=grant_said,
        timestamp=admit_timestamp,
    )
    wait_for_exchange(second_holder_client, grant_said, expected_route="/ipex/grant")
    second_admit_operation = submit_multisig_admit(
        second_holder_client,
        local_member_name=second_holder_name,
        group_name=holder_group_name,
        other_member_prefixes=second_peer_prefixes,
        issuer_prefix=issuer_group_a["prefix"],
        grant_said=grant_said,
        timestamp=admit_timestamp,
    )
    wait_for_operation(first_holder_client, first_admit_operation)
    wait_for_operation(second_holder_client, second_admit_operation)

    # Stage 6: notifications tell us what to inspect, but stored credentials
    # are the authoritative success signal.
    issuer_admit_note_a = wait_for_notification(issuer_client_a, "/exn/ipex/admit")
    issuer_admit_note_b = wait_for_notification(issuer_client_b, "/exn/ipex/admit")
    assert issuer_admit_note_a["a"]["d"] == issuer_admit_note_b["a"]["d"]

    holder_received_a, holder_received_b = wait_for_multisig_received_credential(
        holder_client_a,
        holder_client_b,
        creder_a.said,
    )

    assert registry_a["regk"] == registry_b["regk"]
    assert creder_a.said == creder_b.said
    assert holder_received_a["sad"]["d"] == creder_a.said
    assert holder_received_b["sad"]["d"] == creder_a.said
    _assert_holder_read_surface(
        holder_client_a,
        issuer_prefix=issuer_group_a["prefix"],
        holder_prefix=holder_group_a["prefix"],
        said=creder_a.said,
    )
    _assert_holder_read_surface(
        holder_client_b,
        issuer_prefix=issuer_group_b["prefix"],
        holder_prefix=holder_group_b["prefix"],
        said=creder_a.said,
    )
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


def test_multisig_chained_qvi_le_oor_auth_oor_presentation(client_factory):
    """Prove chained multisig grant/admit flows preserve readable credential chains.

    This is the most complex live credential workflow in the suite, so the
    important shape is worth stating explicitly:
    - GEDA-equivalent group grants QVI to the QVI group
    - QVI group grants LE to the LE group
    - LE group grants OOR Auth back to the QVI group
    - QVI group grants OOR to a single-sig role holder

    Every hop follows the same discipline: shared timestamps per multisig wave,
    finish all grants before any admits, then assert on stored credential
    visibility rather than treating notifications as the final truth.
    """
    geda_client_a = client_factory()
    geda_client_b = client_factory()
    qvi_client_a = client_factory()
    qvi_client_b = client_factory()
    le_client_a = client_factory()
    le_client_b = client_factory()
    role_client = client_factory()

    geda_member_a_name = alias("geda-a")
    geda_member_b_name = alias("geda-b")
    qvi_member_a_name = alias("qvi-a")
    qvi_member_b_name = alias("qvi-b")
    le_member_a_name = alias("le-a")
    le_member_b_name = alias("le-b")
    role_holder_name = alias("oor-holder")
    geda_group_name = alias("geda-group")
    qvi_group_name = alias("qvi-group")
    le_group_name = alias("le-group")
    geda_registry_name = alias("geda-registry")
    qvi_registry_name = alias("qvi-registry")
    le_registry_name = alias("le-registry")

    geda_member_a = create_identifier(geda_client_a, geda_member_a_name, wits=TEST_WITNESS_AIDS)
    geda_member_b = create_identifier(geda_client_b, geda_member_b_name, wits=TEST_WITNESS_AIDS)
    qvi_member_a = create_identifier(qvi_client_a, qvi_member_a_name, wits=TEST_WITNESS_AIDS)
    qvi_member_b = create_identifier(qvi_client_b, qvi_member_b_name, wits=TEST_WITNESS_AIDS)
    le_member_a = create_identifier(le_client_a, le_member_a_name, wits=TEST_WITNESS_AIDS)
    le_member_b = create_identifier(le_client_b, le_member_b_name, wits=TEST_WITNESS_AIDS)
    role_holder = create_identifier(role_client, role_holder_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(geda_client_a, geda_member_a_name, geda_client_b, geda_member_b_name)
    exchange_agent_oobis(qvi_client_a, qvi_member_a_name, qvi_client_b, qvi_member_b_name)
    exchange_agent_oobis(le_client_a, le_member_a_name, le_client_b, le_member_b_name)
    exchange_agent_oobis(qvi_client_a, qvi_member_a_name, role_client, role_holder_name)
    exchange_agent_oobis(qvi_client_b, qvi_member_b_name, role_client, role_holder_name)
    _resolve_schema_set(geda_client_a, QVI_SCHEMA_SAID)
    _resolve_schema_set(geda_client_b, QVI_SCHEMA_SAID)
    _resolve_schema_set(
        qvi_client_a,
        QVI_SCHEMA_SAID,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
    )
    _resolve_schema_set(
        qvi_client_b,
        QVI_SCHEMA_SAID,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
    )
    _resolve_schema_set(
        le_client_a,
        QVI_SCHEMA_SAID,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
    )
    _resolve_schema_set(
        le_client_b,
        QVI_SCHEMA_SAID,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
    )
    _resolve_schema_set(
        role_client,
        QVI_SCHEMA_SAID,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
        ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
    )

    # Stage 1: build the three multisig organizations and expose only the base
    # multisig OOBIs that peers should resolve.
    geda_group_a, geda_group_b = create_multisig_group(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    qvi_group_a, qvi_group_b = create_multisig_group(
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    le_group_a, le_group_b = create_multisig_group(
        le_client_a,
        le_member_a_name,
        le_client_b,
        le_member_b_name,
        le_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    geda_group_oobi = expose_multisig_agent_oobi(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
    )
    qvi_group_oobi = expose_multisig_agent_oobi(
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_group_name,
    )
    le_group_oobi = expose_multisig_agent_oobi(
        le_client_a,
        le_member_a_name,
        le_client_b,
        le_member_b_name,
        le_group_name,
    )
    resolve_oobi(geda_client_a, qvi_group_oobi, alias=qvi_group_name)
    resolve_oobi(geda_client_b, qvi_group_oobi, alias=qvi_group_name)
    resolve_oobi(qvi_client_a, geda_group_oobi, alias=geda_group_name)
    resolve_oobi(qvi_client_b, geda_group_oobi, alias=geda_group_name)
    resolve_oobi(qvi_client_a, le_group_oobi, alias=le_group_name)
    resolve_oobi(qvi_client_b, le_group_oobi, alias=le_group_name)
    resolve_oobi(le_client_a, qvi_group_oobi, alias=qvi_group_name)
    resolve_oobi(le_client_b, qvi_group_oobi, alias=qvi_group_name)
    resolve_oobi(role_client, qvi_group_oobi, alias=qvi_group_name)

    # Stage 2: GEDA bootstraps the QVI group with a real QVI credential.
    geda_registry_nonce = coring.randomNonce()
    geda_registry_operation_a, _ = create_multisig_registry(
        geda_client_a,
        local_member_name=geda_member_a_name,
        group_name=geda_group_name,
        other_member_prefixes=[geda_member_b["prefix"]],
        registry_name=geda_registry_name,
        nonce=geda_registry_nonce,
        is_initiator=True,
    )
    _, geda_registry_request_b = wait_for_multisig_request(geda_client_b, "/multisig/vcp")
    geda_registry_operation_b, _ = create_multisig_registry(
        geda_client_b,
        local_member_name=geda_member_b_name,
        group_name=geda_group_name,
        other_member_prefixes=[geda_member_a["prefix"]],
        registry_name=geda_registry_name,
        nonce=geda_registry_nonce,
        request=geda_registry_request_b,
    )
    wait_for_operation(geda_client_a, geda_registry_operation_a)
    wait_for_operation(geda_client_b, geda_registry_operation_b)
    geda_registry_a, geda_registry_b = wait_for_multisig_registry_convergence(
        geda_client_a,
        geda_client_b,
        group_name=geda_group_name,
        registry_name=geda_registry_name,
    )

    qvi_issue_timestamp = helping.nowIso8601()
    qvi_creder_a, qvi_iss_a, qvi_anc_a, qvi_sigs_a, qvi_issue_operation_a, _ = issue_multisig_credential(
        geda_client_a,
        local_member_name=geda_member_a_name,
        group_name=geda_group_name,
        other_member_prefixes=[geda_member_b["prefix"]],
        registry_name=geda_registry_name,
        recipient=qvi_group_a["prefix"],
        data={"LEI": "254900OPPU84GM83MG36"},
        timestamp=qvi_issue_timestamp,
        is_initiator=True,
    )
    _, qvi_issue_request_b = wait_for_multisig_request(geda_client_b, "/multisig/iss")
    qvi_creder_b, qvi_iss_b, qvi_anc_b, qvi_sigs_b, qvi_issue_operation_b, _ = issue_multisig_credential(
        geda_client_b,
        local_member_name=geda_member_b_name,
        group_name=geda_group_name,
        other_member_prefixes=[geda_member_a["prefix"]],
        registry_name=geda_registry_name,
        recipient=qvi_group_a["prefix"],
        data={"LEI": "254900OPPU84GM83MG36"},
        timestamp=qvi_issue_timestamp,
        request=qvi_issue_request_b,
    )
    wait_for_operation(geda_client_a, qvi_issue_operation_a)
    wait_for_operation(geda_client_b, qvi_issue_operation_b)
    wait_for_issued_credential(geda_client_a, geda_group_a["prefix"], qvi_creder_a.said)
    wait_for_issued_credential(geda_client_b, geda_group_b["prefix"], qvi_creder_a.said)

    # Finish the grant wave first, then let the QVI members admit the same
    # grant SAID.
    qvi_grant_timestamp = helping.nowIso8601()
    qvi_grant_operation_a = send_multisig_credential_grant(
        geda_client_a,
        local_member_name=geda_member_a_name,
        group_name=geda_group_name,
        other_member_prefixes=[geda_member_b["prefix"]],
        recipient=qvi_group_a["prefix"],
        creder=qvi_creder_a,
        iserder=qvi_iss_a,
        anc=qvi_anc_a,
        sigs=qvi_sigs_a,
        timestamp=qvi_grant_timestamp,
        is_initiator=True,
    )
    qvi_grant_operation_b = send_multisig_credential_grant(
        geda_client_b,
        local_member_name=geda_member_b_name,
        group_name=geda_group_name,
        other_member_prefixes=[geda_member_a["prefix"]],
        recipient=qvi_group_a["prefix"],
        creder=qvi_creder_b,
        iserder=qvi_iss_b,
        anc=qvi_anc_b,
        sigs=qvi_sigs_b,
        timestamp=qvi_grant_timestamp,
    )
    wait_for_operation(geda_client_a, qvi_grant_operation_a)
    wait_for_operation(geda_client_b, qvi_grant_operation_b)

    qvi_grant_client_index, qvi_grant_note = wait_for_notification_any(
        [qvi_client_a, qvi_client_b],
        "/exn/ipex/grant",
    )
    qvi_grant_said = qvi_grant_note["a"]["d"]
    qvi_admit_timestamp = helping.nowIso8601()
    if qvi_grant_client_index == 0:
        first_qvi_client, first_qvi_member_name, first_qvi_peer_prefixes = (
            qvi_client_a,
            qvi_member_a_name,
            [qvi_member_b["prefix"]],
        )
        second_qvi_client, second_qvi_member_name, second_qvi_peer_prefixes = (
            qvi_client_b,
            qvi_member_b_name,
            [qvi_member_a["prefix"]],
        )
    else:
        first_qvi_client, first_qvi_member_name, first_qvi_peer_prefixes = (
            qvi_client_b,
            qvi_member_b_name,
            [qvi_member_a["prefix"]],
        )
        second_qvi_client, second_qvi_member_name, second_qvi_peer_prefixes = (
            qvi_client_a,
            qvi_member_a_name,
            [qvi_member_b["prefix"]],
        )
    first_qvi_admit_operation = submit_multisig_admit(
        first_qvi_client,
        local_member_name=first_qvi_member_name,
        group_name=qvi_group_name,
        other_member_prefixes=first_qvi_peer_prefixes,
        issuer_prefix=geda_group_a["prefix"],
        grant_said=qvi_grant_said,
        timestamp=qvi_admit_timestamp,
    )
    wait_for_exchange(second_qvi_client, qvi_grant_said, expected_route="/ipex/grant")
    second_qvi_admit_operation = submit_multisig_admit(
        second_qvi_client,
        local_member_name=second_qvi_member_name,
        group_name=qvi_group_name,
        other_member_prefixes=second_qvi_peer_prefixes,
        issuer_prefix=geda_group_a["prefix"],
        grant_said=qvi_grant_said,
        timestamp=qvi_admit_timestamp,
    )
    wait_for_operation(first_qvi_client, first_qvi_admit_operation)
    wait_for_operation(second_qvi_client, second_qvi_admit_operation)

    geda_admit_note_a = wait_for_notification(geda_client_a, "/exn/ipex/admit")
    geda_admit_note_b = wait_for_notification(geda_client_b, "/exn/ipex/admit")
    assert geda_admit_note_a["a"]["d"] == geda_admit_note_b["a"]["d"]

    qvi_received_qvi_a, qvi_received_qvi_b = wait_for_multisig_received_credential(
        qvi_client_a,
        qvi_client_b,
        qvi_creder_a.said,
    )

    # Stage 3: QVI becomes issuer and grants the chained LE credential to the
    # LE group using the received QVI credential as the `qvi` source edge.
    qvi_registry_nonce = coring.randomNonce()
    qvi_registry_operation_a, _ = create_multisig_registry(
        qvi_client_a,
        local_member_name=qvi_member_a_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_b["prefix"]],
        registry_name=qvi_registry_name,
        nonce=qvi_registry_nonce,
        is_initiator=True,
    )
    _, qvi_registry_request_b = wait_for_multisig_request(qvi_client_b, "/multisig/vcp")
    qvi_registry_operation_b, _ = create_multisig_registry(
        qvi_client_b,
        local_member_name=qvi_member_b_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_a["prefix"]],
        registry_name=qvi_registry_name,
        nonce=qvi_registry_nonce,
        request=qvi_registry_request_b,
    )
    wait_for_operation(qvi_client_a, qvi_registry_operation_a)
    wait_for_operation(qvi_client_b, qvi_registry_operation_b)
    qvi_registry_a, qvi_registry_b = wait_for_multisig_registry_convergence(
        qvi_client_a,
        qvi_client_b,
        group_name=qvi_group_name,
        registry_name=qvi_registry_name,
    )

    le_issue_timestamp = helping.nowIso8601()
    le_creder_a, le_iss_a, le_anc_a, le_sigs_a, le_issue_operation_a, _ = issue_multisig_credential(
        qvi_client_a,
        local_member_name=qvi_member_a_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_b["prefix"]],
        registry_name=qvi_registry_name,
        recipient=le_group_a["prefix"],
        data=LE_DATA,
        schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        edges=_source_edges("qvi", qvi_received_qvi_a),
        rules=_le_rules(),
        timestamp=le_issue_timestamp,
        is_initiator=True,
    )
    _, le_issue_request_b = wait_for_multisig_request(qvi_client_b, "/multisig/iss")
    le_creder_b, le_iss_b, le_anc_b, le_sigs_b, le_issue_operation_b, _ = issue_multisig_credential(
        qvi_client_b,
        local_member_name=qvi_member_b_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_a["prefix"]],
        registry_name=qvi_registry_name,
        recipient=le_group_a["prefix"],
        data=LE_DATA,
        schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        edges=_source_edges("qvi", qvi_received_qvi_b),
        rules=_le_rules(),
        timestamp=le_issue_timestamp,
        request=le_issue_request_b,
    )
    wait_for_operation(qvi_client_a, le_issue_operation_a)
    wait_for_operation(qvi_client_b, le_issue_operation_b)
    wait_for_issued_credential(qvi_client_a, qvi_group_a["prefix"], le_creder_a.said)
    wait_for_issued_credential(qvi_client_b, qvi_group_b["prefix"], le_creder_a.said)

    le_grant_timestamp = helping.nowIso8601()
    le_grant_operation_a = send_multisig_credential_grant(
        qvi_client_a,
        local_member_name=qvi_member_a_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_b["prefix"]],
        recipient=le_group_a["prefix"],
        creder=le_creder_a,
        iserder=le_iss_a,
        anc=le_anc_a,
        sigs=le_sigs_a,
        timestamp=le_grant_timestamp,
        is_initiator=True,
    )
    le_grant_operation_b = send_multisig_credential_grant(
        qvi_client_b,
        local_member_name=qvi_member_b_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_a["prefix"]],
        recipient=le_group_a["prefix"],
        creder=le_creder_b,
        iserder=le_iss_b,
        anc=le_anc_b,
        sigs=le_sigs_b,
        timestamp=le_grant_timestamp,
    )
    wait_for_operation(qvi_client_a, le_grant_operation_a)
    wait_for_operation(qvi_client_b, le_grant_operation_b)

    le_grant_client_index, le_grant_note = wait_for_notification_any(
        [le_client_a, le_client_b],
        "/exn/ipex/grant",
    )
    le_grant_said = le_grant_note["a"]["d"]
    le_admit_timestamp = helping.nowIso8601()
    if le_grant_client_index == 0:
        first_le_client, first_le_member_name, first_le_peer_prefixes = (
            le_client_a,
            le_member_a_name,
            [le_member_b["prefix"]],
        )
        second_le_client, second_le_member_name, second_le_peer_prefixes = (
            le_client_b,
            le_member_b_name,
            [le_member_a["prefix"]],
        )
    else:
        first_le_client, first_le_member_name, first_le_peer_prefixes = (
            le_client_b,
            le_member_b_name,
            [le_member_a["prefix"]],
        )
        second_le_client, second_le_member_name, second_le_peer_prefixes = (
            le_client_a,
            le_member_a_name,
            [le_member_b["prefix"]],
        )
    first_le_admit_operation = submit_multisig_admit(
        first_le_client,
        local_member_name=first_le_member_name,
        group_name=le_group_name,
        other_member_prefixes=first_le_peer_prefixes,
        issuer_prefix=qvi_group_a["prefix"],
        grant_said=le_grant_said,
        timestamp=le_admit_timestamp,
    )
    wait_for_exchange(second_le_client, le_grant_said, expected_route="/ipex/grant")
    second_le_admit_operation = submit_multisig_admit(
        second_le_client,
        local_member_name=second_le_member_name,
        group_name=le_group_name,
        other_member_prefixes=second_le_peer_prefixes,
        issuer_prefix=qvi_group_a["prefix"],
        grant_said=le_grant_said,
        timestamp=le_admit_timestamp,
    )
    wait_for_operation(first_le_client, first_le_admit_operation)
    wait_for_operation(second_le_client, second_le_admit_operation)

    le_issuer_admit_note_a = wait_for_notification(qvi_client_a, "/exn/ipex/admit")
    le_issuer_admit_note_b = wait_for_notification(qvi_client_b, "/exn/ipex/admit")
    assert le_issuer_admit_note_a["a"]["d"] == le_issuer_admit_note_b["a"]["d"]

    le_received_a, le_received_b = wait_for_multisig_received_credential(
        le_client_a,
        le_client_b,
        le_creder_a.said,
    )

    # Stage 4: LE becomes issuer and grants OOR Auth back to the QVI group.
    # This hop is intentionally non-obvious: subject `a.i` is the QVI group,
    # while `AID` names the eventual single-sig role holder.
    le_registry_nonce = coring.randomNonce()
    le_registry_operation_a, _ = create_multisig_registry(
        le_client_a,
        local_member_name=le_member_a_name,
        group_name=le_group_name,
        other_member_prefixes=[le_member_b["prefix"]],
        registry_name=le_registry_name,
        nonce=le_registry_nonce,
        is_initiator=True,
    )
    _, le_registry_request_b = wait_for_multisig_request(le_client_b, "/multisig/vcp")
    le_registry_operation_b, _ = create_multisig_registry(
        le_client_b,
        local_member_name=le_member_b_name,
        group_name=le_group_name,
        other_member_prefixes=[le_member_a["prefix"]],
        registry_name=le_registry_name,
        nonce=le_registry_nonce,
        request=le_registry_request_b,
    )
    wait_for_operation(le_client_a, le_registry_operation_a)
    wait_for_operation(le_client_b, le_registry_operation_b)
    le_registry_a, le_registry_b = wait_for_multisig_registry_convergence(
        le_client_a,
        le_client_b,
        group_name=le_group_name,
        registry_name=le_registry_name,
    )

    oor_auth_data = dict(OOR_DATA, AID=role_holder["prefix"])
    oor_auth_timestamp = helping.nowIso8601()
    oor_auth_creder_a, oor_auth_iss_a, oor_auth_anc_a, oor_auth_sigs_a, oor_auth_operation_a, _ = (
        issue_multisig_credential(
            le_client_a,
            local_member_name=le_member_a_name,
            group_name=le_group_name,
            other_member_prefixes=[le_member_b["prefix"]],
            registry_name=le_registry_name,
            recipient=qvi_group_a["prefix"],
            data=oor_auth_data,
            schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
            edges=_source_edges("le", le_received_a),
            rules=_le_rules(),
            timestamp=oor_auth_timestamp,
            is_initiator=True,
        )
    )
    _, oor_auth_request_b = wait_for_multisig_request(le_client_b, "/multisig/iss")
    oor_auth_creder_b, oor_auth_iss_b, oor_auth_anc_b, oor_auth_sigs_b, oor_auth_operation_b, _ = issue_multisig_credential(
        le_client_b,
        local_member_name=le_member_b_name,
        group_name=le_group_name,
        other_member_prefixes=[le_member_a["prefix"]],
        registry_name=le_registry_name,
        recipient=qvi_group_a["prefix"],
        data=oor_auth_data,
        schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
        edges=_source_edges("le", le_received_b),
        rules=_le_rules(),
        timestamp=oor_auth_timestamp,
        request=oor_auth_request_b,
    )
    wait_for_operation(le_client_a, oor_auth_operation_a)
    wait_for_operation(le_client_b, oor_auth_operation_b)
    wait_for_issued_credential(le_client_a, le_group_a["prefix"], oor_auth_creder_a.said)
    wait_for_issued_credential(le_client_b, le_group_b["prefix"], oor_auth_creder_a.said)

    # As above, finish the entire OOR Auth grant wave before any QVI member
    # starts the matching admit wave.
    oor_auth_grant_timestamp = helping.nowIso8601()
    oor_auth_grant_operation_a = send_multisig_credential_grant(
        le_client_a,
        local_member_name=le_member_a_name,
        group_name=le_group_name,
        other_member_prefixes=[le_member_b["prefix"]],
        recipient=qvi_group_a["prefix"],
        creder=oor_auth_creder_a,
        iserder=oor_auth_iss_a,
        anc=oor_auth_anc_a,
        sigs=oor_auth_sigs_a,
        timestamp=oor_auth_grant_timestamp,
        is_initiator=True,
    )
    oor_auth_grant_operation_b = send_multisig_credential_grant(
        le_client_b,
        local_member_name=le_member_b_name,
        group_name=le_group_name,
        other_member_prefixes=[le_member_a["prefix"]],
        recipient=qvi_group_a["prefix"],
        creder=oor_auth_creder_b,
        iserder=oor_auth_iss_b,
        anc=oor_auth_anc_b,
        sigs=oor_auth_sigs_b,
        timestamp=oor_auth_grant_timestamp,
    )
    wait_for_operation(le_client_a, oor_auth_grant_operation_a)
    wait_for_operation(le_client_b, oor_auth_grant_operation_b)

    oor_auth_grant_client_index, oor_auth_grant_note = wait_for_notification_any(
        [qvi_client_a, qvi_client_b],
        "/exn/ipex/grant",
    )
    oor_auth_grant_said = oor_auth_grant_note["a"]["d"]
    oor_auth_admit_timestamp = helping.nowIso8601()
    if oor_auth_grant_client_index == 0:
        first_oor_auth_client, first_oor_auth_member_name, first_oor_auth_peer_prefixes = (
            qvi_client_a,
            qvi_member_a_name,
            [qvi_member_b["prefix"]],
        )
        second_oor_auth_client, second_oor_auth_member_name, second_oor_auth_peer_prefixes = (
            qvi_client_b,
            qvi_member_b_name,
            [qvi_member_a["prefix"]],
        )
    else:
        first_oor_auth_client, first_oor_auth_member_name, first_oor_auth_peer_prefixes = (
            qvi_client_b,
            qvi_member_b_name,
            [qvi_member_a["prefix"]],
        )
        second_oor_auth_client, second_oor_auth_member_name, second_oor_auth_peer_prefixes = (
            qvi_client_a,
            qvi_member_a_name,
            [qvi_member_b["prefix"]],
        )
    first_oor_auth_admit_operation = submit_multisig_admit(
        first_oor_auth_client,
        local_member_name=first_oor_auth_member_name,
        group_name=qvi_group_name,
        other_member_prefixes=first_oor_auth_peer_prefixes,
        issuer_prefix=le_group_a["prefix"],
        grant_said=oor_auth_grant_said,
        timestamp=oor_auth_admit_timestamp,
    )
    wait_for_exchange(second_oor_auth_client, oor_auth_grant_said, expected_route="/ipex/grant")
    second_oor_auth_admit_operation = submit_multisig_admit(
        second_oor_auth_client,
        local_member_name=second_oor_auth_member_name,
        group_name=qvi_group_name,
        other_member_prefixes=second_oor_auth_peer_prefixes,
        issuer_prefix=le_group_a["prefix"],
        grant_said=oor_auth_grant_said,
        timestamp=oor_auth_admit_timestamp,
    )
    wait_for_operation(first_oor_auth_client, first_oor_auth_admit_operation)
    wait_for_operation(second_oor_auth_client, second_oor_auth_admit_operation)

    oor_auth_issuer_admit_note_a = wait_for_notification(le_client_a, "/exn/ipex/admit")
    oor_auth_issuer_admit_note_b = wait_for_notification(le_client_b, "/exn/ipex/admit")
    assert oor_auth_issuer_admit_note_a["a"]["d"] == oor_auth_issuer_admit_note_b["a"]["d"]

    qvi_received_oor_auth_a, qvi_received_oor_auth_b = wait_for_multisig_received_credential(
        qvi_client_a,
        qvi_client_b,
        oor_auth_creder_a.said,
    )

    # Stage 5: QVI issues the final OOR credential to the single-sig person
    # holder, chaining it to the received OOR Auth credential under `auth`.
    oor_timestamp = helping.nowIso8601()
    oor_creder_a, oor_iss_a, oor_anc_a, oor_sigs_a, oor_operation_a, _ = issue_multisig_credential(
        qvi_client_a,
        local_member_name=qvi_member_a_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_b["prefix"]],
        registry_name=qvi_registry_name,
        recipient=role_holder["prefix"],
        data=OOR_DATA,
        schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
        edges=_source_edges("auth", qvi_received_oor_auth_a, operator="I2I"),
        rules=_le_rules(),
        timestamp=oor_timestamp,
        is_initiator=True,
    )
    _, oor_request_b = wait_for_multisig_request(qvi_client_b, "/multisig/iss")
    oor_creder_b, oor_iss_b, oor_anc_b, oor_sigs_b, oor_operation_b, _ = issue_multisig_credential(
        qvi_client_b,
        local_member_name=qvi_member_b_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_a["prefix"]],
        registry_name=qvi_registry_name,
        recipient=role_holder["prefix"],
        data=OOR_DATA,
        schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
        edges=_source_edges("auth", qvi_received_oor_auth_b, operator="I2I"),
        rules=_le_rules(),
        timestamp=oor_timestamp,
        request=oor_request_b,
    )
    wait_for_operation(qvi_client_a, oor_operation_a)
    wait_for_operation(qvi_client_b, oor_operation_b)
    wait_for_issued_credential(qvi_client_a, qvi_group_a["prefix"], oor_creder_a.said)
    wait_for_issued_credential(qvi_client_b, qvi_group_b["prefix"], oor_creder_a.said)

    oor_grant_timestamp = helping.nowIso8601()
    oor_grant_operation_a = send_multisig_credential_grant(
        qvi_client_a,
        local_member_name=qvi_member_a_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_b["prefix"]],
        recipient=role_holder["prefix"],
        creder=oor_creder_a,
        iserder=oor_iss_a,
        anc=oor_anc_a,
        sigs=oor_sigs_a,
        timestamp=oor_grant_timestamp,
        is_initiator=True,
    )
    oor_grant_operation_b = send_multisig_credential_grant(
        qvi_client_b,
        local_member_name=qvi_member_b_name,
        group_name=qvi_group_name,
        other_member_prefixes=[qvi_member_a["prefix"]],
        recipient=role_holder["prefix"],
        creder=oor_creder_b,
        iserder=oor_iss_b,
        anc=oor_anc_b,
        sigs=oor_sigs_b,
        timestamp=oor_grant_timestamp,
    )
    wait_for_operation(qvi_client_a, oor_grant_operation_a)
    wait_for_operation(qvi_client_b, oor_grant_operation_b)

    # The final holder is single-sig, so the last hop uses the ordinary admit
    # helper after the multisig QVI grant wave has fully completed.
    role_grant_note = wait_for_notification(role_client, "/exn/ipex/grant")
    submit_admit(
        role_client,
        holder_name=role_holder_name,
        issuer_prefix=qvi_group_a["prefix"],
        notification=role_grant_note,
    )
    wait_for_notification(qvi_client_a, "/exn/ipex/admit")
    wait_for_notification(qvi_client_b, "/exn/ipex/admit")
    oor_received = wait_for_credential(role_client, oor_creder_a.said)

    assert geda_group_a["prefix"] == geda_group_b["prefix"]
    assert geda_registry_a["regk"] == geda_registry_b["regk"]
    assert qvi_registry_a["regk"] == qvi_registry_b["regk"]
    assert le_registry_a["regk"] == le_registry_b["regk"]
    assert qvi_creder_a.said == qvi_creder_b.said
    assert le_creder_a.said == le_creder_b.said
    assert oor_auth_creder_a.said == oor_auth_creder_b.said
    assert oor_creder_a.said == oor_creder_b.said

    _assert_holder_read_surface(
        qvi_client_a,
        issuer_prefix=geda_group_a["prefix"],
        holder_prefix=qvi_group_a["prefix"],
        said=qvi_creder_a.said,
        schema_said=QVI_SCHEMA_SAID,
    )
    _assert_holder_read_surface(
        qvi_client_b,
        issuer_prefix=geda_group_b["prefix"],
        holder_prefix=qvi_group_b["prefix"],
        said=qvi_creder_a.said,
        schema_said=QVI_SCHEMA_SAID,
    )
    _assert_holder_read_surface(
        le_client_a,
        issuer_prefix=qvi_group_a["prefix"],
        holder_prefix=le_group_a["prefix"],
        said=le_creder_a.said,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
    )
    _assert_holder_read_surface(
        le_client_b,
        issuer_prefix=qvi_group_b["prefix"],
        holder_prefix=le_group_b["prefix"],
        said=le_creder_a.said,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
    )
    _assert_holder_read_surface(
        qvi_client_a,
        issuer_prefix=le_group_a["prefix"],
        holder_prefix=qvi_group_a["prefix"],
        said=oor_auth_creder_a.said,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
    )
    _assert_holder_read_surface(
        qvi_client_b,
        issuer_prefix=le_group_b["prefix"],
        holder_prefix=qvi_group_b["prefix"],
        said=oor_auth_creder_a.said,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
    )
    _assert_holder_read_surface(
        role_client,
        issuer_prefix=qvi_group_a["prefix"],
        holder_prefix=role_holder["prefix"],
        said=oor_creder_a.said,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
        assert_subject_filter=False,
    )
    assert oor_received["sad"]["d"] == oor_creder_a.said
    assert le_received_a["sad"]["e"]["qvi"]["n"] == qvi_creder_a.said
    assert le_received_b["sad"]["e"]["qvi"]["n"] == qvi_creder_a.said
    assert le_received_a["chains"][0]["sad"]["d"] == qvi_creder_a.said
    assert le_received_b["chains"][0]["sad"]["d"] == qvi_creder_a.said
    assert qvi_received_oor_auth_a["sad"]["e"]["le"]["n"] == le_creder_a.said
    assert qvi_received_oor_auth_b["sad"]["e"]["le"]["n"] == le_creder_a.said
    assert qvi_received_oor_auth_a["chains"][0]["sad"]["d"] == le_creder_a.said
    assert qvi_received_oor_auth_b["chains"][0]["sad"]["d"] == le_creder_a.said
    assert oor_received["sad"]["e"]["auth"]["n"] == oor_auth_creder_a.said
    assert oor_received["sad"]["e"]["auth"]["o"] == "I2I"
    assert oor_received["chains"][0]["sad"]["d"] == oor_auth_creder_a.said
    assert qvi_received_oor_auth_a["sad"]["a"]["i"] == qvi_group_a["prefix"]
    assert qvi_received_oor_auth_a["sad"]["a"]["AID"] == role_holder["prefix"]
    assert qvi_received_oor_auth_b["sad"]["a"]["i"] == qvi_group_b["prefix"]
    assert qvi_received_oor_auth_b["sad"]["a"]["AID"] == role_holder["prefix"]

    _assert_filtered_contains(
        geda_client_a,
        schema_said=QVI_SCHEMA_SAID,
        subject_prefix=qvi_group_a["prefix"],
        said=qvi_creder_a.said,
    )
    _assert_filtered_contains(
        geda_client_b,
        schema_said=QVI_SCHEMA_SAID,
        subject_prefix=qvi_group_b["prefix"],
        said=qvi_creder_a.said,
    )
    _assert_filtered_contains(
        qvi_client_a,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        subject_prefix=le_group_a["prefix"],
        said=le_creder_a.said,
    )
    _assert_filtered_contains(
        qvi_client_b,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        subject_prefix=le_group_b["prefix"],
        said=le_creder_a.said,
    )
    _assert_filtered_contains(
        le_client_a,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
        subject_prefix=qvi_group_a["prefix"],
        said=oor_auth_creder_a.said,
    )
    _assert_filtered_contains(
        le_client_b,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor-auth"],
        subject_prefix=qvi_group_b["prefix"],
        said=oor_auth_creder_a.said,
    )
    _assert_filtered_contains(
        qvi_client_a,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
        subject_prefix=role_holder["prefix"],
        said=oor_creder_a.said,
    )
    _assert_filtered_contains(
        qvi_client_b,
        schema_said=ADDITIONAL_SCHEMA_OOBI_SAIDS["oor"],
        subject_prefix=role_holder["prefix"],
        said=oor_creder_a.said,
    )
