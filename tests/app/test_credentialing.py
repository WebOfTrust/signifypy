# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_credentialing module

Testing credentialing with unit tests
"""

from mockito import mock, unstub, verify, verifyNoUnwantedInteractions, expect, ANY


def test_registries():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.aiding import Identifiers
    mock_ids = mock(spec=Identifiers, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager  # type: ignore

    from requests import Response
    mock_response = mock({'json': lambda: {}}, spec=Response, strict=True)
    mock_hab = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    name = "aid1"
    regName = "reg1"

    expect(mock_client, times=1).identifiers().thenReturn(mock_ids)
    expect(mock_ids, times=1).get(name).thenReturn(mock_hab)

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=2).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])
    expect(mock_client, times=1).post(path=f"/identifiers/{name}/registries", json=ANY()).thenReturn(mock_response)

    from signify.app.credentialing import Registries

    Registries(client=mock_client).create(hab=mock_hab, registryName=regName)
    unstub()


def test_credentials_list():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_response = mock({'json': lambda: {}}, spec=Response, strict=True)
    expect(mock_client, times=1).post('/identifiers/aid1/credentials/query',
                                      json={'filter': {'genre': 'horror'},
                                            'sort': ['updside down'], 'skip': 10, 'limt': 10}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    Credentials(client=mock_client).list('aid1', filtr={'genre': 'horror'}, sort=['updside down'], skip=10,
                                         limit=10)  # type: ignore

    verify(mock_response, times=1).json()

    verifyNoUnwantedInteractions()
    unstub()


def test_credentials_query():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_response = mock({'content': 'things I found'}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/identifiers/aid1/credentials/a_said',
                                     headers={'accept': 'application/json+cesr'}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    out = Credentials(client=mock_client).export('aid1', 'a_said')  # type: ignore

    assert out == 'things I found'

    verifyNoUnwantedInteractions()
    unstub()
