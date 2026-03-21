# -*- encoding: utf-8 -*-
"""Multisig group coordination helpers for SignifyPy."""

from signify.app.clienting import SignifyClient


class Groups:
    """Resource wrapper for multisig group coordination endpoints."""

    def __init__(self, client: SignifyClient):
        """Create a multisig group resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA multisig
                endpoints.
        """
        self.client = client

    def get_request(self, said):
        """ Retrieve full request status of multisig conversation using the SAID of an EXN

        All matching EXNs and attachments are returning with embed sections matching this EXN.

        Parameters:
            said(str): qb64 SAID of the embed section of a multisig exn message

        Returns:
            list: list of dicts of exns matching this conversation

        """

        res = self.client.get(f"/multisig/request/{said}")
        return res.json()

    def send_request(self, name, exn, sigs, atc):
        """ Send multisig exn peer-to-peer message to other members of the multisig group

        Parameters:
            name:
            exn:
            sigs:
            atc:

        Returns:
            dict: ked of sent exn message
        """

        body = dict(
            exn=exn,
            sigs=sigs,
            atc=atc.decode("utf-8")
        )

        res = self.client.post(f"/identifiers/{name}/multisig/request", json=body)
        return res.json()

    def join(self, name, rot, sigs, gid, smids, rmids):
        """Submit a multisig join approval using a received proposal event.

        Parameters:
            name (str): Local member alias submitting the join approval.
            rot (SerderKERI): Embedded proposal event being approved.
            sigs (list): Signatures over the embedded event.
            gid (str): Group identifier prefix.
            smids (list[str]): Signing member AIDs.
            rmids (list[str]): Rotating member AIDs.

        Returns:
            dict: Operation payload returned by KERIA.
        """

        body = dict(
            tpc='multisig',
            rot=rot.ked,
            sigs=sigs,
            gid=gid,
            smids=smids,
            rmids=rmids,
        )

        res = self.client.post(f"/identifiers/{name}/multisig/join", json=body)
        return res.json()
