# -*- encoding: utf-8 -*-
"""Supporting read and utility resources for SignifyPy.

This module groups smaller request families used across many workflows:
long-running operations, OOBI retrieval and resolution, key-state reads, and
key-event reads.
"""
import time

from signify.app.clienting import SignifyClient


class Operations:
    """Resource wrapper for reading and removing long-running KERIA operations."""

    def __init__(self, client: SignifyClient):
        """Create an operations resource bound to one Signify client."""
        self.client = client

    def get(self, name):
        """Fetch one long-running operation by operation name."""
        res = self.client.get(f"/operations/{name}")
        return res.json()

    def list(self, type=None):
        """List long-running operations, optionally filtered by operation type."""
        params = {}
        if type is not None:
            params["type"] = type

        res = self.client.get("/operations", params=params or None)
        return res.json()

    def delete(self, name):
        """Delete one long-running operation by operation name."""
        self.client.delete(f"/operations/{name}")

    def wait(
        self,
        op,
        *,
        timeout=None,
        interval=0.01,
        max_interval=10.0,
        backoff=2.0,
        check_abort=None,
        options=None,
        _deadline=None,
    ):
        """Poll an operation until it completes.

        Python callers should prefer the explicit keyword arguments:
        ``timeout`` in seconds, ``interval`` in seconds, ``max_interval`` in
        seconds, ``backoff`` as the exponential multiplier, and
        ``check_abort(current_op)`` for caller-controlled cancellation. The
        TS-style ``options`` dict remains supported as a compatibility path.
        """
        if options is not None:
            return self._wait_with_options(op, options=options)

        deadline = _deadline
        if deadline is None and timeout is not None:
            deadline = time.monotonic() + timeout

        depends = self._depends(op)
        if depends is not None and depends.get("done") is False:
            self.wait(
                depends,
                interval=interval,
                max_interval=max_interval,
                backoff=backoff,
                check_abort=check_abort,
                _deadline=deadline,
            )

        if op.get("done") is True:
            return op

        retries = 0

        while True:
            op = self.get(op["name"])

            if op.get("done") is True:
                return op

            self._raise_if_timed_out(deadline, op)
            self._check_abort(check_abort, op)

            delay = min(max_interval, interval * (backoff ** retries))
            retries += 1

            if deadline is not None:
                remaining = deadline - time.monotonic()
                self._raise_if_timed_out(deadline, op)
                delay = min(delay, remaining)

            time.sleep(delay)

    @staticmethod
    def _depends(op):
        """Return the dependent operation payload when present."""
        metadata = op.get("metadata")
        if isinstance(metadata, dict):
            depends = metadata.get("depends")
            if isinstance(depends, dict):
                return depends

        depends = op.get("depends")
        if isinstance(depends, dict):
            return depends

        return None

    @staticmethod
    def _throw_if_aborted(signal):
        """Raise the caller-provided abort signal when it has fired."""
        if signal is None:
            return

        if callable(signal):
            signal()
            return

        if hasattr(signal, "throw_if_aborted"):
            signal.throw_if_aborted()
            return

        if hasattr(signal, "throwIfAborted"):
            signal.throwIfAborted()

    @staticmethod
    def _check_abort(check_abort, op):
        """Run an optional caller-provided cancellation hook."""
        if check_abort is not None:
            check_abort(op)

    @staticmethod
    def _raise_if_timed_out(deadline, op):
        """Raise ``TimeoutError`` when the wait deadline has expired."""
        if deadline is not None and time.monotonic() >= deadline:
            raise TimeoutError(
                f"timed out waiting for operation {op['name']}; last_value={op!r}"
            )

    def _wait_with_options(self, op, *, options):
        """Compatibility wrapper for the TS-style wait options dictionary."""
        options = {} if options is None else options
        signal = options.get("signal")
        min_sleep = options.get("minSleep", 10)
        max_sleep = options.get("maxSleep", 10000)
        increase_factor = options.get("increaseFactor", 50)

        depends = self._depends(op)
        if depends is not None and depends.get("done") is False:
            self._wait_with_options(depends, options=options)

        if op.get("done") is True:
            return op

        retries = 0

        while True:
            op = self.get(op["name"])

            if hasattr(signal, "current_op"):
                signal.current_op = op

            delay = max(
                min_sleep,
                min(max_sleep, 2 ** retries * increase_factor),
            )
            retries += 1

            if op.get("done") is True:
                return op

            time.sleep(delay / 1000)
            self._throw_if_aborted(signal)


class Oobis:
    """Resource wrapper for OOBI retrieval and resolution."""

    def __init__(self, client: SignifyClient):
        """Create an OOBI resource bound to one Signify client."""
        self.client = client

    def get(self, name, role="agent"):
        """Return role-specific OOBIs published for one identifier alias."""
        res = self.client.get(f"/identifiers/{name}/oobis?role={role}")
        return res.json()

    def resolve(self, oobi, alias=None):
        """Submit an OOBI for resolution, optionally storing it under an alias."""

        body = dict(
            url=oobi
        )

        if alias is not None:
            body["oobialias"] = alias

        res = self.client.post("/oobis", json=body)
        return res.json()


class KeyStates:
    """Resource wrapper for key-state reads and key-state queries."""

    def __init__(self, client: SignifyClient):
        """Create a key-state resource bound to one Signify client."""
        self.client = client

    def get(self, pre):
        """Fetch the current key state for one AID prefix."""
        res = self.client.get(f"/states?pre={pre}")
        return res.json()

    def list(self, pres):
        """Fetch key states for multiple prefixes in one request."""
        args = "&".join([f"pre={pre}" for pre in pres])
        res = self.client.get(f"/states?{args}")
        return res.json()

    def query(self, pre, sn=None, anchor=None):
        """Submit a key-state query with optional sequence or anchor hints."""
        body = dict(
            pre=pre
        )

        if sn is not None:
            body["sn"] = sn

        if anchor is not None:
            body["anchor"] = anchor

        res = self.client.post(f"/queries", json=body)
        return res.json()


class KeyEvents:
    """Resource wrapper for reading KERI events already known to the agent."""

    def __init__(self, client: SignifyClient):
        """Create a key-event resource bound to one Signify client."""
        self.client = client

    def get(self, pre):
        """Fetch KERI events for one AID prefix."""
        res = self.client.get(f"/events?pre={pre}")
        return res.json()
