# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_exchanging module

Testing the canonical app exchange import surface.
"""


def test_app_exchanges_reexports_peer_exchange_class():
    from signify.app.exchanging import Exchanges
    from signify.peer.exchanging import Exchanges as PeerExchanges

    assert Exchanges is PeerExchanges
