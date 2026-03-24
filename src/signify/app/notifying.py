# -*- encoding: utf-8 -*-
"""Notification read and acknowledgement helpers for SignifyPy."""
from signify.app.clienting import SignifyClient
from signify.core import httping


class Notifications:
    """Resource wrapper for listing, marking, and deleting notifications."""

    def __init__(self, client: SignifyClient):
        """Create a notifications resource bound to one Signify client."""
        self.client = client

    def list(self, start=0, end=24):
        """List notifications visible to the current agent.

        Parameters:
            start (int): start index of list of notifications, defaults to 0
            end (int): end index of list of notifications, defaults to 24

        Returns:
            dict: Window metadata and the returned notification records.
        """
        headers = dict(Range=f"notes={start}-{end}")
        res = self.client.get(f"/notifications", headers=headers)
        cr = res.headers["content-range"]
        start, end, total = httping.parseRangeHeader(cr, "notes")

        return dict(start=start, end=end, total=total, notes=res.json())

    def mark(self, said):
        """Mark one notification as read using the TS-compatible name.

        Parameters:
            said (str): qb64 SAID of notification to mark as read

        Returns:
            bool: ``True`` when KERIA accepts the update request.
        """
        res = self.client.put(f"/notifications/{said}", json={})
        return res.status_code == 202

    def markAsRead(self, nid):
        """Compatibility alias for :meth:`mark`."""
        return self.mark(nid)

    def delete(self, nid):
        """Delete one notification.

        Parameters:
            nid(str): qb64 SAID of notification to delete

        Returns:
            bool: ``True`` when KERIA accepts the delete request.
        """
        res = self.client.delete(path=f"/notifications/{nid}")
        return res.status_code == 202
