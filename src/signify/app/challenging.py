# -*- encoding: utf-8 -*-
"""Challenge generation, response, and verification helpers for SignifyPy."""
from signify.app.clienting import SignifyClient
from signify.keria_types import ChallengeOperation


class Challenges:
    """Resource wrapper for challenge generation, response, and verification."""

    def __init__(self, client: SignifyClient):
        """Create a challenge resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA challenge
                endpoints.
        """
        self.client = client

    def generate(self, strength=128):
        """Request a random challenge phrase from the server.

        Parameters:
            strength (int): BIP39 entropy strength, typically ``128`` or
                ``256``.

        Returns:
            dict: Challenge payload returned by the remote agent, usually with a
            ``words`` list.
        """
        res = self.client.get(f"/challenges?strength={strength}")
        return res.json()

    def respond(self, name, recipient=None, words=None, recp=None):
        """Send a signed challenge response to one recipient via peer exchange.

        ``recipient`` is the TS-compatible parameter name. ``recp`` remains as
        a compatibility alias for older Python callers.
        """
        if recipient is None:
            recipient = recp
        if recipient is None:
            raise ValueError("recipient is required")
        if words is None:
            raise ValueError("words are required")

        hab = self.client.identifiers().get(name)
        exchanges = self.client.exchanges()

        _, _, res = exchanges.send(name, "challenge", sender=hab, route="/challenge/response",
                                   payload=dict(words=words),
                                   embeds=dict(), recipients=[recipient])

        return res

    def verify(self, source, words) -> ChallengeOperation:
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
