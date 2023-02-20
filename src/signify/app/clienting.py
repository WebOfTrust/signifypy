# -*- encoding: utf-8 -*-
"""
KERI
signify.app.clienting module

"""
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin

import requests
from keri import kering
from keri.help import helping
from requests.auth import AuthBase

from signify.core.authing import Authenticater, Controller, Agent


@dataclass
class State:
    kel: dict = None
    ridx: int = None


class SignifyClient:

    def __init__(self, url, bran, tier, temp):

        self.base = url
        self.bran = bran
        self.tier = tier
        self.temp = temp

        self.session = None
        self.ctrl = None
        self.agent = None
        self.authn = None

        up = urlparse(self.base)
        if up.scheme not in kering.Schemes:
            raise ValueError(f"invalid scheme {up.scheme} for SignifyClient")

    def connect(self):

        self.session = requests.Session()
        state = self.state()
        print(state)
        ridx = state.ridx if state.ridx is not None else 0

        # Create controller representing local auth AID
        self.ctrl = Controller(bran=self.bran, tier=self.tier, temp=self.temp, ridx=ridx)

        # Create agent representing the AID of the cloud agent
        self.agent = Agent(kel=state.kel)

        if self.agent.anchor != self.ctrl.pre:
            raise kering.ConfigurationError("commitment to controller AID missing in agent inception event")

        self.authn = Authenticater(agent=self.agent, ctrl=self.ctrl)
        self.session.auth = SignifyAuth(self.authn)

        if state.ridx is None:
            self.boot()

    def state(self):
        res = self.session.get(url=urljoin(self.base, "/boot"))
        data = res.json()
        state = State()
        state.kel = data["kel"]
        state.ridx = data["ridx"] if "ridx" in data else None

        return state

    def boot(self):
        evt, siger = self.ctrl.event()
        res = self.session.post(url=urljoin(self.base, "/boot"),
                                json=dict(
                                    icp=evt.ked,
                                    sig=siger.qb64,
                                    path=self.ctrl.path,
                                    npath=self.ctrl.npath,
                                    tier=self.ctrl.tier,
                                    temp=self.ctrl.temp))

        if res.status_code != requests.codes.accepted:
            raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}")


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

        req.headers = self.authn.sign(headers, req.method, req.path_url)
        return req
