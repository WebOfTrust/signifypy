# -*- encoding: utf-8 -*-
"""Fast tests for the live integration polling helpers."""

from __future__ import annotations

import pytest
from requests import HTTPError

from tests.integration import helpers


def test_poll_until_retries_until_ready(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    calls = {"count": 0}

    def fetch():
        calls["count"] += 1
        return calls["count"]

    value = helpers.poll_until(
        fetch,
        ready=lambda current: current == 3,
        timeout=1.0,
        interval=0.01,
        describe="incrementing counter",
    )

    assert value == 3
    assert calls["count"] == 3


def test_wait_for_operation_delegates_to_operations_wait(monkeypatch):
    operation = {"name": "op-1", "done": False}
    result = {"name": "op-1", "done": True}
    captured = {}

    class FakeOperations:
        def wait(self, op, **kwargs):
            captured["op"] = op
            captured["kwargs"] = kwargs
            return result

    class FakeClient:
        def operations(self):
            return FakeOperations()

    out = helpers.wait_for_operation(FakeClient(), operation, timeout=12.5)

    assert out == result
    assert captured["op"] == operation
    assert captured["kwargs"]["timeout"] == 12.5
    assert captured["kwargs"]["interval"] == helpers.POLL_INTERVAL
    assert captured["kwargs"]["max_interval"] == helpers.POLL_INTERVAL
    assert captured["kwargs"]["backoff"] == 1.0


def test_wait_for_operation_timeout_surfaces_operations_wait_error():
    operation = {"name": "op-2", "done": False}

    class FakeOperations:
        def wait(self, op, **kwargs):
            raise TimeoutError(
                "timed out waiting for operation op-2; "
                "last_value={'name': 'op-2', 'done': False, 'stage': 'still waiting'}"
            )

    class FakeClient:
        def operations(self):
            return FakeOperations()

    with pytest.raises(TimeoutError, match="timed out waiting for operation op-2") as excinfo:
        helpers.wait_for_operation(FakeClient(), operation, timeout=1.0)

    assert "still waiting" in str(excinfo.value)


def test_wait_for_multisig_request_waits_for_stored_request(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    note = {"i": "note-1", "a": {"r": "/multisig/vcp", "d": "said-1"}, "r": False}

    class FakeNotifications:
        def __init__(self):
            self.marked = []

        def list(self):
            return {"notes": [note]}

        def mark(self, nid):
            self.marked.append(nid)
            return True

    class FakeGroups:
        def __init__(self):
            self.calls = 0

        def get_request(self, said):
            assert said == "said-1"
            self.calls += 1
            if self.calls == 1:
                raise HTTPError("request not ready")
            return [{"exn": {"r": "/multisig/vcp", "e": {}, "a": {}}}]

    notifications = FakeNotifications()
    groups = FakeGroups()

    class FakeClient:
        def notifications(self):
            return notifications

        def groups(self):
            return groups

    returned_note, request = helpers.wait_for_multisig_request(
        FakeClient(), "/multisig/vcp", timeout=1.0
    )

    assert returned_note == note
    assert request[0]["exn"]["r"] == "/multisig/vcp"
    assert notifications.marked == ["note-1"]
    assert groups.calls == 2


def test_wait_for_exchange_message_waits_for_retrievable_exchange(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    note = {"i": "note-2", "a": {"r": "/multisig/exn", "d": "said-2"}, "r": False}

    class FakeNotifications:
        def __init__(self):
            self.marked = []

        def list(self):
            return {"notes": [note]}

        def mark(self, nid):
            self.marked.append(nid)
            return True

    class FakeExchanges:
        def __init__(self):
            self.calls = 0

        def get(self, said):
            assert said == "said-2"
            self.calls += 1
            if self.calls == 1:
                raise HTTPError("exchange not ready")
            return {"exn": {"r": "/multisig/exn", "a": {}, "e": {"exn": {"r": "/ipex/grant"}}}}

    notifications = FakeNotifications()
    exchanges = FakeExchanges()

    class FakeClient:
        def notifications(self):
            return notifications

        def exchanges(self):
            return exchanges

    returned_note, exchange = helpers.wait_for_exchange_message(
        FakeClient(), "/multisig/exn", timeout=1.0
    )

    assert returned_note == note
    assert exchange["exn"]["r"] == "/multisig/exn"
    assert notifications.marked == ["note-2"]
    assert exchanges.calls == 2


def test_wait_for_exchange_message_selects_matching_embedded_route(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    notes = [
        {"i": "note-2b", "a": {"r": "/multisig/exn", "d": "said-2b"}, "r": False},
        {"i": "note-2c", "a": {"r": "/multisig/exn", "d": "said-2c"}, "r": False},
    ]

    class FakeNotifications:
        def __init__(self):
            self.marked = []

        def list(self):
            return {"notes": notes}

        def mark(self, nid):
            self.marked.append(nid)
            return True

    class FakeExchanges:
        def get(self, said):
            if said == "said-2b":
                return {"exn": {"r": "/multisig/exn", "a": {}, "e": {"exn": {"r": "/ipex/admit"}}}}
            assert said == "said-2c"
            return {"exn": {"r": "/multisig/exn", "a": {}, "e": {"exn": {"r": "/ipex/grant"}}}}

    notifications = FakeNotifications()
    exchanges = FakeExchanges()

    class FakeClient:
        def notifications(self):
            return notifications

        def exchanges(self):
            return exchanges

    returned_note, exchange = helpers.wait_for_exchange_message(
        FakeClient(),
        "/multisig/exn",
        embedded_route="/ipex/grant",
        timeout=1.0,
    )

    assert returned_note["i"] == "note-2c"
    assert exchange["exn"]["e"]["exn"]["r"] == "/ipex/grant"
    assert notifications.marked == ["note-2c"]


def test_wait_for_contact_challenge_state_waits_for_authenticated_challenge(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    contacts = [
        [{"alias": "bob", "challenges": [], "id": "aid-bob"}],
        [{"alias": "bob", "challenges": [{"authenticated": False}], "id": "aid-bob"}],
        [{"alias": "bob", "challenges": [{"authenticated": True}], "id": "aid-bob"}],
    ]

    class FakeContacts:
        def __init__(self):
            self.calls = 0

        def list(self):
            index = min(self.calls, len(contacts) - 1)
            self.calls += 1
            return contacts[index]

    fake_contacts = FakeContacts()

    class FakeClient:
        def contacts(self):
            return fake_contacts

    contact = helpers.wait_for_contact_challenge_state(
        FakeClient(),
        "bob",
        expected_count=1,
        authenticated=True,
        timeout=1.0,
    )

    assert contact["alias"] == "bob"
    assert contact["challenges"] == [{"authenticated": True}]
    assert fake_contacts.calls == 3


def test_wait_for_notification_marks_only_selected_note(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    notes = [
        {"i": "note-3", "a": {"r": "/multisig/iss", "d": "ignored"}, "r": False},
        {"i": "note-4", "a": {"r": "/exn/ipex/grant", "d": "grant"}, "r": False},
    ]

    class FakeNotifications:
        def __init__(self):
            self.marked = []

        def list(self):
            return {"notes": notes}

        def mark(self, nid):
            self.marked.append(nid)
            return True

    notifications = FakeNotifications()

    class FakeClient:
        def notifications(self):
            return notifications

    note = helpers.wait_for_notification(FakeClient(), "/exn/ipex/grant", timeout=1.0)

    assert note["i"] == "note-4"
    assert notifications.marked == ["note-4"]


def test_wait_for_notification_any_returns_first_available_client_note(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    class FakeNotifications:
        def __init__(self, notes):
            self.notes = notes
            self.marked = []

        def list(self):
            return {"notes": self.notes}

        def mark(self, nid):
            self.marked.append(nid)
            return True

    notifications_a = FakeNotifications(
        [{"i": "note-a", "a": {"r": "/multisig/iss", "d": "ignored"}, "r": False}]
    )
    notifications_b = FakeNotifications(
        [{"i": "note-b", "a": {"r": "/exn/ipex/grant", "d": "grant-said"}, "r": False}]
    )

    class FakeClient:
        def __init__(self, notifications):
            self._notifications = notifications

        def notifications(self):
            return self._notifications

    index, note = helpers.wait_for_notification_any(
        [FakeClient(notifications_a), FakeClient(notifications_b)],
        "/exn/ipex/grant",
        timeout=1.0,
    )

    assert index == 1
    assert note["i"] == "note-b"
    assert notifications_a.marked == []
    assert notifications_b.marked == ["note-b"]


def test_wait_for_exchange_waits_for_retrievable_exchange(monkeypatch):
    monkeypatch.setattr(helpers.time, "sleep", lambda _: None)

    class FakeExchanges:
        def __init__(self):
            self.calls = 0

        def get(self, said):
            assert said == "said-2"
            self.calls += 1
            if self.calls == 1:
                raise HTTPError("exchange not ready")
            return {"exn": {"r": "/multisig/exn", "a": {}}}

    exchanges = FakeExchanges()

    class FakeClient:
        def exchanges(self):
            return exchanges

    exchange = helpers.wait_for_exchange(
        FakeClient(),
        "said-2",
        expected_route="/multisig/exn",
        timeout=1.0,
    )

    assert exchange["exn"]["r"] == "/multisig/exn"
    assert exchanges.calls == 2


def test_send_multisig_credential_grant_returns_raw_operation_and_mirrors_peer_message(
    monkeypatch,
):
    captured_wait = {}

    def fake_wait_for_exchange_message(*args, **kwargs):
        captured_wait["kwargs"] = kwargs
        return "note", "exchange"

    monkeypatch.setattr(helpers, "wait_for_exchange_message", fake_wait_for_exchange_message)
    monkeypatch.setattr(
        helpers.app_signing,
        "serialize",
        lambda *args, **kwargs: b"serialized-acdc",
    )
    messagize_calls = []

    def fake_messagize(**kwargs):
        messagize_calls.append(kwargs)
        return bytearray(b"msg")

    monkeypatch.setattr(helpers.eventing, "messagize", fake_messagize)
    monkeypatch.setattr(helpers.eventing, "SealEvent", lambda **kwargs: kwargs)
    monkeypatch.setattr(helpers.csigning, "Siger", lambda qb64: qb64)
    monkeypatch.setattr(helpers.coring, "Prefixer", lambda qb64: qb64)
    monkeypatch.setattr(helpers.coring, "Seqner", lambda sn: sn)
    monkeypatch.setattr(helpers.coring, "Saider", lambda qb64: qb64)
    fresh_state = {"ee": {"s": "2", "d": "fresh-digest"}}
    query_calls = []

    monkeypatch.setattr(
        helpers,
        "query_key_state",
        lambda *args, **kwargs: query_calls.append((args, kwargs)) or fresh_state,
    )
    monkeypatch.setattr(
        helpers,
        "wait_for_operation",
        lambda *args, **kwargs: pytest.fail("helper should not wait internally"),
    )

    raw_operation = {"done": False, "name": "grant-op"}
    captured = {}

    class FakeIdentifiers:
        def get(self, name):
            mapping = {
                "member-a": {"prefix": "member-prefix"},
                "group": {
                    "prefix": "group-prefix",
                    "state": {"ee": {"s": "1", "d": "stale-digest"}},
                },
            }
            return mapping[name]

    class FakeIpex:
        def grant(self, *args, **kwargs):
            captured["grant"] = {"args": args, "kwargs": kwargs}
            return {"d": "grant-said"}, ["sig-1"], "grant-atc"

        def submitGrant(self, name, **kwargs):
            captured["submitGrant"] = {"name": name, **kwargs}
            return raw_operation

    class FakeRegistries:
        def serialize(self, iserder, anc):
            captured["serialize"] = {"iserder": iserder, "anc": anc}
            return b"serialized-iss"

    class FakeExchanges:
        def send(self, name, topic, **kwargs):
            captured["send"] = {"name": name, "topic": topic, **kwargs}
            return {"done": False, "name": "peer-exn-op"}

    class FakeClient:
        def identifiers(self):
            return FakeIdentifiers()

        def ipex(self):
            return FakeIpex()

        def registries(self):
            return FakeRegistries()

        def exchanges(self):
            return FakeExchanges()

    class FakeIserder:
        pre = "issuer-prefix"
        sn = 0
        said = "iss-said"

    class FakeAnc:
        raw = b"anc-raw"

    timestamp = "2026-03-24T12:00:00.000000+00:00"
    client = FakeClient()
    result = helpers.send_multisig_credential_grant(
        client,
        local_member_name="member-a",
        group_name="group",
        other_member_prefixes=["member-b-prefix"],
        recipient="holder-group-prefix",
        creder={"d": "cred-said"},
        iserder=FakeIserder(),
        anc=FakeAnc(),
        sigs=["sig-anc"],
        timestamp=timestamp,
        is_initiator=False,
    )

    assert result == raw_operation
    assert captured_wait["kwargs"]["embedded_route"] == "/ipex/grant"
    assert len(query_calls) == 1
    assert query_calls[0][0][0] is client
    assert query_calls[0][0][1] == "group-prefix"
    assert captured["grant"]["kwargs"]["dt"] == timestamp
    assert captured["grant"]["args"][0]["state"] == fresh_state
    assert captured["submitGrant"]["name"] == "group"
    assert captured["submitGrant"]["recp"] == ["holder-group-prefix"]
    assert any(call.get("seal") == {"i": "group-prefix", "s": "2", "d": "fresh-digest"} for call in messagize_calls)
    assert captured["send"]["name"] == "member-a"
    assert captured["send"]["topic"] == "multisig"
    assert captured["send"]["route"] == "/multisig/exn"
    assert captured["send"]["recipients"] == ["member-b-prefix"]


def test_submit_multisig_admit_returns_raw_operation_and_mirrors_peer_message(monkeypatch):
    messagize_calls = []

    def fake_messagize(**kwargs):
        messagize_calls.append(kwargs)
        return bytearray(b"msg")

    monkeypatch.setattr(helpers.eventing, "messagize", fake_messagize)
    monkeypatch.setattr(helpers.eventing, "SealEvent", lambda **kwargs: kwargs)
    monkeypatch.setattr(helpers.csigning, "Siger", lambda qb64: qb64)
    fresh_state = {"ee": {"s": "2", "d": "fresh-digest"}}
    query_calls = []

    monkeypatch.setattr(
        helpers,
        "query_key_state",
        lambda *args, **kwargs: query_calls.append((args, kwargs)) or fresh_state,
    )
    monkeypatch.setattr(
        helpers,
        "wait_for_operation",
        lambda *args, **kwargs: pytest.fail("helper should not wait internally"),
    )

    raw_operation = {"done": False, "name": "admit-op"}
    captured = {}

    class FakeIdentifiers:
        def get(self, name):
            mapping = {
                "member-a": {"prefix": "member-prefix"},
                "group": {
                    "prefix": "group-prefix",
                    "state": {"ee": {"s": "1", "d": "stale-digest"}},
                },
            }
            return mapping[name]

    class FakeIpex:
        def admit(self, *args, **kwargs):
            captured["admit"] = {"args": args, "kwargs": kwargs}
            return {"d": "admit-said"}, ["sig-1"], "admit-atc"

        def submitAdmit(self, name, **kwargs):
            captured["submitAdmit"] = {"name": name, **kwargs}
            return raw_operation

    class FakeExchanges:
        def send(self, name, topic, **kwargs):
            captured["send"] = {"name": name, "topic": topic, **kwargs}
            return {"done": False, "name": "peer-exn-op"}

    class FakeClient:
        def identifiers(self):
            return FakeIdentifiers()

        def ipex(self):
            return FakeIpex()

        def exchanges(self):
            return FakeExchanges()

    timestamp = "2026-03-24T12:00:00.000000+00:00"
    client = FakeClient()
    result = helpers.submit_multisig_admit(
        client,
        local_member_name="member-a",
        group_name="group",
        other_member_prefixes=["member-b-prefix"],
        issuer_prefix="issuer-group-prefix",
        grant_said="grant-note-said",
        timestamp=timestamp,
    )

    assert result == raw_operation
    assert len(query_calls) == 1
    assert query_calls[0][0][0] is client
    assert query_calls[0][0][1] == "group-prefix"
    assert captured["admit"]["args"][0]["state"] == fresh_state
    assert captured["admit"]["args"][4] == timestamp
    assert captured["submitAdmit"]["name"] == "group"
    assert captured["submitAdmit"]["recp"] == ["issuer-group-prefix"]
    assert any(call.get("seal") == {"i": "group-prefix", "s": "2", "d": "fresh-digest"} for call in messagize_calls)
    assert captured["send"]["name"] == "member-a"
    assert captured["send"]["topic"] == "multisig"
    assert captured["send"]["route"] == "/multisig/exn"
    assert captured["send"]["recipients"] == ["member-b-prefix"]
