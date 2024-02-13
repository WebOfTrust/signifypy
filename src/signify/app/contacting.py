# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.contacting module

"""
from signify.app.clienting import SignifyClient


class Contacts:
    """ Domain class for accessing Endpoint Role Authorizations """

    def __init__(self, client: SignifyClient):
        self.client = client

    def list(self, start=0, end=24):
        """ Returns list of notifications

        Parameters:
            start (int): start index of list of notifications, defaults to 0
            end (int): end index of list of notifications, defaults to 24

        Returns:
            dict: data with start, end, total and notes of list result

        """
        headers = dict(Range=f"contacts={start}-{end}")
        res = self.client.get(f"/contacts", headers=headers)
        # cr = res.headers["content-range"]
        # start, end, total = httping.parseRangeHeader(cr, "notes")

        contacts = res.json()
        return dict(start=0, end=len(contacts), total=len(contacts), contacts=contacts)

