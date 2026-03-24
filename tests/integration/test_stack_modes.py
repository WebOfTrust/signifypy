"""Focused live smoke coverage for shared and isolated stack fixtures."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


def test_shared_client_factory_attaches_shared_stack(client_factory):
    client = client_factory()

    assert client.agent is not None
    assert client._integration_live_stack["mode"] == "shared"
    assert client._integration_live_stack["runtime_root"].exists()


@pytest.mark.parametrize("case", ["a", "b"])
def test_isolated_client_factory_attaches_isolated_stack(isolated_client_factory, case):
    client = isolated_client_factory()

    assert case in {"a", "b"}
    assert client.agent is not None
    assert client._integration_live_stack["mode"] == "isolated"
    assert client._integration_live_stack["runtime_root"].exists()
