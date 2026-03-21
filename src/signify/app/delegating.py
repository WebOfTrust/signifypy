# -*- encoding: utf-8 -*-
"""Delegation resource helpers for SignifyPy.

This module supports delegation approval for Signify identifiers.
"""

from keri.core import eventing

from signify.app.clienting import SignifyClient


class Delegations:
    """Resource wrapper for delegated identifier approval workflows."""

    def __init__(self, client: SignifyClient):
        """Create a delegations resource bound to one Signify client."""
        self.client = client

    def approve(self, name, anchor):
        """Approve a delegated inception by anchoring it with an interaction event.
        The server still performs the long-running anchoring and witness work;
        this client is only responsible for creating the signed approval event.

        Parameters:
            name (str): Human-readable identifier name or alias of the
                delegator that will approve the delegation.
            anchor (dict): Anchor data describing the delegated event, normally
                containing the delegate prefix, sequence number, and SAID.

        Returns:
            tuple: `(serder, sigs, operation)` where `serder` is the locally
            created interaction event, `sigs` are the signatures over that
            event, and `operation` is the long-running KERIA response payload.
        """
        hab = self.client.identifiers().get(name)
        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]
        # Delegation approval is a normal ixn anchored to the delegator's
        # current event state, with the delegate inception embedded as data.
        serder = eventing.interact(pre=hab["prefix"], sn=sn + 1, data=[anchor], dig=dig)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=serder.raw)
        body = dict(ixn=serder.ked, sigs=sigs)
        body[keeper.algo] = keeper.params()
        res = self.client.post(f"/identifiers/{name}/delegation", json=body)
        return serder, sigs, res.json()
