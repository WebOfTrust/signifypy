"""Launch the SignifyPy integration vLEI helper server."""

from __future__ import annotations

import argparse
import signal

from vlei.server import VLEIConfig, launch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-dir", required=True, help="vLEI schema directory")
    parser.add_argument("--cred-dir", required=True, help="vLEI sample credential directory")
    parser.add_argument("--oobi-dir", required=True, help="vLEI sample OOBI directory")
    parser.add_argument("--http-port", required=True, type=int, help="vLEI HTTP port")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = VLEIConfig(
        http=args.http_port,
        schemaDir=args.schema_dir,
        credDir=args.cred_dir,
        oobiDir=args.oobi_dir,
        logLevel="INFO",
    )

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        launch(config)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
