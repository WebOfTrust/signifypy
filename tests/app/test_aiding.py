# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_aiding module

Testing aiding with unit tests
"""

import pytest
from mockito import mock, verify, verifyNoUnwantedInteractions, when, unstub, expect


def test_aiding_list():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock({'headers': {'content-range': 'aids 0-10/2'}}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/identifiers', headers=dict(Range=f"aids={0}-{24}")).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        ['aid1', 'aid2']
    )

    out = ids.list()
    assert out['start'] == 0
    assert out['end'] == 10
    assert out['total'] == 2
    assert out['aids'] == ['aid1', 'aid2']

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_get():
    from signify.app.clienting import SignifyClient
    client = SignifyClient(passcode='abcdefghijklmnop01234')

    from signify.app.aiding import Identifiers
    id = Identifiers(client=client)

    from requests import Response
    mock_response = mock(spec=Response, strict=True)

    expect(client, times=1).get('/identifiers/aid1').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'name': 'aid1'})

    out = id.get(name='aid1')

    assert out['name'] == 'aid1'

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_create():
    from signify.core import keeping
    mock_keeper = mock({'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    mock_manager = mock(spec=keeping.Manager, strict=True)

    from mockito import kwargs
    expect(mock_manager, times=1).new('salty', 0, **kwargs).thenReturn(mock_keeper)

    keys = ['a signer verfer qb64']
    ndigs = ['next signer digest']

    expect(mock_keeper, times=1).incept(transferable=True).thenReturn((keys, ndigs))

    from keri.core import coring
    mock_serder = mock({'raw': b'raw bytes', 'ked': {'a': 'key event dictionary'}}, spec=coring.Serder, strict=True)

    from keri.core import eventing
    expect(eventing, times=1).incept(keys=keys, isith='1', nsith='1', ndigs=ndigs, code='E', wits=[], toad='0', data=[]).thenReturn(mock_serder)
    expect(mock_keeper, times=1).sign(mock_serder.raw).thenReturn(['a signature'])

    from signify.app.clienting import SignifyClient
    mock_client = mock({'pidx': 0}, spec=SignifyClient, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    from requests import Response
    resp = mock({'json': lambda: {'post': 'success'}}, spec=Response, strict=True)
    expect(mock_client, times=1).post('/identifiers', json={'name': 'new_aid', 'icp': {'a': 'key event dictionary'},
                                                 'sigs': ['a signature'], 'proxy': None, 'salty': {'keeper': 'params'},
                                                 'smids': ['a smid'], 'rmids': ['a rmid']}).thenReturn(resp)

    ids.create(name='new_aid', states=[{'i': 'a smid'}], rstates=[{'i': 'a rmid'}])


    assert mock_client.pidx == 1

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_create_delegation():
    from signify.core import keeping
    mock_keeper = mock({'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    mock_manager = mock(spec=keeping.Manager, strict=True)

    from mockito import kwargs
    expect(mock_manager, times=1).new('salty', 0, **kwargs).thenReturn(mock_keeper)

    keys = ['a signer verfer qb64']
    ndigs = ['next signer digest']

    expect(mock_keeper, times=1).incept(transferable=True).thenReturn((keys, ndigs))

    from keri.core import coring
    mock_serder = mock({'raw': b'raw bytes', 'ked': {'a': 'key event dictionary'}}, spec=coring.Serder, strict=True)

    from keri.core import eventing
    expect(eventing, times=1).delcept(keys=['a signer verfer qb64'], delpre='my delegation', isith='1', nsith='1',
                           ndigs=['next signer digest'], code='E', wits=[], toad='0', data=[]).thenReturn(mock_serder)
    expect(mock_keeper, times=1).sign(mock_serder.raw).thenReturn(['a signature'])

    from signify.app.clienting import SignifyClient
    mock_client = mock({'pidx': 0}, spec=SignifyClient, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    from requests import Response
    resp = mock({'json': lambda: {'post': 'success'}}, spec=Response, strict=True)
    expect(mock_client, times=1).post('/identifiers',
                           json={'name': 'new_aid', 'icp': {'a': 'key event dictionary'}, 'sigs': ['a signature'],
                                 'proxy': None, 'salty': {'keeper': 'params'}, 'smids': ['a smid'],
                                 'rmids': ['a rmid']}).thenReturn(resp)

    ids.create(name='new_aid', delpre='my delegation', states=[{'i': 'a smid'}], rstates=[{'i': 'a rmid'}])

    assert mock_client.pidx == 1

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_update_interact():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore
    expect(ids, times=1).interact('aid1')

    ids.update(name='aid1', typ='interact')

    verify(ids).interact('aid1')

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_update_rotate():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore
    expect(ids, times=1).rotate('aid1')

    ids.update(name='aid1', typ='rotate')

    verify(ids).rotate('aid1')

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_update_bad():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    from keri import kering
    with pytest.raises(kering.KeriError):
        ids.update(name='aid1', typ='basil')

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_delete():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    ids.delete(name='aid1')

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_interact_no_data():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    mock_hab = {'prefix': 'hab prefix', 'name': 'aid1', 'state': {'s': '0', 'd': 'hab digest'}}
    expect(ids, times=1).get('aid1').thenReturn(mock_hab)

    from keri.core import eventing, coring
    mock_serder = mock({'ked': {'a': 'key event dictionary'}, 'raw': b'serder raw bytes'}, spec=coring.Serder, strict=True)
    expect(eventing, times=1).interact('hab prefix', sn=1, data=[None], dig='hab digest').thenReturn(mock_serder)

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=mock_serder.raw).thenReturn(['a signature'])

    expected_data = {
        'ixn': {'a': 'key event dictionary'},
        'sigs': ['a signature'],
        'salty': {'keeper': 'params'}
    }
    from requests import Response
    mock_response = mock({'json': lambda: {'success': 'yay'}}, spec=Response, strict=True)
    expect(mock_client, times=1).put('/identifiers/aid1?type=ixn', json=expected_data).thenReturn(mock_response)

    ids.interact(name='aid1')

    verify(ids).get('aid1')

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_interact_with_data():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    mock_hab = {'prefix': 'hab prefix', 'name': 'aid1', 'state': {'s': '0', 'd': 'hab digest'}}
    expect(ids, times=1).get('aid1').thenReturn(mock_hab)

    from keri.core import eventing, coring
    mock_serder = mock({'ked': {'a': 'key event dictionary'}, 'raw': b'serder raw bytes'}, spec=coring.Serder, strict=True)
    expect(eventing, times=1).interact('hab prefix', sn=1, data=[{'some': 'data'}, {'some': 'more'}], dig='hab digest').thenReturn(
        mock_serder)

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=mock_serder.raw).thenReturn(['a signature'])

    expected_data = {
        'ixn': {'a': 'key event dictionary'},
        'sigs': ['a signature'],
        'salty': {'keeper': 'params'}
    }

    from requests import Response
    mock_response = mock({'json': lambda: {'success': 'yay'}}, spec=Response, strict=True)
    expect(mock_client, times=1).put('/identifiers/aid1?type=ixn', json=expected_data).thenReturn(mock_response)

    ids.interact(name='aid1', data=[{'some': 'data'}, {'some': 'more'}])

    verify(ids).get('aid1')

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_rotate():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    mock_hab = {'prefix': 'hab prefix', 'name': 'aid1',
                'state': {'s': '0', 'd': 'hab digest', 'b': ['wit1', 'wit2', 'wit3'], 'k': ['key1']}}
    expect(ids, times=1).get('aid1').thenReturn(mock_hab)

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(mock_hab).thenReturn(mock_keeper)

    keys = ['key1']
    ndigs = ['ndig1']
    expect(mock_keeper, times=1).rotate(ncodes=['A'], transferable=True, states=[{'i': 'state 1'}, {'i': 'state 2'}],
                             rstates=[{'i': 'rstate 1'}, {'i': 'rstate 2'}]).thenReturn((keys, ndigs))

    from keri.core import coring
    mock_serder = mock({'ked': {'a': 'key event dictionary'}, 'raw': b'serder raw bytes'}, spec=coring.Serder, strict=True)

    from keri.core import eventing
    expect(eventing, times=1).rotate(pre='hab prefix', keys=['key1'], dig='hab digest', sn=1, isith='1', nsith='1',
                          ndigs=['ndig1'], toad=None, wits=['wit1', 'wit2', 'wit3'],
                          cuts=[], adds=[], data=[]).thenReturn(mock_serder)

    expect(mock_keeper, times=1).sign(ser=mock_serder.raw).thenReturn(['a signature'])

    from requests import Response
    mock_response = mock(spec=Response, strict=True)
    expected_data = {'rot': {'a': 'key event dictionary'}, 'sigs': ['a signature'], 'salty': {'keeper': 'params'},
                     'smids': ['state 1', 'state 2'], 'rmids': ['rstate 1', 'rstate 2']}
    expect(mock_client, times=1).put('/identifiers/aid1', json=expected_data).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'success': 'yay'})

    out = ids.rotate(name='aid1', states=[{'i': 'state 1'}, {'i': 'state 2'}],
                     rstates=[{'i': 'rstate 1'}, {'i': 'rstate 2'}])
    assert out['success'] == 'yay'

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_add_end_role():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    mock_hab = {'prefix': 'hab prefix', 'name': 'aid1'}
    expect(ids, times=1).get('aid1').thenReturn(mock_hab)

    from keri.core import coring
    mock_serder = mock({'ked': {'a': 'key event dictionary'}, 'raw': b'serder raw bytes'}, spec=coring.Serder, strict=True)
    expect(ids, times=1).makeEndRole('hab prefix', 'agent', None, None).thenReturn(mock_serder)

    from signify.core import keeping
    mock_keeper = mock({'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=mock_serder.raw).thenReturn(['a signature'])

    from requests import Response
    mock_response = mock(spec=Response, strict=True)
    expected_data = {'rpy': {'a': 'key event dictionary'}, 'sigs': ['a signature']}
    expect(mock_client, times=1).post('/identifiers/aid1/endroles', json=expected_data).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'success': 'yay'})

    out = ids.addEndRole('aid1')
    assert out['success'] == 'yay'

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_sign():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager # type: ignore

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    from keri.core import coring
    mock_serder = mock({'ked': {'a': 'key event dictionary'}, 'raw': b'serder raw bytes'}, spec=coring.Serder, strict=True)

    mock_hab = {'prefix': 'hab prefix', 'name': 'aid1'}
    expect(ids, times=1).get('aid1').thenReturn(mock_hab)

    from signify.core import keeping
    mock_keeper = mock({'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(aid=mock_hab).thenReturn(mock_keeper)

    expect(mock_keeper, times=1).sign(ser=mock_serder.raw).thenReturn(['signature 1', 'signature 2'])

    out = ids.sign('aid1', mock_serder)

    assert out == ['signature 1', 'signature 2']

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_member():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.aiding import Identifiers
    ids = Identifiers(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock(spec=Response, strict=True)
    expect(mock_client, times=1).get('/identifiers/aid1/members').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'success': 'yay'})

    out = ids.members('aid1')

    assert out['success'] == 'yay'

    verifyNoUnwantedInteractions()
    unstub()


def test_aiding_make_end_role():
    expected_data = {'cid': 'a prefix', 'role': 'witness', 'eid': 'an eid'}

    from keri.core import eventing
    expect(eventing, times=1).reply(route='/end/role/add', data=expected_data, stamp='a timestamp')

    from signify.app.aiding import Identifiers
    Identifiers.makeEndRole('a prefix', role='witness', eid='an eid', stamp='a timestamp')

    verifyNoUnwantedInteractions()
    unstub()
