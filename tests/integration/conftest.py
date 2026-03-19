"""Live-stack fixtures for the SignifyPy integration layer.

This file is the harness entry point for every live integration scenario. It
starts a local witness-demo topology, KERIA, and the vLEI helper server inside
pytest-owned temp state so tests can exercise real SignifyPy workflows without
mutating a developer's global `~/.keri`.

The important maintainer constraint is that different services read config from
different `Configer` bases:

- witness demo configs are loaded from `.../keri/cf/main/...`
- KERIA agency config is loaded from `.../keri/cf/...`

If those paths drift, the stack can still appear to "start" while publishing
broken endpoint metadata, which later shows up as empty OOBIs or hanging
multistep workflows.
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

from tests.integration.constants import (
    KERIA_ADMIN_URL,
    KERIA_AGENT_URL,
    KERIA_BOOT_URL,
    VLEI_SCHEMA_URL,
    WITNESS_CONFIG_IURLS,
)

# The following directories are used when running each command or library in an isolated virtualenv below
SIGNIFYPY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = SIGNIFYPY_ROOT.parent
KERIPY_ROOT = SOURCE_ROOT / "keripy"
KERIA_ROOT = SOURCE_ROOT / "keria"
VLEI_ROOT = SOURCE_ROOT / "vLEI"
SIGNIFYPY_PYTHON = SIGNIFYPY_ROOT / "venv" / "bin" / "python"
KERIA_PYTHON = KERIA_ROOT / "venv" / "bin" / "python"
VLEI_PYTHON = VLEI_ROOT / "venv" / "bin" / "python"

KERIPY_WITNESS_CONFIG_DIR = KERIPY_ROOT / "scripts" / "keri" / "cf" / "main"
WITNESS_CONFIG_NAMES = ("wan", "wil", "wes")

# Keep the witness launcher inline so the fixture controls ports, isolated
# state, and teardown without depending on an external shell demo process.
# Important: this must mirror `kli witness demo` closely enough to preserve the
# canonical demo witness AIDs and load config from `.../keri/cf/main/...`.
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
        cf = configing.Configer(name=name, headDirPath=CONFIG_DIR, temp=False, reopen=True, clear=False)
        hby = habbing.Habery(
            name=name,
            salt=Salter(raw=salt).qb64,
            temp=False,
            cf=cf,
            headDirPath=CONFIG_DIR,
        )
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
        agenting.runAgency(config=config, temp=False)
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


def _write_canonical_witness_configs(config_root: Path) -> None:
    """Copy canonical witness-demo configs into the exact path witnesses read.

    Witness startup in the inline launcher uses `Configer(..., base="main")`,
    so these files have to live under `keri/cf/main`. Keeping the canonical
    `wan`/`wil`/`wes` files here preserves the SignifyTS witness AIDs and the
    corresponding witness OOBIs expected by the tests.
    """
    target_dir = config_root / "keri" / "cf" / "main"
    target_dir.mkdir(parents=True, exist_ok=True)

    for name in WITNESS_CONFIG_NAMES:
        source = KERIPY_WITNESS_CONFIG_DIR / f"{name}.json"
        if not source.exists():
            pytest.skip(f"canonical witness config is unavailable at {source}")
        (target_dir / f"{name}.json").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _write_keria_config(config_root: Path) -> None:
    """Write the KERIA harness config into the exact path `runAgency` reads.

    This is intentionally *not* the same path the witness configs use. KERIA's
    `readConfigFile` opens the config with `base=""`, so the agency config must
    live directly under `keri/cf`. If it lands under `keri/cf/main` instead,
    the process still boots but the agency config is effectively empty and
    per-agent configs are written without `curls`, which breaks agent OOBIs.
    """
    target_dir = config_root / "keri" / "cf"
    target_dir.mkdir(parents=True, exist_ok=True)

    witness_config = {
        "dt": "2022-01-20T12:57:59.823350+00:00",
        "keria": {
            "dt": "2022-01-20T12:57:59.823350+00:00",
            "curls": ["http://127.0.0.1:3902/"],
        },
        "iurls": WITNESS_CONFIG_IURLS,
    }
    (target_dir / "demo-witness-oobis.json").write_text(
        json.dumps(witness_config),
        encoding="utf-8",
    )


def _assert_config_readable(config_root: Path, name: str, *, required_keys: tuple[str, ...]) -> None:
    """Fail fast if a witness config is unreadable through the `base="main"` path."""
    from keri.app import configing

    cf = configing.Configer(
        name=name,
        base="main",
        headDirPath=str(config_root),
        temp=False,
        reopen=True,
        clear=False,
    )
    try:
        config = cf.get()
    finally:
        cf.close(clear=False)

    missing = [key for key in required_keys if key not in config]
    if missing:
        raise RuntimeError(
            f"config {name}.json was not readable through Configer at "
            f"{config_root / 'keri' / 'cf' / 'main' / f'{name}.json'}; "
            f"missing keys: {', '.join(missing)}"
        )


def _assert_keria_config_readable(config_root: Path, name: str, *, required_keys: tuple[str, ...]) -> None:
    """Fail fast if KERIA cannot read its config from the non-`main` path it uses."""
    from keri.app import configing

    cf = configing.Configer(
        name=name,
        base="",
        headDirPath=str(config_root),
        temp=False,
        reopen=True,
        clear=False,
    )
    try:
        config = cf.get()
    finally:
        cf.close(clear=False)

    missing = [key for key in required_keys if key not in config]
    if missing:
        raise RuntimeError(
            f"KERIA config {name}.json was not readable through readConfigFile at "
            f"{config_root / 'keri' / 'cf' / f'{name}.json'}; "
            f"missing keys: {', '.join(missing)}"
        )


def _terminate_process(proc: subprocess.Popen[bytes], name: str) -> None:
    """Stop a spawned service process without leaving stray local daemons behind.

    Live integration failures are often followed by a rerun. Cleaning up
    reliably here is what keeps later runs from failing with misleading
    "cannot create http server on port ..." errors caused by stale processes.
    """
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
    """Wait for a service port or fail fast with that service's startup log tail.

    Port readiness is the cheapest believable health signal for these
    subprocesses. When a service exits before binding, surfacing the log tail
    here keeps later test failures from obscuring the real startup defect.
    """
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
    the ports are live, the individual scenarios are comparatively cheap.

    Custom HOME dir isolation per test:
    each spawned service gets `HOME` pointed at the pytest temp runtime
    directory. That means any KERI fallback state that would normally land in
    `~/.keri` is isolated per test run instead. This keeps live integration
    tests reproducible, avoids mutating local personal KERI state, and
    removes the need for destructive cleanup between runs.

    Workflow summary:
    1. Create a fresh runtime root and write the witness and KERIA configs into
       the exact `Configer` paths those processes will read.
    2. Verify those configs are actually readable before starting any service.
    3. Start witnesses, then KERIA, then vLEI, waiting for each service's ports
       before proceeding.
    4. Yield connection details to the tests.
    5. Tear services down in reverse startup order so reruns do not inherit
       stale listeners.
    """
    witness_python = _require_python(SIGNIFYPY_PYTHON, "SignifyPy")
    keria_python = _require_python(KERIA_PYTHON, "KERIA")
    vlei_python = _require_python(VLEI_PYTHON, "vLEI")
    runtime_root = tmp_path_factory.mktemp("signify_live_stack")
    config_root = runtime_root / "config"
    _write_canonical_witness_configs(config_root)
    _write_keria_config(config_root)
    for witness_name in WITNESS_CONFIG_NAMES:
        _assert_config_readable(config_root, witness_name, required_keys=(witness_name, "dt"))
    _assert_keria_config_readable(config_root, "demo-witness-oobis", required_keys=("keria", "iurls", "dt"))

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
        # Witnesses must come up first because KERIA resolves the configured
        # witness introduction OOBIs at startup.
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

        # KERIA comes next so client boot/connect and OOBI routes are ready
        # before any test creates identifiers.
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

        # The vLEI helper server is only needed for schema and sample-credential
        # flows, so it starts last.
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
        # Reverse shutdown order mirrors dependency order and reduces the chance
        # of port or file-handle leaks between reruns.
        for name, proc in reversed(procs):
            _terminate_process(proc, name)
        witness_log.close()
        keria_log.close()
        vlei_log.close()


@pytest.fixture
def client_factory(live_stack):
    """Return a factory for fresh clients so each test controls its own actors.

    The integration suite routinely models multiple participants in one
    scenario. Returning a callable instead of a shared client keeps the test
    bodies honest about which participant owns which state and notifications.
    """
    from tests.integration.helpers import connect_client

    def factory():
        return connect_client(live_stack)

    return factory
