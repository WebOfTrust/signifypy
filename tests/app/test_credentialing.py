# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_credentialing module

Testing credentialing with unit tests
"""
from keri.peer import exchanging
from keri.vdr import eventing as veventing
from keri.core import eventing
from mockito import mock, unstub, verify, verifyNoUnwantedInteractions, expect, ANY

from signify.app import credentialing


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

    registries = Registries(client=mock_client)
    registries.create(hab=mock_hab, registryName=regName)

    expect(mock_client, times=1).get(f"/identifiers/{name}/registries/{regName}").thenReturn(mock_response)
    registries.get(name="aid1", registryName=regName)

    pre = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    dig = "EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0"
    nonce = "ACb_3pGwW3uIjtOg4zRQ66I-SggMcmoyju_uCzuSvgG4"
    serder = veventing.incept(pre=pre, nonce=nonce)
    anc = eventing.interact(pre=pre, dig=dig)

    msg = Registries.serialize(serder, anc)
    assert msg == (b'{"v":"KERI10JSON00010f_","t":"vcp","d":"EGaypC6sODRFyIuhdFzzFmBU'
                   b'4Xe5SNprALGbltnyHYSz","i":"EGaypC6sODRFyIuhdFzzFmBU4Xe5SNprALGbl'
                   b'tnyHYSz","ii":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s"'
                   b':"0","c":[],"bt":"0","b":[],"n":"ACb_3pGwW3uIjtOg4zRQ66I-SggMcmo'
                   b'yju_uCzuSvgG4"}-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAABENns5-voIbnRMADUO'
                   b'so7HDiQ9ZS_AfU8BfgGLHEW54H1')

    unstub()


def test_credentials_list():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_response = mock({'json': lambda: {}}, spec=Response, strict=True)
    expect(mock_client, times=1).post('/credentials/query',
                                      json={'filter': {'genre': 'horror'},
                                            'sort': ['updside down'], 'skip': 10, 'limt': 10}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    Credentials(client=mock_client).list(filtr={'genre': 'horror'}, sort=['updside down'], skip=10,
                                         limit=10)  # type: ignore

    verify(mock_response, times=1).json()

    verifyNoUnwantedInteractions()
    unstub()


def test_credentials_export():
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


def test_credentials_create():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager  # type: ignore

    mock_hab = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_registry = {'regk': "a_regk", 'pre': 'a_prefix', 'state': {'c': ['NB']}}
    data = dict(dt="2023-09-27T16:27:14.376928+00:00", LEI="ABC1234567890AD4456")
    schema = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
    recp = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=2).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])
    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_response, times=1).json().thenReturn({'v': 'ACDC10JSON00014c_'})

    body = {'acdc': {'v': 'ACDC10JSON00014c_', 'd': 'EPXTb9qRHquoEey-QsF-8Sks8nDoXBK6kdlP1G6WynJ3', 'i': 'a_prefix',
                     'ri': 'a_regk', 's': 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                     'a': {'d': 'EHpwssa6tmD2U5W7-aogym-r1NobKBNXydP4MmaebA4O',
                           'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                           'dt': '2023-09-27T16:27:14.376928+00:00', 'LEI': 'ABC1234567890AD4456'}},
            'iss': {'v': 'KERI10JSON0000c7_', 't': 'iss', 'd': 'EKRg7i8jS4O6BYUYiQG7X8YiMYdDXdw28tJRhFndCdGF',
                    'i': 'EPXTb9qRHquoEey-QsF-8Sks8nDoXBK6kdlP1G6WynJ3', 's': '0', 'ri': 'a_regk',
                    'dt': '2023-09-27T16:27:14.376928+00:00'},
            'ixn': {'v': 'KERI10JSON0000f1_', 't': 'ixn', 'd': 'EJM1yhn99LOgCPRsEqpg8nKXQjkSE4-Q4dfvF3wm1Waz',
                    'i': 'a_prefix', 's': '2', 'p': 'ABCDEFG', 'a': [
                    {'i': 'EPXTb9qRHquoEey-QsF-8Sks8nDoXBK6kdlP1G6WynJ3', 's': '0',
                     'd': 'EKRg7i8jS4O6BYUYiQG7X8YiMYdDXdw28tJRhFndCdGF'}]}, 'sigs': ['a signature'],
            'salty': {'keeper': 'params'}}

    expect(mock_client, times=1).post(f"/identifiers/aid1/credentials", json=body).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    creder, iss, ixn, sigs, op = Credentials(client=mock_client).create(mock_hab, mock_registry, data, schema, recp)

    assert creder.said == "EPXTb9qRHquoEey-QsF-8Sks8nDoXBK6kdlP1G6WynJ3"
    assert iss.said == "EKRg7i8jS4O6BYUYiQG7X8YiMYdDXdw28tJRhFndCdGF"
    assert ixn.said == "EJM1yhn99LOgCPRsEqpg8nKXQjkSE4-Q4dfvF3wm1Waz"
    assert op == {'v': 'ACDC10JSON00014c_'}

    verifyNoUnwantedInteractions()
    unstub()


def test_ipex_grant():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.peer.exchanging import Exchanges
    mock_excs = mock(spec=Exchanges, strict=True)

    dt = "2023-09-25T16:01:37.000000+00:00"
    mock_hab = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_acdc = {}
    mock_iss = {}
    mock_anc = {}
    mock_grant = {}
    mock_gsigs = []
    mock_end = ""
    expect(mock_client, times=1).exchanges().thenReturn(mock_excs)
    expect(mock_excs).createExchangeMessage(sender=mock_hab, route="/ipex/grant",
                                            payload={'m': 'this is a test',
                                                     'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'},
                                            embeds={'acdc': {}, 'iss': {}, 'anc': {}}, dt=dt).thenReturn((mock_grant,
                                                                                                          mock_gsigs,
                                                                                                          mock_end))

    ipex = credentialing.Ipex(mock_client)
    recp = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    grant, gsigs, end = ipex.grant(hab=mock_hab, recp=recp, message="this is a test", acdc=mock_acdc, iss=mock_iss,
                                   anc=mock_anc, dt=dt)

    assert grant == mock_grant
    assert gsigs == mock_gsigs
    assert end == mock_end

    unstub()


def test_ipex_admit():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.peer.exchanging import Exchanges
    mock_excs = mock(spec=Exchanges, strict=True)

    grant, _ = exchanging.exchange("/admit/grant", payload={}, sender="EEE")

    dt = "2023-09-25T16:01:37.000000+00:00"
    mock_hab = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_admit = {}
    mock_gsigs = []
    mock_end = ""
    expect(mock_client, times=1).exchanges().thenReturn(mock_excs)
    expect(mock_excs).createExchangeMessage(sender=mock_hab, route="/ipex/admit",
                                            payload={'m': 'this is a test'},
                                            embeds=None, dt=dt, dig=grant.said).thenReturn((mock_admit,
                                                                                            mock_gsigs,
                                                                                            mock_end))

    ipex = credentialing.Ipex(mock_client)  # type: ignore
    grant, gsigs, end = ipex.admit(hab=mock_hab, message="this is a test", dt=dt, grant=grant.said)

    assert grant == mock_admit
    assert gsigs == mock_gsigs
    assert end == mock_end

    unstub()


def test_submit_admit():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_rep = mock(spec=Response, strict=True)

    expect(mock_rep).json().thenReturn(dict(b='c'))

    mock_admit = mock({'ked': dict(a='b')})
    mock_gsigs = []
    mock_end = ""
    recp = ["ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"]

    ipex = credentialing.Ipex(mock_client)  # type: ignore
    body = {'exn': {'a': 'b'}, 'sigs': [], 'atc': '', 'rec': [['ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose']]}
    expect(mock_client, times=1).post(f"/identifiers/aid1/ipex/admit", json=body).thenReturn(mock_rep)
    rep = ipex.submitAdmit("aid1", exn=mock_admit, sigs=mock_gsigs, atc=mock_end, recp=recp)

    assert rep == dict(b='c')

    unstub()
