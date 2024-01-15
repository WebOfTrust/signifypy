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

        op = self.create_from_events(hab=hab, registryName=registryName, vcp=regser.ked, ixn=serder.ked, sigs=sigs)

        return regser, serder, sigs, op

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

        resp = self.client.post(path=f"/identifiers/{name}/registries", json=body)
        return resp.json()

    @staticmethod
    def serialize(serder, anc):
        seqner = coring.Seqner(sn=anc.sn)
        couple = seqner.qb64b + anc.said.encode("utf-8")
        atc = bytearray()
        atc.extend(coring.Counter(code=coring.CtrDex.SealSourceCouples,
                                  count=1).qb64b)
        atc.extend(couple)

        # prepend pipelining counter to attachments
        if len(atc) % 4:
            raise ValueError("Invalid attachments size={}, nonintegral"
                             " quadlets.".format(len(atc)))
        pcnt = coring.Counter(code=coring.CtrDex.AttachedMaterialQuadlets,
                              count=(len(atc) // 4)).qb64b
        msg = bytearray(serder.raw)
        msg.extend(pcnt)
        msg.extend(atc)

        return msg


class Credentials:
    """ Domain class for accessing, presenting, issuing and revoking credentials """

    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.client = client

    def list(self, filtr=None, sort=None, skip=None, limit=None):
        """

        Parameters:
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

        res = self.client.post(f"/credentials/query", json=json)
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

        dt = creder.attrib["dt"] if "dt" in creder.attrib else helping.nowIso8601()
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

        res = self.create_from_events(hab=hab, creder=creder.sad, iss=iserder.sad, anc=anc.sad,
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


class Ipex:
    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.client = client

    def grant(self, hab, recp, message, acdc, iss, anc, agree=None, dt=None):
        exchanges = self.client.exchanges()
        data = dict(
            m=message,
            i=recp,
        )

        embeds = dict(
            acdc=acdc,
            iss=iss,
            anc=anc
        )

        kwa = dict()
        if agree is not None:
            kwa['dig'] = agree.said

        grant, gsigs, end = exchanges.createExchangeMessage(sender=hab, route="/ipex/grant",
                                                            payload=data, embeds=embeds, dt=dt)

        return grant, gsigs, end

    def submitGrant(self, name, exn, sigs, atc, recp):
        """  Send precreated grant message to recipients

        Parameters:
            name (str): human readable identifier alias to send from
            exn (Serder): peer-to-peer message to send
            sigs (list): qb64 signatures over the exn
            atc (string|bytes): additional attachments for exn (usually pathed signatures over embeds)
            recp (list[string]): qb64 recipient AID

        Returns:
            dict: operation response from KERIA

        """

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=atc,
            rec=recp
        )

        res = self.client.post(f"/identifiers/{name}/ipex/grant", json=body)
        return res.json()

    def admit(self, hab, message, grant, dt=None):
        if not grant:
            raise ValueError(f"invalid grant={grant}")

        exchanges = self.client.exchanges()
        data = dict(
            m=message,
        )

        admit, asigs, end = exchanges.createExchangeMessage(sender=hab, route="/ipex/admit",
                                                            payload=data, embeds=None, dt=dt, dig=grant)

        return admit, asigs, end

    def submitAdmit(self, name, exn, sigs, atc, recp):
        """  Send precreated exn message to recipients

        Parameters:
            name (str): human readable identifier alias to send from
            exn (bytes): stream byte string of peer-to-peer message to send
            admit (bytes): stream byte string of admit exn message
            recp (list[string]): qb64 recipient AID

        Returns:
            dict: operation response from KERIA

        """

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=atc,
            rec=recp
        )

        res = self.client.post(f"/identifiers/{name}/ipex/admit", json=body)
        return res.json()

