"""Common JSON-shaped typing helpers for copied KERIA API contracts."""

from typing import Any, NotRequired, TypeAlias, TypedDict

JsonDict: TypeAlias = dict[str, Any]
JsonValue: TypeAlias = Any


class AgentConfig(TypedDict):
    """Agent configuration payload returned by KERIA's ``/config`` endpoint."""

    iurls: NotRequired[list[str]]
