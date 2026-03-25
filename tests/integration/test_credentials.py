"""Live credential presentation coverage for the single-sig grant/admit path."""

from __future__ import annotations

import pytest
from keri.core import coring
from requests import HTTPError

from .constants import ADDITIONAL_SCHEMA_OOBI_SAIDS, QVI_SCHEMA_SAID, TEST_WITNESS_AIDS
from .helpers import (
    alias,
    create_identifier,
    create_registry,
    exchange_agent_oobis,
    issue_credential,
    notification_routes,
    rename_registry,
    revoke_credential,
    resolve_schema_oobi,
    send_credential_grant,
    submit_admit,
    wait_for_credential,
    wait_for_credential_state,
    wait_for_notification,
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


def test_credential_query_filter_contract(client_factory):
    """Mirror the TS credential-list filter contract against a real agent.

    The maintained API surface is not just "list exists"; it needs to honor
    the indexed issuer/schema/subject filters and their combinations in the
    same workflow shape SignifyTS locks down.
    """
    issuer_client = client_factory()
    holder_client = client_factory()
    issuer_name = alias("issuer")
    holder_name = alias("holder")
    registry_name = alias("registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client, holder_name)
    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)

    _, registry = create_registry(issuer_client, issuer_name, registry_name)
    creder, _, _, _ = issue_credential(
        issuer_client,
        issuer_name=issuer_name,
        registry_name=registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
    )

    all_credentials = issuer_client.credentials().list()
    issuer_filtered = issuer_client.credentials().list(filter={"-i": issuer["prefix"]})
    schema_filtered = issuer_client.credentials().list(filter={"-s": QVI_SCHEMA_SAID})
    subject_filtered = issuer_client.credentials().list(filter={"-a-i": holder["prefix"]})
    combined_filtered = issuer_client.credentials().list(
        filter={"-i": issuer["prefix"], "-s": QVI_SCHEMA_SAID, "-a-i": holder["prefix"]}
    )
    missing_filtered = issuer_client.credentials().list(
        filter={"-i": "missing-issuer", "-s": QVI_SCHEMA_SAID, "-a-i": holder["prefix"]}
    )
    state = issuer_client.credentials().state(registry["regk"], creder.said)

    assert len(all_credentials) == 1
    assert len(issuer_filtered) == 1
    assert len(schema_filtered) == 1
    assert len(subject_filtered) == 1
    assert len(combined_filtered) == 1
    assert len(missing_filtered) == 0
    assert issuer_filtered[0]["sad"]["d"] == creder.said
    assert schema_filtered[0]["sad"]["s"] == QVI_SCHEMA_SAID
    assert subject_filtered[0]["sad"]["a"]["i"] == holder["prefix"]
    assert combined_filtered[0]["sad"]["d"] == creder.said
    assert state["et"] == "iss"
    assert state["s"] == "0"


def test_credential_presentation_grant_admit(client_factory):
    """Cover the single-sig IPEX grant/admit happy path end to end.

    This is the baseline presentation contract for SignifyPy's live workflow
    layer: one issuer issues a credential, transports it through IPEX grant,
    the holder admits it, and both sides expose the expected post-exchange
    state through maintained wrappers.
    """
    # Workflow:
    # 1. Create witnessed issuer and holder identifiers and exchange the exact
    #    agent OOBIs the SignifyTS credential flows use.
    # 2. Resolve the schema OOBI on both sides so issuance and later receipt can
    #    validate against the same schema state.
    # 3. Create the issuer registry and issue a credential to the holder.
    # 4. Wrap the issued credential in an IPEX grant and send it to the holder.
    # 5. Wait for the holder-side grant notification, submit the matching admit,
    #    and then assert the holder can see and export the received credential.
    issuer_client = client_factory()
    holder_client = client_factory()
    issuer_name = alias("issuer")
    holder_name = alias("holder")
    registry_name = alias("registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client, holder_name)
    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)

    _, registry = create_registry(issuer_client, issuer_name, registry_name)
    assert registry["name"] == registry_name

    creder, iserder, anc, sigs = issue_credential(
        issuer_client,
        issuer_name=issuer_name,
        registry_name=registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
    )
    send_credential_grant(
        issuer_client,
        issuer_name=issuer_name,
        recipient=holder["prefix"],
        creder=creder,
        iserder=iserder,
        anc=anc,
        sigs=sigs,
    )

    grant_note = wait_for_notification(holder_client, "/exn/ipex/grant")
    assert "/exn/ipex/grant" in notification_routes(holder_client)
    submit_admit(
        holder_client,
        holder_name=holder_name,
        issuer_prefix=issuer["prefix"],
        notification=grant_note,
    )
    admit_note = wait_for_notification(issuer_client, "/exn/ipex/admit")

    received = wait_for_credential(holder_client, creder.said)
    fetched = holder_client.credentials().get(creder.said)
    fetched_cesr = holder_client.credentials().get(creder.said, includeCESR=True)
    exported = holder_client.credentials().export(creder.said)
    received_for_holder = holder_client.credentials().list(filter={"-a-i": holder["prefix"]})

    assert received["sad"]["d"] == creder.said
    assert received["sad"]["i"] == issuer["prefix"]
    assert received["sad"]["a"]["i"] == holder["prefix"]
    assert received["sad"]["s"] == QVI_SCHEMA_SAID
    assert fetched["sad"]["d"] == creder.said
    assert fetched["sad"]["a"]["i"] == holder["prefix"]
    assert admit_note["a"]["r"] == "/exn/ipex/admit"
    assert any(credential["sad"]["d"] == creder.said for credential in received_for_holder)
    assert fetched_cesr
    assert exported


def test_holder_credential_delete_readback(client_factory):
    """Prove local credential deletion removes both JSON and CESR read paths.

    Once the holder deletes the stored credential copy, maintained read
    wrappers should stop finding it.
    """
    issuer_client = client_factory()
    holder_client = client_factory()
    issuer_name = alias("issuer")
    holder_name = alias("holder")
    registry_name = alias("registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client, holder_name)
    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)

    create_registry(issuer_client, issuer_name, registry_name)
    creder, iserder, anc, sigs = issue_credential(
        issuer_client,
        issuer_name=issuer_name,
        registry_name=registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
    )
    send_credential_grant(
        issuer_client,
        issuer_name=issuer_name,
        recipient=holder["prefix"],
        creder=creder,
        iserder=iserder,
        anc=anc,
        sigs=sigs,
    )

    grant_note = wait_for_notification(holder_client, "/exn/ipex/grant")
    submit_admit(
        holder_client,
        holder_name=holder_name,
        issuer_prefix=issuer["prefix"],
        notification=grant_note,
    )
    wait_for_notification(issuer_client, "/exn/ipex/admit")

    fetched = wait_for_credential(holder_client, creder.said)
    fetched_cesr = holder_client.credentials().get(creder.said, includeCESR=True)
    holder_client.credentials().delete(creder.said)

    with pytest.raises(HTTPError):
        holder_client.credentials().get(creder.said)

    with pytest.raises(HTTPError):
        holder_client.credentials().get(creder.said, includeCESR=True)

    listed_all_after_delete = holder_client.credentials().list()
    listed_after_delete = holder_client.credentials().list(filter={"-a-i": holder["prefix"]})
    issuer_still_has_copy = issuer_client.credentials().list(filter={"-i": issuer["prefix"]})

    assert fetched["sad"]["d"] == creder.said
    assert fetched_cesr
    assert listed_all_after_delete == []
    assert all(credential["sad"]["d"] != creder.said for credential in listed_after_delete)
    assert any(credential["sad"]["d"] == creder.said for credential in issuer_still_has_copy)


def test_chained_credential_issue_with_rules_and_edges(client_factory):
    """Prove canonical `issue(...)` handles chained-credential inputs end to end.

    SignifyTS locks down more than the simplest QVI issuance: later credential
    families depend on `issue(...)` carrying source edges and rules cleanly
    enough that the recipient can read back chain material after IPEX.
    """
    issuer_client = client_factory()
    holder_client = client_factory()
    legal_entity_client = client_factory()
    issuer_name = alias("issuer")
    holder_name = alias("holder")
    legal_entity_name = alias("legal-entity")
    issuer_registry_name = alias("issuer-registry")
    holder_registry_name = alias("holder-registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)
    legal_entity = create_identifier(legal_entity_client, legal_entity_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client, holder_name)
    exchange_agent_oobis(holder_client, holder_name, legal_entity_client, legal_entity_name)

    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(legal_entity_client, QVI_SCHEMA_SAID)

    resolve_schema_oobi(
        holder_client,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        alias="legal-entity-schema",
    )
    resolve_schema_oobi(
        legal_entity_client,
        ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        alias="legal-entity-schema",
    )

    create_registry(issuer_client, issuer_name, issuer_registry_name)
    qvi_creder, qvi_iss, qvi_anc, qvi_sigs = issue_credential(
        issuer_client,
        issuer_name=issuer_name,
        registry_name=issuer_registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
    )
    send_credential_grant(
        issuer_client,
        issuer_name=issuer_name,
        recipient=holder["prefix"],
        creder=qvi_creder,
        iserder=qvi_iss,
        anc=qvi_anc,
        sigs=qvi_sigs,
    )
    grant_note = wait_for_notification(holder_client, "/exn/ipex/grant")
    submit_admit(
        holder_client,
        holder_name=holder_name,
        issuer_prefix=issuer["prefix"],
        notification=grant_note,
    )
    wait_for_notification(issuer_client, "/exn/ipex/admit")
    qvi_credential = wait_for_credential(holder_client, qvi_creder.said)

    create_registry(holder_client, holder_name, holder_registry_name)

    rules = coring.Saider.saidify(
        sad={
            "d": "",
            "usageDisclaimer": {
                "l": LE_USAGE_DISCLAIMER
            },
            "issuanceDisclaimer": {
                "l": LE_ISSUANCE_DISCLAIMER
            },
        }
    )[1]
    edges = coring.Saider.saidify(
        sad={
            "d": "",
            "qvi": {
                "n": qvi_credential["sad"]["d"],
                "s": qvi_credential["sad"]["s"],
            },
        }
    )[1]

    le_issue = holder_client.credentials().issue(
        holder_name,
        holder_registry_name,
        data={"LEI": "5493001KJTIIGC8Y1R17"},
        schema=ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"],
        recipient=legal_entity["prefix"],
        edges=edges,
        rules=rules,
    )
    wait_for_operation(holder_client, le_issue.op())
    send_credential_grant(
        holder_client,
        issuer_name=holder_name,
        recipient=legal_entity["prefix"],
        creder=le_issue.acdc,
        iserder=le_issue.iss,
        anc=le_issue.anc,
        sigs=le_issue.sigs,
    )
    grant_note = wait_for_notification(legal_entity_client, "/exn/ipex/grant")
    submit_admit(
        legal_entity_client,
        holder_name=legal_entity_name,
        issuer_prefix=holder["prefix"],
        notification=grant_note,
    )
    wait_for_notification(holder_client, "/exn/ipex/admit")
    legal_entity_credential = wait_for_credential(legal_entity_client, le_issue.acdc.said)
    fetched = legal_entity_client.credentials().get(le_issue.acdc.said)
    holder_filtered = holder_client.credentials().list(
        filter={"-s": ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"]}
    )

    assert le_issue.acdc.sad["s"] == ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"]
    assert le_issue.acdc.sad["a"]["i"] == legal_entity["prefix"]
    assert legal_entity_credential["sad"]["d"] == le_issue.acdc.said
    assert legal_entity_credential["sad"]["s"] == ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"]
    assert legal_entity_credential["sad"]["i"] == holder["prefix"]
    assert legal_entity_credential["status"]["s"] == "0"
    assert fetched["sad"]["d"] == le_issue.acdc.said
    assert isinstance(fetched["chains"], list)
    assert fetched["chains"]
    assert fetched["chains"][0]["sad"]["d"] == qvi_creder.said
    assert fetched["atc"]
    assert any(credential["sad"]["d"] == le_issue.acdc.said for credential in holder_filtered)


def test_registry_rename_read_path(client_factory):
    """Preserve the old registry-rename script as one direct read-path contract.

    The important invariant is that renaming changes the lookup name without
    changing the underlying registry identifier.
    """
    # This absorbs the old `rename_registry.py` script into the live suite.
    client = client_factory()
    issuer_name = alias("issuer")
    original_name = alias("registry")
    renamed_name = alias("registry-renamed")

    create_identifier(client, issuer_name, wits=TEST_WITNESS_AIDS)
    _, registry = create_registry(client, issuer_name, original_name)
    renamed = rename_registry(client, issuer_name, original_name, renamed_name)

    assert registry["name"] == original_name
    assert renamed["name"] == renamed_name
    assert renamed["regk"] == registry["regk"]


def test_single_sig_credential_revocation(client_factory):
    """Lock down single-sig credential revocation without multisig noise.

    This test isolates the revoke/read-state contract so regressions in the
    credential TEL surface can be diagnosed without also reasoning about
    multisig proposal choreography.
    """
    # This isolates the new SignifyPy revoke/state surface from multisig
    # choreography. One issuer creates, issues, and then revokes a credential,
    # and the test proves the credential TEL state converges to `rev`.
    issuer_client = client_factory()
    holder_client = client_factory()
    issuer_name = alias("issuer")
    holder_name = alias("holder")
    registry_name = alias("registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(issuer_client, issuer_name, holder_client, holder_name)
    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)

    _, registry = create_registry(issuer_client, issuer_name, registry_name)
    creder, _, _, _ = issue_credential(
        issuer_client,
        issuer_name=issuer_name,
        registry_name=registry_name,
        recipient=holder["prefix"],
        data={"LEI": "5493001KJTIIGC8Y1R17"},
    )
    revoke_credential(
        issuer_client,
        issuer_name=issuer_name,
        credential_said=creder.said,
    )
    revoked = wait_for_credential_state(
        issuer_client,
        registry_said=registry["regk"],
        credential_said=creder.said,
        expected_et="rev",
    )

    fetched = issuer_client.credentials().get(creder.said)

    assert issuer["prefix"] == fetched["sad"]["i"]
    assert fetched["sad"]["d"] == creder.said
    assert revoked["et"] == "rev"
    assert revoked["s"] == "1"
