# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_excrowing module

Testing escrowing with unit tests
"""

from mockito import mock, expect

def test_end_role_authorizations_name():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.escrowing import Escrows
    escrows = Escrows(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock(spec=Response, strict=True)

    expect(mock_client, times=1).get('/escrows/rpy', params={'route': '/my_route'}).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'output'})

    out = escrows.getEscrowReply(route='/my_route')

    assert out == {'some': 'output'}
