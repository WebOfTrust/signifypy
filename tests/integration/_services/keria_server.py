"""Launch the SignifyPy integration KERIA server."""

from __future__ import annotations

import argparse
from pathlib import Path
import signal

import falcon


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


class TestSignalsEnd:
    """Harness-only route for exercising KERIA's generic SSE signal channel."""

    def __init__(self, streaming):
        self.streaming = streaming

    def on_get(self, req, rep):
        agent = req.context.agent
        rep.status = falcon.HTTP_200
        rep.media = {"subscribers": len(agent.sseBroadcaster.subscribers)}

    def on_post(self, req, rep):
        agent = req.context.agent
        body = req.media or {}
        self.streaming.enqueueSignedReplyCue(
            agent.signalCues,
            event=body.get("event", "agent.signal.test"),
            route=body.get("route", "/test/signals/request"),
            payload=body.get("payload", {}),
            event_id=body.get("event_id", "test-signal"),
        )
        rep.status = falcon.HTTP_202
        rep.media = {"queued": True}


def install_test_signal_route(agenting):
    """Register an authenticated test-only signal trigger route on KERIA admin."""
    original_create_admin_server_doer = agenting.createAdminServerDoer

    def create_admin_server_doer(config, agency):
        admin_app, admin_server_doer = original_create_admin_server_doer(config, agency)
        from keria.app import streaming

        admin_app.add_route("/test/signals", TestSignalsEnd(streaming))
        return admin_app, admin_server_doer

    agenting.createAdminServerDoer = create_admin_server_doer


def main() -> None:
    args = parse_args()
    configure_temp_log_root(args.config_dir)
    from keria.app import agenting

    install_test_signal_route(agenting)

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
