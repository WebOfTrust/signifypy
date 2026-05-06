# -*- encoding: utf-8 -*-
"""Client bootstrap, transport, and resource access for SignifyPy.

``SignifyClient`` owns the controller-to-agent relationship with KERIA. It
boots and connects the remote agent, restores local controller state, signs
HTTP requests, and exposes the resource wrappers that implement the maintained
request families documented in the feature guide.
"""
from dataclasses import asdict
from urllib.parse import quote, urlparse, urljoin, urlsplit

import requests
import sseclient
from keri import kering
from keri.core.coring import Tiers
from keri.end import ending
from keri.help import helping
from requests import HTTPError
from requests.auth import AuthBase
from requests.structures import CaseInsensitiveDict

from signify.core import keeping, authing, api
from signify.signifying import SignifyState


class SignifyClient:
    """Edge-signing client bound to one controller AID and delegated agent."""

    ExternalRequestFields = ["@method", "@path", "Signify-Resource", "Signify-Timestamp"]

    def __init__(self, passcode, url=None, boot_url=None, tier=Tiers.low, extern_modules=None):
        """
        Create a new SignifyClient. Connects to the KERIA instance and delegates from the local
        Signify Client AID (caid) to the KERIA Agent AID with a delegated inception event.
        The delegation is then approved by the Client AID with an interaction event.

        Uses the following derivation path prefixes to generate signing and rotation keys for the Client AID:
        - "signify:controller00" for signing keys
        - "signify:controller01" for rotation keys

        Parameters:
            passcode (str | bytes): 21 character passphrase for the local controller
            url (str): Boot interface URL of the KERIA instance to connect to
            boot_url (str): Boot interface URL of the KERIA instance to connect to for initial boot
            tier (Tiers): tier of the controller (low, med, high)
            extern_modules (dict): external key management modules such as for Google KMS, Trezor, etc.

        Attributes:
            bran (str | bytes): 21 character passphrase for the local controller (passcode)
            pidx (int): prefix index for this keypair sequence
            tier (Tiers): tier of the controller (low, med, high)
            extern_modules (dict): external key management modules such as for Google KMS, Trezor, etc.
            mgr (Manager): key manager for the controller; performs signing and rotation
            session (requests.Session): HTTP session for the client
            agent (Agent): Agent representing the KERIA Agent AID
            authn (Authenticater): Authenticater for the client
            base (str): Boot interface URL of the KERIA instance to connect to
            ctrl (Controller): Controller representing the local controller AID
        """

        if len(passcode) < 21:
            raise kering.ConfigurationError(f"bran of length {len(passcode)} is too short, must be 21 characters")

        self.bran = passcode
        self.pidx = 0
        self.tier = tier
        self.extern_modules = extern_modules

        self.mgr = None
        self.session = None
        self.agent = None
        self.authn = None
        self.base = None
        self._booted_agent = None

        self.ctrl = authing.Controller(bran=self.bran, tier=self.tier)
        self.url = url
        self.boot_url = boot_url

    def _cache_booted_agent(self, state):
        """Cache the agent state returned by ``/boot`` for first-connect checks."""
        try:
            self._booted_agent = authing.Agent(state=state)
        except (KeyError, kering.ValidationError) as ex:
            raise kering.AuthNError(f"invalid agent state from boot response: {ex}") from ex

    def _require_booted_agent_match(self):
        """Ensure first-connect approval targets the agent returned by ``/boot``."""
        if self._booted_agent is None:
            return

        if self.agent.pre != self._booted_agent.pre or self.agent.said != self._booted_agent.said:
            raise kering.ConfigurationError("booted agent does not match connected agent state")

    def boot(self) -> dict:
        """Create the remote cloud agent delegated to this controller AID."""
        evt, siger = self.ctrl.event()
        agent_boot = api.AgentBoot(
            icp=evt.ked,
            sig=siger.qb64,
            stem=self.ctrl.stem,
            pidx=1,
            tier=self.ctrl.tier
        )
        res = requests.post(url=f"{self.boot_url}/boot", json=asdict(agent_boot))
        if res.status_code != requests.codes.accepted:
            raise kering.AuthNError(f"unable to initialize cloud agent connection, {res.status_code}, {res.text}")
        try:
            body = res.json()
        except requests.exceptions.JSONDecodeError as ex:
            raise kering.AuthNError(f"invalid response from server: {ex}") from ex
        self._cache_booted_agent(body)
        return body

    def connect(self, url=None):
        """Connect to KERIA, restore state, and finish first-connect delegation.

        On initial connection this method also approves the controller-to-agent
        delegation before installing the authenticated request hooks used by all
        later resource calls.
        """
        url = self.url if url is None else url
        up = urlparse(url)
        if up.scheme not in kering.Schemes:
            raise kering.ConfigurationError(f"invalid scheme {up.scheme} for SignifyClient")

        self.base = url

        self.session = requests.Session()
        state = self.states()
        self.pidx = state.pidx

        # Create agent representing the AID of the cloud agent
        self.agent = authing.Agent(state=state.agent)

        # Create controller representing local auth AID
        self.ctrl = authing.Controller(bran=self.bran, tier=self.tier, state=state.controller)
        self.mgr = keeping.Manager(salter=self.ctrl.salter, extern_modules=self.extern_modules)

        if self.agent.delpre != self.ctrl.pre:
            raise kering.ConfigurationError("commitment to controller AID missing in agent inception event")

        if self.ctrl.serder.sn == 0:
            self._require_booted_agent_match()
            self.approveDelegation()
            self._booted_agent = None

        self.authn = authing.Authenticater(agent=self.agent, ctrl=self.ctrl)
        self.session.auth = SignifyAuth(self.authn)
        self.session.hooks = dict(response=self.authn.verify)

    def approveDelegation(self):
        """Approve the controller-to-agent delegation with a signed ixn event."""
        serder, sigs = self.ctrl.approveDelegation(self.agent)
        data = dict(ixn=serder.ked, sigs=sigs)
        self.put(path=f"/agent/{self.controller}?type=ixn", json=data)

    def rotate(self, nbran, aids):
        """Rotate the controller commitment and persist the new agent binding."""
        data = self.ctrl.rotate(nbran=nbran, aids=aids)
        self.put(path=f"/agent/{self.controller}", json=data)

    @property
    def controller(self):
        """Return the controller AID prefix."""
        return self.ctrl.pre

    @property
    def icp(self):
        """Return the controller inception serder."""
        return self.ctrl.serder

    @property
    def salter(self):
        """Return the controller salter used by the local key manager."""
        return self.ctrl.salter

    @property
    def manager(self):
        """Return the active local key manager."""
        return self.mgr

    def states(self):
        """Fetch the current controller/agent state bundle from KERIA."""
        caid = self.ctrl.pre
        res = self.session.get(url=urljoin(self.base, f"/agent/{caid}"))
        if res.status_code == 404:
            raise kering.ConfigurationError(f"agent does not exist for controller {caid}")

        data = res.json()
        state = SignifyState()
        state.controller = data["controller"]
        state.agent = data["agent"]
        state.pidx = data["pidx"] if "pidx" in data else 0

        return state

    def state(self):
        """Compatibility wrapper returning the current controller/agent state bundle."""
        return self.states()

    def _save_old_salt(self, salt):
        """Persist the previous controller salt during passcode rotation flows."""
        caid = self.ctrl.pre
        body = dict(salt=salt)
        res = self.put(f"/salt/{caid}", json=body)
        return res.status_code == 204

    def saveOldPasscode(self, passcode):
        """Persist a prior controller passcode during passcode rotation."""
        return self._save_old_salt(passcode)

    def _delete_old_salt(self):
        """Delete the previously persisted controller salt after rotation."""
        caid = self.ctrl.pre
        res = self.delete(f"/salt/{caid}")
        return res.status_code == 204

    def deletePasscode(self):
        """Delete any previously persisted controller passcode backup."""
        return self._delete_old_salt()

    def _request_kwargs(self, *, params=None, headers=None, json=None):
        """Build ``requests`` kwargs for an authenticated relative request."""
        kwargs = dict()
        if params is not None:
            kwargs["params"] = params

        if headers is not None:
            kwargs["headers"] = headers

        if json is not None:
            kwargs["json"] = json

        return kwargs

    def _request(self, method, path, *, params=None, headers=None, json=None):
        """Issue an authenticated HTTP request relative to the client base URL."""
        url = urljoin(self.base, path)
        kwargs = self._request_kwargs(params=params, headers=headers, json=json)

        requester = getattr(self.session, method.lower(), None)
        if requester is None:
            res = self.session.request(method=method, url=url, **kwargs)
        else:
            res = requester(url, **kwargs)

        if not res.ok:
            self.raiseForStatus(res)

        return res

    @staticmethod
    def _signature_path(url):
        """Return the path component used when signing an external request URL."""
        path = urlsplit(url).path
        return path if path else "/"

    @staticmethod
    def _signature_headers_for_signer(headers, method, path, signer):
        """Attach Signify signature headers using one explicit signer."""
        signed_headers = CaseInsensitiveDict(headers)
        header, qsig = ending.siginput(
            "signify",
            method,
            path,
            signed_headers,
            fields=SignifyClient.ExternalRequestFields,
            signers=[signer],
            alg="ed25519",
            keyid=signer.verfer.qb64,
        )
        for key, val in header.items():
            signed_headers[key] = val

        signage = ending.Signage(
            markers=dict(signify=qsig),
            indexed=False,
            signer=None,
            ordinal=None,
            digest=None,
            kind=None,
        )
        for key, val in ending.signature([signage]).items():
            signed_headers[key] = val

        return signed_headers

    def get(self, path, params=None, headers=None, body=None):
        """Issue an authenticated ``GET`` request relative to the client base URL."""
        return self._request("GET", path, params=params, headers=headers, json=body)

    def fetch(self, path, method, data, headers=None):
        """Compatibility wrapper for a unified signed request entrypoint."""
        method = method.upper()
        payload = None if method == "GET" else data
        return self._request(method, path, headers=headers, json=payload)

    def createSignedRequest(self, name, url, req=None):
        """Build a ``PreparedRequest`` signed by the named managed identifier."""
        if self.manager is None:
            raise kering.ConfigurationError("client must be connected before signing external requests")

        req = {} if req is None else dict(req)
        method = req.get("method", "GET").upper()
        headers = CaseInsensitiveDict(req.get("headers") or {})

        hab = self.identifiers().get(name)
        keeper = self.manager.get(aid=hab)
        signer = keeper.signers()[0]

        headers["Signify-Resource"] = hab["prefix"]
        headers["Signify-Timestamp"] = helping.nowIso8601()
        headers = self._signature_headers_for_signer(
            headers=headers,
            method=method,
            path=self._signature_path(url),
            signer=signer,
        )

        body = req.get("data", req.get("body"))
        json_body = req.get("json")
        if body is not None and json_body is not None:
            raise ValueError("req cannot contain both 'body'/'data' and 'json'")

        request = requests.Request(
            method=method,
            url=url,
            headers=dict(headers),
            params=req.get("params"),
            data=body,
            json=json_body,
        )
        return request.prepare()

    def stream(self, path, params=None, headers=None, body=None):
        """Open a server-sent-event stream against an authenticated endpoint."""
        url = urljoin(self.base, path)
        kwargs = self._request_kwargs(params=params, headers=headers, json=body)

        client = sseclient.SSEClient(url, session=self.session, **kwargs)
        for event in client:
            yield event

    def delete(self, path, params=None, headers=None, body=None):
        """Issue an authenticated ``DELETE`` request relative to the client base URL."""
        return self._request("DELETE", path, params=params, headers=headers, json=body)

    def post(self, path, json, params=None, headers=None):
        """Issue an authenticated ``POST`` request relative to the client base URL."""
        return self._request("POST", path, params=params, headers=headers, json=json)

    def put(self, path, json, params=None, headers=None):
        """Issue an authenticated ``PUT`` request relative to the client base URL."""
        return self._request("PUT", path, params=params, headers=headers, json=json)

    def identifiers(self):
        """Return the identifier lifecycle resource wrapper."""
        from signify.app.aiding import Identifiers
        return Identifiers(client=self)

    def operations(self):
        """Return the long-running operation polling resource wrapper."""
        from signify.app.coring import Operations
        return Operations(client=self)

    def oobis(self):
        """Return the OOBI resolution and retrieval resource wrapper."""
        from signify.app.coring import Oobis
        return Oobis(client=self)

    def credentials(self):
        """Return the credential query and issuance resource wrapper."""
        from signify.app.credentialing import Credentials
        return Credentials(client=self)

    def keyStates(self):
        """Return the key-state read and query resource wrapper."""
        from signify.app.coring import KeyStates
        return KeyStates(client=self)

    def keyEvents(self):
        """Return the key-event read resource wrapper."""
        from signify.app.coring import KeyEvents
        return KeyEvents(client=self)

    def escrows(self):
        """Return the escrow inspection resource wrapper."""
        from signify.app.escrowing import Escrows
        return Escrows(client=self)

    def endroles(self):
        """Return the endpoint-role authorization read resource wrapper."""
        from signify.app.ending import EndRoleAuthorizations
        return EndRoleAuthorizations(client=self)

    def notifications(self):
        """Return the notifications resource wrapper."""
        from signify.app.notifying import Notifications
        return Notifications(client=self)

    def groups(self):
        """Return the multisig group coordination resource wrapper."""
        from signify.app.grouping import Groups
        return Groups(client=self)

    def delegations(self):
        """Return the delegation resource for delegated-identifier approval."""
        from signify.app.delegating import Delegations
        return Delegations(client=self)

    def registries(self):
        """Return the credential-registry lifecycle resource wrapper."""
        from signify.app.credentialing import Registries
        return Registries(client=self)

    def schemas(self):
        """Return the schema read resource wrapper."""
        from signify.app.schemas import Schemas
        return Schemas(client=self)

    def config(self):
        """Return the agent-configuration read resource wrapper."""
        from signify.app.coring import Config
        return Config(client=self)

    def exchanges(self):
        """Return the exchange transport resource wrapper."""
        from signify.app.exchanging import Exchanges
        return Exchanges(client=self)

    def ipex(self):
        """Return the IPEX grant/admit resource wrapper."""
        from signify.app.credentialing import Ipex
        return Ipex(client=self)

    def challenges(self):
        """Return the challenge generation and verification resource wrapper."""
        from signify.app.challenging import Challenges
        return Challenges(client=self)

    def contacts(self):
        """Return the contact read resource wrapper."""
        from signify.app.contacting import Contacts
        return Contacts(client=self)

    @staticmethod
    def raiseForStatus(res):
        """Raise ``HTTPError`` with the best server-provided reason text."""
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
    """Requests auth adapter that signs outbound Signify HTTP requests."""

    def __init__(self, authn):
        """Create an auth adapter around a Signify ``Authenticater``."""

        self.authn = authn

    def __call__(self, req):
        """Attach Signify headers and signatures to a prepared HTTP request."""
        headers = req.headers
        headers['Signify-Resource'] = self.authn.ctrl.pre
        headers['Signify-Timestamp'] = helping.nowIso8601()

        if "Content-Length" not in headers and req.body:
            headers["Content-Length"] = len(req.body)

        p = urlsplit(req.url)
        path = p.path if p.path else "/"
        req.headers = self.authn.sign(headers, req.method, quote(path))
        return req
