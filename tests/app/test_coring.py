# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_coring module

Testing coring with unit tests
"""

from mockito import mock, expect, unstub, verifyNoUnwantedInteractions


def test_operations():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ops = coring.Operations(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response, strict=True)
    expect(client, times=1).get('/operations/a_name').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ops.get("a_name")

    verifyNoUnwantedInteractions()
    unstub()

def test_oobis_get():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    oobis = coring.Oobis(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response)
    expect(client, times=1).get('/identifiers/a_name/oobis?role=my_role').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    oobis.get("a_name", "my_role")

    verifyNoUnwantedInteractions()
    unstub()

def test_oobis_resolve():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    oobis = coring.Oobis(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response, strict=True)
    expect(client, times=1).post('/oobis', json={'url': 'my oobi', 'oobialias': 'Harry'}).thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    oobis.resolve("my oobi", alias="Harry")

    verifyNoUnwantedInteractions()
    unstub()

def test_key_states_get():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response, strict=True)
    expect(client, times=1).get('/states?pre=a_prefix').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.get("a_prefix")

    verifyNoUnwantedInteractions()
    unstub()

def test_key_states_list():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response, strict=True)
    expect(client, times=1).get('/states?pre=pre1&pre=pre2').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.list(["pre1", "pre2"])

    verifyNoUnwantedInteractions()
    unstub()

def test_key_states_query():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response, strict=True)
     
    expect(client, times=1).post('/queries', json={'pre': 'a_prefix', 'sn': 0, 'anchor': {'my': 'anchor'}}).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.query("a_prefix", sn=0, anchor={'my': 'anchor'})

    verifyNoUnwantedInteractions()
    unstub()

def test_key_events():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ke = coring.KeyEvents(client=client) # type: ignore

    import requests
    mock_response = mock(spec=requests.Response, strict=True)
    expect(client, times=1).get('/events?pre=my_prefix').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ke.get("my_prefix")

    verifyNoUnwantedInteractions()
    unstub()
