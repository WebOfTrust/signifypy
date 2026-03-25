# -*- encoding: utf-8 -*-
"""Credential, registry, and IPEX workflow helpers for SignifyPy.

This module covers three tightly related request families:

- credential registry lifecycle
- credential issuance and export
- IPEX grant and admit message construction/submission
"""
from collections import namedtuple

from keri.core import coring, counting, serdering
from keri.core.eventing import TraitDex, interact
from keri.help import helping
from keri.vc import proving
from keri.vdr import eventing

from signify.app.clienting import SignifyClient

CredentialTypeage = namedtuple("CredentialTypeage", 'issued received')

CredentialTypes = CredentialTypeage(issued='issued', received='received')


class RegistryResult:
    """Write-path wrapper for registry creation results."""

    def __init__(self, regser, serder, sigs, response):
        self.regser = regser
        self.serder = serder
        self.sigs = sigs
        self.response = response

    def op(self):
        """Return the decoded operation payload from the stored response."""
        return self.response.json()


class CredentialIssueResult:
    """Canonical write-path wrapper for credential issuance results."""

    def __init__(self, acdc, iss, anc, sigs, response):
        self.acdc = acdc
        self.iss = iss
        self.anc = anc
        self.sigs = sigs
        self.response = response

    def op(self):
        """Return the decoded operation payload from the stored response."""
        return self.response.json()

    def __iter__(self):
        """Yield the historical tuple shape for transition safety."""
        yield self.acdc
        yield self.iss
        yield self.anc
        yield self.sigs
        yield self.op()


class CredentialRevokeResult:
    """Canonical write-path wrapper for credential revocation results."""

    def __init__(self, rev, anc, sigs, response):
        self.rev = rev
        self.anc = anc
        self.sigs = sigs
        self.response = response

    def op(self):
        """Return the decoded operation payload from the stored response."""
        return self.response.json()

    def __iter__(self):
        """Yield the historical tuple shape for transition safety."""
        yield self.rev
        yield self.anc
        yield self.sigs
        yield self.op()


class Registries:
    """Resource wrapper for registry lifecycle operations under one identifier.

    The canonical write surface follows the established KERIpy/KERIA/SignifyPy
    camelCase style while preserving SignifyTS behavioral compatibility:

    - ``create(name, registryName, ...)``
    - ``createFromEvents(hab, name, registryName, vcp, ixn, sigs)``
    - ``rename(name, registryName, newName)``

    Compatibility forms remain callable for existing SignifyPy callers:

    - ``create(hab, registryName, ...)``
    - ``create_from_events(hab, registryName, vcp, ixn, sigs)``
    - ``rename(hab, registryName, newName)``
    """

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

    def list(self, name):
        """List credential registries under one identifier alias."""
        res = self.client.get(f"/identifiers/{name}/registries")
        return res.json()

    def create(
        self,
        target,
        registryName=None,
        *,
        noBackers=True,
        estOnly=None,
        baks=None,
        toad=0,
        nonce=None,
    ):
        """Create and submit a new credential registry inception request.

        Canonical usage follows the ecosystem's established camelCase form:
        ``create(name, registryName, *, noBackers=True, baks=None, toad=0, nonce=None)``.

        Compatibility forms stay callable during the parity transition:
        ``create(hab, registryName, ...)``. All forms return :class:`RegistryResult`.
        """
        if isinstance(target, str):
            name = target
            if registryName is None:
                raise TypeError("registryName is required")
            hab = self.client.identifiers().get(name)
            if estOnly is None:
                state_traits = hab["state"].get("c", [])
                estOnly = TraitDex.EstOnly in state_traits or "EO" in state_traits
            if estOnly:
                raise NotImplementedError("establishment only not implemented")
        else:
            hab = target
            if registryName is None:
                raise TypeError("registryName is required")
            name = hab["name"]
            if estOnly is None:
                estOnly = False

        return self._create_result(
            hab=hab,
            name=name,
            registryName=registryName,
            noBackers=noBackers,
            estOnly=estOnly,
            baks=baks,
            toad=toad,
            nonce=nonce,
        )

    def _create_result(self, *, hab, name, registryName, noBackers=True, estOnly=False, baks=None, toad=0, nonce=None):
        """Build registry inception events locally and wrap the submission result."""
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

        regser = eventing.incept(
            pre,
            baks=baks,
            toad=toad,
            nonce=nonce,
            cnfg=cnfg,
            code=coring.MtrDex.Blake3_256,
        )

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]

        rseal = dict(i=regser.pre, s="0", d=regser.pre)
        data = [rseal]

        serder = interact(pre, sn=sn + 1, data=data, dig=dig)

        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=serder.raw)

        response = self._submit_registry_events(
            hab=hab,
            name=name,
            registryName=registryName,
            vcp=regser.ked,
            ixn=serder.ked,
            sigs=sigs,
        )
        return RegistryResult(regser=regser, serder=serder, sigs=sigs, response=response)

    @staticmethod
    def _serder_from_event(event):
        """Normalize a registry or anchoring event into a SerderKERI."""
        if hasattr(event, "ked"):
            return serdering.SerderKERI(sad=event.ked)
        if hasattr(event, "sad"):
            return serdering.SerderKERI(sad=event.sad)
        return serdering.SerderKERI(sad=event)

    def _submit_registry_events(self, *, hab, name, registryName, vcp, ixn, sigs):
        """Submit prebuilt registry inception material and return the raw response."""
        body = dict(
            name=registryName,
            vcp=vcp,
            ixn=ixn,
            sigs=sigs
        )
        keeper = self.client.manager.get(aid=hab)
        body[keeper.algo] = keeper.params()

        return self.client.post(path=f"/identifiers/{name}/registries", json=body)

    def create_from_events(self, hab, registryName, vcp, ixn, sigs):
        """Compatibility wrapper returning the legacy operation JSON payload."""
        return self.createFromEvents(
            hab=hab,
            name=hab["name"],
            registryName=registryName,
            vcp=vcp,
            ixn=ixn,
            sigs=sigs,
        ).op()

    def createFromEvents(self, hab, name, registryName, vcp, ixn, sigs):
        """Submit a registry creation request from prebuilt local events.

        Returns:
            RegistryResult: Wrapper exposing the submitted event material and
                the decoded operation payload through ``op()``.
        """
        regser = self._serder_from_event(vcp)
        serder = self._serder_from_event(ixn)
        response = self._submit_registry_events(
            hab=hab,
            name=name,
            registryName=registryName,
            vcp=regser.ked,
            ixn=serder.ked,
            sigs=sigs,
        )
        return RegistryResult(regser=regser, serder=serder, sigs=sigs, response=response)

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

    def rename(self, target, registryName, newName):
        """Rename a registry alias under an existing identifier.

        Parameters:
            target (str | dict): Canonical identifier alias string or legacy
                habitat dict carrying ``name``.
        """
        name = target if isinstance(target, str) else target["name"]
        body = dict(name=newName)
        resp = self.client.put(path=f"/identifiers/{name}/registries/{registryName}", json=body)
        return resp.json()


class Credentials:
    """Resource wrapper for listing, reading, issuing, and revoking credentials."""

    def __init__(self, client: SignifyClient):
        """Create a credentials resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA credential
                endpoints.
        """
        self.client = client

    def list(self, filter=None, sort=None, skip=0, limit=25):
        """Query credentials stored by the remote agent.

        Parameters:
            filter (dict | None): Maintained credential filter dict.
            sort (list | None): List of SAD Path field references to sort by.
            skip (int): Number of credentials to skip at the front of the list.
            limit (int): Total number of credentials to retrieve.

        Returns:
            list: list of dicts representing the listed credentials
        """
        sort = sort if sort is not None else []
        filter = {} if filter is None else filter

        body = dict(
            filter=filter,
            sort=sort,
            skip=skip,
            limit=limit
        )

        res = self.client.post(f"/credentials/query", json=body)
        return res.json()

    def export(self, said):
        """Compatibility alias for fetching one credential in CESR JSON form."""
        return self.get(said, includeCESR=True)

    def get(self, said, includeCESR=False):
        """Fetch one credential in JSON or CESR form.

        Parameters:
            said (str): SAID of credential to fetch.
            includeCESR (bool): When ``True``, request CESR JSON bytes instead
                of the default decoded JSON payload.
        """
        headers = dict(accept="application/json+cesr" if includeCESR else "application/json")
        res = self.client.get(f"/credentials/{said}", headers=headers)
        return res.content if includeCESR else res.json()

    def delete(self, said):
        """Delete one locally stored credential by SAID."""
        self.client.delete(f"/credentials/{said}")

    def state(self, registry_said, credential_said):
        """Fetch one credential TEL state record under a registry."""
        res = self.client.get(f"/registries/{registry_said}/{credential_said}")
        return res.json()

    def issue(
        self,
        name,
        registryName,
        data,
        schema,
        *,
        recipient=None,
        edges=None,
        rules=None,
        private=False,
        timestamp=None,
    ):
        """Create and submit a credential issuance request using canonical names.

        Parameters:
            name (str): Identifier alias used as the issuer.
            registryName (str): Registry alias under the identifier.
            data (dict): Credential subject attributes.
            schema (str): SAID of the credential schema.
            recipient (str | None): Optional recipient AID.
            edges (dict | None): Optional source edges for chained credentials.
            rules (dict | None): Optional issuance rules block.
            private (bool): Whether to issue a privacy-preserving credential.
            timestamp (str | None): Optional issuance timestamp override.

        Returns:
            CredentialIssueResult: Wrapper exposing the created credential
                material plus synchronous ``op()`` access.
        """
        hab = self.client.identifiers().get(name)
        registry = self.client.registries().get(name, registryName)
        return self._issue_result(
            hab=hab,
            registry=registry,
            data=data,
            schema=schema,
            recipient=recipient,
            edges=edges,
            rules=rules,
            private=private,
            timestamp=timestamp,
        )

    def create(self, hab, registry, data, schema, recipient=None, edges=None, rules=None, private=False,
               timestamp=None):
        """Compatibility wrapper for the older registry-centric issuance API.

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
        result = self._issue_result(
            hab=hab,
            registry=registry,
            data=data,
            schema=schema,
            recipient=recipient,
            edges=edges,
            rules=rules,
            private=private,
            timestamp=timestamp,
        )
        return result.acdc, result.iss, result.anc, result.sigs, result.op()

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

    def revoke(self, name, said, *, timestamp=None):
        """Create and submit a credential revocation request.

        Returns:
            CredentialRevokeResult: Wrapper exposing the created revocation
                material plus synchronous ``op()`` access.
        """
        return self._revoke_result(name=name, said=said, timestamp=timestamp)

    def _issue_result(
        self,
        *,
        hab,
        registry,
        data,
        schema,
        recipient=None,
        edges=None,
        rules=None,
        private=False,
        timestamp=None,
    ):
        creder, iserder, anc, sigs = self._build_issue_artifacts(
            hab=hab,
            registry=registry,
            data=data,
            schema=schema,
            recipient=recipient,
            edges=edges,
            rules=rules,
            private=private,
            timestamp=timestamp,
        )
        response = self.create_from_events(
            hab=hab,
            creder=creder.sad,
            iss=iserder.sad,
            anc=anc.sad,
            sigs=sigs,
        )
        return CredentialIssueResult(
            acdc=creder,
            iss=iserder,
            anc=anc,
            sigs=sigs,
            response=response,
        )

    def _build_issue_artifacts(
        self,
        *,
        hab,
        registry,
        data,
        schema,
        recipient=None,
        edges=None,
        rules=None,
        private=False,
        timestamp=None,
    ):
        pre = hab["prefix"]
        recp = recipient if recipient is not None else None
        body_data = dict(data)
        if timestamp is not None:
            body_data["dt"] = timestamp

        regk = registry['regk']
        creder = proving.credential(
            issuer=registry['pre'],
            schema=schema,
            recipient=recp,
            data=body_data,
            source=edges,
            private=private,
            rules=rules,
            status=regk,
        )

        dt = creder.attrib["dt"] if "dt" in creder.attrib else helping.nowIso8601()
        noBackers = 'NB' in registry['state']['c']
        if noBackers:
            iserder = eventing.issue(vcdig=creder.said, regk=regk, dt=dt)
        else:
            regi = registry['state']['s']
            try:
                regi = int(regi)
            except ValueError:
                raise ValueError(f"invalid registry state sn={regi}")
            regd = registry['state']['d']
            iserder = eventing.backerIssue(vcdig=creder.said, regk=regk, regsn=regi, regd=regd, dt=dt)

        vcid = iserder.ked["i"]
        rseq = coring.Seqner(snh=iserder.ked["s"])
        rseal = eventing.SealEvent(vcid, rseq.snh, iserder.said)
        anchor_data = [dict(i=rseal.i, s=rseal.s, d=rseal.d)]

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]
        anc = interact(pre, sn=sn + 1, data=anchor_data, dig=dig)

        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=anc.raw)
        return creder, iserder, anc, sigs

    def _revoke_result(self, *, name, said, timestamp=None):
        hab, rserder, anc, sigs = self._build_revoke_artifacts(
            name=name,
            said=said,
            timestamp=timestamp,
        )
        keeper = self.client.manager.get(aid=hab)
        body = dict(
            rev=rserder.ked,
            ixn=anc.ked,
            sigs=sigs,
        )
        body[keeper.algo] = keeper.params()
        response = self.client.delete(
            f"/identifiers/{name}/credentials/{said}",
            body=body,
        )
        return CredentialRevokeResult(
            rev=rserder,
            anc=anc,
            sigs=sigs,
            response=response,
        )

    def _build_revoke_artifacts(self, *, name, said, timestamp=None):
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
        return hab, rserder, anc, sigs


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
