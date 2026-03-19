# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.peer.test_exchanging module

Testing exchanging with unit tests
"""
import pytest
from mockito import mock, expect, ANY

pytestmark = pytest.mark.usefixtures("mockito_clean")


def test_exchanges_send(mockHelpingNowIso8601, make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()

    payload = dict(a='b')
    embeds = dict()
    recipients = ['Eqbc123']

    from signify.core import keeping
    sender = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(sender).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])

    mock_response = make_mock_response({'content': 'things I found'})
    expect(mock_response, times=1).json().thenReturn({'content': 'things I found'})
    expect(mock_client, times=1).post("/identifiers/aid1/exchanges",
                                      json={'tpc': 'credentials',
                                            'exn': {'v': 'KERI10JSON0000df_', 't': 'exn',
                                                    'd':
                                                        'EJR8VHK6fQpQK59qPinuhlT9ZzZxuRuRrNhwZldbzF0h',
                                                    'i': 'a_prefix',
                                                    'rp': 'Eqbc123',
                                                    'p': '',
                                                    'dt': '2021-06-27T21:26:21.233257+00:00',
                                                    'r': '/ipex/admit', 'q': {}, 'a': {'i': 'Eqbc123', 'a': 'b'},
                                                    'e': {}}, 'sigs': ['a signature'], 'atc': '',
                                            'rec': ['Eqbc123']}).thenReturn(
        mock_response)

    from signify.peer.exchanging import Exchanges
    exn, sigs, out = Exchanges(client=mock_client).send('aid1', 'credentials', sender=sender, route="/ipex/admit",
                                                        payload=payload,
                                                        embeds=embeds, recipients=recipients)  # type: ignore

    assert exn.said == "EJR8VHK6fQpQK59qPinuhlT9ZzZxuRuRrNhwZldbzF0h"
    assert sigs == ['a signature']
    assert out == {'content': 'things I found'}

def test_exchanges_get(mockHelpingNowIso8601, make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    mock_response = make_mock_response({'content': 'things I found'})
    expect(mock_response, times=1).json().thenReturn({'content': 'an exn'})
    expect(mock_client, times=1).get("/exchanges/EEE",).thenReturn(mock_response)

    from signify.peer.exchanging import Exchanges
    out = Exchanges(client=mock_client).get('EEE')  # type: ignore

    assert out == {'content': 'an exn'}

def test_exchanges_send_multiple_recipients(mockHelpingNowIso8601, make_mock_client_with_manager, make_mock_response):
    mock_client, mock_manager = make_mock_client_with_manager()

    payload = dict(a='b')
    embeds = dict()
    recipients = ['Eqbc123', 'Eqbc456']

    from signify.core import keeping
    sender = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=2).get(sender).thenReturn(mock_keeper)
    expect(mock_keeper, times=2).sign(ser=ANY()).thenReturn(['a signature'])

    first_response = make_mock_response({'content': 'first'})
    second_response = make_mock_response({'content': 'second'})
    expect(first_response, times=1).json().thenReturn({'content': 'first'})
    expect(second_response, times=1).json().thenReturn({'content': 'second'})
    expect(mock_client, times=1).post("/identifiers/aid1/exchanges",
                                      json={'tpc': 'credentials',
                                            'exn': {'v': 'KERI10JSON0000df_', 't': 'exn',
                                                    'd': 'EJR8VHK6fQpQK59qPinuhlT9ZzZxuRuRrNhwZldbzF0h',
                                                    'i': 'a_prefix',
                                                    'rp': 'Eqbc123',
                                                    'p': '',
                                                    'dt': '2021-06-27T21:26:21.233257+00:00',
                                                    'r': '/ipex/admit', 'q': {}, 'a': {'i': 'Eqbc123', 'a': 'b'},
                                                    'e': {}}, 'sigs': ['a signature'], 'atc': '',
                                            'rec': ['Eqbc123']}).thenReturn(first_response)
    expect(mock_client, times=1).post("/identifiers/aid1/exchanges",
                                      json={'tpc': 'credentials',
                                            'exn': {'v': 'KERI10JSON0000df_', 't': 'exn',
                                                    'd': 'ENONx6LhzT1C6_BzCfSGjt7T6DzW39Upi228PFksG_dE',
                                                    'i': 'a_prefix',
                                                    'rp': 'Eqbc456',
                                                    'p': '',
                                                    'dt': '2021-06-27T21:26:21.233257+00:00',
                                                    'r': '/ipex/admit', 'q': {}, 'a': {'i': 'Eqbc456', 'a': 'b'},
                                                    'e': {}}, 'sigs': ['a signature'], 'atc': '',
                                            'rec': ['Eqbc456']}).thenReturn(second_response)

    from signify.peer.exchanging import Exchanges
    results = Exchanges(client=mock_client).send(
        'aid1',
        'credentials',
        sender=sender,
        route="/ipex/admit",
        payload=payload,
        embeds=embeds,
        recipients=recipients,
    )  # type: ignore

    assert len(results) == 2
    assert results[0][0].said == "EJR8VHK6fQpQK59qPinuhlT9ZzZxuRuRrNhwZldbzF0h"
    assert results[0][2] == {'content': 'first'}
    assert results[1][0].said == "ENONx6LhzT1C6_BzCfSGjt7T6DzW39Upi228PFksG_dE"
    assert results[1][2] == {'content': 'second'}
