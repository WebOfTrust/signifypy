# -*- encoding: utf-8 -*-
"""Identifier lifecycle and endpoint-publication helpers for SignifyPy.

This module owns the identifier-facing request surface used throughout the
client: single-sig and multisig inception, delegated inception, interactions,
rotations, endpoint-role publication, location publication, and identifier-
local signing helpers.
"""
from dataclasses import asdict
from math import ceil
from urllib.parse import urlsplit

from keri import kering
from keri.app.keeping import Algos
from keri.core import eventing
from keri.core.coring import MtrDex, Tholder
from keri.kering import Roles

from signify.app.clienting import SignifyClient
from signify.core import httping, api


class Identifiers:
    """Resource wrapper for identifier lifecycle and endpoint publication."""

    def __init__(self, client: SignifyClient):
        """Create an identifier resource bound to one Signify client."""
        self.client = client

    def list(self, start=0, end=24):
        """List identifiers visible to the current agent within a range window."""
        headers = dict(Range=f"aids={start}-{end}")
        res = self.client.get(f"/identifiers", headers=headers)

        cr = res.headers["content-range"]
        start, end, total = httping.parseRangeHeader(cr, "aids")

        return dict(start=start, end=end, total=total, aids=res.json())

    def get(self, name):
        """Return the stored habitat state for one identifier by name."""
        habState = self.client.get(f"/identifiers/{name}")
        return habState.json()

    def rename(self, name, newName):
        """Rename an identifier alias without changing its underlying AID."""
        return self.update(name, {"name": newName})

    def create(self, name, transferable=True, isith="1", nsith="1", wits=None, toad="0", proxy=None, delpre=None,
               dcode=MtrDex.Blake3_256, data=None, algo=Algos.salty, estOnly=False, DnD=False, **kwargs):
        """Create and submit an identifier inception request.

        This method supports the maintained identifier variants in SignifyPy:
        normal single-sig inception, delegated inception via ``delpre``, and
        multisig/group inception via ``states`` and ``rstates`` membership
        inputs.

        Returns:
            tuple: ``(serder, sigs, operation)`` for the locally created event,
            its signatures, and the KERIA long-running operation payload.
        """

        # Get the algo specific key params
        keeper = self.client.manager.new(algo, self.client.pidx, **kwargs)

        keys, ndigs = keeper.incept(transferable=transferable)

        wits = wits if wits is not None else []
        data = [data] if data is not None else []
        cnfg = []
        if estOnly:
            cnfg.append(kering.TraitCodex.EstOnly)
        if DnD:
            cnfg.append(kering.TraitCodex.DoNotDelegate)

        if delpre is not None:
            serder = eventing.delcept(delpre=delpre,
                                      keys=keys,
                                      isith=isith,
                                      nsith=nsith,
                                      ndigs=ndigs,
                                      code=dcode,
                                      wits=wits,
                                      toad=toad,
                                      cnfg=cnfg,
                                      data=data)
        else:
            serder = eventing.incept(keys=keys,
                                     isith=isith,
                                     nsith=nsith,
                                     ndigs=ndigs,
                                     code=dcode,
                                     wits=wits,
                                     toad=toad,
                                     cnfg=cnfg,
                                     data=data)

        sigs = keeper.sign(serder.raw)

        body = dict(
            name=name,
            icp=serder.ked,
            sigs=sigs,
            proxy=proxy)
        body[algo] = keeper.params()

        if 'states' in kwargs:
            body['smids'] = [state['i'] for state in kwargs['states']]

        if 'rstates' in kwargs:
            body['rmids'] = [state['i'] for state in kwargs['rstates']]

        self.client.pidx = self.client.pidx + 1

        res = self.client.post("/identifiers", json=body)
        return serder, sigs, res.json()

    def update(self, name, info=None, typ=None, **kwas):
        """Update identifier metadata or dispatch an interaction/rotation flow.

        ``update(name, {"name": "new-alias"})`` is the TS-compatible rename
        path. The older dispatcher mode remains supported through either
        ``update(name, typ="interact", ...)`` or ``update(name, "interact", ...)``.
        """
        if isinstance(info, dict) and typ is None:
            res = self.client.put(f"/identifiers/{name}", json=info)
            return res.json()

        if typ is None:
            typ = info

        if typ == "interact":
            return self.interact(name, **kwas)
        elif typ == "rotate":
            return self.rotate(name, **kwas)
        else:
            raise kering.KeriError(f"{typ} invalid identifier update type, only 'rotate' or 'interact' allowed")

    def delete(self, name):
        """Delete an identifier by alias from the remote agent."""
        self.client.delete(f"/identifiers/{name}")

    def interact(self, name, data=None):
        """Create and submit a signed interaction event for an identifier."""
        serder, sigs, body = self.createInteract(name, data=data)
        res = self.client.post(f"/identifiers/{name}/events", json=body)
        return serder, sigs, res.json()

    def createInteract(self, name, data=None):
        """Create the local interaction event payload without submitting it."""
        hab = self.get(name)
        pre = hab["prefix"]

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]

        data = data if isinstance(data, list) else [data]

        serder = eventing.interact(pre, sn=sn + 1, data=data, dig=dig)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=serder.raw)

        body = dict(
            ixn=serder.ked,
            sigs=sigs)
        body[keeper.algo] = keeper.params()
        return serder, sigs, body

    def rotate(self, name, *, transferable=True, nsith=None, toad=None, cuts=None, adds=None,
               data=None, ncode=MtrDex.Ed25519_Seed, ncount=1, ncodes=None, states=None, rstates=None):
        """Create and submit a rotation event for an identifier or group.

        ``states`` and ``rstates`` are used by the multisig flows to pass the
        current signing-member and rotating-member state into the KERIA request
        body.
        """
        hab = self.get(name)
        pre = hab["prefix"]

        state = hab["state"]
        count = len(state['k'])
        dig = state["d"]
        ridx = int(state["s"], 16) + 1
        wits = state['b']
        isith = state["kt"] if "kt" in state else None

        if nsith is None:
            nsith = isith  # use new current as default

        if isith is None:  # compute default from newly rotated verfers above
            isith = f"{max(1, ceil(count / 2)):x}"
        if nsith is None:  # compute default from newly rotated digers above
            nsith = f"{max(0, ceil(ncount / 2)):x}"

        cst = Tholder(sith=isith).sith  # current signing threshold
        nst = Tholder(sith=nsith).sith  # next signing threshold

        # Regenerate next keys to sign rotation event
        keeper = self.client.manager.get(hab)
        # Create new keys for next digests
        if ncodes is None:
            ncodes = [ncode] * ncount

        keys, ndigs = keeper.rotate(ncodes=ncodes, transferable=transferable, states=states, rstates=rstates)

        cuts = cuts if cuts is not None else []
        adds = adds if adds is not None else []
        data = [data] if data is not None else []

        serder = eventing.rotate(pre=pre,
                                 keys=keys,
                                 dig=dig,
                                 sn=ridx,
                                 isith=cst,
                                 nsith=nst,
                                 ndigs=ndigs,
                                 toad=toad,
                                 wits=wits,
                                 cuts=cuts,
                                 adds=adds,
                                 data=data)
        sigs = keeper.sign(ser=serder.raw)

        body = dict(
            rot=serder.ked,
            sigs=sigs)
        body[keeper.algo] = keeper.params()

        if states is not None:
            body['smids'] = [state['i'] for state in states]

        if rstates is not None:
            body['rmids'] = [state['i'] for state in rstates]

        res = self.client.post(f"/identifiers/{name}/events", json=body)
        return serder, sigs, res.json()

    def addEndRole(self, name, *, role=Roles.agent, eid=None, stamp=None):
        """Publish an endpoint-role authorization reply for an identifier.

        This is the authorization half of endpoint publication: it asserts that
        `eid` is allowed to serve `role` for the identifier named by `name`.
        In OOBI-heavy flows this record must exist before any role-specific OOBI
        becomes available.
        """
        hab = self.get(name)
        pre = hab["prefix"]

        rpy = self.makeEndRole(pre, role, eid, stamp)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=rpy.raw)
        rpy_msg = api.ReplyMessage(
            rpy=rpy.ked,
            sigs=sigs)

        res = self.client.post(f"/identifiers/{name}/endroles", json=asdict(rpy_msg))
        return rpy, sigs, res.json()

    def addLocScheme(self, name, url, *, eid=None, scheme=None, stamp=None):
        """Publish a location-scheme reply for an identifier-scoped endpoint.

        `addEndRole` authorizes *who* may act in a role; `addLocScheme`
        publishes *where* that endpoint lives. Signify relies on the pair of
        `/end/role/add` and `/loc/scheme` replies when a workflow needs a
        controller, agent, or witness OOBI to resolve into a usable endpoint.
        """
        habState = self.get(name)

        rpy = self.makeLocScheme(url=url, eid=eid, scheme=scheme, stamp=stamp)
        keeper = self.client.manager.get(aid=habState)
        sigs = keeper.sign(ser=rpy.raw)
        rpy_msg = api.ReplyMessage(
            rpy=rpy.ked,
            sigs=sigs)

        res = self.client.post(f"/identifiers/{name}/locschemes", json=asdict(rpy_msg))
        return rpy, sigs, res.json()

    def sign(self, name, ser):
        """Sign an already-built KERI event or reply with an identifier keeper."""
        hab = self.get(name)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=ser.raw)

        return sigs

    def members(self, name):
        """Return multisig member state for a group identifier."""
        res = self.client.get(f"/identifiers/{name}/members")
        return res.json()

    @staticmethod
    def makeEndRole(pre, role=Roles.agent, eid=None, stamp=None):
        """Construct the signed `/end/role/add` reply payload for an AID."""
        data = dict(cid=pre, role=role)
        if eid is not None:
            data['eid'] = eid

        route = "/end/role/add"
        return eventing.reply(route=route, data=data, stamp=stamp)

    @staticmethod
    def makeLocScheme(url, *, eid=None, scheme=None, stamp=None):
        """Construct the signed ``/loc/scheme`` reply payload for an endpoint."""
        splits = urlsplit(url)
        data = dict(
            eid=eid,
            scheme=scheme if scheme is not None else splits.scheme,
            url=url,
        )
        return eventing.reply(route="/loc/scheme", data=data, stamp=stamp)
