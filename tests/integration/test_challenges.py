"""Live challenge-response coverage mirrored from SignifyTS.

The important contract in this file is that challenge exchange uses agent
OOBIs, not witness OOBIs. The challenge response itself travels as a peer
exchange between participants after they have resolved each other's agent
endpoints.
"""

from __future__ import annotations

import time

import pytest
from keri.core import serdering

from .constants import TEST_WITNESS_AIDS
from .helpers import (
    alias,
    create_identifier,
    exchange_agent_oobis,
    wait_for_contact_alias,
    wait_for_operation,
)


pytestmark = pytest.mark.integration


def test_challenge_response(client_factory):
    # Workflow:
    # 1. Create two witnessed identifiers and wait for their agent OOBIs.
    # 2. Exchange agent OOBIs so each side can route peer exchanges to the
    #    other's agent endpoint.
    # 3. Have Bob respond to Alice's challenge words.
    # 4. Ask Alice's agent to verify Bob's signed response.
    # 5. Mark the verified response as accepted and assert the authenticated
    #    challenge state on Alice's contact record for Bob.
    client_a = client_factory()
    client_b = client_factory()
    name_a = alias("alice")
    name_b = alias("bob")

    aid_a = create_identifier(client_a, name_a, wits=TEST_WITNESS_AIDS)
    aid_b = create_identifier(client_b, name_b, wits=TEST_WITNESS_AIDS)
    exchange_agent_oobis(client_a, name_a, client_b, name_b)
    contact = wait_for_contact_alias(client_a, name_b)

    words = client_a.challenges().generate()
    assert len(words) == 12
    assert contact["alias"] == name_b
    assert contact["id"] == aid_b["prefix"]
    assert isinstance(contact["challenges"], list)
    assert len(contact["challenges"]) == 0

    client_b.challenges().respond(name_b, aid_a["prefix"], words)
    verify_operation = client_a.challenges().verify(aid_b["prefix"], words)
    verify_result = wait_for_operation(client_a, verify_operation)
    exn = serdering.SerderKERI(sad=verify_result["response"]["exn"])

    assert verify_result["response"]["exn"]
    assert exn.said
    assert client_a.challenges().responded(aid_b["prefix"], exn.said) is True

    deadline = time.time() + 30
    while time.time() < deadline:
        contact = wait_for_contact_alias(client_a, name_b)
        if len(contact.get("challenges", [])) == 1:
            break
        time.sleep(0.5)

    assert contact["alias"] == name_b
    assert contact["id"] == aid_b["prefix"]
    assert len(contact["challenges"]) == 1
    assert contact["challenges"][0]["authenticated"] is True
