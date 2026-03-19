# -*- encoding: utf-8 -*-
"""Delegation resource helpers for SignifyPy.

This module mirrors the small but important SignifyTS delegation surface used
by the integration suites. The only workflow exposed today is delegation
approval, because that is the step the delegator performs after a delegate has
incepted a delegated identifier.

The substance of that workflow is easy to lose if it is described only as
"approve delegation":

1. Load the delegator's current key state.
2. Build the anchoring interaction event whose `a` field points at the
   delegate's inception.
3. Sign that interaction event with the delegator's keeper.
4. Submit the signed event to KERIA's
   `/identifiers/{name}/delegation` endpoint so the agent can anchor and
   witness the approval.
"""

from keri.core import eventing

from signify.app.clienting import SignifyClient


class Delegations:
    """Resource wrapper for delegated identifier approval workflows.

    This mirrors the SignifyTS `Delegations` resource closely enough that
    integration tests can exercise real client behavior instead of raw HTTP
    calls. The core contract is that approval is represented by a normal KERI
    interaction event on the delegator, not by a separate bespoke approval
    message type.
    """

    def __init__(self, client: SignifyClient):
        """Create a delegations resource bound to one Signify client."""
        self.client = client

    def approve(self, name, anchor):
        """Approve a delegated inception by anchoring it with an interaction event.

        Parameters:
            name (str): Human-readable identifier name or alias of the
                delegator that will approve the delegation.
            anchor (dict): Anchor data describing the delegated event, normally
                containing the delegate prefix, sequence number, and SAID.

        Returns:
            tuple: `(serder, sigs, operation)` where `serder` is the locally
            created interaction event, `sigs` are the signatures over that
            event, and `operation` is the long-running KERIA response payload.

        Maintainer note:
            `anchor` is the exact data that ends up in the interaction event's
            `a` field. For delegated inception flows this is normally the
            delegate prefix plus the delegated inception sequence number and
            SAID. The server still performs the long-running anchoring and
            witness work; this client resource is only responsible for creating
            the signed approval event correctly.
        """
        hab = self.client.identifiers().get(name)
        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]
        # Delegation approval is a normal ixn anchored to the delegator's
        # current event state, with the delegate inception embedded as data.
        serder = eventing.interact(hab["prefix"], sn=sn + 1, data=[anchor], dig=dig)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=serder.raw)
        body = dict(ixn=serder.ked, sigs=sigs)
        body[keeper.algo] = keeper.params()
        res = self.client.post(f"/identifiers/{name}/delegation", json=body)
        return serder, sigs, res.json()
