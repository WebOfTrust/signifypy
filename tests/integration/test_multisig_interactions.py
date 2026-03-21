"""Live multisig interaction coverage for an already-existing group."""

from __future__ import annotations

import pytest

from .constants import TEST_WITNESS_AIDS
from .helpers import (
    alias,
    create_identifier,
    create_multisig_group,
    exchange_agent_oobis,
    interact_multisig_group,
    rotate_multisig_group,
)


pytestmark = pytest.mark.integration


def _state_seal(identifier: dict) -> dict:
    """Create a stable seal-like payload from one identifier state snapshot."""
    return dict(
        i=identifier["prefix"],
        s=identifier["state"]["s"],
        d=identifier["state"]["d"],
    )


def test_multisig_interaction_sequence(client_factory):
    # Workflow:
    # 1. Create a witnessed 2-of-2 group so interaction coverage starts from a
    #    truthful multisig habitat instead of a synthetic fixture object.
    # 2. Submit one existing-group interaction that anchors the inception state.
    # 3. Rotate both members and the group, then assert the last establishment
    #    event (`ee`) advances to that rotation.
    # 4. Submit two more group interactions that anchor, in order, the rotation
    #    state and then the immediately preceding interaction state.
    # 5. Assert the KEL length, event payloads, current sequence number, and
    #    last-establishment anchor after each step.
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
    prefix = group_a["prefix"]

    events = client_a.keyEvents().get(prefix)
    assert group_a["prefix"] == group_b["prefix"]
    assert group_a["state"]["s"] == "0"
    assert group_a["state"]["d"] == group_b["state"]["d"]
    assert group_a["state"]["ee"]["s"] == "0"
    assert group_a["state"]["ee"]["d"] == group_a["state"]["d"]
    assert len(events) == 1
    assert events[0]["ked"]["t"] == "icp"
    assert events[0]["ked"]["d"] == group_a["state"]["d"]

    first_anchor = _state_seal(group_a)
    first_ixn_a, first_ixn_b, after_first_ixn_a, after_first_ixn_b = interact_multisig_group(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
        data=[first_anchor],
    )

    events = client_a.keyEvents().get(prefix)
    assert first_ixn_a.said == first_ixn_b.said
    assert after_first_ixn_a["state"]["s"] == "1"
    assert after_first_ixn_a["state"]["s"] == after_first_ixn_b["state"]["s"]
    assert after_first_ixn_a["state"]["d"] == first_ixn_a.said
    assert after_first_ixn_a["state"]["ee"]["s"] == "0"
    assert after_first_ixn_a["state"]["ee"]["d"] == group_a["state"]["d"]
    assert len(events) == 2
    assert events[1]["ked"]["t"] == "ixn"
    assert events[1]["ked"]["s"] == "1"
    assert events[1]["ked"]["a"] == [first_anchor]
    assert events[1]["ked"]["d"] == first_ixn_a.said

    rotated_a, rotated_b = rotate_multisig_group(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
    )

    events = client_a.keyEvents().get(prefix)
    assert rotated_a["state"]["s"] == "2"
    assert rotated_a["state"]["s"] == rotated_b["state"]["s"]
    assert rotated_a["state"]["ee"]["s"] == "2"
    assert rotated_a["state"]["ee"]["d"] == rotated_a["state"]["d"]
    assert len(events) == 3
    assert events[2]["ked"]["t"] == "rot"
    assert events[2]["ked"]["s"] == "2"
    assert events[2]["ked"]["d"] == rotated_a["state"]["d"]

    second_anchor = _state_seal(rotated_a)
    second_ixn_a, second_ixn_b, after_second_ixn_a, after_second_ixn_b = interact_multisig_group(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
        data=[second_anchor],
    )

    events = client_a.keyEvents().get(prefix)
    assert second_ixn_a.said == second_ixn_b.said
    assert after_second_ixn_a["state"]["s"] == "3"
    assert after_second_ixn_a["state"]["s"] == after_second_ixn_b["state"]["s"]
    assert after_second_ixn_a["state"]["d"] == second_ixn_a.said
    assert after_second_ixn_a["state"]["ee"]["s"] == "2"
    assert after_second_ixn_a["state"]["ee"]["d"] == rotated_a["state"]["d"]
    assert len(events) == 4
    assert events[3]["ked"]["t"] == "ixn"
    assert events[3]["ked"]["s"] == "3"
    assert events[3]["ked"]["a"] == [second_anchor]
    assert events[3]["ked"]["d"] == second_ixn_a.said

    third_anchor = _state_seal(after_second_ixn_a)
    third_ixn_a, third_ixn_b, after_third_ixn_a, after_third_ixn_b = interact_multisig_group(
        client_a,
        member_a_name,
        client_b,
        member_b_name,
        group_name,
        data=[third_anchor],
    )

    events_a = client_a.keyEvents().get(prefix)
    events_b = client_b.keyEvents().get(prefix)
    assert third_ixn_a.said == third_ixn_b.said
    assert after_third_ixn_a["state"]["s"] == "4"
    assert after_third_ixn_a["state"]["s"] == after_third_ixn_b["state"]["s"]
    assert after_third_ixn_a["state"]["d"] == third_ixn_a.said
    assert after_third_ixn_a["state"]["ee"]["s"] == "2"
    assert after_third_ixn_a["state"]["ee"]["d"] == rotated_a["state"]["d"]
    assert len(events_a) == 5
    assert len(events_b) == 5
    assert events_a[4]["ked"]["t"] == "ixn"
    assert events_a[4]["ked"]["s"] == "4"
    assert events_a[4]["ked"]["a"] == [third_anchor]
    assert events_a[4]["ked"]["d"] == third_ixn_a.said
    assert events_b[4]["ked"] == events_a[4]["ked"]
