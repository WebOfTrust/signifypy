# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.peer.test_exchanging module

Testing exchanging with unit tests
"""
from mockito import mock, unstub, verifyNoUnwantedInteractions, expect, ANY


def test_exchanges_send(mockHelpingNowIso8601):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    payload = dict(a='b')
    embeds = dict()
    recipients = ['Eqbc123']

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager  # type: ignore

    sender = {'prefix': 'a_prefix', 'name': 'aid1', 'state': {'s': '1', 'd': "ABCDEFG"}}
    mock_keeper = mock({'algo': 'salty', 'params': lambda: {'keeper': 'params'}}, spec=keeping.SaltyKeeper, strict=True)
    expect(mock_manager, times=1).get(sender).thenReturn(mock_keeper)
    expect(mock_keeper, times=1).sign(ser=ANY()).thenReturn(['a signature'])

    from requests import Response
    mock_response = mock({'content': 'things I found'}, spec=Response, strict=True)
    expect(mock_response, times=1).json().thenReturn({'content': 'things I found'})
    expect(mock_client, times=1).post("/identifiers/aid1/exchanges",
                                      json={'tpc': 'credentals',
                                            'exn': {'v': 'KERI10JSON0000ca_', 't': 'exn',
                                                    'd':
                                                        'EE1dCWxjov6vKtKue_700dmS7sn8dOjhTSiNuEsfuREh',
                                                    'i': 'a_prefix',
                                                    'rp':'',
                                                    'p': '',
                                                    'dt': '2021-06-27T21:26:21.233257+00:00',
                                                    'r': '/ipex/admit', 'q': {}, 'a': {'a': 'b'},
                                                    'e': {}}, 'sigs': ['a signature'], 'atc': '',
                                            'rec': ['Eqbc123']}).thenReturn(
        mock_response)

    from signify.peer.exchanging import Exchanges
    exn, sigs, out = Exchanges(client=mock_client).send('aid1', 'credentals', sender=sender, route="/ipex/admit",
                                                        payload=payload,
                                                        embeds=embeds, recipients=recipients)  # type: ignore

    assert exn.said == "EE1dCWxjov6vKtKue_700dmS7sn8dOjhTSiNuEsfuREh"
    assert sigs == ['a signature']
    assert out == {'content': 'things I found'}

    verifyNoUnwantedInteractions()
    unstub()


def test_exchanges_get(mockHelpingNowIso8601):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from requests import Response
    mock_response = mock({'content': 'things I found'}, spec=Response, strict=True)
    expect(mock_response, times=1).json().thenReturn({'content': 'an exn'})
    expect(mock_client, times=1).get("/exchanges/EEE",).thenReturn(mock_response)

    from signify.peer.exchanging import Exchanges
    out = Exchanges(client=mock_client).get('EEE')  # type: ignore

    assert out == {'content': 'an exn'}

    verifyNoUnwantedInteractions()
    unstub()
