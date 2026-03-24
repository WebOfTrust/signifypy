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
            return {"exn": {"r": "/multisig/exn", "a": {}}}

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
