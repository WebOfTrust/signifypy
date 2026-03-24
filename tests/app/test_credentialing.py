# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_credentialing module

Testing credentialing with unit tests
"""
import pytest
from keri.core import eventing, coring
from keri.peer import exchanging
from keri.vdr import eventing as veventing
from mockito import mock, verify, expect, ANY

from signify.app import credentialing


def test_registries_legacy_create_returns_registry_result(make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()
    from signify.core import keeping
    mock_response = make_mock_response({})
    mock_hab = {'prefix': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    regName = "reg1"

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=2).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])
    expect(mock_client, times=1).post(path="/identifiers/aid1/registries", json=ANY()).thenReturn(mock_response)

    from signify.app.credentialing import Registries

    registries = Registries(client=mock_client)
    result = registries.create(mock_hab, regName)

    assert isinstance(result, credentialing.RegistryResult)
    assert result.regser.pre
    assert result.serder.pre == mock_hab["prefix"]
    assert result.sigs == ['a signature']
    assert result.response == mock_response


def test_registries_name_create_returns_registry_result(make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()

    from signify.app.aiding import Identifiers
    mock_ids = mock(spec=Identifiers, strict=True)
    from signify.core import keeping

    mock_response = make_mock_response({})
    mock_hab = {'prefix': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    regName = "reg1"

    expect(mock_client, times=1).identifiers().thenReturn(mock_ids)
    expect(mock_ids, times=1).get("aid1").thenReturn(mock_hab)
    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=2).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])
    expect(mock_client, times=1).post(path="/identifiers/aid1/registries", json=ANY()).thenReturn(mock_response)

    result = credentialing.Registries(client=mock_client).create(
        "aid1",
        regName,
        nonce="A_NONCE",
    )

    assert isinstance(result, credentialing.RegistryResult)
    assert result.regser.pre
    assert result.serder.pre == mock_hab["prefix"]
    assert result.sigs == ['a signature']
    assert result.response == mock_response


def test_registries_name_create_establishment_only_not_implemented(make_mock_client_with_manager):
    mock_client, _ = make_mock_client_with_manager()

    from signify.app.aiding import Identifiers
    mock_ids = mock(spec=Identifiers, strict=True)
    expect(mock_client, times=1).identifiers().thenReturn(mock_ids)
    expect(mock_ids, times=1).get("aid1").thenReturn({
        "prefix": "EPREFIX",
        "name": "aid1",
        "state": {"s": "1", "d": "ABCDEFG", "c": ["EO"]},
    })

    with pytest.raises(NotImplementedError, match="establishment only not implemented"):
        credentialing.Registries(client=mock_client).create("aid1", "reg1")


def test_registries_list_get_rename_and_serialize(make_mock_client_with_manager, make_mock_response):
    mock_client, _ = make_mock_client_with_manager()
    mock_response = make_mock_response({'json': lambda: {}})
    mock_hab = {'prefix': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    regName = "reg1"

    registries = credentialing.Registries(client=mock_client)

    expect(mock_client, times=1).get("/identifiers/aid1/registries").thenReturn(mock_response)
    registries.list(name="aid1")

    expect(mock_client, times=1).get("/identifiers/aid1/registries/reg1").thenReturn(mock_response)
    registries.get(name="aid1", registryName=regName)

    (expect(mock_client, times=1).put(path="/identifiers/aid1/registries/reg1", json={'name': 'test'})
     .thenReturn(mock_response))
    registries.rename(mock_hab, regName, "test")

    (expect(mock_client, times=1).put(path="/identifiers/aid1/registries/reg1", json={'name': 'again'})
     .thenReturn(mock_response))
    registries.rename("aid1", regName, "again")

    pre = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
    dig = "EOgQvKz8ziRn7FdR_ebwK9BkaVOnGeXQOJ87N6hMLrK0"
    nonce = "ACb_3pGwW3uIjtOg4zRQ66I-SggMcmoyju_uCzuSvgG4"
    serder = veventing.incept(pre=pre, nonce=nonce)
    anc = eventing.interact(pre=pre, dig=dig)

    msg = credentialing.Registries.serialize(serder, anc)
    assert msg == (b'{"v":"KERI10JSON00010f_","t":"vcp","d":"EGaypC6sODRFyIuhdFzzFmBU'
                   b'4Xe5SNprALGbltnyHYSz","i":"EGaypC6sODRFyIuhdFzzFmBU4Xe5SNprALGbl'
                   b'tnyHYSz","ii":"ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose","s"'
                   b':"0","c":[],"bt":"0","b":[],"n":"ACb_3pGwW3uIjtOg4zRQ66I-SggMcmo'
                   b'yju_uCzuSvgG4"}-VAS-GAB0AAAAAAAAAAAAAAAAAAAAAABENns5-voIbnRMADUO'
                   b'so7HDiQ9ZS_AfU8BfgGLHEW54H1')


def test_registry_result_op(make_mock_response):
    mock_response = make_mock_response({"json": lambda: {}})
    expect(mock_response, times=1).json().thenReturn({"done": True})

    result = credentialing.RegistryResult(
        regser="regser",
        serder="serder",
        sigs=["a signature"],
        response=mock_response,
    )

    assert result.regser == "regser"
    assert result.serder == "serder"
    assert result.sigs == ["a signature"]
    assert result.op() == {"done": True}


def test_registries_createFromEvents_returns_registry_result(make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()

    from signify.core import keeping
    mock_hab = {'prefix': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(aid=mock_hab).thenReturn(mock_keeper)

    mock_response = make_mock_response({})
    expect(mock_client, times=1).post(path="/identifiers/aid1/registries", json=ANY()).thenReturn(mock_response)

    vcp = veventing.incept(pre=mock_hab["prefix"], nonce="A_NONCE")
    ixn = eventing.interact(pre=mock_hab["prefix"], dig="ABCDEFG")

    result = credentialing.Registries(client=mock_client).createFromEvents(
        hab=mock_hab,
        name="aid1",
        registryName="reg1",
        vcp=vcp.ked,
        ixn=ixn.ked,
        sigs=["a signature"],
    )

    assert isinstance(result, credentialing.RegistryResult)
    assert result.regser.said == vcp.said
    assert result.serder.said == ixn.said
    assert result.sigs == ["a signature"]
    assert result.response == mock_response


def test_registries_create_from_events_compat_returns_json(make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()

    from signify.core import keeping
    mock_hab = {'prefix': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(aid=mock_hab).thenReturn(mock_keeper)

    mock_response = make_mock_response({})
    expect(mock_client, times=1).post(path="/identifiers/aid1/registries", json=ANY()).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({"done": True})

    vcp = veventing.incept(pre=mock_hab["prefix"], nonce="A_NONCE")
    ixn = eventing.interact(pre=mock_hab["prefix"], dig="ABCDEFG")

    result = credentialing.Registries(client=mock_client).create_from_events(
        hab=mock_hab,
        registryName="reg1",
        vcp=vcp.ked,
        ixn=ixn.ked,
        sigs=["a signature"],
    )

    assert result == {"done": True}


def test_registries_create_uses_nb_trait_for_backerless_registry():
    """Backerless registry inception must use the VDR `NB` trait code.

    This looks small, but it is the difference between a true no-backer
    registry and a backer-capable one. When the wrong trait code is used, the
    live stack silently issues `bis/brv` events instead of `iss/rev`, and
    later revoke coverage fails for the wrong reason.
    """

    class DummyResponse:
        def json(self):
            return {}

    class DummyKeeper:
        algo = "salty"

        @staticmethod
        def params():
            return {"keeper": "params"}

        @staticmethod
        def sign(ser):
            return ["a signature"]

    class DummyManager:
        @staticmethod
        def get(aid):
            return DummyKeeper()

    class DummyClient:
        def __init__(self):
            self.manager = DummyManager()
            self.last_post = None

        def post(self, path, json):
            self.last_post = (path, json)
            return DummyResponse()

    hab = {
        "prefix": "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose",
        "name": "aid1",
        "state": {"s": "1", "d": "ABCDEFG"},
    }

    client = DummyClient()
    credentialing.Registries(client=client).create(hab, "reg1")

    assert client.last_post is not None
    path, body = client.last_post
    assert path == "/identifiers/aid1/registries"
    assert body["vcp"]["c"] == ["NB"]

def test_credentials_list(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    mock_response = make_mock_response({'json': lambda: {}})
    expect(mock_client, times=1).post('/credentials/query',
                                      json={'filter': {'genre': 'horror'},
                                            'sort': ['updside down'], 'skip': 10, 'limit': 10}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    Credentials(client=mock_client).list(filtr={'genre': 'horror'}, sort=['updside down'], skip=10,
                                         limit=10)  # type: ignore

    verify(mock_response, times=1).json()

def test_credentials_export(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    mock_response = make_mock_response({'content': 'things I found'})
    expect(mock_client, times=1).get('/credentials/a_said',
                                     headers={'accept': 'application/json+cesr'}).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    out = Credentials(client=mock_client).export('a_said')  # type: ignore

    assert out == 'things I found'

def test_credentials_create(make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()

    from signify.core import keeping
    mock_hab = {'prefix': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose', 'name': 'aid1',
                'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_registry = {'regk': "EKRg7i8jS4O6BYUYiQG7X8YiMYdDXdw28tJRhFndCdGF",
                     'pre': 'EHpwssa6tmD2U5W7-aogym-r1NobKBNXydP4MmaebA4O', 'state': {'c': ['NB']}}
    data = dict(dt="2023-09-27T16:27:14.376928+00:00", LEI="ABC1234567890AD4456")
    schema = "EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao"
    recp = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=2).get(aid=mock_hab).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])
    mock_response = make_mock_response({})
    expect(mock_response, times=1).json().thenReturn({'v': 'ACDC10JSON00014c_'})

    sad = {'v': 'ACDC10JSON00014c_', 'd': '',
           'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
           'ri': 'a_regk', 's': 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
           'a': {'d': 'EHpwssa6tmD2U5W7-aogym-r1NobKBNXydP4MmaebA4O',
                 'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                 'dt': '2023-09-27T16:27:14.376928+00:00', 'LEI': 'ABC1234567890AD4456'}}

    _, sad = coring.Saider.saidify(sad)

    body = {'acdc': {'v': 'ACDC10JSON000196_', 'd': 'EK2xYrVkfJJHvlGhP79sfEPvQGmkFPPNAj-bjI5oHy7m',
                     'i': 'EHpwssa6tmD2U5W7-aogym-r1NobKBNXydP4MmaebA4O',
                     'ri': 'EKRg7i8jS4O6BYUYiQG7X8YiMYdDXdw28tJRhFndCdGF',
                     's': 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao',
                     'a': {'d': 'EHpwssa6tmD2U5W7-aogym-r1NobKBNXydP4MmaebA4O',
                           'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                           'dt': '2023-09-27T16:27:14.376928+00:00', 'LEI': 'ABC1234567890AD4456'}},
            'iss': {'v': 'KERI10JSON0000ed_', 't': 'iss', 'd': 'EE8yncw1LCyBVtZPtozAFi7qvGn9dRPwTbuq--ulOAtB',
                    'i': 'EK2xYrVkfJJHvlGhP79sfEPvQGmkFPPNAj-bjI5oHy7m', 's': '0',
                    'ri': 'EKRg7i8jS4O6BYUYiQG7X8YiMYdDXdw28tJRhFndCdGF', 'dt': '2023-09-27T16:27:14.376928+00:00'},
            'ixn': {'v': 'KERI10JSON000115_', 't': 'ixn', 'd': 'EC5KxyucpxnOpIpHe2QUPs9YeH1yGvkALg8NcWLYFe6a',
                    'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose', 's': '2', 'p': 'ABCDEFG', 'a': [
                    {'i': 'EK2xYrVkfJJHvlGhP79sfEPvQGmkFPPNAj-bjI5oHy7m', 's': '0',
                     'd': 'EE8yncw1LCyBVtZPtozAFi7qvGn9dRPwTbuq--ulOAtB'}]}, 'sigs': ['a signature'],
            'salty': {'keeper': 'params'}}

    expect(mock_client, times=1).post(f"/identifiers/aid1/credentials", json=body).thenReturn(mock_response)

    from signify.app.credentialing import Credentials
    creder, iss, ixn, sigs, op = Credentials(client=mock_client).create(mock_hab, mock_registry, data, schema, recp)

    assert creder.said == "EK2xYrVkfJJHvlGhP79sfEPvQGmkFPPNAj-bjI5oHy7m"
    assert iss.said == "EE8yncw1LCyBVtZPtozAFi7qvGn9dRPwTbuq--ulOAtB"
    assert ixn.said == "EC5KxyucpxnOpIpHe2QUPs9YeH1yGvkALg8NcWLYFe6a"
    assert op == {'v': 'ACDC10JSON00014c_'}

def test_ipex_grant():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.exchanging import Exchanges
    mock_excs = mock(spec=Exchanges, strict=True)

    dt = "2023-09-25T16:01:37.000000+00:00"
    mock_hab = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_acdc = {}
    mock_iss = {}
    mock_anc = {}
    mock_agree = mock({'said': 'EAGREE123'}, strict=True)
    mock_grant = {}
    mock_gsigs = []
    mock_atc = ""
    expect(mock_client, times=1).exchanges().thenReturn(mock_excs)
    expect(mock_excs).createExchangeMessage(sender=mock_hab, route="/ipex/grant",
                                            payload={'m': 'this is a test',
                                                     'i': 'ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose'},
                                            embeds={'acdc': {}, 'iss': {}, 'anc': {}},
                                            recipient='ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                                            dt=dt,
                                            dig='EAGREE123').thenReturn((mock_grant, mock_gsigs, mock_atc))

    ipex = credentialing.Ipex(mock_client)
    recp = "ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"

    grant, gsigs, atc = ipex.grant(hab=mock_hab, recp=recp, message="this is a test", acdc=mock_acdc, iss=mock_iss,
                                   anc=mock_anc, agree=mock_agree, dt=dt)

    assert grant == mock_grant
    assert gsigs == mock_gsigs
    assert atc == mock_atc

def test_ipex_admit():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.exchanging import Exchanges
    mock_excs = mock(spec=Exchanges, strict=True)

    grant, _ = exchanging.exchange("/admit/grant", payload={}, sender="EEE")

    dt = "2023-09-25T16:01:37.000000+00:00"
    mock_hab = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_admit = {}
    mock_gsigs = []
    mock_atc = ""
    expect(mock_client, times=1).exchanges().thenReturn(mock_excs)
    expect(mock_excs).createExchangeMessage(sender=mock_hab, route="/ipex/admit",
                                            payload={'m': 'this is a test'},
                                            embeds=None,
                                            recipient='ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose',
                                            dt=dt,
                                            dig=grant.said).thenReturn((mock_admit, mock_gsigs, mock_atc))

    ipex = credentialing.Ipex(mock_client)  # type: ignore
    grant, gsigs, atc = ipex.admit(
        hab=mock_hab,
        message="this is a test",
        dt=dt,
        grant=grant.said,
        recp="ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose",
    )

    assert grant == mock_admit
    assert gsigs == mock_gsigs
    assert atc == mock_atc



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
    body = {'exn': {'a': 'b'}, 'sigs': [], 'atc': '', 'rec': ['ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose']}
    expect(mock_client, times=1).post(f"/identifiers/aid1/ipex/admit", json=body).thenReturn(mock_rep)
    rep = ipex.submitAdmit("aid1", exn=mock_admit, sigs=mock_gsigs, atc=mock_end, recp=recp)

    assert rep == dict(b='c')



def test_submit_grant():
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
    body = {'exn': {'a': 'b'}, 'sigs': [], 'atc': '', 'rec': ['ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose']}
    expect(mock_client, times=1).post(f"/identifiers/aid1/ipex/grant", json=body).thenReturn(mock_rep)
    rep = ipex.submitGrant("aid1", exn=mock_admit, sigs=mock_gsigs, atc=mock_end, recp=recp)

    assert rep == dict(b='c')
