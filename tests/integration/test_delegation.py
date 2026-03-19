"""Live delegation matrix coverage for Phase 2.

Each test in this file models a distinct delegator/delegate topology. The main
thing maintainers should watch is that OOBI usage stays role-specific and that
multisig cases use real 2-participant groups on every side that claims to be
multisig.
"""

from __future__ import annotations

import pytest

from .constants import TEST_WITNESS_AIDS
from .helpers import (
    accept_multisig_incept,
    assert_multisig_members,
    alias,
    approve_multisig_delegation,
    approve_single_delegation,
    create_identifier,
    create_multisig_group,
    exchange_agent_oobis,
    expose_multisig_agent_oobi,
    query_key_state,
    resolve_agent_oobi,
    resolve_oobi,
    start_delegated_identifier,
    start_multisig_incept,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_single_sig_delegator_to_single_sig_delegate(client_factory):
    # Workflow:
    # 1. Create the delegator and publish its agent OOBI to the future delegate.
    # 2. Start delegated inception on the delegate side.
    # 3. Approve that delegated inception from the single-sig delegator.
    # 4. Force the delegate to learn the delegator's new key state and then
    #    wait for the pending delegate-side operation to complete.
    delegator_client = client_factory()
    delegate_client = client_factory()
    delegator_name = alias("delegator")
    delegate_name = alias("delegate")

    delegator = create_identifier(delegator_client, delegator_name, wits=TEST_WITNESS_AIDS)
    resolve_agent_oobi(delegator_client, delegator_name, delegate_client, alias=delegator_name)

    delegate_serder, delegate_operation = start_delegated_identifier(
        delegate_client,
        delegate_name,
        delpre=delegator["prefix"],
        wits=TEST_WITNESS_AIDS,
    )
    approval_serder, _ = approve_single_delegation(delegator_client, delegator_name, delegate_serder.pre)
    query_key_state(delegate_client, delegator["prefix"], sn="1")
    wait_for_operation(delegate_client, delegate_operation)

    delegate = delegate_client.identifiers().get(delegate_name)
    assert approval_serder.ked["a"][0] == dict(i=delegate_serder.pre, s="0", d=delegate_serder.pre)
    assert delegate["prefix"] == delegate_serder.pre
    assert delegate["state"]["di"] == delegator["prefix"]


def test_single_sig_delegator_to_multisig_delegate(client_factory):
    # Workflow:
    # 1. Create the single-sig delegator plus both multisig delegate members.
    # 2. Exchange member agent OOBIs so the future delegate group can coordinate
    #    its `/multisig/icp` workflow.
    # 3. Resolve the delegator's agent OOBI on both delegate participants so
    #    both members can learn the delegator state that will authorize them.
    # 4. Start delegated multisig inception from member A and accept it from
    #    member B, producing one delegated group AID.
    # 5. Approve the delegated group from the single-sig delegator, query the
    #    delegator state on both participants, and then wait for both delegate
    #    operations to finish on the same group prefix.
    delegator_client = client_factory()
    delegate_client_a = client_factory()
    delegate_client_b = client_factory()
    delegator_name = alias("delegator")
    delegate_member_a_name = alias("delegate-a")
    delegate_member_b_name = alias("delegate-b")
    delegate_group_name = alias("delegate-group")

    delegator = create_identifier(delegator_client, delegator_name, wits=TEST_WITNESS_AIDS)
    delegate_member_a = create_identifier(delegate_client_a, delegate_member_a_name, wits=TEST_WITNESS_AIDS)
    delegate_member_b = create_identifier(delegate_client_b, delegate_member_b_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(
        delegate_client_a,
        delegate_member_a_name,
        delegate_client_b,
        delegate_member_b_name,
    )
    resolve_agent_oobi(delegator_client, delegator_name, delegate_client_a, alias=delegator_name)
    resolve_agent_oobi(delegator_client, delegator_name, delegate_client_b, alias=delegator_name)

    participant_prefixes = [delegate_member_a["prefix"], delegate_member_b["prefix"]]
    delegate_operation_a, delegate_serder = start_multisig_incept(
        delegate_client_a,
        group_name=delegate_group_name,
        local_member_name=delegate_member_a_name,
        participants=participant_prefixes,
        isith=2,
        nsith=2,
        toad=len(TEST_WITNESS_AIDS),
        wits=TEST_WITNESS_AIDS,
        delpre=delegator["prefix"],
    )
    delegate_operation_b = accept_multisig_incept(
        delegate_client_b,
        group_name=delegate_group_name,
        local_member_name=delegate_member_b_name,
    )

    approval_serder, _ = approve_single_delegation(delegator_client, delegator_name, delegate_serder.pre)
    query_key_state(delegate_client_a, delegator["prefix"], sn="1")
    query_key_state(delegate_client_b, delegator["prefix"], sn="1")

    wait_for_operation(delegate_client_a, delegate_operation_a)
    wait_for_operation(delegate_client_b, delegate_operation_b)
    delegate_group_a = delegate_client_a.identifiers().get(delegate_group_name)
    delegate_group_b = delegate_client_b.identifiers().get(delegate_group_name)

    assert approval_serder.ked["a"][0] == dict(i=delegate_serder.pre, s="0", d=delegate_serder.pre)
    assert delegate_group_a["prefix"] == delegate_serder.pre
    assert delegate_group_a["prefix"] == delegate_group_b["prefix"]
    assert delegate_group_a["state"]["di"] == delegator["prefix"]
    assert delegate_group_b["state"]["di"] == delegator["prefix"]
    assert_multisig_members(
        delegate_client_a,
        delegate_group_name,
        signing_aids=participant_prefixes,
        rotation_aids=participant_prefixes,
    )


def test_multisig_delegator_to_single_sig_delegate(client_factory):
    # Workflow:
    # 1. Create both delegator members and incept the 2-of-2 delegator group.
    # 2. Publish the delegator group's agent OOBI, then resolve the base group
    #    OOBI on the delegate exactly like the SignifyTS delegation-multisig
    #    flow does.
    # 3. Start delegated inception on the single-sig delegate.
    # 4. Approve the delegation from both members of the delegator group via
    #    the `/multisig/ixn` choreography.
    # 5. Query the delegator-group key state on the delegate and wait for the
    #    delegate-side operation to finish.
    delegator_client_a = client_factory()
    delegator_client_b = client_factory()
    delegate_client = client_factory()
    delegator_member_a_name = alias("delegator-a")
    delegator_member_b_name = alias("delegator-b")
    delegator_group_name = alias("delegator-group")
    delegate_name = alias("delegate")

    create_identifier(delegator_client_a, delegator_member_a_name, wits=TEST_WITNESS_AIDS)
    create_identifier(delegator_client_b, delegator_member_b_name, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
    )
    delegator_group_a, delegator_group_b = create_multisig_group(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
        delegator_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    delegator_group_oobi = expose_multisig_agent_oobi(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
        delegator_group_name,
    )
    delegator_group_identifier_oobi = delegator_group_oobi.split("/agent/")[0]
    resolve_oobi(delegate_client, delegator_group_identifier_oobi, alias=delegator_group_name)

    delegate_serder, delegate_operation = start_delegated_identifier(
        delegate_client,
        delegate_name,
        delpre=delegator_group_a["prefix"],
        wits=TEST_WITNESS_AIDS,
    )
    approval_serder_a, approve_result_a, approval_serder_b, approve_result_b = approve_multisig_delegation(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
        delegator_group_name,
        delegate_serder.pre,
    )
    query_key_state(delegate_client, delegator_group_a["prefix"], sn="1")
    wait_for_operation(delegate_client, delegate_operation)

    delegate = delegate_client.identifiers().get(delegate_name)
    expected_anchor = dict(i=delegate_serder.pre, s="0", d=delegate_serder.pre)
    assert approval_serder_a.ked["a"][0] == expected_anchor
    assert approval_serder_b.ked["a"][0] == expected_anchor
    assert delegate["prefix"] == delegate_serder.pre
    assert delegate["state"]["di"] == delegator_group_a["prefix"]
    assert approve_result_a["response"] == approve_result_b["response"]
    assert delegator_group_a["prefix"] == delegator_group_b["prefix"]
    assert_multisig_members(
        delegator_client_a,
        delegator_group_name,
        signing_aids=[
            delegator_client_a.identifiers().get(delegator_member_a_name)["prefix"],
            delegator_client_b.identifiers().get(delegator_member_b_name)["prefix"],
        ],
        rotation_aids=[
            delegator_client_a.identifiers().get(delegator_member_a_name)["prefix"],
            delegator_client_b.identifiers().get(delegator_member_b_name)["prefix"],
        ],
    )


def test_multisig_delegator_to_multisig_delegate(client_factory):
    # Workflow:
    # 1. Create both delegator members and both delegate members as witnessed
    #    single-sig AIDs with agent OOBIs.
    # 2. Incept the 2-of-2 delegator group, publish its agent OOBI, then have
    #    the delegate members resolve the base group OOBI exactly like the
    #    SignifyTS delegation-multisig flow does.
    # 3. Start delegated inception of the 2-of-2 delegate group and have the
    #    second delegate member accept the same `/multisig/icp` request.
    # 4. Approve that delegated group from both members of the delegator group
    #    using the multisig `/multisig/ixn` approval choreography.
    # 5. Query the delegator-group key state on both delegate members, then
    #    wait for both delegate operations and assert convergence on one group
    #    prefix on both the delegator and delegate multisig sides.
    delegator_client_a = client_factory()
    delegator_client_b = client_factory()
    delegate_client_a = client_factory()
    delegate_client_b = client_factory()
    delegator_member_a_name = alias("delegator-a")
    delegator_member_b_name = alias("delegator-b")
    delegate_member_a_name = alias("delegate-a")
    delegate_member_b_name = alias("delegate-b")
    delegator_group_name = alias("delegator-group")
    delegate_group_name = alias("delegate-group")

    create_identifier(delegator_client_a, delegator_member_a_name, wits=TEST_WITNESS_AIDS)
    create_identifier(delegator_client_b, delegator_member_b_name, wits=TEST_WITNESS_AIDS)
    create_identifier(delegate_client_a, delegate_member_a_name, wits=TEST_WITNESS_AIDS)
    create_identifier(delegate_client_b, delegate_member_b_name, wits=TEST_WITNESS_AIDS)

    exchange_agent_oobis(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
    )
    exchange_agent_oobis(
        delegate_client_a,
        delegate_member_a_name,
        delegate_client_b,
        delegate_member_b_name,
    )

    delegator_group_a, delegator_group_b = create_multisig_group(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
        delegator_group_name,
        wits=TEST_WITNESS_AIDS,
    )
    delegator_group_oobi = expose_multisig_agent_oobi(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
        delegator_group_name,
    )
    delegator_group_identifier_oobi = delegator_group_oobi.split("/agent/")[0]
    resolve_oobi(delegate_client_a, delegator_group_identifier_oobi, alias=delegator_group_name)
    resolve_oobi(delegate_client_b, delegator_group_identifier_oobi, alias=delegator_group_name)

    delegate_participants = [
        delegate_client_a.identifiers().get(delegate_member_a_name)["prefix"],
        delegate_client_b.identifiers().get(delegate_member_b_name)["prefix"],
    ]
    delegate_operation_a, delegate_serder = start_multisig_incept(
        delegate_client_a,
        group_name=delegate_group_name,
        local_member_name=delegate_member_a_name,
        participants=delegate_participants,
        isith=2,
        nsith=2,
        toad=len(TEST_WITNESS_AIDS),
        wits=TEST_WITNESS_AIDS,
        delpre=delegator_group_a["prefix"],
    )
    delegate_operation_b = accept_multisig_incept(
        delegate_client_b,
        group_name=delegate_group_name,
        local_member_name=delegate_member_b_name,
    )

    approval_serder_a, approve_result_a, approval_serder_b, approve_result_b = approve_multisig_delegation(
        delegator_client_a,
        delegator_member_a_name,
        delegator_client_b,
        delegator_member_b_name,
        delegator_group_name,
        delegate_serder.pre,
    )
    query_key_state(delegate_client_a, delegator_group_a["prefix"], sn="1")
    query_key_state(delegate_client_b, delegator_group_a["prefix"], sn="1")

    wait_for_operation(delegate_client_a, delegate_operation_a)
    wait_for_operation(delegate_client_b, delegate_operation_b)
    delegate_group_a = delegate_client_a.identifiers().get(delegate_group_name)
    delegate_group_b = delegate_client_b.identifiers().get(delegate_group_name)

    expected_anchor = dict(i=delegate_serder.pre, s="0", d=delegate_serder.pre)
    assert approval_serder_a.ked["a"][0] == expected_anchor
    assert approval_serder_b.ked["a"][0] == expected_anchor
    assert delegate_group_a["prefix"] == delegate_serder.pre
    assert delegate_group_a["prefix"] == delegate_group_b["prefix"]
    assert delegate_group_a["state"]["di"] == delegator_group_a["prefix"]
    assert delegate_group_b["state"]["di"] == delegator_group_a["prefix"]
    assert approve_result_a["response"] == approve_result_b["response"]
    assert delegator_group_a["prefix"] == delegator_group_b["prefix"]
    assert_multisig_members(
        delegator_client_a,
        delegator_group_name,
        signing_aids=[
            delegator_client_a.identifiers().get(delegator_member_a_name)["prefix"],
            delegator_client_b.identifiers().get(delegator_member_b_name)["prefix"],
        ],
        rotation_aids=[
            delegator_client_a.identifiers().get(delegator_member_a_name)["prefix"],
            delegator_client_b.identifiers().get(delegator_member_b_name)["prefix"],
        ],
    )
    assert_multisig_members(
        delegate_client_a,
        delegate_group_name,
        signing_aids=delegate_participants,
        rotation_aids=delegate_participants,
    )
