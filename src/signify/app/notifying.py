# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.notifying module

"""
from signify.app.clienting import SignifyClient
from signify.core import httping


class Notifications:
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
        headers = dict(Range=f"notes={start}-{end}")
        res = self.client.get(f"/notifications", headers=headers)
        cr = res.headers["content-range"]
        start, end, total = httping.parseRangeHeader(cr, "notes")

        return dict(start=start, end=end, total=total, notes=res.json())

    def markAsRead(self, nid):
        """ Mark notification as read

        Parameters:
            nid (str): qb64 SAID of notification to mark as read

        Returns:
            bool: True means notification marked as read

        """
        res = self.client.put(f"/notifications/{nid}", json={})
        return res.status_code == 202

    def delete(self, nid):
        """ Delete notification

        Parameters:
            nid(str): qb64 SAID of notification to delete

        Returns:
            bool: True means notification deleted

        """
        res = self.client.delete(path=f"/notifications/{nid}")
        return res.status_code == 202
