# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_schemas module

Testing schema read helpers with unit tests.
"""

from mockito import mock, expect, verifyNoUnwantedInteractions, unstub


def test_schemas_get(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    mock_response = make_mock_response({"json": lambda: {}})
    expect(mock_client, times=1).get("/schema/EA_SCHEMA").thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({"$id": "EA_SCHEMA"})

    from signify.app.schemas import Schemas
    out = Schemas(client=mock_client).get("EA_SCHEMA")  # type: ignore

    assert out == {"$id": "EA_SCHEMA"}

    verifyNoUnwantedInteractions()
    unstub()


def test_schemas_list(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    mock_response = make_mock_response({"json": lambda: []})
    expect(mock_client, times=1).get("/schema").thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn([{"$id": "EA_SCHEMA"}])

    from signify.app.schemas import Schemas
    out = Schemas(client=mock_client).list()  # type: ignore

    assert out == [{"$id": "EA_SCHEMA"}]

    verifyNoUnwantedInteractions()
    unstub()
