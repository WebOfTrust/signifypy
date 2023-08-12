# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.ending module

"""
from signify.app.clienting import SignifyClient


class EndRoleAuthorizations:
    """ Domain class for accessing Endpoint Role Authorizations """

    def __init__(self, client: SignifyClient):
        self.client = client

    def list(self, name=None, aid=None, role=None):
        if name is not None:
            path = f"/identifiers/{name}/endroles"
        elif aid is not None:
            path = f"/endroles/{aid}"
        else:
            raise ValueError("either `aid` or `name` is required")

        if role is not None:
            path = path + f"/{role}"

        res = self.client.get(path)
        return res.json()

