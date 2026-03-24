# -*- encoding: utf-8 -*-
"""Credential, registry, and IPEX workflow helpers for SignifyPy.

This module covers three tightly related request families:

- credential registry lifecycle
- credential issuance and export
- IPEX grant and admit message construction/submission
"""
from collections import namedtuple

from keri.core import coring, counting
from keri.core.eventing import TraitDex, interact
from keri.help import helping
from keri.vc import proving
from keri.vdr import eventing

from signify.app.clienting import SignifyClient

CredentialTypeage = namedtuple("CredentialTypeage", 'issued received')

CredentialTypes = CredentialTypeage(issued='issued', received='received')


class Registries:
    """Resource wrapper for registry lifecycle operations under one identifier."""

    def __init__(self, client: SignifyClient):
        """Create a registries resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA registry
                endpoints.
        """
        self.client = client

    def get(self, name, registryName):
        """Fetch one credential registry under an identifier alias."""
        res = self.client.get(f"/identifiers/{name}/registries/{registryName}")
        return res.json()

    def create(self, hab, registryName, noBackers=True, estOnly=False, baks=None, toad=0, nonce=None):
        """Create and submit a new credential registry inception request.

        Returns:
            tuple: ``(vcp, anc, sigs, operation)`` for the locally created
            registry inception event, its anchoring interaction, its
            signatures, and the KERIA operation payload.
        """
        baks = baks if baks is not None else []

        pre = hab["prefix"]

        cnfg = []
        if noBackers:
            # Registry VDR inception still keys on the historical `NB` trait
            # code on this stack. Using `NRB` here silently produces a
            # backer-capable registry, which later changes issuance/revocation
            # event types from `iss/rev` to `bis/brv`.
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
        """Submit a registry creation request from prebuilt local events."""
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
        """Serialize a registry event plus its anchoring attachment group."""
        seqner = coring.Seqner(sn=anc.sn)
        couple = seqner.qb64b + anc.said.encode("utf-8")
        atc = bytearray()
        atc.extend(counting.Counter(code=counting.CtrDex_1_0.SealSourceCouples,
                                  count=1).qb64b)
        atc.extend(couple)

        # prepend pipelining counter to attachments
        if len(atc) % 4:
            raise ValueError("Invalid attachments size={}, nonintegral"
                             " quadlets.".format(len(atc)))
        pcnt = counting.Counter(code=counting.CtrDex_1_0.AttachmentGroup,
                              count=(len(atc) // 4)).qb64b
        msg = bytearray(serder.raw)
        msg.extend(pcnt)
        msg.extend(atc)

        return msg

    def rename(self, hab, registryName, newName):
        """Rename a registry alias under an existing identifier."""
        name = hab["name"]
        body = dict(name=newName)
        resp = self.client.put(path=f"/identifiers/{name}/registries/{registryName}", json=body)
        return resp.json()


class Credentials:
    """Resource wrapper for listing, exporting, issuing, and revoking credentials."""

    def __init__(self, client: SignifyClient):
        """Create a credentials resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA credential
                endpoints.
        """
        self.client = client

    def list(self, filtr=None, sort=None, skip=None, limit=None):
        """Query credentials stored by the remote agent.

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

        body = dict(
            filter=filtr,
            sort=sort,
            skip=skip,
            limit=limit
        )

        res = self.client.post(f"/credentials/query", json=body)
        return res.json()

    def export(self, said):
        """Export one credential in CESR JSON form.

        Parameters:
            said (str): SAID of credential to export
        Returns:
            credential (bytes): exported credential
        """
        headers = dict(accept="application/json+cesr")

        res = self.client.get(f"/credentials/{said}", headers=headers)
        return res.content

    def get(self, said):
        """Fetch one credential in JSON form, including its current TEL status."""
        res = self.client.get(f"/credentials/{said}")
        return res.json()

    def state(self, registry_said, credential_said):
        """Fetch one credential TEL state record under a registry."""
        res = self.client.get(f"/registries/{registry_said}/{credential_said}")
        return res.json()

    def create(self, hab, registry, data, schema, recipient=None, edges=None, rules=None, private=False,
               timestamp=None):
        """Create and submit a credential issuance request.

        Parameters:
            hab (dict): Identifier habitat state used as the issuer.
            registry (dict): Registry state under which the credential is issued.
            data (dict): Credential subject attributes.
            schema (str): SAID of the credential schema.
            recipient (str | None): Optional recipient AID.
            edges (dict | None): Optional source edges for chained credentials.
            rules (dict | None): Optional issuance rules block.
            private (bool): Whether to issue a privacy-preserving credential.
            timestamp (str | None): Optional issuance timestamp override.

        Returns:
            tuple: ``(creder, iserder, anc, sigs, operation)`` for the
            credential, issuance event, anchoring interaction, signatures, and
            KERIA operation payload.
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
            try:
                regi = int(regi)  # value is hex though should be parsed as int prior to passing in to backerIssue where it is reconverted to hex
            except ValueError:
                raise ValueError(f"invalid registry state sn={regi}")
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
        """Submit a credential issuance request from prebuilt local events."""
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

    def revoke(self, name, said, timestamp=None):
        """Create and submit a credential revocation request.

        Returns:
            tuple: ``(rserder, anc, sigs, operation)`` for the locally created
            TEL revocation event, its anchoring interaction, its signatures,
            and the KERIA operation payload.
        """
        hab = self.client.identifiers().get(name)
        pre = hab["prefix"]
        dt = timestamp or helping.nowIso8601()

        credential = self.get(said)
        sad = credential["sad"]
        status = credential["status"]

        if "ri" in sad and sad["ri"] is not None:
            registry_said = sad["ri"]
        elif "rd" in sad and sad["rd"] is not None:
            registry_said = sad["rd"]
        else:
            raise ValueError("credential is missing registry reference ri/rd")

        rserder = eventing.revoke(
            vcdig=said,
            regk=registry_said,
            dig=status["d"],
            dt=dt,
        )

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]
        anchor = dict(i=rserder.ked["i"], s=rserder.ked["s"], d=rserder.said)
        anc = interact(pre, sn=sn + 1, data=[anchor], dig=dig)

        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=anc.raw)

        body = dict(
            rev=rserder.ked,
            ixn=anc.ked,
            sigs=sigs,
        )
        body[keeper.algo] = keeper.params()

        operation = self.client.delete(
            f"/identifiers/{name}/credentials/{said}",
            body=body,
        ).json()

        return rserder, anc, sigs, operation


class Ipex:
    """Resource wrapper for IPEX peer exchange message construction and submission."""

    def __init__(self, client: SignifyClient):
        """Create an IPEX resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA IPEX
                endpoints.
        """
        self.client = client

    def grant(self, hab, recp, message, acdc, iss, anc, agree=None, dt=None):
        """Create an IPEX grant exchange message for a recipient.

        Returns:
            tuple: ``(exn, sigs, atc)`` for the grant exchange message, its
            signatures, and any attachment material.
        """
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

        grant, gsigs, atc = exchanges.createExchangeMessage(sender=hab, route="/ipex/grant",
                                                            payload=data, embeds=embeds, recipient=recp,
                                                            dt=dt, **kwa)

        return grant, gsigs, atc

    def submitGrant(self, name, exn, sigs, atc, recp):
        """Send a precreated IPEX grant exchange to recipients.

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

    def admit(self, hab, message, grant, recp, dt=None):
        """Create an IPEX admit exchange that references an existing grant."""
        if not grant:
            raise ValueError(f"invalid grant={grant}")

        exchanges = self.client.exchanges()
        data = dict(
            m=message,
        )

        admit, asigs, atc = exchanges.createExchangeMessage(sender=hab, route="/ipex/admit",
                                                            payload=data, embeds=None, recipient=recp,
                                                            dt=dt, dig=grant)

        return admit, asigs, atc

    def submitAdmit(self, name, exn, sigs, atc, recp):
        """Send a precreated IPEX admit exchange to recipients.

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
