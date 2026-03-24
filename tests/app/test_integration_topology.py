# -*- encoding: utf-8 -*-
"""Fast tests for live integration topology derivation."""

from __future__ import annotations

from tests.integration.constants import SCHEMA_SAID, WITNESS_AIDS
from tests.integration.topology import (
    additional_schema_oobis,
    make_stack_topology,
    stack_runtime_name,
)


def test_make_stack_topology_builds_urls_and_oobis(tmp_path):
    topology = make_stack_topology(
        tmp_path / "stack",
        worker_id="gw1",
        mode="shared",
        ports=(5601, 5602, 5603, 5901, 5902, 5903, 7723),
    )

    assert topology.keria_admin_url == "http://127.0.0.1:5901"
    assert topology.keria_agent_url == "http://127.0.0.1:5902"
    assert topology.keria_boot_url == "http://127.0.0.1:5903"
    assert topology.vlei_schema_url == "http://127.0.0.1:7723"
    assert topology.schema_oobi == f"http://127.0.0.1:7723/oobi/{SCHEMA_SAID}"
    assert topology.witness_oobis == [
        f"http://127.0.0.1:5601/oobi/{WITNESS_AIDS[0]}/controller?name=Wan&tag=witness",
        f"http://127.0.0.1:5602/oobi/{WITNESS_AIDS[1]}/controller?name=Wil&tag=witness",
        f"http://127.0.0.1:5603/oobi/{WITNESS_AIDS[2]}/controller?name=Wes&tag=witness",
    ]
    assert topology.as_live_stack()["witness_config_iurls"] == topology.witness_oobis


def test_additional_schema_oobis_follow_vlei_url():
    oobis = additional_schema_oobis("http://127.0.0.1:9999")

    assert oobis["legal-entity"].startswith("http://127.0.0.1:9999/oobi/")
    assert oobis["ecr-auth"].startswith("http://127.0.0.1:9999/oobi/")
    assert oobis["ecr"].startswith("http://127.0.0.1:9999/oobi/")


def test_stack_runtime_name_distinguishes_shared_and_isolated():
    shared = stack_runtime_name(mode="shared", worker_id="gw1")
    isolated = stack_runtime_name(
        mode="isolated",
        worker_id="gw1",
        nodeid="tests/integration/test_example.py::test_case",
    )

    assert shared == "signify-live-stack-shared-gw1"
    assert "shared" in shared
    assert "isolated" in isolated
    assert "test_example.py-test_case" in isolated
