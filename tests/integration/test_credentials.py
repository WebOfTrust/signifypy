"""Live credential presentation coverage for the single-sig grant/admit path."""

from __future__ import annotations

import pytest

from .constants import SCHEMA_OOBI, SCHEMA_SAID, TEST_WITNESS_AIDS
from .helpers import (
    alias,
    create_identifier,
    create_registry,
    exchange_agent_oobis,
    issue_credential,
    notification_routes,
    rename_registry,
    revoke_credential,
    resolve_oobi,
    send_credential_grant,
    submit_admit,
    wait_for_credential,
    wait_for_credential_state,
    wait_for_notification,
)


pytestmark = pytest.mark.integration


def test_credential_presentation_grant_admit(client_factory):
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
    resolve_oobi(issuer_client, SCHEMA_OOBI, alias="schema")
    resolve_oobi(holder_client, SCHEMA_OOBI, alias="schema")

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
    exported = holder_client.credentials().export(creder.said)
    received_for_holder = holder_client.credentials().list(filtr={"-a-i": holder["prefix"]})

    assert received["sad"]["d"] == creder.said
    assert received["sad"]["i"] == issuer["prefix"]
    assert received["sad"]["a"]["i"] == holder["prefix"]
    assert received["sad"]["s"] == SCHEMA_SAID
    assert admit_note["a"]["r"] == "/exn/ipex/admit"
    assert any(credential["sad"]["d"] == creder.said for credential in received_for_holder)
    assert exported


def test_registry_rename_read_path(client_factory):
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
    resolve_oobi(issuer_client, SCHEMA_OOBI, alias="schema")
    resolve_oobi(holder_client, SCHEMA_OOBI, alias="schema")

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
