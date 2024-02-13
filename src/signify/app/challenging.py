# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.challenging module

"""
from signify.app.clienting import SignifyClient


class Challenges:
    """ Challenges domain object """

    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.client = client

    def generate(self):
        """  Request 12 random word challenge phrase from server

        Returns:
            list: array of 12 random words

        """

        res = self.client.get("/challenges")
        resp = res.json()
        return resp["words"]

    def respond(self, name, recp, words):
        hab = self.client.identifiers().get(name)
        exchanges = self.client.exchanges()

        _, _, res = exchanges.send(name, "challenge", sender=hab, route="/challenge/response",
                                   payload=dict(words=words),
                                   embeds=dict(), recipients=[recp])

        return res

    def verify(self, name, source, words):
        """ Ask Agent to verify a given sender signed the provided words

        Parameters:
            name (str): human readable name of AID environment
            source(str): qb64 AID of source of challenge response to check for
            words(list): list of challenge words to check for
        """

        json = dict(
            words=words
        )

        res = self.client.post(f"/challenges/{name}/verify/{source}", json=json)
        return res.json()

    def responded(self, name, source, said):
        """ Mark challenge response as signed and accepted

        Parameters:
            name (str): human readable name of AID environment
            source (str): qb64 AID of signer
            said (str): qb64 AID of exn message representing the signed response

        Returns:
            bool: True means successful

        """
        json = dict(
            said=said
        )

        self.client.put(f"/challenges/{name}/verify/{source}", json=json)
        return True
