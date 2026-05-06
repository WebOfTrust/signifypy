# -*- encoding: utf-8 -*-
"""Credential registry, credential, and IPEX workflow helpers for SignifyPy.

This module intentionally keeps three adjacent request families together
because real credential workflows cross their boundaries constantly:

- :class:`Registries` owns registry read, create, rename, and serialization
  helpers.
- :class:`Credentials` owns stored-credential reads plus issue and revoke
  operations.
- :class:`Ipex` owns the peer ``exn`` conversation layered on top of those
  credential artifacts: ``apply -> offer -> agree -> grant -> admit``.

Rule of thumb:

- use :class:`Credentials` when the operation is about stored credentials or
  credential TEL state;
- use :class:`Ipex` when the operation is about exchanging credential-related
  messages between participants;
- use :class:`Registries` when the operation is about the VDR registry itself.
"""
from collections import namedtuple
from urllib.parse import quote

from keri.core import coring, counting, serdering
from keri.core.eventing import TraitDex, interact
from keri.help import helping
from keri.vc import proving
from keri.vdr import eventing

from signify.app.clienting import SignifyClient

CredentialTypeage = namedtuple("CredentialTypeage", 'issued received')

CredentialTypes = CredentialTypeage(issued='issued', received='received')


class RegistryResult:
    """Canonical wrapper for registry creation results.

    Attributes:
        regser: Local registry inception event serder.
        serder: Local anchoring interaction serder submitted with the request.
        sigs (list[str]): Signatures over ``serder`` from the local keeper.
        response: Raw HTTP response object returned by the registry submission.

    The wrapper keeps both the locally built event material and the KERIA
    response together so callers can inspect the exact payload they created and
    still retrieve the operation JSON through :meth:`op`.
    """

    def __init__(self, regser, serder, sigs, response):
        self.regser = regser
        self.serder = serder
        self.sigs = sigs
        self.response = response

    def op(self):
        """Return the decoded operation payload from the stored response."""
        return self.response.json()


class CredentialIssueResult:
    """Canonical wrapper for credential issuance results.

    Attributes:
        acdc: The issued credential serder.
        iss: The TEL issuance event serder.
        anc: The KEL anchoring interaction serder.
        sigs (list[str]): Signatures over ``anc`` from the local keeper.
        response: Raw HTTP response object returned by the issuance submission.

    ``CredentialIssueResult`` is the maintained return shape for
    :meth:`Credentials.issue`. It remains iterable for transition safety so
    older tuple-unpacking call sites can migrate gradually.
    """

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
    """Canonical wrapper for credential revocation results.

    Attributes:
        rev: The TEL revocation event serder.
        anc: The KEL anchoring interaction serder for the revoke event.
        sigs (list[str]): Signatures over ``anc`` from the local keeper.
        response: Raw HTTP response object returned by the revoke submission.

    ``CredentialRevokeResult`` is the maintained return shape for
    :meth:`Credentials.revoke`. It remains iterable for transition safety so
    older tuple-unpacking call sites can migrate gradually.
    """

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
            client (SignifyClient): Signify client used to access KERIA
                registry endpoints.
        """
        self.client = client

    def get(self, name, registryName):
        """Fetch one registry record under an identifier alias.

        Parameters:
            name (str): Identifier alias that owns the registry.
            registryName (str): Registry alias under ``name``.

        Returns:
            dict: Decoded registry record returned by KERIA.
        """
        res = self.client.get(f"/identifiers/{name}/registries/{quote(registryName, safe='')}")
        return res.json()

    def list(self, name):
        """List registries under one identifier alias.

        Parameters:
            name (str): Identifier alias whose registries should be listed.

        Returns:
            list[dict]: Decoded registry records returned by KERIA.
        """
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
        """Create and submit a new registry inception request.

        Maintained call shape:
            ``create(name, registryName, *, noBackers=True, baks=None, toad=0, nonce=None)``

        Compatibility call shape:
            ``create(hab, registryName, ...)``

        Parameters:
            target (str | dict): Canonical identifier alias string or legacy
                habitat dict.
            registryName (str | None): Human-readable alias for the new
                registry. Required in both call shapes.
            noBackers (bool): Whether to create a no-backer registry.
            estOnly (bool | None): Optional establishment-only override. When
                omitted in canonical mode, the value is inferred from the
                identifier traits.
            baks (list[str] | None): Optional backer AIDs.
            toad (int): Witness threshold for backer receipts.
            nonce (str | None): Optional nonce for deterministic registry
                inception.

        Returns:
            RegistryResult: Wrapper exposing the locally built events and the
                submitted operation response.
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
        """Compatibility wrapper over :meth:`createFromEvents`.

        This older Python surface returns the decoded operation JSON directly
        instead of :class:`RegistryResult`. Keep it documented as compatibility
        behavior, not as a peer maintained API.
        """
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

        Parameters:
            hab (dict): Habitat state for the signing identifier.
            name (str): Identifier alias used for the request path.
            registryName (str): Registry alias to create.
            vcp: Prebuilt registry inception event.
            ixn: Prebuilt anchoring interaction event.
            sigs (list[str]): Signatures over ``ixn``.

        Returns:
            RegistryResult: Wrapper exposing the normalized event serders and
                the decoded operation payload through :meth:`RegistryResult.op`.
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
        """Serialize a TEL event plus the anchoring attachment group it needs.

        This helper is mainly consumed by IPEX grant workflows, where the
        holder or verifier needs the issuance or revocation event together with
        its source-couple attachment material.
        """
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
            registryName (str): Current registry alias.
            newName (str): Replacement alias to store in KERIA.

        Returns:
            dict: Decoded renamed registry record.
        """
        name = target if isinstance(target, str) else target["name"]
        body = dict(name=newName)
        resp = self.client.put(path=f"/identifiers/{name}/registries/{quote(registryName, safe='')}", json=body)
        return resp.json()


class Credentials:
    """Resource wrapper for stored-credential reads and credential writes.

    Maintained read surface:

    - :meth:`list`
    - :meth:`get`
    - :meth:`export`
    - :meth:`delete`
    - :meth:`state`

    Maintained write surface:

    - :meth:`issue`
    - :meth:`revoke`

    Compatibility write surface:

    - :meth:`create`
    - :meth:`create_from_events`

    Use this class when the concern is the credential itself or its TEL state.
    Use :class:`Ipex` when the concern is the peer exchange conversation that
    transports a credential between participants.
    """

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
            filter (dict | None): Maintained credential filter dict. Common
                fields in live parity coverage include ``-i`` for issuer,
                ``-s`` for schema SAID, and ``-a-i`` for subject AID.
            sort (list | None): Optional list of SAD path sort expressions.
            skip (int): Number of credentials to skip at the front of the list.
            limit (int): Total number of credentials to retrieve.

        Returns:
            list[dict]: Decoded credential records returned by KERIA.

        This method owns the maintained query contract. The older ``filtr``
        spelling is intentionally gone from the public Python surface.
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
        """Compatibility alias for CESR retrieval.

        Parameters:
            said (str): SAID of the credential to export.

        Returns:
            bytes: Raw CESR response body for the credential.

        ``export`` remains callable for older SignifyPy workflows, but the
        maintained contract is :meth:`get` with ``includeCESR=True``.
        """
        return self.get(said, includeCESR=True)

    def get(self, said, includeCESR=False):
        """Fetch one credential in JSON or CESR form.

        Parameters:
            said (str): SAID of credential to fetch.
            includeCESR (bool): When ``True``, request CESR JSON bytes instead
                of the default decoded JSON payload.

        Returns:
            dict | bytes: Decoded credential JSON when ``includeCESR`` is
            ``False``; raw CESR bytes when ``includeCESR`` is ``True``.

        This is the maintained read contract for a single credential. Use
        :meth:`export` only when compatibility with older call sites matters.
        """
        headers = dict(accept="application/json+cesr" if includeCESR else "application/json")
        res = self.client.get(f"/credentials/{said}", headers=headers)
        return res.content if includeCESR else res.json()

    def delete(self, said):
        """Delete one locally stored credential by SAID.

        Parameters:
            said (str): SAID of the locally stored credential copy to delete.

        Returns:
            None: Success is represented by the absence of an HTTP error.

        This deletes the local stored copy on the connected agent; it does not
        revoke the credential.
        """
        self.client.delete(f"/credentials/{said}")

    def state(self, registry_said, credential_said):
        """Fetch one credential TEL state record under a registry.

        Parameters:
            registry_said (str): Registry SAID that owns the credential TEL.
            credential_said (str): Credential SAID whose TEL state is being
                queried.

        Returns:
            dict: Decoded TEL state record from KERIA.

        This method stays intentionally explicit and KERIA-shaped; it does not
        wrap TEL state in a richer Python object.
        """
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

        This is the maintained public issuance API. It looks up the issuer
        habitat and registry by name, builds the ACDC, issuance event, and
        anchoring interaction locally, then submits those events to KERIA.
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

        Keep this method documented as compatibility surface only. New Python
        call sites should prefer :meth:`issue`.
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
        """Submit a credential issuance request from prebuilt local events.

        Parameters:
            hab (dict): Habitat state for the signing identifier.
            creder (dict): Prebuilt credential SAD.
            iss (dict): Prebuilt issuance TEL event SAD.
            anc (dict): Prebuilt anchoring interaction SAD.
            sigs (list[str]): Signatures over ``anc``.

        Returns:
            requests.Response: Raw HTTP response from KERIA.

        This is the low-level replay surface used by advanced and multisig
        flows that must resubmit an exact stored proposal instead of rebuilding
        events locally.
        """
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

        Parameters:
            name (str): Identifier alias used as the revoking issuer.
            said (str): SAID of the credential to revoke.
            timestamp (str | None): Optional revoke timestamp override.

        Returns:
            CredentialRevokeResult: Wrapper exposing the created revocation
                material plus synchronous ``op()`` access.

        The implementation first reads the stored credential to recover its
        registry reference and current TEL status, then builds the revoke event
        and anchoring interaction locally before submitting the delete request.
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
    """Resource wrapper for IPEX credential conversation and presentation.

    The maintained IPEX conversation order is:

    ``apply -> offer -> agree -> grant -> admit``

    Builder methods create one signed ``exn`` message plus any attachment
    material needed for transport:

    - :meth:`apply`
    - :meth:`offer`
    - :meth:`agree`
    - :meth:`grant`
    - :meth:`admit`

    Submit methods send those prebuilt messages to KERIA:

    - :meth:`submitApply`
    - :meth:`submitOffer`
    - :meth:`submitAgree`
    - :meth:`submitGrant`
    - :meth:`submitAdmit`

    Use :class:`Ipex` when the operation is about exchanging credential-related
    peer messages, not when it is about issuing, revoking, or reading stored
    credentials.
    """

    def __init__(self, client: SignifyClient):
        """Create an IPEX resource bound to one Signify client.

        Parameters:
            client (SignifyClient): Signify client used to access KERIA IPEX
                endpoints.
        """
        self.client = client

    def _hab(self, name):
        """Resolve one identifier habitat for the maintained name-based API."""
        return self.client.identifiers().get(name)

    @staticmethod
    def _said(value):
        """Normalize either a SAID string or an object exposing ``said``."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.said

    @staticmethod
    def _acdc_embed(acdc):
        """Normalize one offered ACDC into the raw CESR stream KERIA expects.

        The public IPEX surface accepts either raw CESR bytes, a decoded ACDC
        SAD dict, or a serder-like object with ``raw``.
        """
        if isinstance(acdc, (bytes, bytearray)):
            return bytes(acdc)
        if isinstance(acdc, dict):
            return serdering.SerderACDC(sad=acdc).raw
        return acdc.raw

    @staticmethod
    def _keri_embed(message):
        """Normalize one KERI event into the raw CESR stream KERIA expects.

        The public IPEX surface accepts either raw CESR bytes, a decoded KERI
        SAD dict, or a serder-like object with ``raw``.
        """
        if message is None:
            return None
        if isinstance(message, (bytes, bytearray)):
            return bytes(message)
        if isinstance(message, dict):
            return serdering.SerderKERI(sad=message).raw
        return message.raw

    @staticmethod
    def _append_attachment(raw, attachment):
        """Append one optional attachment to a raw CESR stream.

        KERIA responses may expose attachment material as a string or as a
        list of attachment fragments. This helper flattens that shape into one
        byte stream suitable for embedding in an exchange message.
        """
        if attachment is None:
            return raw
        if isinstance(attachment, (list, tuple)):
            attachment = "".join(attachment)
        if isinstance(attachment, str):
            attachment = attachment.encode("utf-8")
        return bytes(raw) + bytes(attachment)

    def apply(
        self,
        name,
        recipient,
        schemaSaid,
        *,
        message="",
        attributes=None,
        dt=None,
        datetime=None,
    ):
        """Create an IPEX apply exchange for a requested credential shape.

        Parameters:
            name (str): Identifier alias used as the IPEX sender.
            recipient (str): Recipient AID that should receive the apply.
            schemaSaid (str): Schema SAID describing the requested credential.
            message (str): Optional human-readable message.
            attributes (dict | None): Optional attribute filter/request block.
            dt (str | None): Canonical timestamp for the exchange message.
            datetime (str | None): Compatibility alias for ``dt``.

        Returns:
            tuple: ``(exn, sigs, atc)`` where ``exn`` is the built exchange
            serder, ``sigs`` are signatures over it, and ``atc`` is attachment
            material. ``apply`` normally returns an empty attachment string.

        ``apply`` starts an IPEX conversation, so it does not reference a
        prior conversation SAID.
        """
        hab = self._hab(name)
        exchanges = self.client.exchanges()
        data = dict(
            m=message,
            s=schemaSaid,
            a=attributes or {},
        )
        return exchanges.createExchangeMessage(
            sender=hab,
            route="/ipex/apply",
            payload=data,
            embeds={},
            recipient=recipient,
            dt=dt,
            datetime=datetime,
        )

    def submitApply(self, name, exn, sigs, recp):
        """Send a precreated IPEX apply exchange to recipients.

        Parameters:
            name (str): Identifier alias used in the KERIA request path.
            exn: Prebuilt apply exchange serder.
            sigs (list[str]): Signatures over ``exn``.
            recp (list[str]): Recipient AIDs that should receive the apply.

        Returns:
            dict: Decoded KERIA operation payload.
        """
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            rec=recp,
        )
        res = self.client.post(f"/identifiers/{name}/ipex/apply", json=body)
        return res.json()

    def offer(
        self,
        name,
        recipient,
        acdc,
        *,
        message="",
        applySaid=None,
        dt=None,
        datetime=None,
    ):
        """Create an IPEX offer exchange that discloses one metadata ACDC.

        Parameters:
            name (str): Identifier alias used as the IPEX sender.
            recipient (str): Recipient AID that should receive the offer.
            acdc: Offered credential metadata in raw, dict, or serder form.
            message (str): Optional human-readable message.
            applySaid (str | None): Optional SAID of the prior ``apply`` this
                offer answers.
            dt (str | None): Canonical timestamp for the exchange message.
            datetime (str | None): Compatibility alias for ``dt``.

        Returns:
            tuple: ``(exn, sigs, atc)`` where ``atc`` contains the pathed
            attachment material for the embedded ``acdc`` payload.
        """
        hab = self._hab(name)
        exchanges = self.client.exchanges()
        data = dict(m=message)
        return exchanges.createExchangeMessage(
            sender=hab,
            route="/ipex/offer",
            payload=data,
            embeds=dict(acdc=self._acdc_embed(acdc)),
            recipient=recipient,
            dig=applySaid,
            dt=dt,
            datetime=datetime,
        )

    def submitOffer(self, name, exn, sigs, atc, recp):
        """Send a precreated IPEX offer exchange to recipients.

        Parameters:
            name (str): Identifier alias used in the KERIA request path.
            exn: Prebuilt offer exchange serder.
            sigs (list[str]): Signatures over ``exn``.
            atc (str | bytes): Attachment material returned by :meth:`offer`.
            recp (list[str]): Recipient AIDs that should receive the offer.

        Returns:
            dict: Decoded KERIA operation payload.
        """
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=atc,
            rec=recp,
        )
        res = self.client.post(f"/identifiers/{name}/ipex/offer", json=body)
        return res.json()

    def agree(
        self,
        name,
        recipient,
        offerSaid,
        *,
        message="",
        dt=None,
        datetime=None,
    ):
        """Create an IPEX agree exchange that acknowledges an offered credential.

        Parameters:
            name (str): Identifier alias used as the IPEX sender.
            recipient (str): Recipient AID that should receive the agree.
            offerSaid (str): SAID of the prior ``offer`` being accepted.
            message (str): Optional human-readable message.
            dt (str | None): Canonical timestamp for the exchange message.
            datetime (str | None): Compatibility alias for ``dt``.

        Returns:
            tuple: ``(exn, sigs, atc)`` for the agree exchange. ``agree``
            normally returns an empty attachment string.
        """
        hab = self._hab(name)
        exchanges = self.client.exchanges()
        data = dict(m=message)
        return exchanges.createExchangeMessage(
            sender=hab,
            route="/ipex/agree",
            payload=data,
            embeds={},
            recipient=recipient,
            dig=offerSaid,
            dt=dt,
            datetime=datetime,
        )

    def submitAgree(self, name, exn, sigs, recp):
        """Send a precreated IPEX agree exchange to recipients.

        Parameters:
            name (str): Identifier alias used in the KERIA request path.
            exn: Prebuilt agree exchange serder.
            sigs (list[str]): Signatures over ``exn``.
            recp (list[str]): Recipient AIDs that should receive the agree.

        Returns:
            dict: Decoded KERIA operation payload.
        """
        body = dict(
            exn=exn.ked,
            sigs=sigs,
            rec=recp,
        )
        res = self.client.post(f"/identifiers/{name}/ipex/agree", json=body)
        return res.json()

    def grant(
        self,
        hab=None,
        recp=None,
        message="",
        acdc=None,
        iss=None,
        anc=None,
        agree=None,
        dt=None,
        *,
        name=None,
        recipient=None,
        agreeSaid=None,
        acdcAttachment=None,
        issAttachment=None,
        ancAttachment=None,
        datetime=None,
    ):
        """Create an IPEX grant exchange for credential presentation.

        Maintained call shape:
            ``grant(name=..., recipient=..., acdc=..., iss=..., anc=..., ...)``

        Compatibility call shape:
            ``grant(hab, recp=..., acdc=..., iss=..., anc=..., ...)``

        Parameters:
            hab (dict | None): Legacy habitat dict for the compatibility form.
            recp (str | None): Legacy recipient parameter for the compatibility
                form.
            message (str): Optional human-readable message.
            acdc: Credential payload in raw, dict, or serder form.
            iss: Issuance TEL event in raw, dict, or serder form.
            anc: Anchoring KEL event in raw, dict, or serder form.
            agree: Optional legacy agree serder or SAID.
            dt (str | None): Canonical timestamp for the exchange message.
            name (str | None): Maintained identifier alias used as the sender.
            recipient (str | None): Maintained recipient AID.
            agreeSaid (str | None): SAID of the prior ``agree`` this grant
                answers.
            acdcAttachment: Optional ACDC attachment material. When omitted,
                ``acdc`` is embedded as given.
            issAttachment: Optional issuance attachment material.
            ancAttachment: Optional anchoring attachment material.
            datetime (str | None): Compatibility alias for ``dt``.

        Returns:
            tuple: ``(exn, sigs, atc)`` for the grant exchange message, its
            signatures, and any attachment material.

        ``grant`` is the first IPEX step that normally carries non-empty
        embedded attachments because it transports the actual credential,
        issuance event, and anchoring evidence.
        """
        if name is not None:
            hab = self._hab(name)
        if recipient is not None:
            recp = recipient
        if agreeSaid is not None:
            agree = agreeSaid

        exchanges = self.client.exchanges()
        data = dict(
            m=message,
            i=recp,
        )

        embeds = dict(
            acdc=self._append_attachment(self._acdc_embed(acdc), acdcAttachment),
            iss=self._append_attachment(self._keri_embed(iss), issAttachment),
            anc=self._append_attachment(self._keri_embed(anc), ancAttachment),
        )

        kwa = dict()
        if agree is not None:
            kwa['dig'] = self._said(agree)

        grant, gsigs, atc = exchanges.createExchangeMessage(sender=hab, route="/ipex/grant",
                                                            payload=data, embeds=embeds, recipient=recp,
                                                            dt=dt, datetime=datetime, **kwa)

        return grant, gsigs, atc

    def submitGrant(self, name, exn, sigs, atc, recp):
        """Send a precreated IPEX grant exchange to recipients.

        Parameters:
            name (str): human readable identifier alias to send from
            exn: Prebuilt grant exchange serder.
            sigs (list): qb64 signatures over the exn
            atc (string|bytes): Additional pathed attachment material returned
                by :meth:`grant`.
            recp (list[string]): Recipient AIDs that should receive the grant.

        Returns:
            dict: Decoded KERIA operation payload.
        """

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=atc,
            rec=recp
        )

        res = self.client.post(f"/identifiers/{name}/ipex/grant", json=body)
        return res.json()

    def admit(
        self,
        hab=None,
        message="",
        grant=None,
        recp=None,
        dt=None,
        *,
        name=None,
        recipient=None,
        grantSaid=None,
        datetime=None,
    ):
        """Create an IPEX admit exchange that acknowledges a prior grant.

        Maintained call shape:
            ``admit(name=..., recipient=..., grantSaid=..., ...)``

        Compatibility call shape:
            ``admit(hab, message, grant, recp, dt=None)``

        Parameters:
            hab (dict | None): Legacy habitat dict for the compatibility form.
            message (str): Optional human-readable message.
            grant (str | None): Legacy grant SAID parameter.
            recp (str | None): Legacy recipient parameter.
            dt (str | None): Canonical timestamp for the exchange message.
            name (str | None): Maintained identifier alias used as the sender.
            recipient (str | None): Maintained recipient AID.
            grantSaid (str | None): SAID of the prior ``grant`` being
                acknowledged.
            datetime (str | None): Compatibility alias for ``dt``.

        Returns:
            tuple: ``(exn, sigs, atc)`` for the admit exchange. ``admit``
            normally returns an empty attachment string.
        """
        if name is not None:
            hab = self._hab(name)
        if recipient is not None:
            recp = recipient
        if grantSaid is not None:
            grant = grantSaid
        if not grant:
            raise ValueError(f"invalid grant={grant}")

        exchanges = self.client.exchanges()
        data = dict(
            m=message,
        )

        admit, asigs, atc = exchanges.createExchangeMessage(sender=hab, route="/ipex/admit",
                                                            payload=data, embeds=None, recipient=recp,
                                                            dt=dt, datetime=datetime, dig=grant)

        return admit, asigs, atc

    def submitAdmit(self, name, exn, sigs, atc, recp):
        """Send a precreated IPEX admit exchange to recipients.

        Parameters:
            name (str): human readable identifier alias to send from
            exn: Prebuilt admit exchange serder.
            sigs (list[str]): Signatures over ``exn``.
            atc (str | bytes): Additional attachment material returned by
                :meth:`admit`.
            recp (list[string]): Recipient AIDs that should receive the admit.

        Returns:
            dict: Decoded KERIA operation payload.
        """

        body = dict(
            exn=exn.ked,
            sigs=sigs,
            atc=atc,
            rec=recp
        )

        res = self.client.post(f"/identifiers/{name}/ipex/admit", json=body)
        return res.json()
