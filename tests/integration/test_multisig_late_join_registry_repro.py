"""Reproduce late-join multisig registry visibility loss.

These tests isolate KERIA issue #316: a member that joins a multisig group
after registry and credential activity can join the group but cannot see the
preexisting registry. The credential issuance is intentional because current
KERIA/Signify export paths expose registry/TEL CESR material through credential
CESR export, not through a registry CESR export API.
"""

from __future__ import annotations

import pytest
import requests
from keri.core import coring, eventing, parsing
from keri.core import signing as csigning
from keri.help import helping
from requests import HTTPError

from .constants import ADDITIONAL_SCHEMA_OOBI_SAIDS, QVI_SCHEMA_SAID, TEST_WITNESS_AIDS
from .helpers import (
    accept_multisig_incept,
    alias,
    approve_multisig_delegation,
    assert_multisig_members,
    create_identifier,
    create_multisig_group,
    create_multisig_registry,
    exchange_agent_oobis,
    expose_multisig_agent_oobi,
    interact_multisig_group,
    issue_multisig_credential,
    HEAVY_POLL_INTERVAL,
    poll_until,
    POLL_INTERVAL,
    query_key_state,
    resolve_oobi,
    resolve_schema_oobi,
    rotate_in_late_multisig_member,
    send_multisig_credential_grant,
    start_multisig_incept,
    wait_for_exchange,
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

LE_SCHEMA_SAID = ADDITIONAL_SCHEMA_OOBI_SAIDS["legal-entity"]
LE_DATA = {"LEI": "875500ELOZEL05BVXV37"}
QVI_DATA = {"LEI": "254900OPPU84GM83MG36"}
SIMPLE_ISSUE_DATA = {"LEI": "5493001KJTIIGC8Y1R17"}

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


def _resolve_schema_set(client, *schema_saids: str) -> None:
    for schema_said in schema_saids:
        resolve_schema_oobi(client, schema_said)


def _le_rules() -> dict:
    return coring.Saider.saidify(
        sad={
            "d": "",
            "usageDisclaimer": {"l": LE_USAGE_DISCLAIMER},
            "issuanceDisclaimer": {"l": LE_ISSUANCE_DISCLAIMER},
        }
    )[1]


def _source_edges(label: str, credential) -> dict:
    sad = credential["sad"] if isinstance(credential, dict) else credential.sad
    return coring.Saider.saidify(
        sad={"d": "", label: {"n": sad["d"], "s": sad["s"]}}
    )[1]


def _registry_visible(registries: list[dict], registry: dict) -> bool:
    return any(
        entry.get("regk") == registry["regk"] or entry.get("name") == registry["name"]
        for entry in registries
    )


class _CesrKelRecorder:
    def __init__(self):
        self.events = []

    def processEvent(self, serder, **_):
        self.events.append(serder)

    def processAttachedReceiptCouples(self, *_, **__):
        return None

    def processAttachedReceiptQuadruples(self, *_, **__):
        return None

    def processReceipt(self, *_, **__):
        return None

    def processReceiptWitness(self, *_, **__):
        return None

    def processReceiptTrans(self, *_, **__):
        return None

    def processQuery(self, *_, **__):
        return None


class _CesrTelRecorder:
    def __init__(self):
        self.events = []

    def processEvent(self, serder, **_):
        self.events.append(serder)

    def processQuery(self, *_, **__):
        return None


class _CesrCredentialRecorder:
    def __init__(self):
        self.credentials = []

    def processCredential(self, creder, **_):
        self.credentials.append(creder)


class _CesrExchangeRecorder:
    def processEvent(self, *_, **__):
        return None


class _CesrReplyRecorder:
    def processReply(self, *_, **__):
        return None


def _parse_cesr_export(cesr: bytes) -> tuple[list, list, list]:
    kel = _CesrKelRecorder()
    tel = _CesrTelRecorder()
    acdc = _CesrCredentialRecorder()
    parser = parsing.Parser(framed=True)
    parser.parse(
        ims=bytearray(cesr),
        kvy=kel,
        tvy=tel,
        exc=_CesrExchangeRecorder(),
        rvy=_CesrReplyRecorder(),
        vry=acdc,
        local=False,
    )
    return kel.events, tel.events, acdc.credentials


def _assert_cesr_export_contains_registry_and_credential(
    cesr: bytes,
    *,
    registry_said: str,
    credential_said: str,
) -> None:
    _, tel_events, credentials = _parse_cesr_export(cesr)
    registry_events = [
        event
        for event in tel_events
        if event.ilk == coring.Ilks.vcp and event.pre == registry_said
    ]
    issue_events = [
        event
        for event in tel_events
        if (
            event.ilk == coring.Ilks.iss
            and event.pre == credential_said
            and event.ked.get("ri") == registry_said
        )
    ]
    exported_credentials = [
        credential for credential in credentials if credential.said == credential_said
    ]

    assert registry_events, [
        {"ilk": event.ilk, "pre": event.pre, "ked": event.ked}
        for event in tel_events
    ]
    assert issue_events, [
        {"ilk": event.ilk, "pre": event.pre, "ked": event.ked}
        for event in tel_events
    ]
    assert exported_credentials, [
        {"said": credential.said, "registry": credential.regi}
        for credential in credentials
    ]


def _assert_registry_visible(client, group_name: str, registry: dict) -> None:
    registries = client.registries().list(group_name)
    assert _registry_visible(registries, registry), registries


def _assert_registry_not_visible(client, group_name: str, registry: dict) -> None:
    registries = client.registries().list(group_name)
    assert not _registry_visible(registries, registry), registries


def _assert_issued_credential_exportable(
    client,
    *,
    issuer_prefix: str,
    registry_said: str,
    said: str,
) -> None:
    issued = wait_for_issued_credential(client, issuer_prefix, said)
    fetched = poll_until(
        lambda: client.credentials().get(said),
        ready=lambda credential: credential["sad"]["d"] == said,
        timeout=120.0,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"credential {said} direct read",
        retry_exceptions=(HTTPError,),
    )
    fetched_cesr = poll_until(
        lambda: client.credentials().get(said, includeCESR=True),
        ready=bool,
        timeout=120.0,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"credential {said} CESR export",
        retry_exceptions=(HTTPError,),
    )
    exported = client.credentials().export(said)
    state = poll_until(
        lambda: client.credentials().state(registry_said, said),
        ready=lambda credential_state: credential_state["et"] == "iss",
        timeout=120.0,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"credential {said} TEL state in registry {registry_said}",
        retry_exceptions=(HTTPError,),
    )

    assert issued["sad"]["d"] == said
    assert fetched["sad"]["d"] == said
    assert fetched_cesr
    assert exported == fetched_cesr
    assert state["et"] == "iss"
    _assert_cesr_export_contains_registry_and_credential(
        fetched_cesr,
        registry_said=registry_said,
        credential_said=said,
    )


def _create_registry_and_issue_credential(
    client_a,
    member_a_name: str,
    client_b,
    member_b_name: str,
    group_name: str,
    registry_name: str,
    *,
    recipient: str,
    data: dict,
    schema: str = QVI_SCHEMA_SAID,
    edges: dict | None = None,
    rules: dict | None = None,
) -> dict:
    member_a = client_a.identifiers().get(member_a_name)
    member_b = client_b.identifiers().get(member_b_name)
    registry_nonce = coring.randomNonce()
    registry_operation_a, registry_meta_a = create_multisig_registry(
        client_a,
        local_member_name=member_a_name,
        group_name=group_name,
        other_member_prefixes=[member_b["prefix"]],
        registry_name=registry_name,
        nonce=registry_nonce,
        is_initiator=True,
    )
    _, registry_request_b = wait_for_multisig_request(client_b, "/multisig/vcp")
    registry_operation_b, registry_meta_b = create_multisig_registry(
        client_b,
        local_member_name=member_b_name,
        group_name=group_name,
        other_member_prefixes=[member_a["prefix"]],
        registry_name=registry_name,
        nonce=registry_nonce,
        request=registry_request_b,
    )
    wait_for_operation(client_a, registry_operation_a)
    wait_for_operation(client_b, registry_operation_b)
    registry_a, registry_b = wait_for_multisig_registry_convergence(
        client_a,
        client_b,
        group_name=group_name,
        registry_name=registry_name,
    )

    timestamp = helping.nowIso8601()
    creder_a, iserder_a, anc_a, sigs_a, issue_operation_a, _ = issue_multisig_credential(
        client_a,
        local_member_name=member_a_name,
        group_name=group_name,
        other_member_prefixes=[member_b["prefix"]],
        registry_name=registry_name,
        recipient=recipient,
        data=data,
        schema=schema,
        edges=edges,
        rules=rules,
        timestamp=timestamp,
        is_initiator=True,
    )
    _, issue_request_b = wait_for_multisig_request(client_b, "/multisig/iss")
    creder_b, iserder_b, anc_b, sigs_b, issue_operation_b, _ = issue_multisig_credential(
        client_b,
        local_member_name=member_b_name,
        group_name=group_name,
        other_member_prefixes=[member_a["prefix"]],
        registry_name=registry_name,
        recipient=recipient,
        data=data,
        schema=schema,
        edges=edges,
        rules=rules,
        timestamp=timestamp,
        request=issue_request_b,
    )
    wait_for_operation(client_a, issue_operation_a)
    wait_for_operation(client_b, issue_operation_b)
    wait_for_multisig_credential_state_convergence(
        client_a,
        client_b,
        registry_said=registry_a["regk"],
        credential_said=creder_a.said,
        expected_et="iss",
    )

    group_a = client_a.identifiers().get(group_name)
    group_b = client_b.identifiers().get(group_name)
    assert registry_meta_a["vcp_said"] == registry_meta_b["vcp_said"]
    assert registry_a["regk"] == registry_b["regk"]
    assert creder_a.said == creder_b.said
    _assert_registry_visible(client_a, group_name, registry_a)
    _assert_registry_visible(client_b, group_name, registry_b)
    _assert_issued_credential_exportable(
        client_a,
        issuer_prefix=group_a["prefix"],
        registry_said=registry_a["regk"],
        said=creder_a.said,
    )
    _assert_issued_credential_exportable(
        client_b,
        issuer_prefix=group_b["prefix"],
        registry_said=registry_b["regk"],
        said=creder_a.said,
    )

    return {
        "registry_a": registry_a,
        "registry_b": registry_b,
        "creder_a": creder_a,
        "creder_b": creder_b,
        "iserder_a": iserder_a,
        "iserder_b": iserder_b,
        "anc_a": anc_a,
        "anc_b": anc_b,
        "sigs_a": sigs_a,
        "sigs_b": sigs_b,
    }


def _wait_for_credential_state_convergence(
    clients: list,
    *,
    registry_said: str,
    credential_said: str,
    expected_et: str,
) -> tuple[dict, ...]:
    def normalized_state(state: dict) -> dict:
        normalized = dict(state)
        normalized.pop("dt", None)
        return normalized

    return poll_until(
        lambda: tuple(
            client.credentials().state(registry_said, credential_said)
            for client in clients
        ),
        ready=lambda states: (
            all(state.get("et") == expected_et for state in states)
            and all(
                normalized_state(state) == normalized_state(states[0])
                for state in states
            )
        ),
        timeout=120.0,
        interval=POLL_INTERVAL,
        describe=(
            "multisig credential state convergence "
            f"(registry_said={registry_said}, credential_said={credential_said}, expected_et={expected_et!r})"
        ),
        retry_exceptions=(HTTPError,),
    )


def _wait_for_multisig_issuance_request(client, credential_said: str) -> tuple[dict, list[dict]]:
    def fetch_matching_request():
        notes = [
            note
            for note in client.notifications().list().get("notes", [])
            if not note.get("r") and note.get("a", {}).get("r") == "/multisig/iss"
        ]
        for note in reversed(notes):
            try:
                request = client.groups().get_request(note["a"]["d"])
            except HTTPError:
                continue

            if not request or request[0]["exn"]["r"] != "/multisig/iss":
                continue

            acdc = request[0]["exn"].get("e", {}).get("acdc", {})
            if acdc.get("d") == credential_said:
                return note, request

        return None

    note, request = poll_until(
        fetch_matching_request,
        ready=lambda value: value is not None,
        timeout=120.0,
        interval=POLL_INTERVAL,
        describe=f"multisig issuance request for credential {credential_said}",
        retry_exceptions=(HTTPError,),
    )
    client.notifications().mark(note["i"])
    return note, request


def _issue_post_join_credential_with_all_members(
    client_a,
    member_a_name: str,
    client_b,
    member_b_name: str,
    client_c,
    member_c_name: str,
    group_name: str,
    registry: dict,
    *,
    recipient: str,
    data: dict,
    schema: str = QVI_SCHEMA_SAID,
    edges: dict | None = None,
    rules: dict | None = None,
) -> dict:
    member_a = client_a.identifiers().get(member_a_name)
    member_b = client_b.identifiers().get(member_b_name)
    member_c = client_c.identifiers().get(member_c_name)
    group_a = client_a.identifiers().get(group_name)
    group_b = client_b.identifiers().get(group_name)
    group_c = client_c.identifiers().get(group_name)
    assert group_a["prefix"] == group_b["prefix"] == group_c["prefix"]

    timestamp = helping.nowIso8601()
    creder_a, _, _, _, issue_operation_a, _ = issue_multisig_credential(
        client_a,
        local_member_name=member_a_name,
        group_name=group_name,
        other_member_prefixes=[member_b["prefix"], member_c["prefix"]],
        registry_name=registry["name"],
        recipient=recipient,
        data=data,
        schema=schema,
        edges=edges,
        rules=rules,
        timestamp=timestamp,
        is_initiator=True,
    )
    _, issue_request_b = _wait_for_multisig_issuance_request(client_b, creder_a.said)
    _, issue_request_c = _wait_for_multisig_issuance_request(client_c, creder_a.said)

    creder_b, _, _, _, issue_operation_b, _ = issue_multisig_credential(
        client_b,
        local_member_name=member_b_name,
        group_name=group_name,
        other_member_prefixes=[member_a["prefix"], member_c["prefix"]],
        registry_name=registry["name"],
        recipient=recipient,
        data=data,
        schema=schema,
        edges=edges,
        rules=rules,
        timestamp=timestamp,
        request=issue_request_b,
    )
    creder_c, _, _, _, issue_operation_c, _ = issue_multisig_credential(
        client_c,
        local_member_name=member_c_name,
        group_name=group_name,
        other_member_prefixes=[member_a["prefix"], member_b["prefix"]],
        registry_name=registry["name"],
        recipient=recipient,
        data=data,
        schema=schema,
        edges=edges,
        rules=rules,
        timestamp=timestamp,
        request=issue_request_c,
    )

    assert creder_a.said == creder_b.said == creder_c.said
    wait_for_operation(client_a, issue_operation_a)
    wait_for_operation(client_b, issue_operation_b)
    wait_for_operation(client_c, issue_operation_c)
    _wait_for_credential_state_convergence(
        [client_a, client_b, client_c],
        registry_said=registry["regk"],
        credential_said=creder_a.said,
        expected_et="iss",
    )
    for client in (client_a, client_b, client_c):
        _assert_registry_visible(client, group_name, registry)
        _assert_issued_credential_exportable(
            client,
            issuer_prefix=group_a["prefix"],
            registry_said=registry["regk"],
            said=creder_a.said,
        )

    return {
        "creder_a": creder_a,
        "creder_b": creder_b,
        "creder_c": creder_c,
    }


def _import_credential_cesr_to_late_member(
    *,
    exporting_client,
    late_client,
    late_member_prefix: str,
    registry_said: str,
    credential_said: str,
) -> None:
    cesr = exporting_client.credentials().get(credential_said, includeCESR=True)
    assert cesr
    _assert_cesr_export_contains_registry_and_credential(
        cesr,
        registry_said=registry_said,
        credential_said=credential_said,
    )

    live_stack = late_client._integration_live_stack
    response = requests.put(
        f"{live_stack['keria_agent_url']}/",
        data=cesr,
        headers={
            "CESR-DESTINATION": late_member_prefix,
            "Content-Type": "application/octet-stream",
        },
        timeout=30,
    )
    response.raise_for_status()
    assert response.status_code == 204


def _assert_credential_visible(client, credential_said: str) -> None:
    poll_until(
        lambda: client.credentials().get(credential_said),
        ready=lambda credential: credential["sad"]["d"] == credential_said,
        timeout=45.0,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"imported credential {credential_said} direct read",
        retry_exceptions=(HTTPError,),
    )


def _assert_credential_state_visible(
    client,
    *,
    registry_said: str,
    credential_said: str,
) -> None:
    poll_until(
        lambda: client.credentials().state(registry_said, credential_said),
        ready=lambda state: state["et"] == "iss",
        timeout=120.0,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"imported credential {credential_said} TEL state in registry {registry_said}",
        retry_exceptions=(HTTPError,),
    )


def _rename_imported_registry(client, group_name: str, registry: dict) -> dict:
    def fetch_or_rename():
        try:
            return client.registries().get(group_name, registry["name"])
        except HTTPError:
            return client.registries().rename(
                group_name,
                registry["regk"],
                registry["name"],
            )

    return poll_until(
        fetch_or_rename,
        ready=lambda renamed: renamed["regk"] == registry["regk"] and renamed["name"] == registry["name"],
        timeout=120.0,
        interval=POLL_INTERVAL,
        describe=f"imported registry {registry['regk']} renamed to {registry['name']} for {group_name}",
        retry_exceptions=(HTTPError,),
    )


def _apply_arsh_registry_import_workaround(
    *,
    exporting_client,
    late_client,
    late_member_prefix: str,
    group_name: str,
    registry: dict,
    credential_said: str,
) -> None:
    _import_credential_cesr_to_late_member(
        exporting_client=exporting_client,
        late_client=late_client,
        late_member_prefix=late_member_prefix,
        registry_said=registry["regk"],
        credential_said=credential_said,
    )
    _rename_imported_registry(late_client, group_name, registry)
    _assert_registry_visible(late_client, group_name, registry)
    _assert_credential_state_visible(
        late_client,
        registry_said=registry["regk"],
        credential_said=credential_said,
    )
    _assert_credential_visible(late_client, credential_said)


def _submit_multisig_admit_from_local_state(
    client,
    *,
    local_member_name: str,
    group_name: str,
    other_member_prefixes: list[str],
    issuer_prefix: str,
    grant_said: str,
    timestamp: str,
) -> dict:
    local_member = client.identifiers().get(local_member_name)
    group_hab = client.identifiers().get(group_name)
    admit, sigs, atc = client.ipex().admit(
        group_hab,
        "",
        grant_said,
        issuer_prefix,
        timestamp,
    )
    result = client.ipex().submitAdmit(
        group_name,
        exn=admit,
        sigs=sigs,
        atc=atc,
        recp=[issuer_prefix],
    )
    seal = eventing.SealEvent(
        i=group_hab["prefix"],
        s=group_hab["state"]["ee"]["s"],
        d=group_hab["state"]["ee"]["d"],
    )
    admit_ims = eventing.messagize(
        serder=admit,
        sigers=[csigning.Siger(qb64=sig) for sig in sigs],
        seal=seal,
    )
    admit_ims.extend(atc.encode("utf-8"))
    client.exchanges().send(
        local_member_name,
        "multisig",
        sender=local_member,
        route="/multisig/exn",
        payload=dict(gid=group_hab["prefix"]),
        embeds=dict(exn=admit_ims),
        recipients=other_member_prefixes,
    )
    return result


def _admit_multisig_credential_to_holder_group(
    issuer_client_a,
    issuer_member_a_name: str,
    issuer_client_b,
    issuer_member_b_name: str,
    issuer_group_name: str,
    holder_client_a,
    holder_member_a_name: str,
    holder_client_b,
    holder_member_b_name: str,
    holder_group_name: str,
    *,
    issuer_prefix: str,
    holder_prefix: str,
    issued: dict,
) -> tuple[dict, dict]:
    issuer_member_a = issuer_client_a.identifiers().get(issuer_member_a_name)
    issuer_member_b = issuer_client_b.identifiers().get(issuer_member_b_name)
    holder_member_a = holder_client_a.identifiers().get(holder_member_a_name)
    holder_member_b = holder_client_b.identifiers().get(holder_member_b_name)

    grant_timestamp = helping.nowIso8601()
    grant_operation_a = send_multisig_credential_grant(
        issuer_client_a,
        local_member_name=issuer_member_a_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_b["prefix"]],
        recipient=holder_prefix,
        creder=issued["creder_a"],
        iserder=issued["iserder_a"],
        anc=issued["anc_a"],
        sigs=issued["sigs_a"],
        timestamp=grant_timestamp,
        is_initiator=True,
    )
    grant_operation_b = send_multisig_credential_grant(
        issuer_client_b,
        local_member_name=issuer_member_b_name,
        group_name=issuer_group_name,
        other_member_prefixes=[issuer_member_a["prefix"]],
        recipient=holder_prefix,
        creder=issued["creder_b"],
        iserder=issued["iserder_b"],
        anc=issued["anc_b"],
        sigs=issued["sigs_b"],
        timestamp=grant_timestamp,
    )
    wait_for_operation(issuer_client_a, grant_operation_a)
    wait_for_operation(issuer_client_b, grant_operation_b)

    grant_client_index, grant_note = wait_for_notification_any(
        [holder_client_a, holder_client_b],
        "/exn/ipex/grant",
    )
    grant_said = grant_note["a"]["d"]
    admit_timestamp = helping.nowIso8601()
    if grant_client_index == 0:
        first_client, first_name, first_peers = holder_client_a, holder_member_a_name, [holder_member_b["prefix"]]
        second_client, second_name, second_peers = holder_client_b, holder_member_b_name, [holder_member_a["prefix"]]
    else:
        first_client, first_name, first_peers = holder_client_b, holder_member_b_name, [holder_member_a["prefix"]]
        second_client, second_name, second_peers = holder_client_a, holder_member_a_name, [holder_member_b["prefix"]]

    first_admit_operation = _submit_multisig_admit_from_local_state(
        first_client,
        local_member_name=first_name,
        group_name=holder_group_name,
        other_member_prefixes=first_peers,
        issuer_prefix=issuer_prefix,
        grant_said=grant_said,
        timestamp=admit_timestamp,
    )
    wait_for_exchange(second_client, grant_said, expected_route="/ipex/grant")
    second_admit_operation = _submit_multisig_admit_from_local_state(
        second_client,
        local_member_name=second_name,
        group_name=holder_group_name,
        other_member_prefixes=second_peers,
        issuer_prefix=issuer_prefix,
        grant_said=grant_said,
        timestamp=admit_timestamp,
    )
    wait_for_operation(first_client, first_admit_operation)
    wait_for_operation(second_client, second_admit_operation)
    assert wait_for_notification(issuer_client_a, "/exn/ipex/admit")["a"]["r"] == "/exn/ipex/admit"
    assert wait_for_notification(issuer_client_b, "/exn/ipex/admit")["a"]["r"] == "/exn/ipex/admit"

    return wait_for_multisig_received_credential(
        holder_client_a,
        holder_client_b,
        issued["creder_a"].said,
    )


def test_late_joined_member_cannot_see_existing_multisig_registry_with_issued_credential(client_factory):
    issuer_client_a = client_factory()
    issuer_client_b = client_factory()
    late_client_c = client_factory()
    holder_client = client_factory()

    member_a_name = alias("issuer-a")
    member_b_name = alias("issuer-b")
    late_member_name = alias("issuer-c")
    holder_name = alias("holder")
    group_name = alias("issuer-group")
    registry_name = alias("issuer-registry")

    member_a = create_identifier(issuer_client_a, member_a_name, wits=TEST_WITNESS_AIDS)
    member_b = create_identifier(issuer_client_b, member_b_name, wits=TEST_WITNESS_AIDS)
    late_member = create_identifier(late_client_c, late_member_name, wits=TEST_WITNESS_AIDS)
    holder = create_identifier(holder_client, holder_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(issuer_client_a, member_a_name, issuer_client_b, member_b_name)
    exchange_agent_oobis(issuer_client_a, member_a_name, holder_client, holder_name)
    exchange_agent_oobis(issuer_client_b, member_b_name, holder_client, holder_name)
    _resolve_schema_set(issuer_client_a, QVI_SCHEMA_SAID)
    _resolve_schema_set(issuer_client_b, QVI_SCHEMA_SAID)
    _resolve_schema_set(late_client_c, QVI_SCHEMA_SAID)

    group_a, group_b = create_multisig_group(
        issuer_client_a,
        member_a_name,
        issuer_client_b,
        member_b_name,
        group_name,
        wits=TEST_WITNESS_AIDS,
    )
    group_oobi = expose_multisig_agent_oobi(
        issuer_client_a,
        member_a_name,
        issuer_client_b,
        member_b_name,
        group_name,
    )
    resolve_oobi(holder_client, group_oobi, alias=group_name)

    issued = _create_registry_and_issue_credential(
        issuer_client_a,
        member_a_name,
        issuer_client_b,
        member_b_name,
        group_name,
        registry_name,
        recipient=holder["prefix"],
        data=SIMPLE_ISSUE_DATA,
    )

    _, _, group_c = rotate_in_late_multisig_member(
        issuer_client_a,
        member_a_name,
        issuer_client_b,
        member_b_name,
        late_client_c,
        late_member_name,
        group_name,
        group_oobi=group_oobi,
    )
    assert group_c["prefix"] == group_a["prefix"] == group_b["prefix"]
    assert_multisig_members(
        late_client_c,
        group_name,
        count=3,
        signing_aids=[member_a["prefix"], member_b["prefix"], late_member["prefix"]],
        rotation_aids=[member_a["prefix"], member_b["prefix"], late_member["prefix"]],
    )
    _assert_registry_visible(issuer_client_a, group_name, issued["registry_a"])
    _assert_registry_visible(issuer_client_b, group_name, issued["registry_b"])
    _assert_registry_not_visible(late_client_c, group_name, issued["registry_a"])
    _apply_arsh_registry_import_workaround(
        exporting_client=issuer_client_a,
        late_client=late_client_c,
        late_member_prefix=late_member["prefix"],
        group_name=group_name,
        registry=issued["registry_a"],
        credential_said=issued["creder_a"].said,
    )
    post_join_issued = _issue_post_join_credential_with_all_members(
        issuer_client_a,
        member_a_name,
        issuer_client_b,
        member_b_name,
        late_client_c,
        late_member_name,
        group_name,
        issued["registry_a"],
        recipient=holder["prefix"],
        data={"LEI": "54930084UKLVMY22DS16"},
    )
    assert post_join_issued["creder_a"].said != issued["creder_a"].said


def test_late_joined_qvi_member_cannot_see_delegated_qvi_registry_with_issued_credential(client_factory):
    geda_client_a = client_factory()
    geda_client_b = client_factory()
    qvi_client_a = client_factory()
    qvi_client_b = client_factory()
    qvi_late_client_c = client_factory()
    le_client = client_factory()

    geda_member_a_name = alias("geda-a")
    geda_member_b_name = alias("geda-b")
    qvi_member_a_name = alias("qvi-a")
    qvi_member_b_name = alias("qvi-b")
    qvi_late_member_name = alias("qvi-c")
    le_name = alias("legal-entity")
    geda_group_name = alias("geda-group")
    qvi_group_name = alias("qvi-group")
    geda_registry_name = alias("geda-registry")
    qvi_registry_name = alias("qvi-registry")

    geda_member_a = create_identifier(geda_client_a, geda_member_a_name, wits=TEST_WITNESS_AIDS)
    geda_member_b = create_identifier(geda_client_b, geda_member_b_name, wits=TEST_WITNESS_AIDS)
    qvi_member_a = create_identifier(qvi_client_a, qvi_member_a_name, wits=TEST_WITNESS_AIDS)
    qvi_member_b = create_identifier(qvi_client_b, qvi_member_b_name, wits=TEST_WITNESS_AIDS)
    qvi_late_member = create_identifier(qvi_late_client_c, qvi_late_member_name, wits=TEST_WITNESS_AIDS)
    le_holder = create_identifier(le_client, le_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(geda_client_a, geda_member_a_name, geda_client_b, geda_member_b_name)
    exchange_agent_oobis(qvi_client_a, qvi_member_a_name, qvi_client_b, qvi_member_b_name)
    exchange_agent_oobis(qvi_client_a, qvi_member_a_name, le_client, le_name)
    exchange_agent_oobis(qvi_client_b, qvi_member_b_name, le_client, le_name)
    _resolve_schema_set(geda_client_a, QVI_SCHEMA_SAID)
    _resolve_schema_set(geda_client_b, QVI_SCHEMA_SAID)
    _resolve_schema_set(qvi_client_a, QVI_SCHEMA_SAID, LE_SCHEMA_SAID)
    _resolve_schema_set(qvi_client_b, QVI_SCHEMA_SAID, LE_SCHEMA_SAID)
    _resolve_schema_set(qvi_late_client_c, QVI_SCHEMA_SAID, LE_SCHEMA_SAID)

    geda_group_a, geda_group_b = create_multisig_group(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    geda_group_oobi = expose_multisig_agent_oobi(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
    )
    resolve_oobi(qvi_client_a, geda_group_oobi, alias=geda_group_name)
    resolve_oobi(qvi_client_b, geda_group_oobi, alias=geda_group_name)

    qvi_participants = [qvi_member_a["prefix"], qvi_member_b["prefix"]]
    qvi_operation_a, qvi_serder = start_multisig_incept(
        qvi_client_a,
        group_name=qvi_group_name,
        local_member_name=qvi_member_a_name,
        participants=qvi_participants,
        isith=2,
        nsith=2,
        toad=len(TEST_WITNESS_AIDS),
        wits=TEST_WITNESS_AIDS,
        delpre=geda_group_a["prefix"],
    )
    qvi_operation_b = accept_multisig_incept(
        qvi_client_b,
        group_name=qvi_group_name,
        local_member_name=qvi_member_b_name,
    )
    approve_multisig_delegation(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
        qvi_serder.pre,
    )
    query_key_state(qvi_client_a, geda_group_a["prefix"], sn="1")
    query_key_state(qvi_client_b, geda_group_a["prefix"], sn="1")
    wait_for_operation(qvi_client_a, qvi_operation_a)
    wait_for_operation(qvi_client_b, qvi_operation_b)
    qvi_group_a = qvi_client_a.identifiers().get(qvi_group_name)
    qvi_group_b = qvi_client_b.identifiers().get(qvi_group_name)
    assert qvi_group_a["prefix"] == qvi_group_b["prefix"] == qvi_serder.pre
    assert qvi_group_a["state"]["di"] == geda_group_a["prefix"]
    assert qvi_group_b["state"]["di"] == geda_group_a["prefix"]

    qvi_group_oobi = expose_multisig_agent_oobi(
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_group_name,
    )
    resolve_oobi(geda_client_a, qvi_group_oobi, alias=qvi_group_name)
    resolve_oobi(geda_client_b, qvi_group_oobi, alias=qvi_group_name)
    resolve_oobi(le_client, qvi_group_oobi, alias=qvi_group_name)

    geda_issued_qvi = _create_registry_and_issue_credential(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
        geda_registry_name,
        recipient=qvi_group_a["prefix"],
        data=QVI_DATA,
    )
    qvi_received_qvi_a, qvi_received_qvi_b = _admit_multisig_credential_to_holder_group(
        geda_client_a,
        geda_member_a_name,
        geda_client_b,
        geda_member_b_name,
        geda_group_name,
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_group_name,
        issuer_prefix=geda_group_a["prefix"],
        holder_prefix=qvi_group_a["prefix"],
        issued=geda_issued_qvi,
    )

    qvi_issued_le = _create_registry_and_issue_credential(
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_group_name,
        qvi_registry_name,
        recipient=le_holder["prefix"],
        data=LE_DATA,
        schema=LE_SCHEMA_SAID,
        edges=_source_edges("qvi", qvi_received_qvi_a),
        rules=_le_rules(),
    )
    resolve_oobi(qvi_late_client_c, geda_group_oobi, alias=geda_group_name)

    def approve_qvi_rotation(rotation_serder):
        anchor = dict(
            i=rotation_serder.pre,
            s=rotation_serder.ked["s"],
            d=rotation_serder.said,
        )
        interact_multisig_group(
            geda_client_a,
            geda_member_a_name,
            geda_client_b,
            geda_member_b_name,
            geda_group_name,
            data=[anchor],
        )
        geda_state = geda_client_a.identifiers().get(geda_group_name)["state"]
        query_key_state(qvi_client_a, geda_group_a["prefix"], sn=geda_state["s"])
        query_key_state(qvi_client_b, geda_group_a["prefix"], sn=geda_state["s"])
        query_key_state(qvi_late_client_c, geda_group_a["prefix"], sn=geda_state["s"])

    _, _, qvi_group_c = rotate_in_late_multisig_member(
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_late_client_c,
        qvi_late_member_name,
        qvi_group_name,
        group_oobi=qvi_group_oobi,
        approve_delegated_rotation=approve_qvi_rotation,
    )
    assert qvi_group_c["prefix"] == qvi_group_a["prefix"]
    assert qvi_group_c["state"]["di"] == geda_group_a["prefix"]
    assert_multisig_members(
        qvi_late_client_c,
        qvi_group_name,
        count=3,
        signing_aids=[qvi_member_a["prefix"], qvi_member_b["prefix"], qvi_late_member["prefix"]],
        rotation_aids=[qvi_member_a["prefix"], qvi_member_b["prefix"], qvi_late_member["prefix"]],
    )
    _assert_registry_visible(qvi_client_a, qvi_group_name, qvi_issued_le["registry_a"])
    _assert_registry_visible(qvi_client_b, qvi_group_name, qvi_issued_le["registry_b"])
    _assert_registry_not_visible(qvi_late_client_c, qvi_group_name, qvi_issued_le["registry_a"])
    _apply_arsh_registry_import_workaround(
        exporting_client=qvi_client_a,
        late_client=qvi_late_client_c,
        late_member_prefix=qvi_late_member["prefix"],
        group_name=qvi_group_name,
        registry=qvi_issued_le["registry_a"],
        credential_said=qvi_issued_le["creder_a"].said,
    )
    post_join_qvi_issued_le = _issue_post_join_credential_with_all_members(
        qvi_client_a,
        qvi_member_a_name,
        qvi_client_b,
        qvi_member_b_name,
        qvi_late_client_c,
        qvi_late_member_name,
        qvi_group_name,
        qvi_issued_le["registry_a"],
        recipient=le_holder["prefix"],
        data={"LEI": "875500T18L8QJY2K8O09"},
        schema=LE_SCHEMA_SAID,
        edges=_source_edges("qvi", qvi_received_qvi_a),
        rules=_le_rules(),
    )
    assert post_join_qvi_issued_le["creder_a"].said != qvi_issued_le["creder_a"].said
