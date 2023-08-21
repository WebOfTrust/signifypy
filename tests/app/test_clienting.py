# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_clienting module

Testing clienting with unit tests
"""

from keri import kering
from keri.core.coring import Tiers
import pytest
from signify.app.clienting import SignifyClient
from signify.core.authing import Controller


def test_signify_client_defaults():
    client = SignifyClient(passcode="abcdefghijklmnop01234")

    assert client.bran == "abcdefghijklmnop01234"
    assert client.pidx == 0
    assert client.tier == Tiers.low
    assert client.extern_modules is None

    assert isinstance(client.ctrl, Controller)
    assert client.mgr is None
    assert client.session is None
    assert client.agent is None
    assert client.authn is None
    assert client.base is None


def test_signify_client_bad_passcode_length():
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(passcode="too short")
