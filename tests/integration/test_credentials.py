"""Live single-sig credential and IPEX workflow coverage.

These tests are intentionally written as end-to-end protocol narratives rather
than tiny isolated assertions. The important maintainer question here is not
just "did one method return?" but "did the full issuance, exchange, and
storage workflow converge in the same shape SignifyTS and KERIA expect?"
"""

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


def test_ipex_apply_offer_agree_grant_admit(client_factory):
    """Prove the full single-sig IPEX conversation path, not just presentation.

    This is the missing early-conversation parity slice relative to SignifyTS:
    a verifier applies, the holder offers, the verifier agrees, the holder
    grants, and the verifier admits and stores the credential.

    Mental model:
    - issuer -> holder bootstraps a real stored credential
    - verifier -> holder starts a request conversation for that credential
    - each later message points back to the prior message SAID
    - only the final admit should cause the verifier to store the credential
    """
    issuer_client = client_factory()
    holder_client = client_factory()
    verifier_client = client_factory()
    issuer_name = alias("issuer")
    holder_name = alias("holder")
    verifier_name = alias("verifier")
    registry_name = alias("registry")

    issuer = create_identifier(issuer_client, issuer_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)
    verifier = create_identifier(verifier_client, verifier_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(issuer_client, issuer_name, holder_client, holder_name)
    exchange_agent_oobis(holder_client, holder_name, verifier_client, verifier_name)
    resolve_schema_oobi(issuer_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(holder_client, QVI_SCHEMA_SAID)
    resolve_schema_oobi(verifier_client, QVI_SCHEMA_SAID)

    # Stage 1: bootstrap a real credential onto the holder so the later offer
    # can reference a stored credential instead of a synthetic payload.
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

    initial_grant_note = wait_for_notification(holder_client, "/exn/ipex/grant")
    submit_admit(
        holder_client,
        holder_name=holder_name,
        issuer_prefix=issuer["prefix"],
        notification=initial_grant_note,
    )
    wait_for_notification(issuer_client, "/exn/ipex/admit")
    wait_for_credential(holder_client, creder.said)

    # Stage 2: verifier asks the holder for a credential matching the target
    # schema plus subject attributes.
    apply, apply_sigs, _ = verifier_client.ipex().apply(
        verifier_name,
        holder["prefix"],
        QVI_SCHEMA_SAID,
        attributes={"LEI": "5493001KJTIIGC8Y1R17"},
        dt="2026-03-25T00:00:00.000000+00:00",
    )
    wait_for_operation(
        verifier_client,
        verifier_client.ipex().submitApply(verifier_name, apply, apply_sigs, [holder["prefix"]]),
    )

    holder_apply_note = wait_for_notification(holder_client, "/exn/ipex/apply")
    apply_exchange = holder_client.exchanges().get(holder_apply_note["a"]["d"])
    apply_said = apply_exchange["exn"]["d"]

    filter_kwargs = {"-s": apply_exchange["exn"]["a"]["s"]}
    for key, value in apply_exchange["exn"]["a"]["a"].items():
        filter_kwargs[f"-a-{key}"] = value
    matching_credentials = holder_client.credentials().list(filter=filter_kwargs)

    assert len(matching_credentials) == 1
    assert matching_credentials[0]["sad"]["d"] == creder.said

    # Stage 3: holder answers the request with an offer that references the
    # stored credential and points back to the apply SAID.
    offer, offer_sigs, offer_atc = holder_client.ipex().offer(
        holder_name,
        verifier["prefix"],
        matching_credentials[0]["sad"],
        applySaid=apply_said,
        dt="2026-03-25T00:00:01.000000+00:00",
    )
    wait_for_operation(
        holder_client,
        holder_client.ipex().submitOffer(holder_name, offer, offer_sigs, offer_atc, [verifier["prefix"]]),
    )

    verifier_offer_note = wait_for_notification(verifier_client, "/exn/ipex/offer")
    offer_exchange = verifier_client.exchanges().get(verifier_offer_note["a"]["d"])
    offer_said = offer_exchange["exn"]["d"]

    assert offer_exchange["exn"]["p"] == apply_said
    assert offer_exchange["exn"]["e"]["acdc"]["a"]["LEI"] == "5493001KJTIIGC8Y1R17"

    # Stage 4: verifier explicitly agrees to the offered credential before the
    # holder is allowed to grant it.
    agree, agree_sigs, _ = verifier_client.ipex().agree(
        verifier_name,
        holder["prefix"],
        offer_said,
        dt="2026-03-25T00:00:02.000000+00:00",
    )
    wait_for_operation(
        verifier_client,
        verifier_client.ipex().submitAgree(verifier_name, agree, agree_sigs, [holder["prefix"]]),
    )

    holder_agree_note = wait_for_notification(holder_client, "/exn/ipex/agree")
    agree_exchange = holder_client.exchanges().get(holder_agree_note["a"]["d"])
    agree_said = agree_exchange["exn"]["d"]

    assert agree_exchange["exn"]["p"] == offer_said

    # Stage 5: holder grants the concrete credential artifacts and chains that
    # grant back to the agree SAID.
    holder_stored = holder_client.credentials().get(creder.said)
    grant, grant_sigs, grant_atc = holder_client.ipex().grant(
        name=holder_name,
        recipient=verifier["prefix"],
        acdc=holder_stored["sad"],
        iss=holder_stored["iss"],
        anc=holder_stored["anc"],
        acdcAttachment=holder_stored.get("atc"),
        issAttachment=holder_stored.get("issatc"),
        ancAttachment=holder_stored.get("ancatc"),
        agreeSaid=agree_said,
        dt="2026-03-25T00:00:03.000000+00:00",
    )
    wait_for_operation(
        holder_client,
        holder_client.ipex().submitGrant(holder_name, grant, grant_sigs, grant_atc, [verifier["prefix"]]),
    )

    verifier_grant_note = wait_for_notification(verifier_client, "/exn/ipex/grant")
    verifier_grant = verifier_client.exchanges().get(verifier_grant_note["a"]["d"])
    assert verifier_grant["exn"]["p"] == agree_said

    # Stage 6: verifier admits the grant, which is the protocol step that
    # should result in a stored credential on the verifier side.
    admit, admit_sigs, admit_atc = verifier_client.ipex().admit(
        name=verifier_name,
        recipient=holder["prefix"],
        grantSaid=verifier_grant_note["a"]["d"],
        dt="2026-03-25T00:00:04.000000+00:00",
    )
    wait_for_operation(
        verifier_client,
        verifier_client.ipex().submitAdmit(verifier_name, admit, admit_sigs, admit_atc, [holder["prefix"]]),
    )
    wait_for_notification(holder_client, "/exn/ipex/admit")

    verifier_received = wait_for_credential(verifier_client, creder.said)
    verifier_fetched = verifier_client.credentials().get(creder.said)
    verifier_exported = verifier_client.credentials().export(creder.said)
    verifier_filtered = verifier_client.credentials().list(filter={"-a-i": holder["prefix"]})

    assert verifier_received["sad"]["d"] == creder.said
    assert verifier_received["sad"]["a"]["i"] == holder["prefix"]
    assert verifier_received["sad"]["i"] == issuer["prefix"]
    assert verifier_fetched["sad"]["d"] == creder.said
    assert any(credential["sad"]["d"] == creder.said for credential in verifier_filtered)
    assert verifier_exported


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

    Workflow summary:
    - issuer issues a QVI credential to holder
    - holder receives it through grant/admit
    - holder then acts as issuer for a legal-entity credential
    - the legal-entity credential must carry both rules and a source edge back
      to the received QVI credential
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

    # Stage 1: bootstrap the parent QVI credential that later source edges
    # should reference.
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

    # Stage 2: issuer of the downstream credential creates its own registry and
    # builds the explicit rules and source-edge material.
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

    # Stage 3: issue the chained legal-entity credential and transport it
    # through the same single-sig grant/admit path.
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
