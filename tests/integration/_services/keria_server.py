"""Launch the SignifyPy integration KERIA server."""

from __future__ import annotations

import argparse
from pathlib import Path
import signal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", required=True, help="runtime config root")
    parser.add_argument("--admin-port", required=True, type=int, help="KERIA admin port")
    parser.add_argument("--http-port", required=True, type=int, help="KERIA agent HTTP port")
    parser.add_argument("--boot-port", required=True, type=int, help="KERIA boot port")
    return parser.parse_args()


def configure_temp_log_root(config_dir: str) -> None:
    """Point KERIA temp logging at this stack's runtime root before import."""
    from hio.help import ogling

    runtime_root = Path(config_dir).resolve().parent
    temp_head_dir = runtime_root / "keria-tmp"
    temp_head_dir.mkdir(parents=True, exist_ok=True)
    ogling.Ogler.TempHeadDir = str(temp_head_dir)


def main() -> None:
    args = parse_args()
    configure_temp_log_root(args.config_dir)
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
