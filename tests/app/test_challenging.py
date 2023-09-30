# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_challenging module

Testing challenge with unit tests
"""

import pytest
from mockito import mock, verify, verifyNoUnwantedInteractions, unstub, expect


def test_challenges_generate():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.challenging import Challenges
    chas = Challenges(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/challenges').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        {"words": ["word", "one", "two", "three"]}
    )

    out = chas.generate()
    assert out == ["word", "one", "two", "three"]

    verifyNoUnwantedInteractions()
    unstub()


def test_challenge_verify():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.challenging import Challenges
    chas = Challenges(client=mock_client)  # type: ignore

    name = "test"
    source = "E123"
    words = ["word", "one", "two", "three"]
    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).post(f'/challenges/{name}/verify/{source}',
                                      json=dict(words=words)).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        {"done": False}
    )

    out = chas.verify(name, source, words)
    assert out["done"] is False

    verifyNoUnwantedInteractions()
    unstub()


def test_challenge_responded():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.challenging import Challenges
    chas = Challenges(client=mock_client)  # type: ignore

    name = "test"
    source = "E123"
    said = "E456"
    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).post(f'/challenges/{name}/verify/{source}',
                                      json=dict(said=said)).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        {"done": False}
    )

    out = chas.responded(name, source, said)
    assert out["done"] is False

    verifyNoUnwantedInteractions()
    unstub()


def test_challenge_respond():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.aiding import Identifiers
    mock_ids = Identifiers(client=mock_client)  # type: ignore

    from signify.peer.exchanging import Exchanges
    mock_exc = Exchanges(client=mock_client)  # type: ignore

    from signify.app.challenging import Challenges
    chas = Challenges(client=mock_client)  # type: ignore

    mock_hab = {}
    name = "test"
    recp = "E123"
    words = ["word", "one", "two", "three"]
    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).identifiers().thenReturn(mock_ids)
    expect(mock_ids, times=1).get(name).thenReturn(mock_hab)
    expect(mock_client, times=1).exchanges().thenReturn(mock_exc)
    expect(mock_exc, times=1).send(name, "challenge", sender=mock_hab, route="/challenge/response",
                                   payload=dict(words=words),
                                   embeds=dict(),
                                   recipients=[recp]).thenReturn((None, None, mock_response))

    out = chas.respond(name, recp, words)
    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()
