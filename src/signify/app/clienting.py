# -*- encoding: utf-8 -*-
"""
KERI
signify.app.clienting module

"""
from dataclasses import dataclass
from math import ceil
from urllib.parse import urlparse, urljoin, urlsplit, quote

import requests
from keri import kering
from keri.app.keeping import SaltyCreator
from keri.core import eventing
from keri.core.coring import Tiers, MtrDex, Salter, Diger, Tholder
from keri.help import helping
from keri.kering import Roles
from requests.auth import AuthBase

from signify.core.authing import Authenticater, Controller, Agent


@dataclass
class State:
    kel: dict = None
    ridx: int = None
    pidx: int = None


class SignifyClient:

    def __init__(self, url, bran, tier, temp):

        up = urlparse(url)
        if up.scheme not in kering.Schemes:
            raise kering.ConfigurationError(f"invalid scheme {up.scheme} for SignifyClient")

        self.base = url
        if len(bran) < 21:
            raise kering.ConfigurationError(f"bran of length {len(bran)} is too short, must be 21 characters")

        self.pidx = 0

        self.session = None
        self.agent = None
        self.authn = None
        self.ctrl = Controller(bran=bran, tier=tier, temp=temp)

    def connect(self):

        self.session = requests.Session()
        state = self.state()
        self.pidx = state.pidx
        ridx = state.ridx if state.ridx is not None else 0

        # Create controller representing local auth AID
        self.ctrl.ridx = ridx

        # Create agent representing the AID of the cloud agent
        self.agent = Agent(kel=state.kel)

        if self.agent.anchor != self.ctrl.pre:
            raise kering.ConfigurationError("commitment to controller AID missing in agent inception event")

        self.authn = Authenticater(agent=self.agent, ctrl=self.ctrl)
        self.session.auth = SignifyAuth(self.authn)

        if state.ridx is None:
            self.__boot__()

    @property
    def controller(self):
        return self.ctrl.pre

    @property
    def salter(self):
        return self.ctrl.salter

    def __boot__(self):
        evt, siger = self.ctrl.event()
        res = self.session.post(url=urljoin(self.base, "/boot"),
                                json=dict(
                                    icp=evt.ked,
                                    sig=siger.qb64,
                                    stem=self.ctrl.stem,
                                    pidx=1,
                                    tier=self.ctrl.tier,
                                    temp=self.ctrl.temp))

        if res.status_code != requests.codes.accepted:
            raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")

    def state(self):
        res = self.session.get(url=urljoin(self.base, "/boot"))
        data = res.json()
        state = State()
        state.kel = data["kel"]
        state.ridx = data["ridx"] if "ridx" in data else None
        state.pidx = data["pidx"] if "pidx" in data else 0

        return state

    def get(self, path, params=None, headers=None):
        url = urljoin(self.base, path)

        kwargs = dict()
        if params is not None:
            kwargs["params"] = params

        if headers is not None:
            kwargs["headers"] = headers

        res = self.session.get(url, **kwargs)
        if not res.ok:
            res.raise_for_status()

        return res

    def post(self, path, json, params=None, headers=None):
        url = urljoin(self.base, path)

        kwargs = dict(json=json)
        if params is not None:
            kwargs["params"] = params

        if headers is not None:
            kwargs["headers"] = headers

        res = self.session.post(url, **kwargs)
        if not res.ok:
            res.raise_for_status()

        return res

    def put(self, path, json, params=None, headers=None):
        url = urljoin(self.base, path)

        kwargs = dict(json=json)
        if params is not None:
            kwargs["params"] = params

        if headers is not None:
            kwargs["headers"] = headers

        res = self.session.put(url, **kwargs)
        if not res.ok:
            res.raise_for_status()

        return res

    def identifiers(self):
        return Identifiers(client=self)

    def operations(self):
        return Operations(client=self)

    def oobis(self):
        return Oobis(client=self)


class SignifyAuth(AuthBase):

    def __init__(self, authn):
        """

        Args:
            authn(Authenticater): Provides request signing for AuthBase
        """

        self.authn = authn

    def __call__(self, req):
        headers = req.headers
        headers['Signify-Resource'] = self.authn.ctrl.pre
        headers['Signify-Timestamp'] = helping.nowIso8601()

        if "Content-Length" not in headers and req.body:
            headers["Content-Length"] = len(req.body)

        p = urlsplit(req.url)
        path = p.path if p.path else "/"
        req.headers = self.authn.sign(headers, req.method, path)
        return req


class Identifiers:
    """ Domain class for accessing, creating and rotating KERI Autonomic IDentifiers (AIDs) """

    stem = "signify:aid"

    def __init__(self, client):
        self.client = client

    def list(self, **kwas):
        res = self.client.get("/identifiers")
        return res.json()

    def get(self, name):
        res = self.client.get(f"/identifiers/{name}")
        return res.json()

    def create(self, name, tier=Tiers.low, temp=False, transferable=True, code=MtrDex.Ed25519_Seed, count=1,
               ncount=1, isith="1", nsith="1", wits=None, toad="0", delpre=None, data=None):

        salter = self.client.salter
        creator = SaltyCreator(salt=salter.qb64, stem=self.stem, tier=tier)

        signers = creator.create(code=code, count=count, pidx=self.client.pidx, ridx=0, kidx=0,
                                 transferable=transferable, temp=temp)

        nsigners = creator.create(code=code, count=ncount, pidx=self.client.pidx, ridx=1, kidx=len(signers),
                                  transferable=transferable, temp=temp)

        keys = [signer.verfer.qb64 for signer in signers]
        ndigs = [Diger(ser=nsigner.verfer.qb64b).qb64 for nsigner in nsigners]

        wits = wits if wits is not None else []
        data = [data] if data is not None else []
        if delpre is not None:
            serder = eventing.delcept(delpre=delpre,
                                      keys=keys,
                                      isith=isith,
                                      nsith=nsith,
                                      ndigs=ndigs,
                                      code=MtrDex.Blake3_256,
                                      wits=wits,
                                      toad=toad,
                                      data=data)
        else:
            serder = eventing.incept(keys=keys,
                                     isith=isith,
                                     nsith=nsith,
                                     ndigs=ndigs,
                                     code=MtrDex.Blake3_256,
                                     wits=wits,
                                     toad=toad,
                                     data=data)

        sigs = [signer.sign(ser=serder.raw, index=idx).qb64 for idx, signer in enumerate(signers)]

        rpy = self.makeEndRole(serder.pre, eid=self.client.agent.pre)
        rsigs = [signer.sign(ser=rpy.raw, index=idx).qb64 for idx, signer in enumerate(signers)]

        json = dict(
            name=name,
            icp=serder.ked,
            sigs=sigs,
            rpy=rpy.ked,
            rsigs=rsigs,
            stem=self.stem,
            pidx=self.client.pidx,
            tier=tier,
            temp=temp)

        self.client.pidx = self.client.pidx + 1

        res = self.client.post("/identifiers", json=json)
        return res.json()

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
        salter = self.client.salter
        hab = self.get(name)
        pre = hab["prefix"]
        stem = hab["stem"]
        tier = hab["tier"]
        pidx = hab["pidx"]
        temp = hab["temp"]
        state = hab["state"]
        sn = int(state["s"], 16)
        dig = state["d"]
        count = len(state['k'])
        ridx = int(state["ee"]["s"], 16)

        data = data if isinstance(data, list) else [data]

        creator = SaltyCreator(salt=salter.qb64, stem=stem, tier=tier)
        signers = creator.create(count=count, pidx=pidx, ridx=ridx, kidx=count, temp=temp)

        serder = eventing.interact(pre, sn=sn + 1, data=data, dig=dig)
        sigs = [signer.sign(ser=serder.raw, index=idx).qb64 for idx, signer in enumerate(signers)]

        json = dict(
            ixn=serder.ked,
            sigs=sigs)

        res = self.client.put(f"/identifiers/{name}?type=ixn", json=json)
        return res.json()

    def rotate(self, name, *, isith=None, nsith=None, ncount=1, toad=None, cuts=None, adds=None,
               data=None):
        salter = self.client.salter

        hab = self.get(name)
        pre = hab["prefix"]
        stem = hab["stem"]
        tier = hab["tier"]
        pidx = hab["pidx"]
        temp = hab["temp"]
        state = hab["state"]
        count = len(state['k'])
        dig = state["d"]
        ridx = int(state["ee"]["s"], 16) + 1
        wits = state['b']
        sith = state["kt"]

        if isith is None:
            isith = sith  # use prior next sith as default
        if nsith is None:
            nsith = isith  # use new current as default

        if isith is None:  # compute default from newly rotated verfers above
            isith = f"{max(1, ceil(count / 2)):x}"
        if nsith is None:  # compute default from newly rotated digers above
            nsith = f"{max(0, ceil(ncount / 2)):x}"

        cst = Tholder(sith=isith).sith  # current signing threshold
        nst = Tholder(sith=nsith).sith  # next signing threshold

        creator = SaltyCreator(salt=salter.qb64, stem=stem, tier=tier)

        # Regenerate next keys to sign rotation event
        signers = creator.create(count=count, pidx=pidx, ridx=ridx, kidx=count, temp=temp)

        # Create new keys for next digests
        nsigners = creator.create(count=ncount, pidx=pidx, ridx=ridx + 1, kidx=ncount,
                                  temp=temp)

        keys = [signer.verfer.qb64 for signer in signers]
        ndigs = [Diger(ser=nsigner.verfer.qb64b).qb64 for nsigner in nsigners]

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
        sigs = [signer.sign(ser=serder.raw, index=idx).qb64 for idx, signer in enumerate(signers)]

        json = dict(
            rot=serder.ked,
            sigs=sigs,
            stem=stem,
            pidx=pidx,
            tier=tier,
            temp=temp)

        res = self.client.put(f"/identifiers/{name}", json=json)
        return res.json()

    @staticmethod
    def makeEndRole(pre, eid):
        data = dict(cid=pre, role=Roles.agent, eid=eid)
        route = "/end/role/add"
        return eventing.reply(route=route, data=data)


class Operations:
    """ Domain class for accessing long running operations"""

    def __init__(self, client):
        self.client = client

    def get(self, name):
        res = self.client.get(f"/operations/{name}")
        return res.json()


class Oobis:
    """ Domain class for accessing OOBIs"""

    def __init__(self, client):
        self.client = client

    def get(self, name):
        res = self.client.get(f"/identifiers/{name}/oobis")
        return res.json()

    def resolve(self, oobi, alias=None):

        json = dict(
            url=oobi
        )

        if alias is not None:
            json["oobialias"] = alias

        res = self.client.post("/oobis", json=json)
        return res.json()
