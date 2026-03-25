"""Live-stack fixtures for the SignifyPy integration layer.

This file is the harness entry point for every live integration scenario. It
starts a local witness-demo topology, KERIA, and the vLEI helper server inside
pytest-owned temp state so tests can exercise real SignifyPy workflows without
mutating a developer's global `~/.keri`.

This module assumes that the following repositories are cloned in the same
containing directory SignifyPy is cloned to:
    - KERIA
    - VLEI
    - KERIpy

The test fixtures in this file use Python subprocesses and file-backed harness
entrypoints under `tests/integration/_services`.

The important constraint is that different services read config from
different `Configer` bases:

- witness demo configs are loaded from `.../keri/cf/main/...`
- KERIA agency config is loaded from `.../keri/cf/...`

If those paths drift, the stack can still appear to "start" while publishing
broken endpoint metadata, which later shows up as empty OOBIs or hanging
multistep workflows.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
import socket
import subprocess
from pathlib import Path

import pytest

from tests.integration.helpers import poll_until
from tests.integration.topology import make_stack_topology, stack_runtime_name

# The following directories are used when running each command or library in an
# isolated virtualenv below.
SIGNIFYPY_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = SIGNIFYPY_ROOT.parent
KERIPY_ROOT = SOURCE_ROOT / "keripy"
KERIA_ROOT = SOURCE_ROOT / "keria"
VLEI_ROOT = SOURCE_ROOT / "vLEI"
SIGNIFYPY_PYTHON = SIGNIFYPY_ROOT / "venv" / "bin" / "python"
KERIA_PYTHON = KERIA_ROOT / "venv" / "bin" / "python"
VLEI_PYTHON = VLEI_ROOT / "venv" / "bin" / "python"

KERIPY_WITNESS_CONFIG_DIR = KERIPY_ROOT / "scripts" / "keri" / "cf" / "main"
WITNESS_CONFIG_NAMES = ("wan", "wil", "wes")
SERVICE_SCRIPTS_ROOT = INTEGRATION_ROOT / "_services"
WITNESS_SERVER_SCRIPT = SERVICE_SCRIPTS_ROOT / "witness_server.py"
KERIA_SERVER_SCRIPT = SERVICE_SCRIPTS_ROOT / "keria_server.py"
VLEI_SERVER_SCRIPT = SERVICE_SCRIPTS_ROOT / "vlei_server.py"
PORT_POLL_INTERVAL = float(os.getenv("SIGNIFYPY_INTEGRATION_PORT_POLL_INTERVAL", "0.1"))


# Runtime and config helpers

def _require_python(path: Path, name: str) -> str:
    """Return the runtime path or skip when that repo-local interpreter is unavailable."""
    if not path.exists():
        pytest.skip(f"{name} runtime is unavailable at {path}")
    return str(path)


def _write_canonical_witness_configs(config_root: Path, live_stack: dict) -> None:
    """Copy canonical witness-demo configs into the exact path witnesses read.

    Witness startup in the harness launcher uses `Configer(..., base="main")`,
    so these files have to live under `keri/cf/main`. Keeping the canonical
    `wan`/`wil`/`wes` files here preserves the SignifyTS witness AIDs and the
    corresponding witness OOBIs expected by the tests.
    """
    target_dir = config_root / "keri" / "cf" / "main"
    target_dir.mkdir(parents=True, exist_ok=True)

    for index, name in enumerate(WITNESS_CONFIG_NAMES):
        source = KERIPY_WITNESS_CONFIG_DIR / f"{name}.json"
        if not source.exists():
            pytest.skip(f"canonical witness config is unavailable at {source}")
        config = json.loads(source.read_text(encoding="utf-8"))
        config[name]["curls"] = [
            curl if not curl.startswith("http://") else f"http://{live_stack['host']}:{live_stack['witness_ports'][index]}/"
            for curl in config[name]["curls"]
        ]
        (target_dir / f"{name}.json").write_text(json.dumps(config), encoding="utf-8")


def _write_keria_config(config_root: Path, live_stack: dict) -> None:
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
            "curls": [live_stack["keria_agent_url"] + "/"],
        },
        "iurls": live_stack["witness_config_iurls"],
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
    def _fetch() -> bool:
        if proc.poll() is not None:
            raise RuntimeError(
                f"{name} exited early with code {proc.returncode}:\n"
                f"{_read_log_tail(log_path)}"
            )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex((host, port)) == 0

    try:
        poll_until(
            _fetch,
            ready=bool,
            timeout=timeout,
            interval=PORT_POLL_INTERVAL,
            describe=f"{name} on {host}:{port}",
        )
    except TimeoutError as err:
        raise TimeoutError(
            f"{err}\n{_read_log_tail(log_path)}"
        ) from err


def _current_worker_id() -> str:
    """Return the pytest xdist worker id, or `master` outside xdist."""
    return os.getenv("PYTEST_XDIST_WORKER", "master")


def _port_conflict(err: BaseException) -> bool:
    """Return True when startup failed because a port was already in use."""
    text = str(err).lower()
    return (
        "address already in use" in text
        or "cannot create http server on port" in text
        or "errno 98" in text
        or "errno 48" in text
    )


def _build_live_stack(tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest, *, mode: str, attempt: int = 0) -> dict:
    """Create one runtime-generated live stack mapping for the requested mode.

    The returned mapping is the shared contract between topology generation,
    subprocess launch, and the client-side helper layer. Keeping that shape
    centralized here is what lets the harness evolve without leaking stack
    internals into test bodies.
    """
    worker_id = _current_worker_id()
    nodeid = request.node.nodeid if mode == "isolated" else None
    runtime_root = tmp_path_factory.mktemp(
        stack_runtime_name(mode=mode, worker_id=worker_id, nodeid=nodeid, attempt=attempt)
    )
    topology = make_stack_topology(runtime_root, worker_id=worker_id, mode=mode)
    return topology.as_live_stack()


@contextmanager
def _launch_live_stack(live_stack: dict):
    """Launch one live stack instance from a runtime-generated topology.

    This context manager owns the full lifecycle of the live harness: write
    stack-specific configs, launch witnesses/KERIA/vLEI, wait for their ports,
    then tear everything down in reverse order.
    """
    witness_python = _require_python(SIGNIFYPY_PYTHON, "SignifyPy")
    keria_python = _require_python(KERIA_PYTHON, "KERIA")
    vlei_python = _require_python(VLEI_PYTHON, "vLEI")
    runtime_root = live_stack["runtime_root"]
    config_root = live_stack["config_root"]

    _write_canonical_witness_configs(config_root, live_stack)
    _write_keria_config(config_root, live_stack)
    for witness_name in WITNESS_CONFIG_NAMES:
        _assert_config_readable(config_root, witness_name, required_keys=(witness_name, "dt"))
    _assert_keria_config_readable(config_root, "demo-witness-oobis", required_keys=("keria", "iurls", "dt"))

    shared_env = os.environ.copy()
    # Every stack gets its own HOME so KERI/KERIA state stays inside the
    # pytest-owned runtime directory rather than leaking into the maintainer's
    # real ~/.keri.
    shared_env["HOME"] = str(live_stack["home"])

    witness_env = shared_env.copy()
    keria_env = shared_env.copy()
    keria_env["PYTHONPATH"] = str(KERIA_ROOT / "src")

    vlei_env = shared_env.copy()
    vlei_env["PYTHONPATH"] = str(VLEI_ROOT / "src")

    procs: list[tuple[str, subprocess.Popen[bytes]]] = []
    witness_log_path = live_stack["log_root"] / "witness.log"
    keria_log_path = live_stack["log_root"] / "keria.log"
    vlei_log_path = live_stack["log_root"] / "vlei.log"
    witness_log = witness_log_path.open("wb")
    keria_log = keria_log_path.open("wb")
    vlei_log = vlei_log_path.open("wb")

    try:
        witness = subprocess.Popen(
            [
                witness_python,
                "-u",
                str(WITNESS_SERVER_SCRIPT),
                "--config-dir",
                str(config_root),
                "--wan-port",
                str(live_stack["witness_ports"][0]),
                "--wil-port",
                str(live_stack["witness_ports"][1]),
                "--wes-port",
                str(live_stack["witness_ports"][2]),
            ],
            cwd=SIGNIFYPY_ROOT,
            env=witness_env,
            stdout=witness_log,
            stderr=subprocess.STDOUT,
        )
        procs.append(("witness-demo", witness))
        for port in live_stack["witness_ports"]:
            _wait_for_port(live_stack["host"], port, witness, "witness-demo", log_path=witness_log_path)

        keria = subprocess.Popen(
            [
                keria_python,
                "-u",
                str(KERIA_SERVER_SCRIPT),
                "--config-dir",
                str(config_root),
                "--admin-port",
                str(live_stack["topology"].keria_admin_port),
                "--http-port",
                str(live_stack["topology"].keria_http_port),
                "--boot-port",
                str(live_stack["topology"].keria_boot_port),
            ],
            cwd=SIGNIFYPY_ROOT,
            env=keria_env,
            stdout=keria_log,
            stderr=subprocess.STDOUT,
        )
        procs.append(("keria", keria))
        _wait_for_port(live_stack["host"], live_stack["topology"].keria_admin_port, keria, "keria", log_path=keria_log_path)
        _wait_for_port(live_stack["host"], live_stack["topology"].keria_http_port, keria, "keria", log_path=keria_log_path)
        _wait_for_port(live_stack["host"], live_stack["topology"].keria_boot_port, keria, "keria", log_path=keria_log_path)

        vlei = subprocess.Popen(
            [
                vlei_python,
                "-u",
                str(VLEI_SERVER_SCRIPT),
                "--schema-dir",
                str(VLEI_ROOT / "schema" / "acdc"),
                "--cred-dir",
                str(VLEI_ROOT / "samples" / "acdc"),
                "--oobi-dir",
                str(VLEI_ROOT / "samples" / "oobis"),
                "--http-port",
                str(live_stack["topology"].vlei_port),
            ],
            cwd=SIGNIFYPY_ROOT,
            env=vlei_env,
            stdout=vlei_log,
            stderr=subprocess.STDOUT,
        )
        procs.append(("vlei-server", vlei))
        _wait_for_port(live_stack["host"], live_stack["topology"].vlei_port, vlei, "vlei-server", log_path=vlei_log_path)

        yield live_stack
    finally:
        for name, proc in reversed(procs):
            _terminate_process(proc, name)
        witness_log.close()
        keria_log.close()
        vlei_log.close()


def _stack_fixture(tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest, *, mode: str):
    """Launch one stack instance with retry-on-port-conflict semantics.

    Dynamic ports make conflicts unlikely, not impossible. Retrying the whole
    topology launch is simpler and safer than trying to recover from a partial
    startup where one subprocess bound and another failed.
    """
    last_err = None
    for attempt in range(3):
        live_stack = _build_live_stack(tmp_path_factory, request, mode=mode, attempt=attempt)
        try:
            with _launch_live_stack(live_stack) as launched:
                yield launched
                return
        except (RuntimeError, TimeoutError) as err:
            if not _port_conflict(err):
                raise
            last_err = err

    raise RuntimeError(
        f"failed to launch {mode} live stack after repeated port conflicts"
    ) from last_err


def _client_factory(live_stack):
    """Return a factory for fresh clients so each test controls its own actors.

    The integration suite routinely models multiple participants in one
    scenario. Returning a callable instead of a shared client keeps the test
    bodies honest about which participant owns which state and notifications.
    """
    from tests.integration.helpers import connect_client

    def factory(**kwargs):
        return connect_client(live_stack, **kwargs)

    return factory


@pytest.fixture(scope="session")
def shared_live_stack(tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest):
    """Launch one live stack per worker session.

    This is the default cost/performance tradeoff for integration work: each
    xdist worker gets one deployment to reuse across many tests, while each
    test still creates fresh agents and controllers on top of that deployment.
    """
    yield from _stack_fixture(tmp_path_factory, request, mode="shared")


@pytest.fixture
def isolated_live_stack(tmp_path_factory: pytest.TempPathFactory, request: pytest.FixtureRequest):
    """Launch one fully isolated live stack per test.

    Reach for this only when the test is about runtime isolation itself, or
    when shared-stack reuse would make the behavior under test ambiguous.
    """
    yield from _stack_fixture(tmp_path_factory, request, mode="isolated")


@pytest.fixture(scope="session")
def live_stack(shared_live_stack):
    """Compatibility alias for the shared-per-worker live stack.

    Older tests still refer to `live_stack`; newer ones should usually depend
    on `client_factory` instead so the actor boundary stays explicit.
    """
    return shared_live_stack


@pytest.fixture
def client_factory(shared_live_stack):
    """Return fresh clients bound to the worker-shared live stack.

    This is the default fixture for workflow tests: each call creates a new
    controller/agent pair, but all actors in the same test still talk to the
    same live deployment.
    """
    return _client_factory(shared_live_stack)


@pytest.fixture
def isolated_client_factory(isolated_live_stack):
    """Return fresh clients bound to a per-test isolated live stack.

    Use this when the test is explicitly about stack isolation or fresh runtime
    boundaries. Most business-workflow tests should stay on `client_factory`.
    """
    return _client_factory(isolated_live_stack)
