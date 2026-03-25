"""Runtime-generated topology for the SignifyPy live integration harness."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import secrets
import socket

from .constants import ADDITIONAL_SCHEMA_OOBI_SAIDS, QVI_SCHEMA_SAID, WITNESS_AIDS


def _slug(text: str) -> str:
    """Convert a worker id or node id into a filesystem-friendly slug."""
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")
    return slug or "default"


def reserve_random_ports(*, count: int, host: str = "127.0.0.1") -> tuple[int, ...]:
    """Reserve a set of random high ports for one stack instance.

    The sockets are closed immediately after allocation because the launched
    subprocesses need to re-bind them. Collisions are still possible in theory,
    so the harness retries full stack startup when it sees an address-in-use
    failure.
    """
    ports: list[int] = []
    while len(ports) < count:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, 0))
            port = sock.getsockname()[1]
        if port not in ports:
            ports.append(port)
    return tuple(ports)


def additional_schema_oobis(vlei_schema_url: str) -> dict[str, str]:
    """Build the additional sample schema OOBIs for one vLEI server URL."""
    return {
        alias: f"{vlei_schema_url}/oobi/{said}"
        for alias, said in ADDITIONAL_SCHEMA_OOBI_SAIDS.items()
    }


@dataclass(frozen=True)
class IntegrationStackTopology:
    """Concrete runtime topology for one live integration stack instance."""

    stack_id: str
    worker_id: str
    mode: str
    runtime_root: Path
    config_root: Path
    log_root: Path
    home: Path
    host: str
    witness_ports: tuple[int, int, int]
    keria_admin_port: int
    keria_http_port: int
    keria_boot_port: int
    vlei_port: int

    @property
    def keria_admin_url(self) -> str:
        return f"http://{self.host}:{self.keria_admin_port}"

    @property
    def keria_agent_url(self) -> str:
        return f"http://{self.host}:{self.keria_http_port}"

    @property
    def keria_boot_url(self) -> str:
        return f"http://{self.host}:{self.keria_boot_port}"

    @property
    def vlei_schema_url(self) -> str:
        return f"http://{self.host}:{self.vlei_port}"

    @property
    def schema_oobi(self) -> str:
        return f"{self.vlei_schema_url}/oobi/{QVI_SCHEMA_SAID}"

    @property
    def witness_oobis(self) -> list[str]:
        return [
            f"http://{self.host}:{port}/oobi/{aid}/controller?name={name}&tag=witness"
            for port, aid, name in zip(self.witness_ports, WITNESS_AIDS, ("Wan", "Wil", "Wes"))
        ]

    @property
    def witness_config_iurls(self) -> list[str]:
        return self.witness_oobis

    @property
    def sample_schema_oobis(self) -> dict[str, str]:
        return additional_schema_oobis(self.vlei_schema_url)

    def as_live_stack(self) -> dict:
        """Return the mapping shape the current helpers and fixtures expect."""
        return {
            "topology": self,
            "stack_id": self.stack_id,
            "worker_id": self.worker_id,
            "mode": self.mode,
            "runtime_root": self.runtime_root,
            "config_root": self.config_root,
            "log_root": self.log_root,
            "home": self.home,
            "host": self.host,
            "witness_ports": self.witness_ports,
            "keria_admin_url": self.keria_admin_url,
            "keria_agent_url": self.keria_agent_url,
            "keria_boot_url": self.keria_boot_url,
            "vlei_schema_url": self.vlei_schema_url,
            "schema_oobi": self.schema_oobi,
            "additional_schema_oobis": self.sample_schema_oobis,
            "witness_oobis": self.witness_oobis,
            "witness_config_iurls": self.witness_config_iurls,
        }


def make_stack_topology(
    runtime_root: Path,
    *,
    worker_id: str,
    mode: str,
    host: str = "127.0.0.1",
    stack_id: str | None = None,
    ports: tuple[int, ...] | None = None,
) -> IntegrationStackTopology:
    """Create one topology object rooted in a caller-owned runtime directory."""
    runtime_root.mkdir(parents=True, exist_ok=True)
    config_root = runtime_root / "config"
    log_root = runtime_root / "logs"
    config_root.mkdir(parents=True, exist_ok=True)
    log_root.mkdir(parents=True, exist_ok=True)

    allocated_ports = ports or reserve_random_ports(count=7, host=host)
    witness_ports = tuple(allocated_ports[:3])
    keria_admin_port, keria_http_port, keria_boot_port, vlei_port = allocated_ports[3:]

    return IntegrationStackTopology(
        stack_id=stack_id or f"{mode}-{_slug(worker_id)}-{secrets.token_hex(4)}",
        worker_id=worker_id,
        mode=mode,
        runtime_root=runtime_root,
        config_root=config_root,
        log_root=log_root,
        home=runtime_root,
        host=host,
        witness_ports=witness_ports,
        keria_admin_port=keria_admin_port,
        keria_http_port=keria_http_port,
        keria_boot_port=keria_boot_port,
        vlei_port=vlei_port,
    )


def stack_runtime_name(*, mode: str, worker_id: str, nodeid: str | None = None, attempt: int = 0) -> str:
    """Build a stable runtime directory prefix for one worker or isolated test."""
    parts = ["signify-live-stack", mode, _slug(worker_id)]
    if nodeid is not None:
        parts.append(_slug(nodeid))
    if attempt:
        parts.append(f"retry{attempt}")
    return "-".join(parts)
