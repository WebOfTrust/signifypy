# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.aiding module

"""
from math import ceil

from keri import kering
from keri.app.keeping import Algos
from keri.core import eventing
from keri.core.coring import MtrDex, Tholder
from keri.kering import Roles

from signify.app.clienting import SignifyClient
from signify.core import httping


class Identifiers:
    """ Domain class for accessing, creating and rotating KERI Autonomic IDentifiers (AIDs) """

    def __init__(self, client: SignifyClient):
        self.client = client

    def list(self, start=0, end=24):
        headers = dict(Range=f"aids={start}-{end}")
        res = self.client.get(f"/identifiers", headers=headers)

        cr = res.headers["content-range"]
        start, end, total = httping.parseRangeHeader(cr, "aids")

        return dict(start=start, end=end, total=total, aids=res.json())

    def get(self, name):
        res = self.client.get(f"/identifiers/{name}")
        return res.json()

    def create(self, name, transferable=True, isith="1", nsith="1", wits=None, toad="0", proxy=None, delpre=None,
               dcode=MtrDex.Blake3_256, data=None, algo=Algos.salty, estOnly=False, DnD=False, **kwargs):

        # Get the algo specific key params
        keeper = self.client.manager.new(algo, self.client.pidx, **kwargs)

        keys, ndigs = keeper.incept(transferable=transferable)

        wits = wits if wits is not None else []
        data = [data] if data is not None else []
        cnfg = []
        if estOnly:
            cnfg.append(eventing.TraitCodex.EstOnly)
        if DnD:
            cnfg.append(eventing.TraitCodex.DoNotDelegate)

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

        json = dict(
            name=name,
            icp=serder.ked,
            sigs=sigs,
            proxy=proxy)
        json[algo] = keeper.params()

        if 'states' in kwargs:
            json['smids'] = [state['i'] for state in kwargs['states']]

        if 'rstates' in kwargs:
            json['rmids'] = [state['i'] for state in kwargs['rstates']]

        self.client.pidx = self.client.pidx + 1

        res = self.client.post("/identifiers", json=json)
        return serder, sigs, res.json()

    def update(self, name, typ, **kwas):
        if typ == "interact":
            self.interact(name, **kwas)
        elif typ == "rotate":
            self.rotate(name, **kwas)
        else:
            raise kering.KeriError(f"{typ} invalid identifier update type, only 'rotate' or 'interact' allowed")

        pass

    def delete(self, name):
        pass

    def interact(self, name, data=None):
        hab = self.get(name)
        pre = hab["prefix"]

        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]

        data = data if isinstance(data, list) else [data]

        serder = eventing.interact(pre, sn=sn + 1, data=data, dig=dig)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=serder.raw)

        json = dict(
            ixn=serder.ked,
            sigs=sigs)
        json[keeper.algo] = keeper.params()

        res = self.client.put(f"/identifiers/{name}?type=ixn", json=json)
        return serder, sigs, res.json()

    def rotate(self, name, *, transferable=True, nsith=None, toad=None, cuts=None, adds=None,
               data=None, ncode=MtrDex.Ed25519_Seed, ncount=1, ncodes=None, states=None, rstates=None):
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

        json = dict(
            rot=serder.ked,
            sigs=sigs)
        json[keeper.algo] = keeper.params()

        if states is not None:
            json['smids'] = [state['i'] for state in states]

        if rstates is not None:
            json['rmids'] = [state['i'] for state in rstates]

        res = self.client.put(f"/identifiers/{name}", json=json)
        return serder, sigs, res.json()

    def addEndRole(self, name, *, role=Roles.agent, eid=None, stamp=None):
        hab = self.get(name)
        pre = hab["prefix"]

        rpy = self.makeEndRole(pre, role, eid, stamp)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=rpy.raw)
        json = dict(
            rpy=rpy.ked,
            sigs=sigs
        )

        res = self.client.post(f"/identifiers/{name}/endroles", json=json)
        return rpy, sigs, res.json()

    def sign(self, name, ser):
        hab = self.get(name)
        keeper = self.client.manager.get(aid=hab)
        sigs = keeper.sign(ser=ser.raw)

        return sigs

    def members(self, name):
        res = self.client.get(f"/identifiers/{name}/members")
        return res.json()

    @staticmethod
    def makeEndRole(pre, role=Roles.agent, eid=None, stamp=None):
        data = dict(cid=pre, role=role)
        if eid is not None:
            data['eid'] = eid

        route = "/end/role/add"
        return eventing.reply(route=route, data=data, stamp=stamp)
