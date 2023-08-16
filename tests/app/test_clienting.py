
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
    assert client.extern_modules == None

    assert isinstance(client.ctrl, Controller)
    assert client.mgr == None
    assert client.session == None
    assert client.agent == None
    assert client.authn == None
    assert client.base == None

def test_signify_client_bad_passcode_length():
    with pytest.raises(kering.ConfigurationError):
        SignifyClient(passcode="too short")
