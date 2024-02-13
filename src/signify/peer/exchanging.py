# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.exchanging module

"""
from keri.peer import exchanging

from signify.app.clienting import SignifyClient


class Exchanges:
    """ Domain class for performing operations on and with group multisig AIDs """

    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

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
            dict: operation response from KERIA

        """

        exn, sigs, atc = self.createExchangeMessage(sender, route, payload, embeds, dig=dig)
        json = self.sendFromEvents(name, topic, exn=exn, sigs=sigs, atc=atc, recipients=recipients)

        return exn, sigs, json

    def createExchangeMessage(self, sender, route, payload, embeds, dig=None, dt=None):
        """  Create exn message from parameters and return Serder with signatures and additional attachments.

        Parameters:
            sender (dict): Identifier dict from identifiers.get
            route (str):  exn route field
            payload (dict): payload of the exn message
            embeds (dict): map of label to bytes of encoded KERI event to embed in exn
            dig (str): Optional qb64 SAID of exchange message reverse chain
            dt (str): Iso formatted date string

        Returns:
            (exn, sigs, end): tuple of Serder, list, bytes of event, signatures over the event and any transposed
                              attachments from embeds

        """

        keeper = self.client.manager.get(sender)

        exn, end = exchanging.exchange(route=route,
                                       payload=payload,
                                       sender=sender["prefix"],
                                       embeds=embeds,
                                       dig=dig,
                                       date=dt)

        sigs = keeper.sign(ser=exn.raw)

        return exn, sigs, bytes(end).decode("utf-8")

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
        """

        Parameters:
            said (str): qb64 SAID of the exn message to retrieve

        Returns:
            dict: exn message

        """

        res = self.client.get(f"/exchanges/{said}")
        return res.json()
