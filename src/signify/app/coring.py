# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.coring module

"""
from signify.app.clienting import SignifyClient


class Operations:
    """ Domain class for accessing long running operations"""

    def __init__(self, client: SignifyClient):
        self.client = client

    def get(self, name):
        res = self.client.get(f"/operations/{name}")
        return res.json()


class Oobis:
    """ Domain class for accessing OOBIs"""

    def __init__(self, client: SignifyClient):
        self.client = client

    def get(self, name, role="agent"):
        res = self.client.get(f"/identifiers/{name}/oobis?role={role}")
        return res.json()

    def resolve(self, oobi, alias=None):

        json = dict(
            url=oobi
        )

        if alias is not None:
            json["oobialias"] = alias

        res = self.client.post("/oobis", json=json)
        return res.json()


class KeyStates:
    """ Domain class for accessing KeyStates"""

    def __init__(self, client: SignifyClient):
        self.client = client

    def get(self, pre):
        res = self.client.get(f"/states?pre={pre}")
        return res.json()

    def list(self, pres):
        args = "&".join([f"pre={pre}" for pre in pres])
        res = self.client.get(f"/states?{args}")
        return res.json()

    def query(self, pre, sn=None, anchor=None):
        json = dict(
            pre=pre
        )

        if sn is not None:
            json["sn"] = sn

        if anchor is not None:
            json["anchor"] = anchor

        res = self.client.post(f"/queries", json=json)
        return res.json()


class KeyEvents:
    """ Domain class for accessing KeyEvents"""

    def __init__(self, client: SignifyClient):
        self.client = client

    def get(self, pre):
        res = self.client.get(f"/events?pre={pre}")
        return res.json()



