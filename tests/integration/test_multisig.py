"""Live multisig lifecycle coverage for the 2-of-2 Phase 2 happy path."""

from __future__ import annotations

import pytest

from .constants import TEST_WITNESS_AIDS
from .helpers import (
    assert_multisig_members,
    alias,
    create_identifier,
    create_multisig_group,
    exchange_agent_oobis,
    expose_multisig_agent_oobi,
    resolve_oobi,
    rotate_multisig_group,
    wait_for_contact_alias,
)


pytestmark = pytest.mark.integration


def test_multisig_lifecycle_2_of_2(client_factory):
    # Workflow:
    # 1. Create two witnessed member identifiers and exchange their agent OOBIs
    #    so they can coordinate through peer exchanges.
    # 2. Incept the 2-of-2 group and assert both local group views converge on
    #    the same group prefix and member roster.
    # 3. Publish the group's agent end-role replies, derive the group agent
    #    OOBI, and prove a third-party observer can resolve it into a contact.
    # 4. Rotate both member AIDs and then rotate the group itself, asserting
    #    both sides converge on the same post-rotation sequence number.
    client_a = client_factory()
    client_b = client_factory()
    observer = client_factory()

    member_a_name = alias("member-a")
    member_b_name = alias("member-b")
    group_name = alias("multisig")

    member_a = create_identifier(client_a, member_a_name, wits=TEST_WITNESS_AIDS)
    member_b = create_identifier(client_b, member_b_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(client_a, member_a_name, client_b, member_b_name)

    group_a, group_b = create_multisig_group(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
        wits=TEST_WITNESS_AIDS,
    )
    members = assert_multisig_members(
        client_a,
        group_name,
        signing_aids=[member_a["prefix"], member_b["prefix"]],
        rotation_aids=[member_a["prefix"], member_b["prefix"]],
    )
    assert group_a["prefix"] == group_b["prefix"]
    assert group_a["name"] == group_name
    assert group_b["name"] == group_name
    assert group_a["state"]["b"] == TEST_WITNESS_AIDS
    assert group_b["state"]["b"] == TEST_WITNESS_AIDS
    assert len(members["signing"]) == 2

    group_oobi = expose_multisig_agent_oobi(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
    )
    resolve_oobi(observer, group_oobi, alias=group_name)
    contact = wait_for_contact_alias(observer, group_name)

    assert contact["alias"] == group_name
    assert contact["id"] == group_a["prefix"]

    created_digest = group_a["state"]["d"]
    rotated_a, rotated_b = rotate_multisig_group(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
    )

    assert int(rotated_a["state"]["s"], 16) == 1
    assert rotated_a["state"]["s"] == rotated_b["state"]["s"]
    assert rotated_a["state"]["d"] == rotated_b["state"]["d"]
    assert rotated_a["state"]["d"] != created_digest
