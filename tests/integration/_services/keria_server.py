"""Launch the SignifyPy integration KERIA server."""

from __future__ import annotations

import argparse
import signal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", required=True, help="runtime config root")
    parser.add_argument("--admin-port", required=True, type=int, help="KERIA admin port")
    parser.add_argument("--http-port", required=True, type=int, help="KERIA agent HTTP port")
    parser.add_argument("--boot-port", required=True, type=int, help="KERIA boot port")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    from keria.app import agenting

    config = agenting.KERIAServerConfig(
        name="keria",
        base="",
        adminPort=args.admin_port,
        httpPort=args.http_port,
        bootPort=args.boot_port,
        configFile="demo-witness-oobis",
        configDir=args.config_dir,
        logLevel="INFO",
    )

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        agenting.runAgency(config=config, temp=False)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
