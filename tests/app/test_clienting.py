
from mockito import mock, patch, unstub, verify, verifyNoUnwantedInteractions, expect, expect, when
import pytest

def test_signify_client_defaults():
    from signify.app.clienting import SignifyClient
    patch(SignifyClient, 'connect', lambda str: None)
    client = SignifyClient(passcode='abcdefghijklmnop01234', url='http://example.com')

    assert client.bran == 'abcdefghijklmnop01234'
    assert client.pidx == 0
    from keri.core.coring import Tiers
    assert client.tier == Tiers.low
    assert client.extern_modules == None

    from signify.core.authing import Controller
    assert isinstance(client.ctrl, Controller)
    assert client.mgr == None
    assert client.session == None
    assert client.agent == None
    assert client.authn == None
    assert client.base == None

    verify(SignifyClient, times=1).connect('http://example.com')

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_bad_passcode_length():
    from keri import kering
    with pytest.raises(kering.ConfigurationError, match='too short'):
        from signify.app.clienting import SignifyClient
        SignifyClient(passcode='too short')

def test_signify_client_connect_no_delegation():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_init_controller = mock(spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_init_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    expect(requests, times=1).Session().thenReturn(mock_session)

    from signify.signifying import State
    mock_state = mock({'pidx': 0, 'agent': 'agent info', 'controller': 'controller info'}, spec=State, strict=True)
    expect(client, times=1).states().thenReturn(mock_state)

    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent, strict=True)
    expect(authing, times=1).Agent(state=mock_state.agent).thenReturn(mock_agent)

    from keri.core import serdering
    mock_serder = mock({'sn': 1}, spec=serdering.Serder, strict=True)
    from keri.core import coring
    mock_salter = mock(spec=coring.Salter, strict=True)
    mock_controller = mock({'pre': 'a prefix', 'salter': mock_salter, 'serder': mock_serder}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low, state=mock_state.controller).thenReturn(mock_controller)
    
    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    expect(keeping, times=1).Manager(salter=mock_salter, extern_modules=None).thenReturn(mock_manager)

    from signify.core import authing
    mock_authenticator = mock({'verify': lambda: {'hook1': 'hook1 info', 'hook2': 'hook2 info'}}, spec=authing.Authenticater, strict=True)
    expect(authing, times=1).Authenticater(agent=mock_agent, ctrl=mock_controller).thenReturn(mock_authenticator)

    from signify.app import clienting
    mock_signify_auth = mock(spec=clienting.SignifyAuth, strict=True)
    expect(clienting, times=1).SignifyAuth(mock_authenticator).thenReturn(mock_signify_auth)

    client.connect('http://example.com')

    assert client.pidx == mock_state.pidx
    assert client.session.auth == mock_signify_auth #type: ignore
    assert client.session.hooks == {'response': mock_authenticator.verify} #type: ignore

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_connect_delegation():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_init_controller = mock(spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_init_controller)

    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    import requests
    mock_session = mock(spec=requests.Session, strict=True)
    expect(requests, times=1).Session().thenReturn(mock_session)

    from signify.signifying import State
    mock_state = mock({'pidx': 0, 'agent': 'agent info', 'controller': 'controller info'}, spec=State, strict=True)
    expect(client, times=1).states().thenReturn(mock_state)

    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent, strict=True)
    expect(authing, times=1).Agent(state=mock_state.agent).thenReturn(mock_agent)

    from keri.core import serdering
    mock_serder = mock({'sn': 0}, spec=serdering.Serder, strict=True)
    from keri.core import coring
    mock_salter = mock(spec=coring.Salter, strict=True)
    mock_controller = mock({'pre': 'a prefix', 'salter': mock_salter, 'serder': mock_serder}, spec=authing.Controller, strict=True)
    expect(authing, times=1).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low, state=mock_state.controller).thenReturn(mock_controller)
    
    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    expect(keeping, times=1).Manager(salter=mock_salter, extern_modules=None).thenReturn(mock_manager)

    expect(client, times=1).approveDelegation()

    from signify.core import authing
    mock_authenticator = mock({'verify': lambda: {'hook1': 'hook1 info', 'hook2': 'hook2 info'}}, spec=authing.Authenticater, strict=True)
    expect(authing, times=1).Authenticater(agent=mock_agent, ctrl=mock_controller).thenReturn(mock_authenticator)

    from signify.app import clienting
    mock_signify_auth = mock(spec=clienting.SignifyAuth, strict=True)
    expect(clienting, times=1).SignifyAuth(mock_authenticator).thenReturn(mock_signify_auth)

    client.connect('http://example.com')

    verifyNoUnwantedInteractions()
    unstub()

def test_signify_client_connect_bad_scheme():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    from keri.kering import ConfigurationError
    with pytest.raises(ConfigurationError, match='invalid scheme foo for SignifyClient'):
        client.connect('foo://example.com')

def test_signify_client_connect_bad_delegation():
    from signify.core import authing
    from keri.core.coring import Tiers
    mock_init_controller = mock(spec=authing.Controller)
    when(authing).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low).thenReturn(mock_init_controller)
    
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    import requests
    mock_session = mock(spec=requests.Session)
    when(requests).Session().thenReturn(mock_session)

    from signify.signifying import State
    mock_state = mock({'pidx': 0, 'agent': 'agent info', 'controller': 'controller info'}, spec=State)
    when(client).states().thenReturn(mock_state)

    from signify.core import authing
    mock_agent = mock({'delpre': 'a prefix'}, spec=authing.Agent)
    when(authing).Agent(state=mock_state.agent).thenReturn(mock_agent)

    from keri.core import serdering
    mock_serder = mock({'sn': 1}, spec=serdering.Serder)
    from keri.core import coring
    mock_salter = mock(spec=coring.Salter)
    mock_controller = mock({'pre': 'a different prefix', 'salter': mock_salter, 'serder': mock_serder}, spec=authing.Controller)
    when(authing).Controller(bran='abcdefghijklmnop01234', tier=Tiers.low, state=mock_state.controller).thenReturn(mock_controller)
    
    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    when(keeping).Manager(salter=mock_salter, extern_modules=None).thenReturn(mock_manager)

    from signify.core import authing
    mock_authenticator = mock({'verify': lambda: {'hook1': 'hook1 info', 'hook2': 'hook2 info'}}, spec=authing.Authenticater)
    when(authing).Authenticater(agent=mock_agent, ctrl=mock_controller).thenReturn(mock_authenticator)

    from signify.app import clienting
    mock_signify_auth = mock(spec=clienting.SignifyAuth)
    when(clienting).SignifyAuth(mock_authenticator).thenReturn(mock_signify_auth)

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

    from keri.core import coring
    mock_salter = mock(spec=coring.Salter, strict=True)

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
    when(mock_session).get(url='http://example.com/agent/a_prefix').thenReturn(mock_response)

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
    from mockito import kwargs
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
    client.session = mock_session # type: ignore

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

def test_signify_client_identfiers():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.identifiers()

    from signify.app.aiding import Identifiers
    assert type(out) is Identifiers
    assert out.client == client

def test_signify_client_operations():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.operations()

    from signify.app.coring import Operations
    assert type(out) is Operations
    assert out.client == client

def test_signify_client_oobis():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.oobis()

    from signify.app.coring import Oobis
    assert type(out) is Oobis
    assert out.client == client

def test_signify_client_credentials():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.credentials()

    from signify.app.credentialing import Credentials
    assert type(out) is Credentials
    assert out.client == client

def test_signify_client_key_states():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.keyStates()

    from signify.app.coring import KeyStates
    assert type(out) is KeyStates
    assert out.client == client

def test_signify_client_key_events():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.keyEvents()

    from signify.app.coring import KeyEvents
    assert type(out) is KeyEvents
    assert out.client == client

def test_signify_client_escrows():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.escrows()

    from signify.app.escrowing import Escrows
    assert type(out) is Escrows
    assert out.client == client

def test_signify_client_endroles():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    out = client.endroles()

    from signify.app.ending import EndRoleAuthorizations
    assert type(out) is EndRoleAuthorizations
    assert out.client == client


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
