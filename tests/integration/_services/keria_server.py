"""Launch the SignifyPy integration KERIA server."""

from __future__ import annotations

import argparse
import signal

from keria.app import agenting


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", required=True, help="runtime config root")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = agenting.KERIAServerConfig(
        name="keria",
        base="",
        adminPort=3901,
        httpPort=3902,
        bootPort=3903,
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
