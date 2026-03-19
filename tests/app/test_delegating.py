# -*- encoding: utf-8 -*-
"""Unit tests for the delegation client resource.

These tests intentionally stay close to the wire contract: build the anchoring
interaction event locally, sign it with the keeper, and post it to the
delegation endpoint.
"""

from mockito import expect, mock, unstub, verifyNoUnwantedInteractions


def test_delegations_approve():
    # This test locks down the exact payload shape for delegated-inception
    # approval so integration tests can trust `client.delegations().approve(...)`
    # instead of dropping down to raw HTTP.
    mock_manager = mock()
    mock_client = mock({"manager": mock_manager})

    hab = {
        "prefix": "delegator-prefix",
        "state": {
            "s": "0",
            "d": "EANCHOR-DIGEST",
        },
    }
    expect(mock_client, times=1).identifiers().thenReturn(mock_client)
    expect(mock_client, times=1).get("delegator").thenReturn(hab)

    from keri.core import eventing
    mock_serder = mock({"ked": {"t": "ixn"}, "raw": b"ixn-bytes"}, strict=True)
    expect(eventing, times=1).interact(
        "delegator-prefix",
        sn=1,
        data=[{"i": "delegate-prefix", "s": "0", "d": "delegate-prefix"}],
        dig="EANCHOR-DIGEST",
    ).thenReturn(mock_serder)

    mock_keeper = mock({"algo": "salty"}, strict=True)
    expect(mock_manager, times=1).get(aid=hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=b"ixn-bytes").thenReturn(["sig1", "sig2"])
    expect(mock_keeper, times=1).params().thenReturn({"keeper": "params"})

    mock_response = mock({"json": lambda: {"name": "op1", "done": False}}, strict=True)
    expect(mock_client, times=1).post(
        "/identifiers/delegator/delegation",
        json={
            "ixn": {"t": "ixn"},
            "sigs": ["sig1", "sig2"],
            "salty": {"keeper": "params"},
        },
    ).thenReturn(mock_response)

    from signify.app.delegating import Delegations

    serder, sigs, op = Delegations(client=mock_client).approve(
        "delegator",
        {"i": "delegate-prefix", "s": "0", "d": "delegate-prefix"},
    )

    assert serder == mock_serder
    assert sigs == ["sig1", "sig2"]
    assert op == {"name": "op1", "done": False}

    unstub()
    verifyNoUnwantedInteractions()
