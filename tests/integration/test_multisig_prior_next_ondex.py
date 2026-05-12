"""Multisig replacement rotation coverage for prior-next signing indexes."""

from __future__ import annotations

import pytest
from keri.core import signing as csigning

from .helpers import (
    accept_multisig_incept,
    alias,
    create_identifier,
    query_key_state,
    resolve_agent_oobi,
    rotate_identifier,
    start_multisig_incept,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_3_of_3_replacement_rotation_signs_with_prior_next_ondexes(client_factory):
    """A departing full-threshold member still signs from the prior next set."""
    clients = [client_factory() for _ in range(4)]
    client_a, client_b, client_c, client_d = clients
    member_names = [alias(f"ondex-member-{index + 1}") for index in range(4)]
    member_a_name, member_b_name, member_c_name, member_d_name = member_names
    group_name = alias("ondex-group")

    member_a = create_identifier(client_a, member_a_name, wits=[])
    member_b = create_identifier(client_b, member_b_name, wits=[])
    member_c = create_identifier(client_c, member_c_name, wits=[])
    member_d = create_identifier(client_d, member_d_name, wits=[])
    members = [member_a, member_b, member_c, member_d]

    # The three current group participants must know all existing and incoming
    # member KELs before they can build the same replacement rotation inputs.
    _resolve_oobis_for_replacement(
        targets=[
            (client_a, member_a_name),
            (client_b, member_b_name),
            (client_c, member_c_name),
        ],
        sources=[
            (client_a, member_a_name),
            (client_b, member_b_name),
            (client_c, member_c_name),
            (client_d, member_d_name),
        ],
    )

    participants = [member_a["prefix"], member_b["prefix"], member_c["prefix"]]
    operation_a, _ = start_multisig_incept(
        client_a,
        group_name=group_name,
        local_member_name=member_a_name,
        participants=participants,
        isith=3,
        nsith=3,
        toad=0,
        wits=[],
    )
    operation_b = accept_multisig_incept(
        client_b,
        group_name=group_name,
        local_member_name=member_b_name,
    )
    operation_c = accept_multisig_incept(
        client_c,
        group_name=group_name,
        local_member_name=member_c_name,
    )
    wait_for_operation(client_a, operation_a, timeout=20)
    wait_for_operation(client_b, operation_b, timeout=20)
    wait_for_operation(client_c, operation_c, timeout=20)

    # Rotate only the current group members. The group inception precommitted
    # to these next keys, so these rotated member states are the current signer
    # keys for the next group rotation.
    rotate_identifier(client_a, member_a_name)
    rotate_identifier(client_b, member_b_name)
    rotate_identifier(client_c, member_c_name)

    (
        member_a_state,
        member_b_state,
        member_c_state,
        member_d_state,
    ) = _query_replacement_states(client_a, members)

    # The other current participants need the same exact member KEL state so
    # they can sign the same proposed replacement event locally.
    _query_replacement_states(client_b, members)
    _query_replacement_states(client_c, members)

    # This is the valid first replacement rotation: C is still in the current
    # signing set, but D replaces C in the proposed next digest list.
    states = [member_a_state, member_b_state, member_c_state]
    rstates = [member_a_state, member_b_state, member_d_state]

    rot_a, sigs_a, _ = client_a.identifiers().rotate(
        group_name,
        states=states,
        rstates=rstates,
    )
    sig_a = csigning.Siger(qb64=sigs_a[0])
    assert rot_a.ked["n"] == [state["n"][0] for state in rstates]
    assert sig_a.index == 0
    assert sig_a.ondex == 0

    rot_b, sigs_b, _ = client_b.identifiers().rotate(
        group_name,
        states=states,
        rstates=rstates,
    )
    sig_b = csigning.Siger(qb64=sigs_b[0])
    assert rot_b.ked["n"] == [state["n"][0] for state in rstates]
    assert sig_b.index == 1
    assert sig_b.ondex == 1

    # This is the regression. C is intentionally absent from the proposed
    # rstates, but C must still expose ondex=2 because C's current key was
    # committed at position 2 in the group's prior next digest list.
    rot_c, sigs_c, _ = client_c.identifiers().rotate(
        group_name,
        states=states,
        rstates=rstates,
    )
    sig_c = csigning.Siger(qb64=sigs_c[0])
    assert rot_c.ked["n"] == [state["n"][0] for state in rstates]
    assert sig_c.index == 2
    assert sig_c.ondex == 2


def _query_replacement_states(client, members: list[dict]) -> tuple[dict, dict, dict, dict]:
    """Fetch exact sequence-number states for rotated A/B/C and unrotated D."""
    state_a = query_key_state(client, members[0]["prefix"], sn="1")
    state_b = query_key_state(client, members[1]["prefix"], sn="1")
    state_c = query_key_state(client, members[2]["prefix"], sn="1")
    state_d = query_key_state(client, members[3]["prefix"], sn="0")
    return state_a, state_b, state_c, state_d


def _resolve_oobis_for_replacement(
    *,
    targets: list[tuple[object, str]],
    sources: list[tuple[object, str]],
) -> None:
    """Resolve all replacement member agent OOBIs into current participants."""
    for target_client, _ in targets:
        for source_client, source_name in sources:
            if source_client is target_client:
                continue
            resolve_agent_oobi(
                source_client,
                source_name,
                target_client,
                alias=source_name,
            )
