# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.escrowing module

"""
from signify.app.clienting import SignifyClient


class Escrows:
    """ Domain class for accessing event escrows in your Agent """

    def __init__(self, client: SignifyClient):
        self.client = client

    def getEscrowReply(self, route=None):
        params = {}
        if route is not None:
            params['route'] = route

        res = self.client.get(f"/escrows/rpy", params=params)
        return res.json()
