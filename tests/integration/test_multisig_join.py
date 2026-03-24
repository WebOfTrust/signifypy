"""Live multisig join and expansion coverage beyond the 2-of-2 happy path."""

from __future__ import annotations

import pytest

from .constants import TEST_WITNESS_AIDS
from .helpers import (
    alias,
    assert_multisig_members,
    create_identifier,
    create_multisig_group_n,
    exchange_agent_oobis_among,
    expose_multisig_agent_oobi_n,
    resolve_oobi,
    rotate_multisig_group_n,
    wait_for_contact_alias,
)


pytestmark = pytest.mark.integration


def test_multisig_join_lifecycle_4_of_4(client_factory):
    """Replace the old quartet scripts with one truthful 4-of-4 live workflow.

    The contract here is broader than basic creation: all four members must
    converge on one group prefix, an outside observer must be able to resolve
    the group agent OOBI, and the full group must rotate coherently after every
    member rotates.
    """
    # This replaces the old create/join quartet scripts with one isolated live
    # scenario: create four member AIDs, exchange the exact agent OOBIs they
    # need to coordinate, incept one 4-of-4 group, publish the group agent
    # OOBI, and then rotate the whole group after every member rotates.
    clients = [client_factory() for _ in range(5)]
    member_clients = clients[:4]
    observer = clients[4]
    member_names = [alias(f"member-{index + 1}") for index in range(4)]
    group_name = alias("quadlet")
    participants = list(zip(member_clients, member_names))

    member_habs = [
        create_identifier(client, member_name, wits=TEST_WITNESS_AIDS)
        for client, member_name in participants
    ]
    exchange_agent_oobis_among(participants)
    # The ordered participant list is the source of truth for later group
    # membership assertions and for the N-party helper choreography.
    groups = create_multisig_group_n(
        participants,
        group_name,
        wits=TEST_WITNESS_AIDS,
    )

    expected_prefixes = [member["prefix"] for member in member_habs]
    members = assert_multisig_members(
        member_clients[0],
        group_name,
        count=4,
        signing_aids=expected_prefixes,
        rotation_aids=expected_prefixes,
    )
    assert len({group["prefix"] for group in groups}) == 1
    assert all(group["name"] == group_name for group in groups)
    assert all(group["state"]["b"] == TEST_WITNESS_AIDS for group in groups)
    assert len(members["signing"]) == 4

    group_oobi = expose_multisig_agent_oobi_n(participants, group_name)
    resolve_oobi(observer, group_oobi, alias=group_name)
    contact = wait_for_contact_alias(observer, group_name)

    created_digest = groups[0]["state"]["d"]
    rotated_groups = rotate_multisig_group_n(participants, group_name)

    assert contact["alias"] == group_name
    assert contact["id"] == groups[0]["prefix"]
    assert int(rotated_groups[0]["state"]["s"], 16) == 1
    assert len({group["state"]["s"] for group in rotated_groups}) == 1
    assert len({group["state"]["d"] for group in rotated_groups}) == 1
    assert rotated_groups[0]["state"]["d"] != created_digest
