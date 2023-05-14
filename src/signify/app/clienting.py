# -*- encoding: utf-8 -*-
"""
KERI
signify.app.clienting module

"""
import importlib
import json
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin, urlsplit

import requests
from keri import kering
from keri.core.coring import Tiers
from keri.help import helping
from requests import HTTPError
from requests.auth import AuthBase

from signify.core import keeping
from signify.core.authing import Authenticater, Controller, Agent


@dataclass
class State:
    controller: dict = None
    agent : dict = None
    ridx: int = None
    pidx: int = None


class SignifyClient:

    def __init__(self, passcode, url=None, tier=Tiers.low, extern_modules=None):

        if len(passcode) < 21:
            raise kering.ConfigurationError(f"bran of length {len(passcode)} is too short, must be 21 characters")

        self.bran = passcode
        self.pidx = 0
        self.tier = tier
        self.extern_modules = extern_modules

        self.ctrl = None
        self.mgr = None
        self.session = None
        self.agent = None
        self.authn = None
        self.base = None

        self.ctrl = Controller(bran=self.bran, tier=self.tier)
        if url is not None:
            self.connect(url)

    def connect(self, url):
        up = urlparse(url)
        if up.scheme not in kering.Schemes:
            raise kering.ConfigurationError(f"invalid scheme {up.scheme} for SignifyClient")

        self.base = url

        self.session = requests.Session()
        state = self.states()
        self.pidx = state.pidx

        # Create controller representing local auth AID
        self.ctrl = Controller(bran=self.bran, tier=self.tier, state=state.controller)
        self.mgr = keeping.Manager(salter=self.ctrl.salter, extern_modules=self.extern_modules)

        # Create agent representing the AID of the cloud agent
        self.agent = Agent(state=state.agent)

        if self.agent.delpre != self.ctrl.pre:
            raise kering.ConfigurationError("commitment to controller AID missing in agent inception event")

        self.authn = Authenticater(agent=self.agent, ctrl=self.ctrl)
        self.session.auth = SignifyAuth(self.authn)

    def rotate(self, nbran, aids):
        data = self.ctrl.rotate(nbran=nbran, aids=aids)
        self.put(path=f"/agent/{self.controller}", json=data)

    @property
    def controller(self):
        return self.ctrl.pre

    @property
    def icp(self):
        return self.ctrl.serder

    @property
    def salter(self):
        return self.ctrl.salter

    @property
    def manager(self):
        return self.mgr

    def states(self):
        caid = self.ctrl.pre
        res = self.session.get(url=urljoin(self.base, f"/agent/{caid}"))
        if res.status_code == 404:
            raise kering.ConfigurationError(f"agent does not exist for controller {caid}")

        data = res.json()
        state = State()
        state.controller = data["controller"]
        state.agent = data["agent"]
        state.pidx = data["pidx"] if "pidx" in data else 0

        return state

    def _save_old_salt(self, salt):
        caid = self.ctrl.pre
        body = dict(salt=salt)
        res = self.put(f"/salt/{caid}", json=body)
        return res.status_code == 204

    def _delete_old_salt(self):
        caid = self.ctrl.pre
        res = self.delete(f"/salt/{caid}")
        return res.status_code == 204

    def get(self, path, params=None, headers=None):
        url = urljoin(self.base, path)

        kwargs = dict()
        if params is not None:
            kwargs["params"] = params

        if headers is not None:
            kwargs["headers"] = headers

        res = self.session.get(url, **kwargs)
        if not res.ok:
            self.raiseForStatus(res)

        return res

    def delete(self, path, params=None, headers=None):
        url = urljoin(self.base, path)

        kwargs = dict()
        if params is not None:
            kwargs["params"] = params

        if headers is not None:
            kwargs["headers"] = headers

        res = self.session.delete(url, **kwargs)
        if not res.ok:
            self.raiseForStatus(res)

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
            self.raiseForStatus(res)

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
            self.raiseForStatus(res)

        return res

    def identifiers(self):
        from signify.app.aiding import Identifiers
        return Identifiers(client=self)

    def operations(self):
        from signify.app.coring import Operations
        return Operations(client=self)

    def oobis(self):
        from signify.app.coring import Oobis
        return Oobis(client=self)

    def groups(self):
        from signify.app.grouping import Groups
        return Groups(client=self)

    def keyStates(self):
        from signify.app.coring import KeyStates
        return KeyStates(client=self)

    def keyEvents(self):
        from signify.app.coring import KeyEvents
        return KeyEvents(client=self)

    @staticmethod
    def raiseForStatus(res):
        try:
            body = res.json()

            if "description" in body:
                reason = body["description"]
            elif "title" in body:
                reason = body["title"]
            else:
                reason = "Unknown"
        except Exception:
            reason = res.text

        http_error_msg = ""
        if 400 <= res.status_code < 500:
            http_error_msg = (
                f"{res.status_code} Client Error: {reason} for url: {res.url}"
            )

        elif 500 <= res.status_code < 600:
            http_error_msg = (
                f"{res.status_code} Server Error: {reason} for url: {res.url}"
            )
        raise HTTPError(http_error_msg, response=res)


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
