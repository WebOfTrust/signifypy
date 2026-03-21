# -*- encoding: utf-8 -*-
"""Peer exchange message helpers for SignifyPy.

This module owns the app-level ``exn`` transport used by challenges,
multisig coordination, and IPEX grant/admit workflows.
"""
from keri.peer import exchanging

from signify.app.clienting import SignifyClient


class Exchanges:
    """Resource wrapper for peer exchange message creation and submission."""

    def __init__(self, client: SignifyClient):
        """Create an exchanges resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA peer
                exchange endpoints.
        """
        self.client = client

    def send(self, name, topic, sender, route, payload, embeds, recipients, dig=None):
        """  Send exn message to recipients

        Parameters:
            name (str): human readable identifier alias to send from
            topic (Str): message topic
            sender (dict): Identifier dict from identifiers.get
            route (str):  exn route field
            payload (dict): payload of the exn message
            embeds (dict): map of label to bytes of encoded KERI event to embed in exn
            recipients (list[string]): list of qb64 recipient AIDs
            dig (str): Optional qb64 SAID of exchange message reverse chain

        Returns:
            tuple|list[tuple]: one `(exn, sigs, response)` tuple for a single
            recipient, or one tuple per recipient when a broadcast fan-out is
            requested.

        """
        if not recipients:
            raise ValueError("recipients must not be empty")

        results = []
        for recipient in recipients:
            exn, sigs, atc = self.createExchangeMessage(
                sender,
                route,
                payload,
                embeds,
                recipient=recipient,
                dig=dig,
            )
            json = self.sendFromEvents(name, topic, exn=exn, sigs=sigs, atc=atc, recipients=[recipient])
            results.append((exn, sigs, json))

        return results[0] if len(results) == 1 else results

    def createExchangeMessage(self, sender, route, payload, embeds, recipient=None, dig=None, dt=None):
        """  Create exn message from parameters and return Serder with signatures and additional attachments.

        Parameters:
            sender (dict): Identifier dict from identifiers.get
            route (str):  exn route field
            payload (dict): payload of the exn message
            embeds (dict): map of label to bytes of encoded KERI event to embed in exn
            recipient (str): Optional qb64 recipient to mirror TS peer exchange semantics
            dig (str): Optional qb64 SAID of exchange message reverse chain
            dt (str): Iso formatted date string

        Returns:
            (exn, sigs, atc): tuple of Serder, list, bytes of event, signatures over the event and any transposed
                              attachments from embeds

        """

        keeper = self.client.manager.get(sender)

        exn, atc = exchanging.exchange(route=route,
                                       payload=payload,
                                       sender=sender["prefix"],
                                       recipient=recipient,
                                       embeds=embeds,
                                       dig=dig,
                                       date=dt)

        sigs = keeper.sign(ser=exn.raw)

        return exn, sigs, bytes(atc).decode("utf-8")

    def sendFromEvents(self, name, topic, exn, sigs, atc, recipients):
        """  Send precreated exn message to recipients

        Parameters:
            name (str): human readable identifier alias to send from
            topic (Str): message topic
            exn (SerderKERI): peer-to-peer message to send
            sigs (list): qb64 signatures over the exn
            atc (string|bytes): additional attachments for exn (usually pathed signatures over embeds)
            recipients (list[string]): list of qb64 recipient AIDs

        Returns:
            dict: operation response from KERIA

        """

        body = dict(
            tpc=topic,
            exn=exn.ked,
            sigs=sigs,
            atc=atc,
            rec=recipients
        )

        res = self.client.post(f"/identifiers/{name}/exchanges", json=body)
        return res.json()

    def get(self, said):
        """Fetch one stored exchange message by SAID.

        Parameters:
            said (str): qb64 SAID of the exn message to retrieve

        Returns:
            dict: exn message
        """

        res = self.client.get(f"/exchanges/{said}")
        return res.json()
