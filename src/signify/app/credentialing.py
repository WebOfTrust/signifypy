# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.credentialing module

"""
from collections import namedtuple

from keri.core import coring
from keri.core.eventing import TraitDex, interact
from keri.help import helping
from keri.vc import proving
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

    def get(self, name, registryName):
        res = self.client.get(f"/identifiers/{name}/registries/{registryName}")
        return res.json()

    def create(self, hab, registryName, noBackers=True, estOnly=False, baks=None, toad=0, nonce=None):
        baks = baks if baks is not None else []

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

        res = self.create_from_events(hab=hab, registryName=registryName, vcp=regser.ked, ixn=serder.ked, sigs=sigs)

        return regser, serder, sigs, res.json()

    def create_from_events(self, hab, registryName, vcp, ixn, sigs):
        body = dict(
            name=registryName,
            vcp=vcp,
            ixn=ixn,
            sigs=sigs
        )
        keeper = self.client.manager.get(aid=hab)
        body[keeper.algo] = keeper.params()
        name = hab["name"]

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

    def create(self, hab, registry, data, schema, recipient=None, edges=None, rules=None, private=False,
               timestamp=None):
        """ Create and submit a credential

        Parameters:
            hab:
            registry:
            data:
            schema:
            recipient:
            edges:
            rules:
            private:
            timestamp:

        Returns:

        """
        pre = hab["prefix"]

        if recipient is None:
            recp = None
        else:
            recp = recipient

        if timestamp is not None:
            data["dt"] = timestamp

        regk = registry['regk']
        creder = proving.credential(issuer=registry['pre'],
                                    schema=schema,
                                    recipient=recp,
                                    data=data,
                                    source=edges,
                                    private=private,
                                    rules=rules,
                                    status=regk)

        dt = creder.subject["dt"] if "dt" in creder.subject else helping.nowIso8601()
        noBackers = 'NB' in registry['state']['c']
        if noBackers:
            iserder = eventing.issue(vcdig=creder.said, regk=regk, dt=dt)
        else:
            regi = registry['state']['s']
            regd = registry['state']['d']
            iserder = eventing.backerIssue(vcdig=creder.said, regk=regk, regsn=regi, regd=regd, dt=dt)

        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        data = [rseal]

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]
        anc = interact(pre, sn=sn + 1, data=data, dig=dig)

        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=anc.raw)

        res = self.create_from_events(hab=hab, creder=creder.ked, iss=iserder.ked, anc=anc.ked,
                                      sigs=sigs)

        return creder, iserder, anc, sigs, res.json()

    def create_from_events(self, hab, creder, iss, anc, sigs):
        body = dict(
            acdc=creder,
            iss=iss,
            ixn=anc,
            sigs=sigs
        )
        keeper = self.client.manager.get(aid=hab)
        body[keeper.algo] = keeper.params()
        name = hab["name"]

        return self.client.post(f"/identifiers/{name}/credentials", json=body)
