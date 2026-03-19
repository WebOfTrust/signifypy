# -*- encoding: utf-8 -*-
"""Unit tests for the SignifyPy CLI status command."""

from types import SimpleNamespace

import pytest


def test_status_connects_before_loading_identifier(monkeypatch):
    from signify.app.cli.commands import status as status_cmd

    seen = {}
    aid = {
        "name": "aid1",
        "prefix": "EAID123",
        "state": {"s": "0", "di": "", "b": [], "bt": "0", "k": []},
        "windexes": [],
    }

    class FakeIdentifiers:
        def __init__(self, client):
            self.client = client

        def get(self, alias):
            assert self.client.connected is True
            seen["alias"] = alias
            return aid

    class FakeClient:
        def __init__(self, *, passcode, tier, url):
            seen["client_args"] = {
                "passcode": passcode,
                "tier": tier,
                "url": url,
            }
            self.connected = False

        def connect(self):
            self.connected = True
            seen["connected"] = True

        def identifiers(self):
            return FakeIdentifiers(self)

    def fake_print_identifier(loaded_aid, label="Identifier"):
        seen["printed_aid"] = loaded_aid
        seen["label"] = label

    monkeypatch.setattr(status_cmd.clienting, "SignifyClient", FakeClient)
    monkeypatch.setattr(status_cmd, "printIdentifier", fake_print_identifier)

    args = SimpleNamespace(
        alias="aid1",
        bran="abcdefghijklmnop01234",
        url="http://example.com",
        verbose=False,
    )

    doer = status_cmd.status(lambda: 0.0, args=args)
    assert next(doer) == 0.0
    with pytest.raises(StopIteration):
        next(doer)

    assert seen["connected"] is True
    assert seen["alias"] == "aid1"
    assert seen["printed_aid"] == aid


def test_print_identifier_uses_local_identifier_label(capsys):
    from signify.app.cli.commands.status import printIdentifier

    aid = {
        "name": "group-aid",
        "prefix": "EGroup123",
        "state": {
            "s": "1",
            "di": "",
            "b": ["EWit123"],
            "bt": "1",
            "k": ["DK1"],
        },
        "group": {"mhab": {"prefix": "ELocalMember123"}},
        "windexes": [0],
    }

    printIdentifier(aid)
    out = capsys.readouterr().out

    assert "Local Identifier" in out
    assert "Local Indentifier" not in out
