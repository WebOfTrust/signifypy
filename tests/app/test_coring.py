# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_coring module

Testing coring with unit tests
"""

import pytest
from mockito import mock, expect

pytestmark = pytest.mark.usefixtures("mockito_clean")


def test_operations(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ops = coring.Operations(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/operations/a_name').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ops.get("a_name")

def test_oobis_get(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    oobis = coring.Oobis(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/identifiers/a_name/oobis?role=my_role').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    oobis.get("a_name", "my_role")

def test_oobis_resolve(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    oobis = coring.Oobis(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).post('/oobis', json={'url': 'my oobi', 'oobialias': 'Harry'}).thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    oobis.resolve("my oobi", alias="Harry")

def test_key_states_get(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/states?pre=a_prefix').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.get("a_prefix")

def test_key_states_list(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/states?pre=pre1&pre=pre2').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.list(["pre1", "pre2"])

def test_key_states_query(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    mock_response = make_mock_response()
     
    expect(client, times=1).post('/queries', json={'pre': 'a_prefix', 'sn': 0, 'anchor': {'my': 'anchor'}}).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.query("a_prefix", sn=0, anchor={'my': 'anchor'})

def test_key_events(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ke = coring.KeyEvents(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/events?pre=my_prefix').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ke.get("my_prefix")
