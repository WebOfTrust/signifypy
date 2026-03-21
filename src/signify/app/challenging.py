# -*- encoding: utf-8 -*-
"""Challenge generation, response, and verification helpers for SignifyPy."""
from signify.app.clienting import SignifyClient


class Challenges:
    """Resource wrapper for challenge generation, response, and verification."""

    def __init__(self, client: SignifyClient):
        """Create a challenge resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA challenge
                endpoints.
        """
        self.client = client

    def generate(self):
        """Request a random challenge phrase from the server.

        Returns:
            list: Array of challenge words chosen by the remote agent.
        """

        res = self.client.get("/challenges")
        resp = res.json()
        return resp["words"]

    def respond(self, name, recp, words):
        """Send a signed challenge response to one recipient via peer exchange."""
        hab = self.client.identifiers().get(name)
        exchanges = self.client.exchanges()

        _, _, res = exchanges.send(name, "challenge", sender=hab, route="/challenge/response",
                                   payload=dict(words=words),
                                   embeds=dict(), recipients=[recp])

        return res

    def verify(self, source, words):
        """Ask the agent to verify that ``source`` signed the given words.

        Parameters:
            source (str): qb64 AID of the signer to verify.
            words (list): Challenge words expected in the signed response.
        """

        body = dict(
            words=words
        )

        res = self.client.post(f"/challenges_verify/{source}", json=body)
        return res.json()

    def responded(self, source, said):
        """Mark a challenge response as reviewed and accepted.

        Parameters:
            source (str): qb64 AID of signer
            said (str): qb64 AID of exn message representing the signed response

        Returns:
            bool: ``True`` if the acceptance request was submitted.
        """
        body = dict(
            said=said
        )

        self.client.put(f"/challenges_verify/{source}", json=body)
        return True
