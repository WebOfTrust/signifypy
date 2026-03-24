"""
Shared helpers for live SignifyPy integration workflows.

These helpers intentionally encode the workflow substance that SignifyTS uses
in its own integration suite: witness-backed identifiers by default for
OOBI-dependent scenarios, explicit waits around long-running operations, and
multisig choreography expressed in small reusable steps instead of inline test
bodies.
"""

from __future__ import annotations

import secrets
import string
import time
import json
import os

import requests
from keri.app import signing as app_signing
from keri.app.keeping import Algos
from keri.core import coring, eventing, serdering
from keri.core import signing as csigning
from keri.core.coring import Tiers
from keri.help import helping
from requests import HTTPError

from signify.app.clienting import SignifyClient
from tests.integration.constants import (
    SCHEMA_SAID,
    TEST_WITNESS_AIDS,
    WITNESS_AIDS,
)

# The live stack runs entirely on localhost, so polling every 500-1000ms is
# more conservative than necessary for most long-running op and notification
# waits. Keep the defaults tighter to reduce idle time across the suite, but
# allow maintainers/CI to tune them back up if a slower environment needs it.
POLL_INTERVAL = float(os.getenv("SIGNIFYPY_INTEGRATION_POLL_INTERVAL", "0.25"))
HEAVY_POLL_INTERVAL = float(
    os.getenv("SIGNIFYPY_INTEGRATION_HEAVY_POLL_INTERVAL", "0.5")
)
_UNSET = object()


# Bootstrap and stack-derived lookup helpers

def random_passcode() -> str:
    """Create a 21-character passcode suitable for booting a fresh client."""
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(21))


def alias(prefix: str) -> str:
    """Create a collision-resistant alias so live tests stay independent."""
    return f"{prefix}-{secrets.token_hex(4)}"


def controller_boot_data(client: SignifyClient) -> dict:
    """Build the explicit boot payload used by manual-controller tests."""
    evt, siger = client.ctrl.event()
    return dict(
        icp=evt.ked,
        sig=siger.qb64,
        stem=client.ctrl.stem,
        pidx=1,
        tier=client.ctrl.tier,
    )


def boot_client_manually(client: SignifyClient, live_stack) -> dict:
    """Boot a controller by posting the inception payload directly to KERIA."""
    response = requests.post(
        f"{live_stack['keria_boot_url']}/boot",
        json=controller_boot_data(client),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def connect_client(
    live_stack,
    *,
    passcode: str | None = None,
    boot_mode: str = "client",
) -> SignifyClient:
    """Boot and connect a brand-new Signify client against the live stack.

    This helper owns the full controller bootstrap path used by the live tests:
    boot the remote agent, connect the local controller, and assert the agent
    delegation relationship is present before returning the client.

    The returned client also carries the active live-stack mapping on a private
    attribute so later helpers can derive stack-local witness/schema OOBIs
    without reaching back into pytest fixtures.
    """
    client = SignifyClient(
        passcode=passcode or random_passcode(),
        tier=Tiers.low,
        url=live_stack["keria_admin_url"],
        boot_url=live_stack["keria_boot_url"],
    )
    if boot_mode == "client":
        body = client.boot()
    elif boot_mode == "manual":
        body = boot_client_manually(client, live_stack)
    else:
        raise ValueError(f"unsupported boot_mode={boot_mode}")
    assert isinstance(body, dict)
    client.connect()
    assert client.agent is not None
    client._integration_live_stack = live_stack
    return client


def _require_live_stack(client: SignifyClient) -> dict:
    """Return the active live stack topology attached to a test client."""
    live_stack = getattr(client, "_integration_live_stack", None)
    if not isinstance(live_stack, dict):
        raise RuntimeError("integration client is missing attached live stack topology")
    return live_stack


def witness_oobi_by_aid(client: SignifyClient) -> dict[str, str]:
    """Return the current stack's witness OOBIs keyed by witness AID."""
    return dict(zip(WITNESS_AIDS, _require_live_stack(client)["witness_oobis"]))


def schema_oobi(client: SignifyClient) -> str:
    """Return the current stack's primary schema OOBI."""
    return _require_live_stack(client)["schema_oobi"]


def additional_schema_oobis(client: SignifyClient) -> dict[str, str]:
    """Return the current stack's additional sample schema OOBIs."""
    return dict(_require_live_stack(client)["additional_schema_oobis"])


def resolve_schema_oobi(client: SignifyClient, *, alias: str = "schema") -> dict:
    """Resolve the current stack's primary schema OOBI."""
    return resolve_oobi(client, schema_oobi(client), alias=alias)


def _format_poll_value(value) -> str:
    """Render the last observed poll value in timeout messages."""
    if value is _UNSET:
        return "unset"
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, sort_keys=True)
        except TypeError:
            return repr(value)
    return repr(value)


def poll_until(
    fetch,
    *,
    ready,
    timeout: float,
    interval: float,
    describe: str,
    retry_exceptions: tuple[type[BaseException], ...] = (),
):
    """Poll until a fetched value satisfies `ready`, or raise a rich timeout.

    The live integration layer spends most of its time waiting on remote KERIA
    state. Centralizing the wait loop keeps timeout diagnostics consistent and
    makes it cheaper to strengthen weak transport waits into stronger state
    checks later.

    Maintainer rule of thumb: prefer wrapping this in a domain-specific helper
    over adding raw `time.sleep(...)` loops to tests. That keeps the wait
    contract explicit and the timeout errors actionable.
    """
    deadline = time.monotonic() + timeout
    last_value = _UNSET
    last_error = None

    while True:
        try:
            value = fetch()
        except retry_exceptions as err:
            last_error = str(err)
        else:
            last_value = value
            if ready(value):
                return value

        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"timed out waiting for {describe}; "
                f"last_error={last_error!r}; "
                f"last_value={_format_poll_value(last_value)}"
            )
        time.sleep(interval)


def _matching_unread_notes(client: SignifyClient, route: str) -> list[dict]:
    """Return unread notifications for one route."""
    return [
        note
        for note in client.notifications().list()["notes"]
        if note["a"].get("r") == route and note.get("r") is False
    ]


def _contact_by_alias(client: SignifyClient, contact_alias: str) -> dict | None:
    """Return one contact record by alias when present."""
    for contact in client.contacts().list():
        if contact.get("alias") == contact_alias:
            return contact
    return None


def wait_for_operation(client: SignifyClient, operation: dict, *, timeout: float = 120.0) -> dict:
    """Poll a KERIA long-running operation until completion or timeout."""
    if operation["done"]:
        return operation

    return client.operations().wait(
        operation,
        timeout=timeout,
        interval=POLL_INTERVAL,
        max_interval=POLL_INTERVAL,
        backoff=1.0,
    )


def wait_for_notification(
    client: SignifyClient,
    route: str,
    *,
    timeout: float = 120.0,
    mark_read: bool = True,
) -> dict:
    """Wait for the next unread notification on a specific route.

    Multistep workflows in this suite are driven by notifications, not just
    long-running operations. The route is therefore part of the contract:
    waiting on the wrong route often means the scenario choreography is wrong,
    not just slow.
    """
    note = poll_until(
        lambda: _matching_unread_notes(client, route),
        ready=bool,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"notification route {route}",
    )[-1]  # -1 for last, most recent notification
    if mark_read:
        client.notifications().mark(note["i"])
    return note


def notification_routes(client: SignifyClient) -> list[str]:
    """Return current notification routes for read-path assertions."""
    return [note["a"].get("r") for note in client.notifications().list()["notes"]]


def wait_for_contact_alias(client: SignifyClient, contact_alias: str, *, timeout: float = 60.0) -> dict:
    """Poll the contact list until the requested alias becomes visible."""
    return poll_until(
        lambda: _contact_by_alias(client, contact_alias),
        ready=lambda contact: contact is not None,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"contact alias {contact_alias}",
    )


def wait_for_contact_challenge_state(
    client: SignifyClient,
    contact_alias: str,
    *,
    expected_count: int = 1,
    authenticated: bool | None = True,
    timeout: float = 60.0,
) -> dict:
    """Poll one contact record until its challenge list reaches the expected state."""

    def _ready(contact: dict | None) -> bool:
        if contact is None:
            return False
        challenges = contact.get("challenges", [])
        if len(challenges) != expected_count:
            return False
        if authenticated is None:
            return True
        return all(challenge.get("authenticated") is authenticated for challenge in challenges)

    return poll_until(
        lambda: _contact_by_alias(client, contact_alias),
        ready=_ready,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=(
            f"contact challenge state for alias {contact_alias} "
            f"(expected_count={expected_count}, authenticated={authenticated})"
        ),
    )


def contact_aliases(client: SignifyClient) -> set[str]:
    """Return the current visible contact aliases."""
    return {contact.get("alias") for contact in client.contacts().list()}


def wait_for_credential(client: SignifyClient, said: str, *, timeout: float = 120.0) -> dict:
    """Poll received credentials until the expected SAID appears."""
    return poll_until(
        lambda: next(
            (
                credential
                for credential in client.credentials().list()
                if credential["sad"]["d"] == said
            ),
            None,
        ),
        ready=lambda credential: credential is not None,
        timeout=timeout,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"credential {said}",
    )


def wait_for_multisig_request(
    client: SignifyClient,
    route: str,
    *,
    timeout: float = 120.0,
) -> tuple[dict, list[dict]]:
    """Wait for a multisig notification and the corresponding stored request payload.

    This is useful for registry/issuance diagnostics on the non-initiator path:
    we can prove the join signal arrived and inspect the embedded payload before
    deciding whether local reconstruction drifted from the peer proposal.

    The notification is only the discovery mechanism. Success means the stored
    request payload is retrievable and parseable through `groups().get_request`.
    """
    note = wait_for_notification(client, route, timeout=timeout)
    request = poll_until(
        lambda: client.groups().get_request(note["a"]["d"]),
        ready=lambda request: bool(request) and request[0]["exn"]["r"] == route,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"multisig request payload for route {route}",
        retry_exceptions=(HTTPError,),
    )
    return note, request


def wait_for_exchange_message(
    client: SignifyClient,
    route: str,
    *,
    timeout: float = 120.0,
) -> tuple[dict, dict]:
    """Wait for a notification and the corresponding stored exchange payload.

    This is the exchange-message sibling of `wait_for_multisig_request(...)`:
    the notification identifies *which* exchange matters, but the stronger
    readiness condition is that the exchange itself is retrievable.
    """
    note = wait_for_notification(client, route, timeout=timeout)
    exchange = poll_until(
        lambda: client.exchanges().get(note["a"]["d"]),
        ready=lambda exchange: exchange["exn"]["r"] == route,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"exchange payload for route {route}",
        retry_exceptions=(HTTPError,),
    )
    return note, exchange


def wait_for_issued_credential(
    client: SignifyClient,
    issuer_prefix: str,
    said: str,
    *,
    timeout: float = 120.0,
) -> dict:
    """Poll issued-credential visibility until the expected SAID appears."""
    return poll_until(
        lambda: next(
            (
                credential
                for credential in client.credentials().list(filtr={"-i": issuer_prefix})
                if credential["sad"]["d"] == said
            ),
            None,
        ),
        ready=lambda credential: credential is not None,
        timeout=timeout,
        interval=HEAVY_POLL_INTERVAL,
        describe=f"issued credential {said} from issuer {issuer_prefix}",
    )


def wait_for_credential_state(
    client: SignifyClient,
    *,
    registry_said: str,
    credential_said: str,
    expected_et: str | None = None,
    expected_sn: str | None = None,
    timeout: float = 120.0,
) -> dict:
    """Poll one credential TEL state until the expected revocation/issuance state is visible."""
    return poll_until(
        lambda: client.credentials().state(registry_said, credential_said),
        ready=lambda state: (
            (expected_et is None or state.get("et") == expected_et)
            and (expected_sn is None or state.get("s") == expected_sn)
        ),
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=(
            f"credential state {credential_said} in registry {registry_said} "
            f"(expected_et={expected_et!r}, expected_sn={expected_sn!r})"
        ),
        retry_exceptions=(HTTPError,),
    )


def wait_for_multisig_credential_state_convergence(
    client_a: SignifyClient,
    client_b: SignifyClient,
    *,
    registry_said: str,
    credential_said: str,
    expected_et: str,
    timeout: float = 120.0,
) -> tuple[dict, dict]:
    """Poll both issuer members until they expose one converged credential TEL state."""

    def normalized_state(state: dict) -> dict:
        normalized = dict(state)
        normalized.pop("dt", None)
        return normalized

    return poll_until(
        lambda: (
            client_a.credentials().state(registry_said, credential_said),
            client_b.credentials().state(registry_said, credential_said),
        ),
        ready=lambda states: (
            states[0].get("et") == expected_et
            and states[1].get("et") == expected_et
            and normalized_state(states[0]) == normalized_state(states[1])
        ),
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=(
            "multisig credential state convergence "
            f"(registry_said={registry_said}, credential_said={credential_said}, expected_et={expected_et!r})"
        ),
        retry_exceptions=(HTTPError,),
    )


def wait_for_multisig_registry_convergence(
    client_a: SignifyClient,
    client_b: SignifyClient,
    *,
    group_name: str,
    registry_name: str,
    timeout: float = 120.0,
) -> tuple[dict, dict]:
    """Poll both members until one multisig registry view converges on both sides."""
    def normalized_state(registry: dict) -> dict:
        """
        Pops the datetime field out so that comparing two registry dicts for the same registry
        will work. Only the datetime should be different between the two, during registry inception,
        so popping it out allows straightforward comparison.
        """
        state = dict(registry["state"])
        state.pop("dt", None)
        return state

    return poll_until(
        lambda: (
            client_a.registries().get(group_name, registry_name),
            client_b.registries().get(group_name, registry_name),
        ),
        ready=lambda registries: (
            registries[0]["regk"] == registries[1]["regk"]
            and normalized_state(registries[0]) == normalized_state(registries[1])
        ),
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"multisig registry {registry_name} convergence for {group_name}",
        retry_exceptions=(HTTPError,),
    )


def resolve_oobi(client: SignifyClient, oobi: str, alias: str | None = None) -> dict:
    """Resolve an OOBI and wait for the corresponding operation to complete.

    This is the shared bridge between explicit OOBI publication in one
    participant and contact/key-state visibility in another.
    """
    operation = client.oobis().resolve(oobi, alias=alias)
    return wait_for_operation(client, operation)


def get_end_roles(client: SignifyClient, name: str, role: str = "agent") -> list[dict]:
    """Fetch end-role authorizations for an identifier."""
    return client.get(f"/identifiers/{name}/endroles/{role}").json()


def wait_for_end_role(
    client: SignifyClient,
    name: str,
    *,
    eid: str,
    role: str = "agent",
    timeout: float = 60.0,
) -> dict:
    """Poll until an identifier exposes the expected end-role authorization."""
    return poll_until(
        lambda: next(
            (
                end_role
                for end_role in get_end_roles(client, name, role=role)
                if end_role.get("role") == role and end_role.get("eid") == eid
            ),
            None,
        ),
        ready=lambda end_role: end_role is not None,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"{role} end-role {eid} on {name}",
    )


def wait_for_identifier_oobi(
    client: SignifyClient,
    name: str,
    *,
    role: str,
    timeout: float = 60.0,
) -> list[str]:
    """Poll until an identifier exposes at least one OOBI for the requested role.

    The role is intentionally mandatory because SignifyTS is explicit about
    which publication route each workflow relies on. Hiding role selection
    behind a fallback makes tests look greener than the actual client contract.
    """
    return poll_until(
        lambda: client.oobis().get(name, role=role)["oobis"],
        ready=bool,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"{role} OOBI on {name}",
        retry_exceptions=(HTTPError,),
    )


def ensure_witness_oobis(client: SignifyClient, wits: list[str]) -> None:
    """Resolve witness OOBIs once per client before witness-backed inception.

    This mirrors the SignifyTS integration habit of making witness knowledge an
    explicit precondition of witness-backed identifier creation rather than
    relying on ambient local state.
    """
    resolved = getattr(client, "_integration_witness_oobis_resolved", set())
    if not isinstance(resolved, set):
        resolved = set()

    witness_oobis = witness_oobi_by_aid(client)
    for witness in wits:
        if witness in resolved:
            continue
        resolve_oobi(client, witness_oobis[witness], alias=f"wit-{witness[:6]}")
        resolved.add(witness)

    client._integration_witness_oobis_resolved = resolved


def resolve_identifier_oobi(
    source_client: SignifyClient,
    source_name: str,
    target_client: SignifyClient,
    *,
    role: str,
    alias: str | None = None,
) -> dict:
    """Resolve a specific published identifier OOBI from one client to another.

    Integration helpers must mirror the SignifyTS scenario's chosen OOBI role
    instead of silently falling back to some other publication route. If a test
    needs an agent OOBI, it should fail when no agent OOBI is available.
    """
    oobis = wait_for_identifier_oobi(source_client, source_name, role=role)
    return resolve_oobi(target_client, oobis[0], alias=alias or source_name)


def resolve_agent_oobi(
    source_client: SignifyClient,
    source_name: str,
    target_client: SignifyClient,
    *,
    alias: str | None = None,
) -> dict:
    """Resolve an agent OOBI exactly like the SignifyTS integration flows do."""
    return resolve_identifier_oobi(
        source_client,
        source_name,
        target_client,
        role="agent",
        alias=alias,
    )


def exchange_identifier_oobis(
    client_a: SignifyClient,
    name_a: str,
    client_b: SignifyClient,
    name_b: str,
    *,
    role: str,
) -> None:
    """Exchange a specific identifier OOBI role symmetrically between two clients."""
    resolve_identifier_oobi(client_a, name_a, client_b, role=role, alias=name_a)
    resolve_identifier_oobi(client_b, name_b, client_a, role=role, alias=name_b)


def exchange_agent_oobis(
    client_a: SignifyClient,
    name_a: str,
    client_b: SignifyClient,
    name_b: str,
) -> None:
    """Exchange agent OOBIs exactly like the SignifyTS integration flows do."""
    exchange_identifier_oobis(client_a, name_a, client_b, name_b, role="agent")


def exchange_agent_oobis_among(participants: list[tuple[SignifyClient, str]]) -> None:
    """Exchange agent OOBIs pairwise across an ordered participant list."""
    for index, (source_client, source_name) in enumerate(participants):
        for target_client, target_name in participants[index + 1 :]:
            exchange_agent_oobis(source_client, source_name, target_client, target_name)


def create_identifier(
    client: SignifyClient,
    name: str,
    *,
    wits: list[str] | None = None,
    add_end_role: bool = True,
    **kwargs,
) -> dict:
    """Create an identifier and, by default, wait until its agent OOBI is queryable.

    For OOBI-heavy Phase 2 scenarios this mirrors the SignifyTS helper
    `getOrCreateIdentifier`: use witness-backed inception by default, wait for
    the creation operation, add the agent end-role if requested, and wait for
    the resulting agent OOBI before returning.
    """
    wits = TEST_WITNESS_AIDS if wits is None else wits
    if wits:
        # Witness-backed inception only works once the client already knows the
        # witness introduction OOBIs.
        ensure_witness_oobis(client, wits)
    toad = kwargs.pop("toad", str(len(wits)) if wits else "0")
    _, _, operation = client.identifiers().create(name, toad=toad, wits=wits, **kwargs)
    result = wait_for_operation(client, operation)
    serder = serdering.SerderKERI(sad=result["response"])
    assert serder.pre
    if add_end_role:
        # Agent OOBIs are only meaningful after the identifier authorizes the
        # agent endpoint role and that reply becomes queryable.
        _, _, endrole_op = client.identifiers().addEndRole(name=name, eid=client.agent.pre)
        wait_for_operation(client, endrole_op)
        wait_for_end_role(client, name, eid=client.agent.pre)
        wait_for_identifier_oobi(client, name, role="agent")
    return client.identifiers().get(name)


def start_delegated_identifier(
    client: SignifyClient,
    name: str,
    *,
    delpre: str,
    wits: list[str] | None = None,
    **kwargs,
) -> tuple[serdering.SerderKERI, dict]:
    """Start delegated inception and return the pending operation without waiting.

    The caller is responsible for the second half of the workflow:
    obtaining delegator approval, forcing any needed key-state queries, and
    then waiting for the delegate-side operation to complete.
    """
    wits = TEST_WITNESS_AIDS if wits is None else wits
    if wits:
        ensure_witness_oobis(client, wits)
    toad = kwargs.pop("toad", str(len(wits)) if wits else "0")
    serder, _, operation = client.identifiers().create(name, delpre=delpre, toad=toad, wits=wits, **kwargs)
    return serder, operation


def rotate_identifier(client: SignifyClient, name: str, **kwargs) -> dict:
    """Rotate a single-sig identifier and return the refreshed identifier state."""
    _, _, operation = client.identifiers().rotate(name, **kwargs)
    wait_for_operation(client, operation)
    return client.identifiers().get(name)


def query_key_state(
    client: SignifyClient,
    pre: str,
    *,
    sn: str | None = None,
    anchor: dict | None = None,
) -> dict:
    """Query a key state through KERIA's operations API and return the response.

    This helper matters most in delegation flows where the delegate has to
    learn that the delegator anchored an approval event before its own pending
    operation can finish.
    """
    operation = client.keyStates().query(pre=pre, sn=sn, anchor=anchor)
    result = wait_for_operation(client, operation)
    return _normalize_state(result["response"])


def list_key_states(client: SignifyClient, prefixes: list[str]) -> list[dict]:
    """Fetch key states in order for simple list/read assertions."""
    return [_normalize_state(client.keyStates().get(prefix)) for prefix in prefixes]


def _normalize_state(state_or_states):
    """Unwrap single-item key state list responses into the state dict callers expect.

    KERIA sometimes returns a list for key-state queries even when the caller is
    conceptually asking about one prefix. Group helpers are easier to read if
    they can work with normalized state dicts.
    """
    if isinstance(state_or_states, list):
        assert len(state_or_states) == 1
        return state_or_states[0]
    return state_or_states


def get_states(client: SignifyClient, prefixes: list[str]) -> list[dict]:
    """Fetch the current key state for each participant prefix in order."""
    return [_normalize_state(client.keyStates().get(pre)) for pre in prefixes]


def _messagize(serder, sigs, *, seal=None):
    """Encode a serder plus signatures into the attachment form peers expect.

    Multisig exchange payloads embed fully messagized events or replies so
    peers can reconstruct the same local join/rotation/authorization step from
    notifications alone.
    """
    sigers = [csigning.Siger(qb64=sig) for sig in sigs]
    return eventing.messagize(serder=serder, sigers=sigers, seal=seal)


# Identifier and multisig workflow helpers

def _state_order(client: SignifyClient, member_names: list[str]) -> list[dict]:
    """Return member states in a stable caller-provided name order."""
    return [client.identifiers().get(name)["state"] for name in member_names]


def start_multisig_incept(
    client: SignifyClient,
    *,
    group_name: str,
    local_member_name: str,
    participants: list[str],
    isith=2,
    nsith=2,
    toad: int | None = None,
    wits: list[str] | None = None,
    delpre: str | None = None,
) -> tuple[dict, serdering.SerderKERI]:
    """Start a multisig inception from one participant and fan out `/multisig/icp`.

    Workflow substance:
    1. Load the initiating member's local habitat and the current key states for
       every signing participant.
    2. Create the local group inception event with `algo=group`.
    3. Send a `/multisig/icp` exchange to the other participants containing the
       messagized inception event plus the member lists needed to reconstruct
       the same group locally.

    This helper only performs the initiator half; peers still need to accept
    the notification with `accept_multisig_incept`.
    """
    member = client.identifiers().get(local_member_name)
    states = get_states(client, participants)
    group_wits = [] if wits is None else wits
    # The local participant creates the group event from the current member
    # states; remote participants will later reconstruct that same event from
    # the `/multisig/icp` notification.
    serder, sigs, operation = client.identifiers().create(
        group_name,
        algo=Algos.group,
        mhab=member,
        isith=isith,
        nsith=nsith,
        toad=len(group_wits) if toad is None else toad,
        wits=group_wits,
        delpre=delpre,
        states=states,
        rstates=states,
    )
    smids = [state["i"] for state in states]
    recipients = [pre for pre in participants if pre != member["prefix"]]
    # The exchange carries both the event and the participant roster so peers
    # can perform a matching group creation step.
    client.exchanges().send(
        local_member_name,
        "multisig",
        sender=member,
        route="/multisig/icp",
        payload=dict(gid=serder.pre, smids=smids, rmids=smids),
        embeds=dict(icp=_messagize(serder, sigs)),
        recipients=recipients,
    )
    return operation, serder


def accept_multisig_incept(
    client: SignifyClient,
    *,
    group_name: str,
    local_member_name: str,
) -> dict:
    """Accept a pending `/multisig/icp` request and return the join operation.

    Workflow substance:
    1. Wait for the initiator's `/multisig/icp` notification.
    2. Load the stored exchange request and unpack the embedded inception event.
    3. Rebuild the same group inception locally using the received participant
       lists and witness/delegation settings.
    4. Echo a matching `/multisig/icp` exchange so the initiator sees the peer
       contribution and both sides can converge on the same group AID.
    """
    _, request = wait_for_multisig_request(client, "/multisig/icp")
    exn = request[0]["exn"]
    icp = exn["e"]["icp"]
    smids = exn["a"]["smids"]
    rmids = exn["a"]["rmids"]
    member = client.identifiers().get(local_member_name)
    states = get_states(client, smids)
    rstates = get_states(client, rmids)
    serder, sigs, operation = client.identifiers().create(
        group_name,
        algo=Algos.group,
        mhab=member,
        isith=icp["kt"],
        nsith=icp["nt"],
        toad=int(icp["bt"]),
        wits=icp["b"],
        delpre=icp.get("di"),
        states=states,
        rstates=rstates,
    )
    recipients = [pre for pre in smids if pre != member["prefix"]]
    client.exchanges().send(
        local_member_name,
        "multisig",
        sender=member,
        route="/multisig/icp",
        payload=dict(gid=serder.pre, smids=smids, rmids=rmids),
        embeds=dict(icp=_messagize(serder, sigs)),
        recipients=recipients,
    )
    return operation


def create_multisig_group(
    client_a: SignifyClient,
    member_a_name: str,
    client_b: SignifyClient,
    member_b_name: str,
    group_name: str,
    *,
    delpre: str | None = None,
    wits: list[str] | None = None,
) -> tuple[dict, dict]:
    """Create a 2-of-2 multisig group and return both members' group views.

    This is the shared happy-path choreography for multisig inception in the
    Phase 2 suite: initiator starts, second member accepts, both operations
    complete, and both local views are compared to ensure the same group prefix
    emerged on each side.
    """
    participant_prefixes = [
        client_a.identifiers().get(member_a_name)["prefix"],
        client_b.identifiers().get(member_b_name)["prefix"],
    ]
    # Member A initiates the group inception and member B reconstructs the same
    # group from the `/multisig/icp` request it receives.
    operation_a, _ = start_multisig_incept(
        client_a,
        group_name=group_name,
        local_member_name=member_a_name,
        participants=participant_prefixes,
        isith=2,
        nsith=2,
        wits=wits,
        delpre=delpre,
    )
    operation_b = accept_multisig_incept(
        client_b,
        group_name=group_name,
        local_member_name=member_b_name,
    )
    wait_for_operation(client_a, operation_a)
    wait_for_operation(client_b, operation_b)
    group_a = client_a.identifiers().get(group_name)
    group_b = client_b.identifiers().get(group_name)
    assert group_a["prefix"] == group_b["prefix"]
    return group_a, group_b


def create_multisig_group_n(
    participants: list[tuple[SignifyClient, str]],
    group_name: str,
    *,
    isith: int | str | list[str] | None = None,
    nsith: int | str | list[str] | None = None,
    delpre: str | None = None,
    wits: list[str] | None = None,
) -> list[dict]:
    """Create one multisig group across an ordered participant list.

    Participant order is part of the contract here, not just presentation.
    Helpers and tests reuse this ordering for state lookup, peer exchange, and
    later membership assertions.
    """
    if len(participants) < 2:
        raise ValueError("multisig groups require at least two participants")

    participant_prefixes = [
        client.identifiers().get(member_name)["prefix"]
        for client, member_name in participants
    ]
    threshold = len(participants)
    initiator_client, initiator_member_name = participants[0]
    operations: list[tuple[SignifyClient, dict]] = []
    operation, _ = start_multisig_incept(
        initiator_client,
        group_name=group_name,
        local_member_name=initiator_member_name,
        participants=participant_prefixes,
        isith=threshold if isith is None else isith,
        nsith=threshold if nsith is None else nsith,
        toad=len(wits or []),
        wits=wits,
        delpre=delpre,
    )
    operations.append((initiator_client, operation))
    for client, member_name in participants[1:]:
        operations.append(
            (
                client,
                accept_multisig_incept(
                    client,
                    group_name=group_name,
                    local_member_name=member_name,
                ),
            )
        )

    for client, operation in operations:
        wait_for_operation(client, operation)

    groups = [client.identifiers().get(group_name) for client, _ in participants]
    assert len({group["prefix"] for group in groups}) == 1
    return groups


def assert_multisig_members(
    client: SignifyClient,
    group_name: str,
    *,
    count: int = 2,
    signing_aids: list[str] | None = None,
    rotation_aids: list[str] | None = None,
) -> dict:
    """Assert multisig membership count and, optionally, exact member identities."""
    members = client.identifiers().members(group_name)
    assert len(members["signing"]) == count
    assert len(members["rotation"]) == count
    if signing_aids is not None:
        assert {member["aid"] for member in members["signing"]} == set(signing_aids)
    if rotation_aids is not None:
        assert {member["aid"] for member in members["rotation"]} == set(rotation_aids)
    return members


def expected_multisig_agent_eids(client: SignifyClient, group_name: str) -> set[str]:
    """Return the full set of member-agent EIDs a group agent OOBI must publish.

    The source of truth is the multisig membership record itself, not a hard-
    coded count. Once member agent OOBIs have been exchanged, each signing
    participant advertises its known agent endpoints through
    `identifiers().members(...)`.
    """
    members = client.identifiers().members(group_name)
    eids = set()
    for signing in members["signing"]:
        eids.update(signing.get("ends", {}).get("agent", {}).keys())
    return eids


def wait_for_group_agent_endroles(
    client: SignifyClient,
    group_name: str,
    *,
    expected_eids: set[str],
    timeout: float = 60.0,
) -> list[dict]:
    """Poll until the group exposes the full expected agent end-role set.

    `/multisig/rpy` notifications are only a transport signal. The stable proof
    that the group can publish an agent OOBI is that the group end-role list now
    exposes every member agent EID that should be authorized under the group.
    """
    return poll_until(
        lambda: get_end_roles(client, group_name, role="agent"),
        ready=lambda end_roles: {
            end_role.get("eid")
            for end_role in end_roles
            if end_role.get("role") == "agent" and end_role.get("eid")
        }
        == expected_eids,
        timeout=timeout,
        interval=POLL_INTERVAL,
        describe=f"group agent end-roles {sorted(expected_eids)} on {group_name}",
    )


def add_multisig_agent_endroles(
    client: SignifyClient,
    *,
    member_name: str,
    group_name: str,
    stamp: str,
    is_initiator: bool = False,
) -> list[dict]:
    """Publish the agent end-role replies needed for multisig agent OOBIs.

    A multisig group does not get a usable agent OOBI merely because the member
    AIDs have agent endpoints. Each participant has to publish the group's
    agent-role authorization replies under the group KEL, then send those
    replies to the peer via `/multisig/rpy`.
    """
    if not is_initiator:
        # Mirror the SignifyTS choreography: the non-initiating member waits
        # for the initiator's `/multisig/rpy` exchange before publishing its
        # own group end-role replies back to the peer.
        wait_for_multisig_request(client, "/multisig/rpy")

    group_hab = client.identifiers().get(group_name)
    member_hab = client.identifiers().get(member_name)
    members = client.identifiers().members(group_name)
    recipients = [entry["aid"] for entry in members["signing"] if entry["aid"] != member_hab["prefix"]]
    operations = []
    for signing in members["signing"]:
        for eid in signing.get("ends", {}).get("agent", {}).keys():
            # Each known agent endpoint has to be re-authorized under the group
            # AID, not just under the member AID that originally published it.
            rpy, sigs, operation = client.identifiers().addEndRole(group_name, eid=eid, stamp=stamp)
            operations.append(operation)
            seal = eventing.SealEvent(
                i=group_hab["prefix"],
                s=group_hab["state"]["ee"]["s"],
                d=group_hab["state"]["ee"]["d"],
            )
            client.exchanges().send(
                member_name,
                "multisig",
                sender=member_hab,
                route="/multisig/rpy",
                payload=dict(gid=group_hab["prefix"]),
                embeds=dict(rpy=_messagize(rpy, sigs, seal=seal)),
                recipients=recipients,
            )
    return operations


def add_one_multisig_agent_endrole(
    client: SignifyClient,
    *,
    member_name: str,
    group_name: str,
    eid: str,
    stamp: str,
    is_initiator: bool = False,
    request: list[dict] | None = None,
) -> tuple[serdering.SerderKERI, list[str], dict, list[dict] | None]:
    """Publish one deterministic group `/multisig/rpy` proposal and mirror it to peers.

    This helper exists for the focused replay regression. It intentionally
    stages only one group end-role reply so the follower can assert that the
    stored `/multisig/rpy` request payload is the exact reply participant A
    proposed before participant B locally approves the same authorization.
    """
    if not is_initiator and request is None:
        _, request = wait_for_multisig_request(client, "/multisig/rpy")

    local_member = client.identifiers().get(member_name)
    group_hab = client.identifiers().get(group_name)
    members = client.identifiers().members(group_name)
    recipients = [
        entry["aid"]
        for entry in members["signing"]
        if entry["aid"] != local_member["prefix"]
    ]

    rpy, sigs, operation = client.identifiers().addEndRole(group_name, eid=eid, stamp=stamp)
    seal = eventing.SealEvent(
        i=group_hab["prefix"],
        s=group_hab["state"]["ee"]["s"],
        d=group_hab["state"]["ee"]["d"],
    )
    client.exchanges().send(
        member_name,
        "multisig",
        sender=local_member,
        route="/multisig/rpy",
        payload=dict(gid=group_hab["prefix"]),
        embeds=dict(rpy=_messagize(rpy, sigs, seal=seal)),
        recipients=recipients,
    )
    return rpy, sigs, operation, request


def expose_multisig_agent_oobi(
    client_a: SignifyClient,
    member_a_name: str,
    client_b: SignifyClient,
    member_b_name: str,
    group_name: str,
) -> str:
    """Expose a multisig agent OOBI after both members publish end-role replies.

    Workflow substance:
    1. Both members publish the group's agent-role authorization replies.
    2. Only the non-initiator waits for the initiator's first `/multisig/rpy`
       controller notification before publishing its matching replies.
    3. After the local `addEndRole(...)` operations finish, both participants
       wait for the group end-role list to expose the full expected member agent
       EID set.
    4. Each member waits for a non-empty group agent OOBI and both answers are
       compared to confirm convergence on one publication route.

    Important contract detail:
    Once an embedded `rpy` is already locally approved, the peer echo may be
    parsed silently rather than surfaced as another controller notification.
    The initiator must therefore not wait for a second `/multisig/rpy`
    notification after it already submitted matching local replies.
    """
    expected_eids_a = expected_multisig_agent_eids(client_a, group_name)
    expected_eids_b = expected_multisig_agent_eids(client_b, group_name)
    assert expected_eids_a == expected_eids_b

    stamp = helping.nowIso8601()
    operations_a = add_multisig_agent_endroles(
        client_a,
        member_name=member_a_name,
        group_name=group_name,
        stamp=stamp,
        is_initiator=True,
    )
    operations_b = add_multisig_agent_endroles(
        client_b,
        member_name=member_b_name,
        group_name=group_name,
        stamp=stamp,
    )
    # Every published group end-role reply must complete locally before the
    # group agent OOBI can be queried reliably.
    for operation in operations_a:
        wait_for_operation(client_a, operation)
    for operation in operations_b:
        wait_for_operation(client_b, operation)
    wait_for_group_agent_endroles(client_a, group_name, expected_eids=expected_eids_a)
    wait_for_group_agent_endroles(client_b, group_name, expected_eids=expected_eids_a)
    oobi_a = wait_for_identifier_oobi(client_a, group_name, role="agent")[0]
    oobi_b = wait_for_identifier_oobi(client_b, group_name, role="agent")[0]
    assert oobi_a == oobi_b
    return oobi_a


def expose_multisig_agent_oobi_n(
    participants: list[tuple[SignifyClient, str]],
    group_name: str,
) -> str:
    """Expose a multisig agent OOBI for an ordered participant list.

    This is the N-party analogue of `expose_multisig_agent_oobi(...)`: publish
    the required group end-role replies on every member, wait for multisig state convergence,
    and return one verified shared OOBI string.
    """
    if len(participants) < 2:
        raise ValueError("multisig groups require at least two participants")

    initiator_client, initiator_member_name = participants[0]
    expected_eids = expected_multisig_agent_eids(initiator_client, group_name)
    stamp = helping.nowIso8601()
    operations: list[tuple[SignifyClient, dict]] = []
    operations.extend(
        (initiator_client, operation)
        for operation in add_multisig_agent_endroles(
            initiator_client,
            member_name=initiator_member_name,
            group_name=group_name,
            stamp=stamp,
            is_initiator=True,
        )
    )
    for client, member_name in participants[1:]:
        operations.extend(
            (client, operation)
            for operation in add_multisig_agent_endroles(
                client,
                member_name=member_name,
                group_name=group_name,
                stamp=stamp,
            )
        )

    for client, operation in operations:
        wait_for_operation(client, operation)

    oobis = []
    for client, _ in participants:
        wait_for_group_agent_endroles(client, group_name, expected_eids=expected_eids)
        oobis.append(wait_for_identifier_oobi(client, group_name, role="agent")[0])

    assert len(set(oobis)) == 1
    return oobis[0]


def start_multisig_rotation(
    client: SignifyClient,
    *,
    member_name: str,
    group_name: str,
    states: list[dict],
) -> dict:
    """Start a multisig rotation from one participant and send `/multisig/rot`.

    The initiator builds the group rotation from the latest member states, then
    ships the messagized rotation event to peers so they can join the same
    rotation locally.
    """
    member = client.identifiers().get(member_name)
    group_hab = client.identifiers().get(group_name)
    # The initiator rotates the group from the latest known member states and
    # ships that exact rotation event to peers for matching participation.
    serder, sigs, operation = client.identifiers().rotate(group_name, states=states, rstates=states)
    smids = [state["i"] for state in states]
    recipients = [pre for pre in smids if pre != member["prefix"]]
    client.exchanges().send(
        member_name,
        "multisig",
        sender=member,
        route="/multisig/rot",
        payload=dict(gid=group_hab["prefix"], smids=smids, rmids=smids),
        embeds=dict(rot=_messagize(serder, sigs)),
        recipients=recipients,
    )
    return operation


def accept_multisig_rotation(
    client: SignifyClient,
    *,
    member_name: str,
    group_name: str,
    participant_states: dict[str, dict],
) -> dict:
    """Accept a pending multisig rotation for an already-existing group.

    Workflow substance:
    1. Wait for the initiator's `/multisig/rot` proposal so the local participant
       learns the ordered signer lists for this group rotation.
    2. Rebuild the `states`/`rstates` inputs in the exact order carried by the
       exchange payload, using the freshly queried single-sig member states.
    3. Rotate the already-existing group locally with `identifiers().rotate(...)`
    4. Send the participant's matching embedded rotation event back to the peer.
    """
    member = client.identifiers().get(member_name)
    _, exchange = wait_for_exchange_message(client, "/multisig/rot")
    exn = exchange["exn"]
    gid = exn["a"]["gid"]
    smids = exn["a"]["smids"]
    rmids = exn["a"]["rmids"]
    states = [participant_states[pre] for pre in smids]
    rstates = [participant_states[pre] for pre in rmids]
    recipients = [pre for pre in smids if pre != member["prefix"]]
    # Existing group members do not "join" the group again for rotation. They
    # rotate their local group habitat from the shared participant states.
    rot, sigs, operation = client.identifiers().rotate(
        group_name,
        states=states,
        rstates=rstates,
    )
    client.exchanges().send(
        member_name,
        "multisig",
        sender=member,
        route="/multisig/ixn",
        payload=dict(gid=gid, smids=smids, rmids=rmids),
        embeds=dict(rot=_messagize(rot, sigs)),
        recipients=recipients,
    )
    return operation


def rotate_multisig_group(
    client_a: SignifyClient,
    member_a_name: str,
    client_b: SignifyClient,
    member_b_name: str,
    group_name: str,
) -> tuple[dict, dict]:
    """Rotate both member AIDs, then rotate the 2-of-2 multisig group itself.

    Workflow substance:
    1. Rotate each single-sig member so the group has fresh participant states.
    2. Query the remote participant state on the opposite client so both group
       participants agree on the same latest member-state inputs.
    3. Start the group rotation from one member and accept it from the other by
       rotating the already-existing group locally on both sides.
    4. Compare the resulting group sequence numbers to prove convergence.
    """
    member_a = rotate_identifier(client_a, member_a_name)
    member_b = rotate_identifier(client_b, member_b_name)
    # Each participant needs the other's freshly rotated single-sig state
    # before computing the next group rotation event.
    state_a = member_a["state"]
    state_b = member_b["state"]
    state_b_for_a = query_key_state(client_a, member_b["prefix"], sn=state_b["s"])
    state_a_for_b = query_key_state(client_b, member_a["prefix"], sn=state_a["s"])
    operation_a = start_multisig_rotation(
        client_a,
        member_name=member_a_name,
        group_name=group_name,
        states=[state_a, state_b_for_a],
    )
    operation_b = accept_multisig_rotation(
        client_b,
        member_name=member_b_name,
        group_name=group_name,
        participant_states={
            member_a["prefix"]: state_a_for_b,
            member_b["prefix"]: state_b,
        },
    )
    wait_for_operation(client_a, operation_a)
    wait_for_operation(client_b, operation_b)
    group_a = client_a.identifiers().get(group_name)
    group_b = client_b.identifiers().get(group_name)
    assert group_a["state"]["s"] == group_b["state"]["s"]
    return group_a, group_b


def interact_multisig_group(
    client_a: SignifyClient,
    member_a_name: str,
    client_b: SignifyClient,
    member_b_name: str,
    group_name: str,
    *,
    data: list[dict],
) -> tuple[serdering.SerderKERI, serdering.SerderKERI, dict, dict]:
    """Perform one existing-group multisig interaction across both members.

    This is the generic multisig `/multisig/ixn` choreography similar to SignifyTS:
    1. Member A authors the interaction on the existing group habitat.
    2. Member A sends the messagized event to member B via `/multisig/ixn`.
    3. Member B rebuilds the same interaction from the embedded payload and
       submits its local matching approval.
    4. Member B echoes the matching interaction back so member A's pending
       group operation can converge too.

    The helper returns both local serders plus the refreshed group views after
    both long-running operations complete.
    """
    group = client_a.identifiers().get(group_name)
    member_a = client_a.identifiers().get(member_a_name)
    member_b = client_b.identifiers().get(member_b_name)
    participants = [member_a["prefix"], member_b["prefix"]]

    serder_a, sigs_a, operation_a = client_a.identifiers().interact(group_name, data=data)
    client_a.exchanges().send(
        member_a_name,
        "multisig",
        sender=member_a,
        route="/multisig/ixn",
        payload=dict(gid=group["prefix"], smids=participants, rmids=participants),
        embeds=dict(ixn=_messagize(serder_a, sigs_a)),
        recipients=[member_b["prefix"]],
    )

    _, request = wait_for_multisig_request(client_b, "/multisig/ixn")
    request_data = request[0]["exn"]["e"]["ixn"]["a"]
    # Rebuild the interaction from the received payload instead of local memory
    # so both members prove they are converging on the same shared event data.
    serder_b, sigs_b, operation_b = client_b.identifiers().interact(group_name, data=request_data)
    client_b.exchanges().send(
        member_b_name,
        "multisig",
        sender=member_b,
        route="/multisig/ixn",
        payload=dict(gid=group["prefix"], smids=participants, rmids=participants),
        embeds=dict(ixn=_messagize(serder_b, sigs_b)),
        recipients=[member_a["prefix"]],
    )

    wait_for_operation(client_a, operation_a)
    wait_for_operation(client_b, operation_b)
    group_a = client_a.identifiers().get(group_name)
    group_b = client_b.identifiers().get(group_name)
    assert group_a["state"]["s"] == group_b["state"]["s"]
    assert group_a["state"]["d"] == group_b["state"]["d"]
    return serder_a, serder_b, group_a, group_b


def rotate_multisig_group_n(
    participants: list[tuple[SignifyClient, str]],
    group_name: str,
) -> list[dict]:
    """Rotate every member AID and then rotate the multisig group itself.

    Use this helper when the test cares about the converged N-party result more
    than the mechanics of each intermediate participant step.
    """
    if len(participants) < 2:
        raise ValueError("multisig groups require at least two participants")

    # rotate single sig and create client tuples of
    # (client, name, keystate)
    rotated_members = [
        (client, member_name, rotate_identifier(client, member_name))
        for client, member_name in participants
    ]

    # refresh key state between all rotated members
    ordered_prefixes = [member["prefix"] for _, _, member in rotated_members]
    state_maps: list[dict[str, dict]] = []
    for client, _, local_member in rotated_members:
        # store key states for smids and rmids later
        state_map: dict[str, dict] = {}
        for _, _, member in rotated_members:
            if member["prefix"] == local_member["prefix"]:
                state_map[member["prefix"]] = member["state"]
            else:
                state_map[member["prefix"]] = query_key_state(client, member["prefix"], sn=member["state"]["s"])
        state_maps.append(state_map)

    # get first member to initiate multisig
    initiator_client, initiator_member_name, _ = rotated_members[0]
    operations: list[tuple[SignifyClient, dict]] = [
        (
            initiator_client,
            start_multisig_rotation(
                initiator_client,
                member_name=initiator_member_name,
                group_name=group_name,
                states=[state_maps[0][prefix] for prefix in ordered_prefixes],
            ),
        )
    ]
    # join multisig op with other members
    for (client, member_name, _), state_map in zip(rotated_members[1:], state_maps[1:]):
        operations.append(
            (
                client,
                accept_multisig_rotation(
                    client,
                    member_name=member_name,
                    group_name=group_name,
                    participant_states=state_map,
                ),
            )
        )

    # wait for all members to complete the multisig op
    for client, operation in operations:
        wait_for_operation(client, operation)

    groups = [client.identifiers().get(group_name) for client, _, _ in rotated_members]
    assert len({group["state"]["s"] for group in groups}) == 1
    assert len({group["state"]["d"] for group in groups}) == 1
    return groups


def approve_single_delegation(
    client: SignifyClient,
    delegator_name: str,
    delegate_prefix: str,
) -> tuple[serdering.SerderKERI, dict]:
    """Approve a single-sig delegated inception and return the approval event plus result.

    The anchor data mirrors the delegated inception event at sequence `0`, which
    is what the delegator interaction event has to point at.
    """
    anchor = dict(i=delegate_prefix, s="0", d=delegate_prefix)
    serder, _, operation = client.delegations().approve(delegator_name, anchor)
    return serder, wait_for_operation(client, operation)


# Delegation and credential workflow helpers

def approve_multisig_delegation(
    client_a: SignifyClient,
    member_a_name: str,
    client_b: SignifyClient,
    member_b_name: str,
    group_name: str,
    delegate_prefix: str,
) -> tuple[serdering.SerderKERI, dict, serdering.SerderKERI, dict]:
    """Approve delegation from both members of a 2-of-2 multisig delegator.

    Workflow substance:
    1. The initiating member creates the group interaction event that anchors
       the delegate's inception.
    2. That interaction is sent to the second member via `/multisig/ixn`.
    3. The second member loads the stored request, reconstructs the same anchor
       from the embedded interaction payload, and submits its matching approval.
    4. Both members wait for their local long-running approval operations so the
       caller can compare the converged result.
    """
    group = client_a.identifiers().get(group_name)
    member_a = client_a.identifiers().get(member_a_name)
    member_b = client_b.identifiers().get(member_b_name)
    participants = [member_a["prefix"], member_b["prefix"]]
    anchor = dict(i=delegate_prefix, s="0", d=delegate_prefix)

    # Member A authors the anchoring ixn first and forwards it to member B so
    # both participants approve the exact same anchor payload.
    serder_a, sigs_a, operation_a = client_a.delegations().approve(group_name, anchor)
    client_a.exchanges().send(
        member_a_name,
        group_name,
        sender=member_a,
        route="/multisig/ixn",
        payload=dict(gid=group["prefix"], smids=participants, rmids=participants),
        embeds=dict(ixn=_messagize(serder_a, sigs_a)),
        recipients=[member_b["prefix"]],
    )

    _, request = wait_for_multisig_request(client_b, "/multisig/ixn")
    request_anchor = request[0]["exn"]["e"]["ixn"]["a"][0]
    # Member B must reconstruct the anchor from the received request rather
    # than trust local assumptions, or the two approvals can diverge.
    serder_b, sigs_b, operation_b = client_b.delegations().approve(group_name, request_anchor)
    client_b.exchanges().send(
        member_b_name,
        group_name,
        sender=member_b,
        route="/multisig/ixn",
        payload=dict(gid=group["prefix"], smids=participants, rmids=participants),
        embeds=dict(ixn=_messagize(serder_b, sigs_b)),
        recipients=[member_a["prefix"]],
    )

    return (
        serder_a,
        wait_for_operation(client_a, operation_a),
        serder_b,
        wait_for_operation(client_b, operation_b),
    )


def create_registry(client: SignifyClient, issuer_name: str, registry_name: str) -> tuple[dict, dict]:
    """Create a single-sig registry and return refreshed issuer and registry state.

    Registry inception mutates the issuer's identifier state by anchoring a
    registry event, so callers almost always need the refreshed issuer habitat
    returned here before attempting credential issuance.
    """
    issuer_hab = client.identifiers().get(issuer_name)
    _, _, _, operation = client.registries().create(issuer_hab, registry_name)
    wait_for_operation(client, operation)
    issuer_hab = client.identifiers().get(issuer_name)
    registry = client.registries().get(issuer_name, registry_name)
    return issuer_hab, registry


def rename_registry(client: SignifyClient, issuer_name: str, registry_name: str, new_name: str) -> dict:
    """Rename a registry and return the refreshed renamed registry view."""
    issuer_hab = client.identifiers().get(issuer_name)
    client.registries().rename(issuer_hab, registry_name, new_name)
    return client.registries().get(issuer_name, new_name)


def issue_credential(
    client: SignifyClient,
    *,
    issuer_name: str,
    registry_name: str,
    recipient: str,
    data: dict,
    schema: str = SCHEMA_SAID,
):
    """Issue a credential through SignifyPy and wait for the issuance operation.

    This helper owns the "issue but do not yet transport" part of the
    credential flow. Transport to the holder still happens later through IPEX.
    """
    issuer_hab = client.identifiers().get(issuer_name)
    registry = client.registries().get(issuer_name, registry_name)
    creder, iserder, anc, sigs, operation = client.credentials().create(
        issuer_hab,
        registry=registry,
        data=data,
        schema=schema,
        recipient=recipient,
        timestamp=helping.nowIso8601(),
    )
    wait_for_operation(client, operation)
    return creder, iserder, anc, sigs


def revoke_credential(
    client: SignifyClient,
    *,
    issuer_name: str,
    credential_said: str,
    timestamp: str | None = None,
):
    """Revoke one single-sig credential and wait for the local revoke operation."""
    rserder, anc, sigs, operation = client.credentials().revoke(
        issuer_name,
        credential_said,
        timestamp=timestamp,
    )
    wait_for_operation(client, operation)
    return rserder, anc, sigs


def send_credential_grant(
    client: SignifyClient,
    *,
    issuer_name: str,
    recipient: str,
    creder,
    iserder,
    anc,
    sigs: list[str],
) -> None:
    """Create and submit the IPEX grant message for an issued credential.

    The grant packages the credential, the issuance event, and the anchoring
    event into the message shape the holder later acknowledges with `admit`.
    """
    issuer_hab = client.identifiers().get(issuer_name)
    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    # IPEX grant packages the credential plus the issuance and anchor evidence
    # so the holder can validate and later admit the exact credential being sent.
    acdc = app_signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iserder.said))
    iss = client.registries().serialize(iserder, anc)
    grant, grant_sigs, atc = client.ipex().grant(
        issuer_hab,
        recp=recipient,
        message="",
        acdc=acdc,
        iss=iss,
        anc=eventing.messagize(
            serder=anc,
            sigers=[csigning.Siger(qb64=sig) for sig in sigs],
        ),
        dt=helping.nowIso8601(),
    )
    client.ipex().submitGrant(issuer_name, exn=grant, sigs=grant_sigs, atc=atc, recp=[recipient])


def create_multisig_registry(
    client: SignifyClient,
    *,
    local_member_name: str,
    group_name: str,
    other_member_prefixes: list[str],
    registry_name: str,
    nonce: str | None = None,
    is_initiator: bool = False,
    request: list[dict] | None = None,
) -> tuple[dict, dict]:
    """Start multisig registry creation and fan out `/multisig/vcp`.

    The caller owns the convergence phase. This mirrors the SignifyTS helper
    shape: stage every participant's registry operation first, then wait for
    all operations and finally verify cross-member registry convergence.

    On the non-initiator path, the incoming `/multisig/vcp` embeds are the
    canonical proposal. The joiner signs and submits that exact embedded VCP
    and anchoring interaction event instead of reconstructing a fresh local
    anchor candidate.
    """
    if not is_initiator and request is None:
        _, request = wait_for_multisig_request(client, "/multisig/vcp")

    local_member = client.identifiers().get(local_member_name)
    group_hab = client.identifiers().get(group_name)
    if request is not None:
        # The follower path intentionally reuses the stored proposal payload.
        # That is the actual replay contract the multisig tests are protecting.
        proposal = request[0]["exn"]["e"]
        vcp = serdering.SerderKERI(sad=proposal["vcp"])
        anc = serdering.SerderKERI(sad=proposal["anc"])
        keeper = client.manager.get(aid=group_hab)
        sigs = keeper.sign(ser=anc.raw)
        operation = client.registries().create_from_events(
            hab=group_hab,
            registryName=registry_name,
            vcp=vcp.ked,
            ixn=anc.ked,
            sigs=sigs,
        )
    else:
        vcp, anc, sigs, operation = client.registries().create(
            hab=group_hab,
            registryName=registry_name,
            nonce=nonce,
        )
    client.exchanges().send(
        local_member_name,
        "registry",
        sender=local_member,
        route="/multisig/vcp",
        payload=dict(gid=group_hab["prefix"]),
        embeds=dict(
            vcp=vcp.raw,
            anc=_messagize(anc, sigs),
        ),
        recipients=other_member_prefixes,
    )
    return operation, {
        "name": registry_name,
        "group_prefix": group_hab["prefix"],
        "vcp_said": vcp.said,
        "anc_said": anc.said,
        "vcp": vcp,
        "anc": anc,
        "request": request,
    }


def issue_multisig_credential(
    client: SignifyClient,
    *,
    local_member_name: str,
    group_name: str,
    other_member_prefixes: list[str],
    registry_name: str,
    recipient: str,
    data: dict,
    schema: str = SCHEMA_SAID,
    timestamp: str | None = None,
    is_initiator: bool = False,
    request: list[dict] | None = None,
):
    """Start multisig credential issuance and fan out `/multisig/iss`.

    The caller owns the convergence phase so both members can stage their local
    issuance operations before waiting for completion and asserting one shared
    credential SAID.

    On the non-initiator path, the incoming `/multisig/iss` embeds are the
    canonical proposal. The joiner signs and submits that exact credential
    issuance payload, including the same anchoring interaction event.
    """
    if not is_initiator and request is None:
        _, request = wait_for_multisig_request(client, "/multisig/iss")

    local_member = client.identifiers().get(local_member_name)
    group_hab = client.identifiers().get(group_name)
    registry = client.registries().get(group_name, registry_name)
    if request is not None:
        # As with `/multisig/vcp`, the follower path is only correct if it
        # approves the stored proposal instead of reconstructing one locally.
        proposal = request[0]["exn"]["e"]
        creder = serdering.SerderACDC(sad=proposal["acdc"])
        iserder = serdering.SerderKERI(sad=proposal["iss"])
        anc = serdering.SerderKERI(sad=proposal["anc"])
        keeper = client.manager.get(aid=group_hab)
        sigs = keeper.sign(ser=anc.raw)
        operation = client.credentials().create_from_events(
            hab=group_hab,
            creder=creder.sad,
            iss=iserder.sad,
            anc=anc.sad,
            sigs=sigs,
        ).json()
    else:
        creder, iserder, anc, sigs, operation = client.credentials().create(
            group_hab,
            registry=registry,
            data=data,
            schema=schema,
            recipient=recipient,
            timestamp=timestamp or helping.nowIso8601(),
        )
    client.exchanges().send(
        local_member_name,
        "multisig",
        sender=local_member,
        route="/multisig/iss",
        payload=dict(gid=group_hab["prefix"]),
        embeds=dict(
            acdc=app_signing.serialize(
                creder,
                coring.Prefixer(qb64=iserder.pre),
                coring.Seqner(sn=iserder.sn),
                coring.Saider(qb64=iserder.said),
            ),
            iss=client.registries().serialize(iserder, anc),
            anc=_messagize(anc, sigs),
        ),
        recipients=other_member_prefixes,
    )
    return creder, iserder, anc, sigs, operation, request


def revoke_multisig_credential(
    client: SignifyClient,
    *,
    local_member_name: str,
    group_name: str,
    other_member_prefixes: list[str],
    credential_said: str,
    timestamp: str,
    is_initiator: bool = False,
    request: list[dict] | None = None,
):
    """Start multisig credential revocation and fan out `/multisig/rev`.

    The caller owns the convergence phase. This helper mirrors the existing
    staged multisig issuance choreography: both members submit local revocation
    approval first, then the test waits operations and asserts one converged
    credential TEL state.

    On the non-initiator path, the stored `/multisig/rev` request is returned
    so the test can assert that participant B is joining the exact `rev` and
    `anc` proposal participant A sent.
    """
    if not is_initiator and request is None:
        _, request = wait_for_multisig_request(client, "/multisig/rev")

    local_member = client.identifiers().get(local_member_name)
    group_hab = client.identifiers().get(group_name)
    # Revocation still begins with the local wrapper call; the regression
    # assertion is that all members converge on one revoke event and TEL state.
    rserder, anc, sigs, operation = client.credentials().revoke(
        group_name,
        credential_said,
        timestamp=timestamp,
    )
    client.exchanges().send(
        local_member_name,
        "multisig",
        sender=local_member,
        route="/multisig/rev",
        payload=dict(gid=group_hab["prefix"], said=credential_said),
        embeds=dict(
            rev=rserder.raw,
            anc=_messagize(anc, sigs),
        ),
        recipients=other_member_prefixes,
    )
    return rserder, anc, sigs, operation, request


def send_multisig_credential_grant(
    client: SignifyClient,
    *,
    local_member_name: str,
    group_name: str,
    other_member_prefixes: list[str],
    recipient: str,
    creder,
    iserder,
    anc,
    sigs: list[str],
    is_initiator: bool = False,
) -> dict:
    """Submit a multisig grant and mirror it to peer members via `/multisig/exn`.

    The first member submits the real IPEX grant to the holder. The extra
    `/multisig/exn` wrapper exists so peer members can record and approve that
    exact grant message as part of the shared multisig workflow.
    """
    if not is_initiator:
        wait_for_exchange_message(client, "/multisig/exn")

    local_member = client.identifiers().get(local_member_name)
    group_hab = client.identifiers().get(group_name)
    prefixer = coring.Prefixer(qb64=iserder.pre)
    seqner = coring.Seqner(sn=iserder.sn)
    grant, grant_sigs, atc = client.ipex().grant(
        group_hab,
        recp=recipient,
        message="",
        acdc=app_signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iserder.said)),
        iss=client.registries().serialize(iserder, anc),
        anc=eventing.messagize(
            serder=anc,
            sigers=[csigning.Siger(qb64=sig) for sig in sigs],
        ),
        dt=helping.nowIso8601(),
    )
    result = client.ipex().submitGrant(group_name, exn=grant, sigs=grant_sigs, atc=atc, recp=[recipient])
    seal = eventing.SealEvent(
        i=group_hab["prefix"],
        s=group_hab["state"]["ee"]["s"],
        d=group_hab["state"]["ee"]["d"],
    )
    grant_ims = eventing.messagize(
        serder=grant,
        sigers=[csigning.Siger(qb64=sig) for sig in grant_sigs],
        seal=seal,
    )
    grant_ims.extend(atc.encode("utf-8"))
    exn, exn_sigs, exn_atc = client.exchanges().createExchangeMessage(
        sender=local_member,
        route="/multisig/exn",
        payload=dict(gid=group_hab["prefix"]),
        embeds=dict(exn=grant_ims),
    )
    client.exchanges().sendFromEvents(
        local_member_name,
        "multisig",
        exn=exn,
        sigs=exn_sigs,
        atc=exn_atc,
        recipients=other_member_prefixes,
    )
    if isinstance(result, dict) and "done" in result:
        return wait_for_operation(client, result)
    return result


def submit_admit(
    client: SignifyClient,
    *,
    holder_name: str,
    issuer_prefix: str,
    notification: dict,
) -> None:
    """Submit an IPEX admit in response to a previously received grant notification.

    This is the holder-side acknowledgement step in the grant/admit
    presentation workflow. It consumes the previously received grant
    notification and sends the corresponding admit back to the issuer.
    """
    holder_hab = client.identifiers().get(holder_name)
    # The admit references the previously received grant notification SAID,
    # which is why the notification object itself is part of the helper API.
    admit, sigs, atc = client.ipex().admit(
        holder_hab,
        "",
        notification["a"]["d"],
        issuer_prefix,
        helping.nowIso8601(),
    )
    client.ipex().submitAdmit(holder_name, exn=admit, sigs=sigs, atc=atc, recp=[issuer_prefix])


def submit_multisig_admit(
    client: SignifyClient,
    *,
    local_member_name: str,
    group_name: str,
    other_member_prefixes: list[str],
    issuer_prefix: str,
    notification: dict,
) -> dict:
    """Submit a multisig admit and mirror it to peer members via `/multisig/exn`.

    This mirrors `submit_admit(...)` for group workflows: submit the admit for
    the shared group AID, then forward the exact admit message to peer members
    so all participants observe the same group-side exchange.
    """
    local_member = client.identifiers().get(local_member_name)
    group_hab = client.identifiers().get(group_name)
    admit, sigs, atc = client.ipex().admit(
        group_hab,
        "",
        notification["a"]["d"],
        issuer_prefix,
        helping.nowIso8601(),
    )
    result = client.ipex().submitAdmit(group_name, exn=admit, sigs=sigs, atc=atc, recp=[issuer_prefix])
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
    exn, exn_sigs, exn_atc = client.exchanges().createExchangeMessage(
        sender=local_member,
        route="/multisig/exn",
        payload=dict(gid=group_hab["prefix"]),
        embeds=dict(exn=admit_ims),
    )
    client.exchanges().sendFromEvents(
        local_member_name,
        "multisig",
        exn=exn,
        sigs=exn_sigs,
        atc=exn_atc,
        recipients=other_member_prefixes,
    )
    if isinstance(result, dict) and "done" in result:
        return wait_for_operation(client, result)
    return result
