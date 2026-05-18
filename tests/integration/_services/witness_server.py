"""Launch the SignifyPy integration witness-demo topology."""

from __future__ import annotations

import argparse
import signal

import falcon
from hio.base import doing
from keri import help
from keri.app import configing, habbing, indirecting
from keri.core import Salter

WITNESSES = (
    ("wan", b"wann-the-witness"),
    ("wil", b"will-the-witness"),
    ("wes", b"wess-the-witness"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", required=True, help="runtime config root")
    parser.add_argument("--wan-port", required=True, type=int, help="wan witness HTTP port")
    parser.add_argument("--wil-port", required=True, type=int, help="wil witness HTTP port")
    parser.add_argument("--wes-port", required=True, type=int, help="wes witness HTTP port")
    return parser.parse_args()


def install_harness_patches() -> None:
    # GitHub-hosted runners can reject listeners bound to all interfaces.
    # Force the witness demo topology onto loopback so the live harness matches
    # the 127.0.0.1 URLs the tests already use.
    original_create_http_server = indirecting.createHttpServer

    def create_loopback_http_server(
        host,
        port,
        app,
        keypath=None,
        certpath=None,
        cafilepath=None,
    ):
        return original_create_http_server("127.0.0.1", port, app, keypath, certpath, cafilepath)

    indirecting.createHttpServer = create_loopback_http_server

    class NoopQueryEnd:
        def __init__(self, hab, **_kwa):
            self.hab = hab

        def on_get(self, req, rep):
            raise falcon.HTTPNotFound(
                description="witness query endpoint disabled for this SignifyPy harness"
            )

    # KERIpy 1.2.12 opens the same LMDB-backed Reger twice when setupWitness
    # constructs QueryEnd in-process on Linux. Phase 1 does not use the witness
    # /query endpoint, so replace it with a minimal no-op endpoint instead of
    # taking on a deeper local fork of the witness bootstrap logic.
    indirecting.QueryEnd = NoopQueryEnd


def main() -> None:
    args = parse_args()
    witness_ports = {
        "wan": args.wan_port,
        "wil": args.wil_port,
        "wes": args.wes_port,
    }

    help.ogler.level = 20
    install_harness_patches()

    doers = []
    for name, salt in WITNESSES:
        cf = configing.Configer(
            name=name,
            headDirPath=args.config_dir,
            temp=False,
            reopen=True,
            clear=False,
        )
        hby = habbing.Habery(
            name=name,
            salt=Salter(raw=salt).qb64,
            temp=False,
            cf=cf,
            headDirPath=args.config_dir,
        )
        # The current SignifyPy integration slice only needs witness HTTP
        # endpoints. Disabling the witness TCP listener keeps the harness off
        # all-interface socket paths that can fail on hosted runners without
        # patching deeper hio internals.
        doers.extend(
            indirecting.setupWitness(
                alias=name,
                hby=hby,
                tcpPort=None,
                httpPort=witness_ports[name],
            )
        )

    doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
    doist.doers = doers
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        doist.do()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
