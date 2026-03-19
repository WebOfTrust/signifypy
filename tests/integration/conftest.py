"""
Fixtures for live SignifyPy integration tests.
Includes:
- three witnesses
  - wan
  - wil
  - wes
- vLEI-server
- keria server

All run using Python's subprocess.Popen, custom HOME and temp dir per test run, and a context
manager for setup and teardown of all of this. Has decently good performance.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import textwrap
import time
from pathlib import Path

import pytest

# The following directories are used when running each command or library in an isolated virtualenv below
SIGNIFYPY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = SIGNIFYPY_ROOT.parent
KERIA_ROOT = SOURCE_ROOT / "keria"
VLEI_ROOT = SOURCE_ROOT / "vLEI"
SIGNIFYPY_PYTHON = SIGNIFYPY_ROOT / "venv" / "bin" / "python"
KERIA_PYTHON = KERIA_ROOT / "venv" / "bin" / "python"
VLEI_PYTHON = VLEI_ROOT / "venv" / "bin" / "python"

# KERIA and vLEI-server are started up locally, along with witnesses, by process scripts defined below,
# on the following URLs.
KERIA_ADMIN_URL = "http://127.0.0.1:3901"
KERIA_AGENT_URL = "http://127.0.0.1:3902"
KERIA_BOOT_URL = "http://127.0.0.1:3903"
VLEI_SCHEMA_URL = "http://127.0.0.1:7723"


# Keep the witness launcher inline so the fixture controls ports, temp storage,
# and teardown without depending on an external shell demo process.
WITNESS_SERVER_SCRIPT = textwrap.dedent(
    """
    import signal
    import falcon
    from hio.base import doing
    from keri import help
    from keri.app import habbing, indirecting, configing
    from keri.core import Salter

    CONFIG_DIR = {config_dir!r}
    WITNESSES = [
        ("wan", b"wann-the-witness", 5632, 5642),
        ("wil", b"will-the-witness", 5633, 5643),
        ("wes", b"wess-the-witness", 5634, 5644),
    ]

    help.ogler.level = 20
    # GitHub-hosted runners can reject listeners bound to all interfaces.
    # Force the witness demo topology onto loopback so the live harness matches
    # the 127.0.0.1 URLs the tests already use.
    _create_http_server = indirecting.createHttpServer
    def create_loopback_http_server(host, port, app, keypath=None, certpath=None, cafilepath=None):
        return _create_http_server("127.0.0.1", port, app, keypath, certpath, cafilepath)
    indirecting.createHttpServer = create_loopback_http_server

    class NoopQueryEnd:
        def __init__(self, hab):
            self.hab = hab

        def on_get(self, req, rep):
            raise falcon.HTTPNotFound(description="witness query endpoint disabled for this SignifyPy harness")

    # KERIpy 1.2.12 opens the same LMDB-backed Reger twice when setupWitness
    # constructs QueryEnd in-process on Linux. Phase 1 does not use the witness
    # /query endpoint, so replace it with a minimal no-op endpoint instead of
    # taking on a deeper local fork of the witness bootstrap logic.
    indirecting.QueryEnd = NoopQueryEnd

    doers = []
    for name, salt, tcp_port, http_port in WITNESSES:
        cf = configing.Configer(name=name, headDirPath=CONFIG_DIR, temp=True, reopen=True, clear=False)
        hby = habbing.Habery(name=name, salt=Salter(raw=salt).qb64, temp=True, cf=cf)
        # The current SignifyPy integration slice only needs witness HTTP
        # endpoints. Disabling the witness TCP listener keeps the harness off
        # all-interface socket paths that can fail on hosted runners without
        # patching deeper hio internals.
        doers.extend(indirecting.setupWitness(alias=name, hby=hby, tcpPort=None, httpPort=http_port))

    doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
    doist.doers = doers
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        doist.do()
    except KeyboardInterrupt:
        pass
    """
)

# Launch KERIA with the same demo topology the shell scripts expect, but under
# pytest-owned temp state so reruns stay isolated and cheap.
KERIA_SERVER_SCRIPT = textwrap.dedent(
    """
    import signal
    from keria.app import agenting

    config = agenting.KERIAServerConfig(
        name="keria",
        base="",
        adminPort=3901,
        httpPort=3902,
        bootPort=3903,
        configFile="demo-witness-oobis",
        configDir={config_dir!r},
        logLevel="INFO",
    )

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        agenting.runAgency(config=config, temp=True)
    except KeyboardInterrupt:
        pass
    """
)


VLEI_SERVER_SCRIPT = textwrap.dedent(
    """
    import signal
    from vlei.server import launch, VLEIConfig

    config = VLEIConfig(
        http=7723,
        schemaDir={schema_dir!r},
        credDir={cred_dir!r},
        oobiDir={oobi_dir!r},
        logLevel="INFO",
    )

    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        launch(config)
    except KeyboardInterrupt:
        pass
    """
)


def _require_python(path: Path, name: str) -> str:
    """Return the runtime path or skip when that repo-local interpreter is unavailable."""
    if not path.exists():
        pytest.skip(f"{name} runtime is unavailable at {path}")
    return str(path)


def _terminate_process(proc: subprocess.Popen[bytes], name: str) -> None:
    """Stop a spawned service process without leaving stray local daemons behind."""
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _read_log_tail(log_path: Path, *, max_chars: int = 8000) -> str:
    """
    Return the tail of a captured service log for startup-failure diagnostics.

    Subprocess output is redirected to files so logs can be inspected
    after pytest exits. When startup fails early we need to read those files
    directly; `proc.stdout` is `None` in that mode.
    """
    if not log_path.exists():
        return "(log file not found)"

    text = log_path.read_text(encoding="utf-8", errors="replace")
    return text[-max_chars:] if text else "(log file was empty)"


def _wait_for_port(
    host: str,
    port: int,
    proc: subprocess.Popen[bytes],
    name: str,
    *,
    log_path: Path,
    timeout: float = 45.0,
) -> None:
    """Wait for a service port or fail fast with that service's startup log tail."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"{name} exited early with code {proc.returncode}:\n"
                f"{_read_log_tail(log_path)}"
            )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.25)

    raise TimeoutError(
        f"timed out waiting for {name} on {host}:{port}:\n"
        f"{_read_log_tail(log_path)}"
    )


@pytest.fixture(scope="session")
def live_stack(tmp_path_factory: pytest.TempPathFactory):
    """
    Launch the local witness demo topology, KERIA, and vLEI schema server.

    The stack is session-scoped because service startup dominates runtime; once
    the ports are live, the individual smoke scenarios are comparatively cheap.

    Custom HOME dir isolation per test:
    each spawned service gets `HOME` pointed at the pytest temp runtime
    directory. That means any KERI fallback state that would normally land in
    `~/.keri` is isolated per test run instead. This keeps live integration
    tests reproducible, avoids mutating local personal KERI state, and
    removes the need for destructive cleanup between runs.
    """
    witness_python = _require_python(SIGNIFYPY_PYTHON, "SignifyPy")
    keria_python = _require_python(KERIA_PYTHON, "KERIA")
    vlei_python = _require_python(VLEI_PYTHON, "vLEI")
    runtime_root = tmp_path_factory.mktemp("signify_live_stack")
    config_root = runtime_root / "config"
    (config_root / "keri" / "cf").mkdir(parents=True, exist_ok=True)

    witness_config = {
        "dt": "2022-01-20T12:57:59.823350+00:00",
        "keria": {
            "dt": "2022-01-20T12:57:59.823350+00:00",
            "curls": ["http://127.0.0.1:3902/"],
        },
        "iurls": [
            "http://127.0.0.1:5642/oobi/BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha/controller?name=Wan&tag=witness",
            "http://127.0.0.1:5643/oobi/BLskRTInXnMxWaGqcpSyMgo0nYbalW99cGZESrz3zapM/controller?name=Wil&tag=witness",
            "http://127.0.0.1:5644/oobi/BIKKuvBwpmDVA4Ds-EpL5bt9OqPzWPja2LigFYZN2YfX/controller?name=Wes&tag=witness",
        ],
    }
    (config_root / "keri" / "cf" / "demo-witness-oobis.json").write_text(
        json.dumps(witness_config),
        encoding="utf-8",
    )

    shared_env = os.environ.copy()
    # Force every service's fallback `~/.keri` state into pytest temp space so
    # the harness does not depend on or mutate the developer's global KERI data.
    shared_env["HOME"] = str(runtime_root)

    witness_env = shared_env.copy()
    keria_env = os.environ.copy()
    keria_env["HOME"] = str(runtime_root)
    keria_env["PYTHONPATH"] = str(KERIA_ROOT / "src")

    vlei_env = shared_env.copy()
    vlei_env["PYTHONPATH"] = str(VLEI_ROOT / "src")

    procs: list[tuple[str, subprocess.Popen[bytes]]] = []
    # Persist service logs in the temp runtime directory so backend exceptions
    # can be inspected after pytest only surfaces a client-side HTTP failure.
    witness_log = (runtime_root / "witness.log").open("wb")
    keria_log = (runtime_root / "keria.log").open("wb")
    vlei_log = (runtime_root / "vlei.log").open("wb")

    try:
        witness = subprocess.Popen(
            [witness_python, "-u", "-c", WITNESS_SERVER_SCRIPT.format(config_dir=str(config_root))],
            cwd=SIGNIFYPY_ROOT,
            env=witness_env,
            stdout=witness_log,
            stderr=subprocess.STDOUT,
        )
        procs.append(("witness-demo", witness))
        _wait_for_port("127.0.0.1", 5642, witness, "witness-demo", log_path=runtime_root / "witness.log")
        _wait_for_port("127.0.0.1", 5643, witness, "witness-demo", log_path=runtime_root / "witness.log")
        _wait_for_port("127.0.0.1", 5644, witness, "witness-demo", log_path=runtime_root / "witness.log")

        keria = subprocess.Popen(
            [keria_python, "-u", "-c", KERIA_SERVER_SCRIPT.format(config_dir=str(config_root))],
            cwd=SIGNIFYPY_ROOT,
            env=keria_env,
            stdout=keria_log,
            stderr=subprocess.STDOUT,
        )
        procs.append(("keria", keria))
        _wait_for_port("127.0.0.1", 3901, keria, "keria", log_path=runtime_root / "keria.log")
        _wait_for_port("127.0.0.1", 3902, keria, "keria", log_path=runtime_root / "keria.log")
        _wait_for_port("127.0.0.1", 3903, keria, "keria", log_path=runtime_root / "keria.log")

        vlei = subprocess.Popen(
            [
                vlei_python,
                "-u",
                "-c",
                VLEI_SERVER_SCRIPT.format(
                    schema_dir=str(VLEI_ROOT / "schema" / "acdc"),
                    cred_dir=str(VLEI_ROOT / "samples" / "acdc"),
                    oobi_dir=str(VLEI_ROOT / "samples" / "oobis"),
                ),
            ],
            cwd=SIGNIFYPY_ROOT,
            env=vlei_env,
            stdout=vlei_log,
            stderr=subprocess.STDOUT,
        )
        procs.append(("vlei-server", vlei))
        _wait_for_port("127.0.0.1", 7723, vlei, "vlei-server", log_path=runtime_root / "vlei.log")

        yield {
            "keria_admin_url": KERIA_ADMIN_URL,
            "keria_agent_url": KERIA_AGENT_URL,
            "keria_boot_url": KERIA_BOOT_URL,
            "vlei_schema_url": VLEI_SCHEMA_URL,
            "runtime_root": runtime_root,
        }
    finally:
        for name, proc in reversed(procs):
            _terminate_process(proc, name)
        witness_log.close()
        keria_log.close()
        vlei_log.close()
