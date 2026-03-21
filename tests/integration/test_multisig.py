"""Live multisig lifecycle coverage for the 2-of-2 Phase 2 happy path."""

from __future__ import annotations

import pytest

from .constants import TEST_WITNESS_AIDS
from .helpers import (
    assert_multisig_members,
    add_one_multisig_agent_endrole,
    alias,
    create_identifier,
    create_multisig_group,
    exchange_agent_oobis,
    expected_multisig_agent_eids,
    expose_multisig_agent_oobi,
    resolve_oobi,
    rotate_multisig_group,
    wait_for_contact_alias,
    wait_for_end_role,
    wait_for_multisig_request,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_multisig_rpy_follower_reuses_initiator_reply_payload(client_factory):
    # This is the focused `/multisig/rpy` replay regression for the local-after-
    # remote follower path.
    #
    # Participant A: `client_a` / `member_a_name`
    # Participant B: `client_b` / `member_b_name`
    #
    # Workflow:
    # 1. A and B create member AIDs, exchange agent OOBIs, and incept one 2-of-2 group.
    # 2. A publishes exactly one group end-role authorization reply and sends
    #    `/multisig/rpy` to B.
    # 3. B waits for the stored `/multisig/rpy` request, proves the embedded
    #    `rpy` equals A's exact local reply KED, then publishes the matching
    #    local approval.
    # 4. Both sides wait for concrete end-role convergence, not initiator echo
    #    notifications.
    client_a = client_factory()
    client_b = client_factory()

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
    assert group_a["prefix"] == group_b["prefix"]

    members = assert_multisig_members(
        client_a,
        group_name,
        signing_aids=[member_a["prefix"], member_b["prefix"]],
        rotation_aids=[member_a["prefix"], member_b["prefix"]],
    )
    member_agent_eids = expected_multisig_agent_eids(client_a, group_name)
    # Publish one deterministic group agent end-role: participant A's agent EID
    # as advertised in the multisig membership record. The member helper return
    # value itself does not carry `ends`; the group membership view does.
    member_a_record = next(
        signing for signing in members["signing"] if signing["aid"] == member_a["prefix"]
    )
    target_eid = next(iter(member_a_record["ends"]["agent"].keys()))
    assert target_eid in member_agent_eids

    stamp = group_a["state"]["dt"]
    initiator_rpy, _, initiator_operation, _ = add_one_multisig_agent_endrole(
        client_a,
        member_name=member_a_name,
        group_name=group_name,
        eid=target_eid,
        stamp=stamp,
        is_initiator=True,
    )
    _, follower_request = wait_for_multisig_request(client_b, "/multisig/rpy")
    follower_rpy, _, follower_operation, follower_request = add_one_multisig_agent_endrole(
        client_b,
        member_name=member_b_name,
        group_name=group_name,
        eid=target_eid,
        stamp=stamp,
        request=follower_request,
    )

    wait_for_operation(client_a, initiator_operation)
    wait_for_operation(client_b, follower_operation)
    end_role_a = wait_for_end_role(client_a, group_name, eid=target_eid)
    end_role_b = wait_for_end_role(client_b, group_name, eid=target_eid)

    # The stored request payload is the canonical proposal participant B joins.
    assert follower_request[0]["exn"]["e"]["rpy"] == initiator_rpy.ked
    # Matching local reconstruction proves both members endorsed the same reply.
    assert follower_rpy.ked == initiator_rpy.ked
    assert end_role_a["eid"] == target_eid
    assert end_role_b["eid"] == target_eid


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
