# -*- encoding: utf-8 -*-
"""Contact lookup helpers for SignifyPy."""
from signify.app.clienting import SignifyClient


class Contacts:
    """Resource wrapper for listing and managing resolved contact records."""

    def __init__(self, client: SignifyClient):
        """Create a contact resource bound to one Signify client."""
        self.client = client

    def list(self, group=None, filter_field=None, filter_value=None, *, start=None, end=None):
        """List contacts using either the TS-style query contract or the legacy range form.

        Parameters:
            group (str | None): Optional group name used by KERIA to bucket
                contact results.
            filter_field (str | None): Optional field name to filter by.
            filter_value (str | None): Optional field value to filter by.
            start (int | None): Legacy range-list start offset.
            end (int | None): Legacy range-list end offset.

        Returns:
            list | dict: Raw contact JSON for the TS-style path, or the legacy
            wrapped range payload when ``start`` or ``end`` is used.
        """
        if start is not None or end is not None:
            start = 0 if start is None else start
            end = 24 if end is None else end
            headers = dict(Range=f"contacts={start}-{end}")
            res = self.client.get("/contacts", headers=headers)
            contacts = res.json()
            return dict(start=0, end=len(contacts), total=len(contacts), contacts=contacts)

        params = {}
        if group is not None:
            params["group"] = group
        if filter_field is not None:
            params["filter_field"] = filter_field
        if filter_value is not None:
            params["filter_value"] = filter_value

        res = self.client.get("/contacts", params=params or None)
        return res.json()

    def get(self, pre):
        """Fetch one contact by remote identifier prefix."""
        res = self.client.get(f"/contacts/{pre}")
        return res.json()

    def add(self, pre, info):
        """Create contact metadata for one already-known remote identifier."""
        res = self.client.post(f"/contacts/{pre}", json=info)
        return res.json()

    def update(self, pre, info):
        """Update contact metadata for one already-known remote identifier."""
        res = self.client.put(f"/contacts/{pre}", json=info)
        return res.json()

    def delete(self, pre):
        """Delete contact metadata for one remote identifier."""
        res = self.client.delete(f"/contacts/{pre}")
        return res.status_code in (200, 202, 204)
