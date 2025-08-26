# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.clienting module

Testing clienting with integration tests that require a running KERIA Cloud Agent
"""

import pytest
import requests
from keri import kering
from keri.core.coring import Tiers

from signify.app.clienting import SignifyClient


def create_agent_and_controller():
    """Creates an agent using the SignifyClient"""
    url = "http://localhost:3901"
    boot_url = "http://localhost:3903"
    bran = b'0123456789abcdefghijk'
    tier = Tiers.med

    client = SignifyClient(passcode=bran, tier=tier, url=url, boot_url=boot_url)
    assert client.controller == "EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0"

    # Raises configuration error because the started agent has a different controller AID
    with pytest.raises(kering.ConfigurationError):
        client.connect(url=url)

    tier = Tiers.low
    client = SignifyClient(passcode=bran, tier=tier, url=url, boot_url=boot_url)
    assert client.controller == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    evt, siger = client.ctrl.event()
    body = client.boot()
    print(body)

    client.connect(url=url, )
    assert client.agent is not None
    assert client.agent.pre == "EEXekkGu9IAzav6pZVJhkLnjtjM5v3AcyA-pdKUcaGei"
    assert client.agent.delpre == "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    print("Person agent created")


if __name__ == "__main__":
    create_agent_and_controller()
