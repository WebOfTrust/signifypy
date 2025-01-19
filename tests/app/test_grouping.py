# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_grouping module

Testing grouping with unit tests
"""

from mockito import mock, verifyNoUnwantedInteractions, unstub, expect


def test_grouping_get_request():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager  # type: ignore

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({'headers': {'content-range': 'aids 0-10/2'}}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/multisig/request/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        [{'d': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}]
    )

    res = groups.get_request(said="EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4")
    assert len(res) == 1
    assert res[0]['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"

    verifyNoUnwantedInteractions()
    unstub()


def test_grouping_send_request():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager  # type: ignore

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    from requests import Response

    mock_exn = {}
    mock_sigs = ['sig']
    mock_atc = b'-attachment'

    body = {
        'exn': mock_exn,
        'sigs': mock_sigs,
        'atc': mock_atc.decode("utf-8")
    }

    mock_response = mock({'headers': {'content-range': 'aids 0-10/2'}}, spec=Response, strict=True)
    expect(mock_client, times=1).post(
        '/identifiers/test/multisig/request',
        json=body).thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn(
        {'t': 'exn', 'd': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}
    )

    res = groups.send_request(name="test", exn=mock_exn, sigs=mock_sigs, atc=mock_atc)
    assert res['t'] == 'exn'
    assert res['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"

    verifyNoUnwantedInteractions()
    unstub()


def test_grouping_join():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.core import keeping
    mock_manager = mock(spec=keeping.Manager, strict=True)
    mock_client.manager = mock_manager  # type: ignore

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    from requests import Response
    from keri.core.serdering import SerderKERI
    mock_rot = mock({'ked': {}}, spec=SerderKERI, strict=True)
    mock_sigs = ['sig']
    mock_smids = ['1', '2', '3']
    mock_rmids = ['a', 'b', 'c']

    body = {
        'tpc': 'multisig',
        'rot': {},
        'sigs': mock_sigs,
        'gid': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",
        'smids': mock_smids,
        'rmids': mock_rmids
    }

    mock_response = mock({'headers': {'content-range': 'aids 0-10/2'}}, spec=Response, strict=True)
    expect(mock_client, times=1).post(
        '/identifiers/test/multisig/join',
        json=body).thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn(
        {'t': 'op', 'd': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}
    )

    res = groups.join(name="test", rot=mock_rot, sigs=mock_sigs, gid="EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4",
                      smids=mock_smids, rmids=mock_rmids)
    assert res['t'] == 'op'
    assert res['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"

    verifyNoUnwantedInteractions()
    unstub()




