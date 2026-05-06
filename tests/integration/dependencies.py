"""Pinned source dependencies for the live integration harness."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationDependency:
    name: str
    repo: str
    ref: str
    path_name: str
    env_root: str
    env_ref: str


KERIPY = IntegrationDependency(
    name="KERIpy",
    repo="https://github.com/WebOfTrust/keripy.git",
    ref="4ee02c0213770d25a0114fe7ebd7ab4ab5500cde",
    path_name="keripy",
    env_root="SIGNIFYPY_INTEGRATION_KERIPY_ROOT",
    env_ref="SIGNIFYPY_INTEGRATION_KERIPY_REF",
)

KERIA = IntegrationDependency(
    name="KERIA",
    repo="https://github.com/WebOfTrust/keria.git",
    ref="9e2461550f373ad7bdbe7eebeaceac689cb15397",
    path_name="keria",
    env_root="SIGNIFYPY_INTEGRATION_KERIA_ROOT",
    env_ref="SIGNIFYPY_INTEGRATION_KERIA_REF",
)

VLEI = IntegrationDependency(
    name="vLEI",
    repo="https://github.com/WebOfTrust/vLEI.git",
    ref="f514b9431c5f965b5f7f64a8693e19df2f181564",
    path_name="vLEI",
    env_root="SIGNIFYPY_INTEGRATION_VLEI_ROOT",
    env_ref="SIGNIFYPY_INTEGRATION_VLEI_REF",
)

INTEGRATION_DEPENDENCIES = (KERIPY, KERIA, VLEI)
