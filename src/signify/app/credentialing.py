# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.credentialing module

"""
from collections import namedtuple

from keri.core import coring
from keri.core.eventing import TraitDex, interact
from keri.vdr import eventing

from signify.app.clienting import SignifyClient

CredentialTypeage = namedtuple("CredentialTypeage", 'issued received')

CredentialTypes = CredentialTypeage(issued='issued', received='received')


class Registries:

    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.client = client

    def create(self, name, registryName, noBackers=True, estOnly=False, baks=None, toad=0, nonce=None):
        baks = baks if baks is not None else []

        identifiers = self.client.identifiers()
        hab = identifiers.get(name)
        pre = hab["prefix"]

        cnfg = []
        if noBackers:
            cnfg.append(TraitDex.NoBackers)
        if estOnly:
            cnfg.append(TraitDex.EstOnly)

        regser = eventing.incept(pre,
                                 baks=baks,
                                 toad=toad,
                                 nonce=nonce,
                                 cnfg=cnfg,
                                 code=coring.MtrDex.Blake3_256)

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]

        rseal = dict(i=regser.pre, s="0", d=regser.pre)
        data = [rseal]

        serder = interact(pre, sn=sn + 1, data=data, dig=dig)

        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=serder.raw)

        res = self.create_from_events(name=name, hab=hab, registryName=registryName, vcp=regser.ked, ixn=serder.ked,
                                      sigs=sigs)

        return regser, serder, sigs, res.json()

    def create_from_events(self, name, hab, registryName, vcp, ixn, sigs):
        body = dict(
            name=registryName,
            vcp=vcp,
            ixn=ixn,
            sigs=sigs
        )
        keeper = self.client.manager.get(aid=hab)
        body[keeper.algo] = keeper.params()

        return self.client.post(path=f"/identifiers/{name}/registries", json=body)


class Credentials:
    """ Domain class for accessing, presenting, issuing and revoking credentials """

    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.client = client

    def list(self, name, filtr=None, sort=None, skip=None, limit=None):
        """

        Parameters:
            name (str): Alias associated with the AID
            filtr (dict): Credential filter dict
            sort(list): list of SAD Path field references to sort by
            skip (int): number of credentials to skip at the front of the list
            limit (int): total number of credentials to retrieve

        Returns:
            list: list of dicts representing the listed credentials

        """
        filtr = filtr if filtr is not None else {}
        sort = sort if sort is not None else []
        skip = skip if skip is not None else 0
        limit = limit if limit is not None else 25

        json = dict(
            filter=filtr,
            sort=sort,
            skip=skip,
            limt=limit
        )

        res = self.client.post(f"/identifiers/{name}/credentials/query", json=json)
        return res.json()

    def export(self, name, said):
        """

        Parameters:
            name (str): Name associated with the AID
            said (str): SAID of credential to export
        Returns:
            credential (bytes): exported credential

        """
        headers = dict(accept="application/json+cesr")

        res = self.client.get(f"/identifiers/{name}/credentials/{said}", headers=headers)
        return res.content
