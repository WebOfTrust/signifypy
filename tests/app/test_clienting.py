# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_clienting module

Testing clienting with unit tests
"""

import pytest
from mockito import mock, patch, unstub, verify, verifyNoUnwantedInteractions, expect, ANY


def test_signify_client_defaults(make_signify_client):
    from signify.app.clienting import SignifyClient
    patch(SignifyClient, 'connect', lambda: None)
    client = make_signify_client(url='http://example.com')
    client.connect()

    assert client.bran == 'abcdefghijklmnop01234'
    assert client.pidx == 0
    from keri.core.coring import Tiers
    assert client.tier == Tiers.low
    assert client.extern_modules is None

    from signify.core.authing import Controller
    assert isinstance(client.ctrl, Controller)
    assert client.mgr is None
    assert client.session is None
    assert client.agent is None
    assert client.authn is None
    assert client.base is None

    verify(SignifyClient, times=1).connect()

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_bad_passcode_length():
    from keri import kering
    with pytest.raises(kering.ConfigurationError, match='too short'):
        from signify.app.clienting import SignifyClient
        SignifyClient(passcode='too short')

def test_signify_client_connect_no_delegation(make_signify_client, make_mock_session):
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_init_controller = mock(spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_init_controller)

    client = make_signify_client()

    import requests
    mock_session = make_mock_session()
    expect(requests, times=1).Session().thenReturn(mock_session)

    from signify.signifying import SignifyState
    mock_state = mock({'pidx': 0, 'agent': 'agent info', 'controller': 'controller info'}, spec=SignifyState, strict=True)
    expect(client, times=1).states().thenReturn(mock_state)

    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent, strict=True)
    expect(authing, times=1).Agent(state=mock_state.agent).thenReturn(mock_agent)

    from keri.core import serdering
    mock_serder = mock({'sn': 1}, spec=serdering.Serder, strict=True)
    from keri.core import signing
    mock_salter = mock(spec=signing.Salter, strict=True)
    mock_controller = mock({'pre': 'a prefix', 'salter': mock_salter, 'serder': mock_serder}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low, state=mock_state.controller).thenReturn(mock_controller)
    
    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    expect(keeping, times=1).Manager(salter=mock_salter, extern_modules=None).thenReturn(mock_manager)

    from signify.core import authing
    mock_authenticator = mock({'verify': lambda: {'hook1': 'hook1 info', 'hook2': 'hook2 info'}}, spec=authing.Authenticater, strict=True)
    expect(authing, times=1).Authenticater(agent=mock_agent, ctrl=ANY).thenReturn(mock_authenticator)

    from signify.app import clienting
    mock_signify_auth = mock(spec=clienting.SignifyAuth, strict=True)
    expect(clienting, times=1).SignifyAuth(mock_authenticator).thenReturn(mock_signify_auth)

    client.connect('http://example.com')

    assert client.pidx == mock_state.pidx
    assert client.session.auth == mock_signify_auth #type: ignore
    assert client.session.hooks == {'response': mock_authenticator.verify} #type: ignore

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_connect_delegation(make_signify_client, make_mock_session):
    # setup for client init
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_init_controller = mock(spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_init_controller)

    client = make_signify_client()

    # setup for client.connect()
    import requests
    mock_session = make_mock_session()
    expect(requests, times=1).Session().thenReturn(mock_session)

    from signify.signifying import SignifyState
    mock_state = mock({'pidx': 0, 'agent': 'agent info', 'controller': 'controller info'}, spec=SignifyState, strict=True)
    expect(client, times=1).states().thenReturn(mock_state)

    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent, strict=True)
    expect(authing, times=1).Agent(state=mock_state.agent).thenReturn(mock_agent)

    from keri.core import serdering
    mock_serder = mock({'sn': 0}, spec=serdering.Serder, strict=True)
    from keri.core import signing
    mock_salter = mock(spec=signing.Salter, strict=True)
    mock_controller = mock({'pre': 'a prefix', 'salter': mock_salter, 'serder': mock_serder}, spec=authing.Controller, strict=True)
    # when(authing.Controller).thenReturn(mock_controller)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low, state=mock_state.controller).thenReturn(mock_controller)
    
    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    expect(keeping, times=1).Manager(salter=mock_salter, extern_modules=None).thenReturn(mock_manager)

    expect(client, times=1).approveDelegation()

    from signify.core import authing
    mock_authenticator = mock({'verify': lambda: {'hook1': 'hook1 info', 'hook2': 'hook2 info'}}, spec=authing.Authenticater, strict=True)
    expect(authing, times=1).Authenticater(agent=mock_agent, ctrl=ANY).thenReturn(mock_authenticator)

    from signify.app import clienting
    mock_signify_auth = mock(spec=clienting.SignifyAuth, strict=True)
    expect(clienting, times=1).SignifyAuth(mock_authenticator).thenReturn(mock_signify_auth)

    client.connect('http://example.com')

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_connect_bad_scheme(make_signify_client):
    client = make_signify_client()

    from keri.kering import ConfigurationError
    with pytest.raises(ConfigurationError, match='invalid scheme foo for SignifyClient'):
        client.connect('foo://example.com')

def test_signify_client_connect_bad_delegation():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_init_controller = mock(spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_init_controller)
    
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    expect(requests, times=1).Session().thenReturn(mock_session)

    from signify.signifying import SignifyState
    mock_state = mock({'pidx': 0, 'agent': 'agent info', 'controller': 'controller info'}, spec=SignifyState, strict=True)
    expect(client, times=1).states().thenReturn(mock_state)

    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent, strict=True)
    expect(authing, times=1).Agent(state=mock_state.agent).thenReturn(mock_agent)

    from keri.core import serdering
    mock_serder = mock({'sn': 1}, spec=serdering.Serder, strict=True)
    from keri.core import signing
    mock_salter = mock(spec=signing.Salter, strict=True)
    mock_controller = mock({'pre': 'a different prefix', 'salter': mock_salter, 'serder': mock_serder}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low, state=mock_state.controller).thenReturn(mock_controller)
    
    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    expect(keeping, times=1).Manager(salter=mock_salter, extern_modules=None).thenReturn(mock_manager)

    from keri.kering import ConfigurationError
    with pytest.raises(ConfigurationError, match='commitment to controller AID missing in agent inception event'):
        client.connect('https://example.com')

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_approve_delegation():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)
    
    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent, strict=True)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.agent = mock_agent # type: ignore

    from keri.core import serdering
    mock_serder = mock({'ked': 'key event dictionary'}, spec=serdering.Serder, strict=True)
    signatures = ["signature 1", "signature 2"]
    expect(client.ctrl, times=1).approveDelegation(mock_agent).thenReturn((mock_serder, signatures))

    expected_data = {'ixn': 'key event dictionary', 'sigs': ['signature 1', 'signature 2']}
    expect(client, times=1).put(path="/agent/a_prefix?type=ixn", json=expected_data)

    client.approveDelegation()

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_rotate():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    expect(mock_controller, times=1).rotate(nbran="new bran", aids=["aid1", "aid2"]).thenReturn({'rotate': 'data'})

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    expect(client, times=1).put(path="/agent/a_prefix", json={'rotate': 'data'})

    client.rotate("new bran", ["aid1", "aid2"])

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_properties():
    from keri.core import serdering
    mock_serder = mock(spec=serdering.Serder, strict=True)

    from keri.core import signing
    mock_salter = mock(spec=signing.Salter, strict=True)

    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({
        'pre': 'a_prefix', 
        'serder': mock_serder, 
        'salter': mock_salter
        }, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    client.mgr = mock_manager # type: ignore

    assert client.controller == "a_prefix"
    assert client.icp == mock_serder
    assert client.salter == mock_salter
    assert client.manager == mock_manager

    verifyNoUnwantedInteractions()
    unstub()

@pytest.mark.parametrize("data,expected_pidx", [
    ({'controller': 'controller info', 'agent': 'agent info'}, 0),
    ({'controller': 'controller info', 'agent': 'agent info', 'pidx': 1}, 1),
])
def test_signify_client_states(data, expected_pidx):
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'status_code': 200}, spec=requests.Response, strict=True)
    expect(mock_session, times=1).get(url='http://example.com/agent/a_prefix').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn(data)

    states = client.states()

    assert states.controller == 'controller info'
    assert states.agent == 'agent info'
    assert states.pidx == expected_pidx

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_state_wrapper(make_signify_client):
    client = make_signify_client()
    expect(client, times=1).states().thenReturn("state bundle")

    assert client.state() == "state bundle"

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_states_agent_error():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'status_code': 404}, spec=requests.Response, strict=True)
    expect(mock_session, times=1).get(url='http://example.com/agent/a_prefix').thenReturn(mock_response)

    from keri import kering
    with pytest.raises(kering.ConfigurationError, match='agent does not exist for controller a_prefix'):
        client.states()

    unstub()
    verifyNoUnwantedInteractions()

@pytest.mark.parametrize("status_code,expected", [
    (200, False), 
    (204, True), 
    (500, False), 
    (400, False),
])
def test_signify_client_save_old_salt(status_code, expected):
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    
    import requests
    mock_response = mock({'status_code': status_code}, spec=requests.Response, strict=True)

    expected_data = {'salt': 'salty'}
    expect(client, times=1).put('/salt/a_prefix', json=expected_data).thenReturn(mock_response)
    
    assert client._save_old_salt("salty") == expected

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_save_old_passcode(make_signify_client):
    client = make_signify_client()
    expect(client, times=1)._save_old_salt("salty").thenReturn(True)

    assert client.saveOldPasscode("salty") is True

    verifyNoUnwantedInteractions()
    unstub()

@pytest.mark.parametrize("status_code,expected", [
    (200, False), 
    (204, True), 
    (500, False), 
    (400, False),
])
def test_signify_client_delete_old_salt(status_code, expected):
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    
    import requests
    mock_response = mock({'status_code': status_code}, spec=requests.Response, strict=True)

    expect(client, times=1).delete('/salt/a_prefix').thenReturn(mock_response)
    
    assert client._delete_old_salt() == expected

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_delete_passcode(make_signify_client):
    client = make_signify_client()
    expect(client, times=1)._delete_old_salt().thenReturn(True)

    assert client.deletePasscode() is True

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_get():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': True}, spec=requests.Response, strict=True)
    expect(mock_session).get('http://example.com/my_path', params={'a': 'param'}, headers={'a': 'header'}, json={'a': 'body'}).thenReturn(mock_response)

    out = client.get('my_path', params={'a': 'param'}, headers={'a': 'header'}, body={'a': 'body'})
    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_fetch_get(make_signify_client, make_mock_response):
    client = make_signify_client()
    mock_response = make_mock_response()
    expect(client, times=1)._request("GET", "/contacts", headers={"a": "header"}, json=None).thenReturn(mock_response)

    out = client.fetch("/contacts", "GET", {"ignored": True}, headers={"a": "header"})

    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_fetch_post(make_signify_client, make_mock_response):
    client = make_signify_client()
    mock_response = make_mock_response()
    expect(client, times=1)._request("POST", "/contacts", headers={"a": "header"}, json={"foo": "bar"}).thenReturn(mock_response)

    out = client.fetch("/contacts", "POST", {"foo": "bar"}, headers={"a": "header"})

    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_get_not_ok():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': False}, spec=requests.Response, strict=True)
    from mockito import kwargs
    expect(mock_session).get('http://example.com/my_path', **kwargs).thenReturn(mock_response)

    expect(client, times=1).raiseForStatus(mock_response)
    client.get('my_path', params={'a': 'param'}, headers={'a': 'header'}, body={'a': 'body'})

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_stream():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    from mockito import kwargs
    import sseclient
    expect(sseclient, times=1).SSEClient('http://example.com/my_path', session=mock_session, **kwargs).thenReturn([])

    # probably a cleaner way to do this
    with pytest.raises(StopIteration):
        next(client.stream('my_path', params={'a': 'param'}, headers={'a': 'header'}, body={'a': 'body'}))

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_delete():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': True}, spec=requests.Response, strict=True)
    expect(mock_session).delete('http://example.com/my_path', params={'a': 'param'}, headers={'a': 'header'}).thenReturn(mock_response)

    out = client.delete('my_path', params={'a': 'param'}, headers={'a': 'header'})
    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_delete_not_ok():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session  # type: ignore

    mock_response = mock({'ok': False}, spec=requests.Response, strict=True)
    from mockito import kwargs
    expect(mock_session).delete('http://example.com/my_path', **kwargs).thenReturn(mock_response)

    expect(client, times=1).raiseForStatus(mock_response)
    client.delete('my_path', params={'a': 'param'}, headers={'a': 'header'})

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_post():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': True}, spec=requests.Response, strict=True)
    expect(mock_session).post('http://example.com/my_path', json={'a': 'json'}, params={'a': 'param'}, headers={'a': 'header'}).thenReturn(mock_response)

    json = {'a': 'json'}
    out = client.post('my_path', json, params={'a': 'param'}, headers={'a': 'header'})
    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_post_not_ok():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': False}, spec=requests.Response, strict=True)
    from mockito import kwargs
    expect(mock_session).post('http://example.com/my_path', **kwargs).thenReturn(mock_response)
    expect(client, times=1).raiseForStatus(mock_response)

    json = {'a': 'json'}
    client.post('my_path', json, params={'a': 'param'}, headers={'a': 'header'})

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_put():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': True}, spec=requests.Response, strict=True)
    expect(mock_session).put('http://example.com/my_path', json={'a': 'json'}, params={'a': 'param'}, headers={'a': 'header'}).thenReturn(mock_response)

    json = {'a': 'json'}
    out = client.put('my_path', json, params={'a': 'param'}, headers={'a': 'header'})
    assert out == mock_response

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_put_not_ok():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_controller = mock({'pre': 'a_prefix'}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.base = 'http://example.com'

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    client.session = mock_session # type: ignore

    mock_response = mock({'ok': False}, spec=requests.Response, strict=True)
    from mockito import kwargs
    expect(mock_session).put('http://example.com/my_path', **kwargs).thenReturn(mock_response)
    expect(client, times=1).raiseForStatus(mock_response)

    json = {'a': 'json'}
    client.put('my_path', json, params={'a': 'param'}, headers={'a': 'header'})

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_identifiers(make_signify_client):
    client = make_signify_client()

    out = client.identifiers()

    from signify.app.aiding import Identifiers
    assert type(out) is Identifiers
    assert out.client == client

def test_signify_client_operations(make_signify_client):
    client = make_signify_client()

    out = client.operations()

    from signify.app.coring import Operations
    assert type(out) is Operations
    assert out.client == client

def test_signify_client_oobis(make_signify_client):
    client = make_signify_client()

    out = client.oobis()

    from signify.app.coring import Oobis
    assert type(out) is Oobis
    assert out.client == client

def test_signify_client_credentials(make_signify_client):
    client = make_signify_client()

    out = client.credentials()

    from signify.app.credentialing import Credentials
    assert type(out) is Credentials
    assert out.client == client

def test_signify_client_key_states(make_signify_client):
    client = make_signify_client()

    out = client.keyStates()

    from signify.app.coring import KeyStates
    assert type(out) is KeyStates
    assert out.client == client

def test_signify_client_key_events(make_signify_client):
    client = make_signify_client()

    out = client.keyEvents()

    from signify.app.coring import KeyEvents
    assert type(out) is KeyEvents
    assert out.client == client


def test_signify_client_escrows(make_signify_client):
    client = make_signify_client()

    out = client.escrows()

    from signify.app.escrowing import Escrows
    assert type(out) is Escrows
    assert out.client == client


def test_signify_client_endroles(make_signify_client):
    client = make_signify_client()

    out = client.endroles()

    from signify.app.ending import EndRoleAuthorizations
    assert type(out) is EndRoleAuthorizations
    assert out.client == client


def test_signify_client_notifications(make_signify_client):
    client = make_signify_client()

    out = client.notifications()

    from signify.app.notifying import Notifications
    assert type(out) is Notifications
    assert out.client == client


def test_signify_client_groups(make_signify_client):
    client = make_signify_client()

    out = client.groups()

    from signify.app.grouping import Groups
    assert type(out) is Groups
    assert out.client == client


def test_signify_client_delegations(make_signify_client):
    # The accessor test is small on purpose: parity is the point. If this
    # resource lookup disappears, the integration suite falls back toward raw
    # HTTP instead of exercising the real client surface.
    client = make_signify_client()

    out = client.delegations()

    from signify.app.delegating import Delegations
    assert type(out) is Delegations
    assert out.client == client


def test_signify_client_registries(make_signify_client):
    client = make_signify_client()

    out = client.registries()

    from signify.app.credentialing import Registries
    assert type(out) is Registries
    assert out.client == client


def test_signify_client_schemas(make_signify_client):
    client = make_signify_client()

    out = client.schemas()

    from signify.app.schemas import Schemas
    assert type(out) is Schemas
    assert out.client == client


def test_signify_client_config(make_signify_client):
    client = make_signify_client()

    out = client.config()

    from signify.app.coring import Config
    assert type(out) is Config
    assert out.client == client


def test_signify_client_exchanges(make_signify_client):
    client = make_signify_client()

    out = client.exchanges()

    from signify.app.exchanging import Exchanges
    assert type(out) is Exchanges
    assert out.client == client


def test_signify_client_create_signed_request(mockHelpingNowIso8601):
    import requests
    from keri.app.keeping import Algos
    from keri.core import eventing
    from keri.end import ending
    from signify.app.clienting import SignifyClient
    from signify.core import keeping

    client = SignifyClient(passcode='abcdefghijklmnop01234')
    client.mgr = keeping.Manager(salter=client.ctrl.salter)

    keeper = client.manager.new(Algos.salty, 0, bran='0123456789abcdefghijk')
    keys, ndigs = keeper.incept(transferable=True)
    signer = keeper.signers()[0]
    serder = eventing.incept(keys=keys, isith='1', nsith='1', ndigs=ndigs, code='E', wits=[], toad='0', cnfg=[], data=[])
    hab = {
        'prefix': serder.pre,
        'state': {'k': keys, 'n': ndigs},
        'salty': keeper.params(),
    }

    mock_identifiers = mock(strict=True)
    expect(client, times=1).identifiers().thenReturn(mock_identifiers)
    expect(mock_identifiers, times=1).get('aid1').thenReturn(hab)

    prepared = client.createSignedRequest(
        'aid1',
        'http://example.com/test',
        {
            'method': 'POST',
            'headers': {'Content-Type': 'application/json'},
            'body': '{"foo": true}',
        },
    )

    assert isinstance(prepared, requests.PreparedRequest)
    assert prepared.url == 'http://example.com/test'
    assert prepared.method == 'POST'
    assert prepared.body == '{"foo": true}'
    assert prepared.headers['Signify-Resource'] == hab['prefix']
    assert prepared.headers['Signify-Timestamp'] == '2021-06-27T21:26:21.233257+00:00'
    assert 'Signature-Input' in prepared.headers
    assert 'Signature' in prepared.headers
    assert f'keyid="{signer.verfer.qb64}"' in prepared.headers['Signature-Input']
    assert 'alg="ed25519"' in prepared.headers['Signature-Input']

    inputage = ending.desiginput(prepared.headers['Signature-Input'].encode('utf-8'))[0]
    items = []
    for field in inputage.fields:
        if field == '@method':
            items.append(f'"{field}": {prepared.method}')
        elif field == '@path':
            items.append(f'"{field}": /test')
        else:
            items.append(f'"{field}": {ending.normalize(prepared.headers[field.upper()])}')

    values = [f"({' '.join(inputage.fields)})", f"created={inputage.created}"]
    if inputage.keyid is not None:
        values.append(f"keyid={inputage.keyid}")
    if inputage.alg is not None:
        values.append(f"alg={inputage.alg}")
    items.append(f'"@signature-params: {";".join(values)}"')

    signature = ending.designature(prepared.headers['Signature'])[0].markers[inputage.name]
    assert signer.verfer.verify(sig=signature.raw, ser="\n".join(items).encode("utf-8"))

    unstub()
    verifyNoUnwantedInteractions()


@pytest.mark.parametrize("resp,err", [
    ({'json': lambda : {'description': {'raise a description'}}, 'status_code': 400, 'url': 'http://example.com'}, "400 Client Error: {'raise a description'} for url: http://example.com"),
    ({'json': lambda : {'title': {'raise a title'}}, 'status_code': 400, 'url': 'http://example.com'}, "400 Client Error: {'raise a title'} for url: http://example.com"),
    ({'json': lambda : {'unknown': {'raise unknown'}}, 'status_code': 400, 'url': 'http://example.com'}, "400 Client Error: Unknown for url: http://example.com"),
    ({'json': lambda : {'description': {'raise a description'}}, 'status_code': 500, 'url': 'http://example.com'}, "500 Server Error: {'raise a description'} for url: http://example.com"),
    ({'json': lambda : {'title': {'raise a title'}}, 'status_code': 500, 'url': 'http://example.com'}, "500 Server Error: {'raise a title'} for url: http://example.com"),
    ({'json': lambda : {'unknown': {'raise unknown'}}, 'status_code': 500, 'url': 'http://example.com'}, "500 Server Error: Unknown for url: http://example.com"),
    ({'text': 'a text error', 'status_code': 400, 'url': 'http://example.com'}, "400 Client Error: a text error for url: http://example.com"),
    ({'text': 'a text error', 'status_code': 500, 'url': 'http://example.com'}, "500 Server Error: a text error for url: http://example.com"),
])
def test_signify_client_raise_for_status(resp, err):
    import requests
    mock_response = mock(resp, spec=requests.Response)

    from signify.app.clienting import SignifyClient

    with pytest.raises(requests.HTTPError, match=err):
        SignifyClient.raiseForStatus(mock_response)

    unstub()
    verifyNoUnwantedInteractions()

def test_signify_auth():
    from signify.core import authing
    mock_agent = mock(spec=authing.Agent, strict=True)
    mock_controller = mock({'pre': 'a prefix'}, spec=authing.Controller, strict=True)

    from signify.core import authing
    mock_authenticator = mock({'ctrl': mock_controller}, spec=authing.Authenticater, strict=True)
    expect(authing, times=1).Authenticater(agent=mock_agent, ctrl=mock_controller).thenReturn(mock_authenticator)

    from signify.app.clienting import SignifyAuth
    signify_auth = SignifyAuth(mock_authenticator)

    import requests
    mock_request = mock({'method': 'GET', 'url': 'http://example.com/my_path', 'headers': {}, 'body': "a body for len"}, spec=requests.Request, strict=True)

    from keri.help import helping
    expect(helping).nowIso8601().thenReturn('now ISO8601!')

    expected_headers = {
        'Signify-Resource': 'a prefix',
        'Signify-Timestamp': 'now ISO8601!',
        'Content-Length': 11
    }
    expect(mock_authenticator, times=1).sign({'Signify-Resource': 'a prefix', 'Signify-Timestamp': 'now ISO8601!', 'Content-Length': 14}, 'GET', '/my_path').thenReturn({'headers': 'modified'})

    out = signify_auth.__call__(mock_request)
    assert out.headers == {'headers': 'modified'}

    unstub()
    verifyNoUnwantedInteractions()
