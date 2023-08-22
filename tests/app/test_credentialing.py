# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_credentialing module

Testing credentialing with unit tests
"""

from mockito import mock, unstub, verify, verifyNoUnwantedInteractions, expect

def test_registries():
    from signify.app.credentialing import Registries
    mock_hab = mock({'pre': 'a_prefix'})

    from keri.vdr import eventing
    expect(eventing, times=1).incept('a_prefix', 
                            baks=None, 
                            toad=None, 
                            nonce=None, 
                            cnfg=['NB'], 
                            code='E')
    
    Registries().registryIncept(mock_hab, {'noBackers': True,})

def test_credentials_list():  
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_response = mock({'json': lambda: {}}, spec=Response, strict=True)
    expect(mock_client, times=1).post('/identifiers/aid1/credentials/query', json={'filter': {'genre': 'horror'}, 'sort': 'updside down', 'skip': 10, 'limt': 10}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    Credentials(client=mock_client).list('aid1', filtr={'genre': 'horror'}, sort='updside down', skip=10, limit=10) # type: ignore

    verify(mock_response, times=1).json()

    verifyNoUnwantedInteractions()
    unstub()

def test_credentials_query():  
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_response = mock({'content': 'things I found'}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/identifiers/aid1/credentials/a_said', headers={'accept': 'application/json+cesr'}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    out = Credentials(client=mock_client).export('aid1', 'a_said') # type: ignore

    assert out == 'things I found'

    verifyNoUnwantedInteractions()
    unstub()