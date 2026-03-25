# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_grouping module

Testing grouping with unit tests
"""

import pytest
from mockito import mock, expect

pytestmark = pytest.mark.usefixtures("mockito_clean")


def test_grouping_get_request(make_mock_client_with_manager, make_mock_response):
    mock_client, _ = make_mock_client_with_manager()

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    mock_response = make_mock_response({'headers': {'content-range': 'aids 0-10/2'}})
    expect(mock_client, times=1).get('/multisig/request/EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        [{'d': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}]
    )

    res = groups.get_request(said="EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4")
    assert len(res) == 1
    assert res[0]['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"


def test_grouping_getRequest_alias(make_mock_client_with_manager):
    mock_client, _ = make_mock_client_with_manager()

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    expect(groups, times=1).get_request("EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4").thenReturn(
        [{'d': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}]
    )

    res = groups.getRequest("EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4")
    assert res[0]['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"

def test_grouping_send_request(make_mock_client_with_manager, make_mock_response):
    mock_client, _ = make_mock_client_with_manager()

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    mock_exn = {}
    mock_sigs = ['sig']
    mock_atc = b'-attachment'

    body = {
        'exn': mock_exn,
        'sigs': mock_sigs,
        'atc': mock_atc.decode("utf-8")
    }

    mock_response = make_mock_response({'headers': {'content-range': 'aids 0-10/2'}})
    expect(mock_client, times=1).post(
        '/identifiers/test/multisig/request',
        json=body).thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn(
        {'t': 'exn', 'd': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}
    )

    res = groups.send_request(name="test", exn=mock_exn, sigs=mock_sigs, atc=mock_atc)
    assert res['t'] == 'exn'
    assert res['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"


def test_grouping_sendRequest_alias(make_mock_client_with_manager):
    mock_client, _ = make_mock_client_with_manager()

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

    expect(groups, times=1).send_request("test", {}, ['sig'], '-attachment').thenReturn(
        {'t': 'exn', 'd': "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"}
    )

    res = groups.sendRequest("test", {}, ['sig'], '-attachment')
    assert res['t'] == 'exn'
    assert res['d'] == "EKYLUMmNPZeEs77Zvclf0bSN5IN-mLfLpx2ySb-HDlk4"

def test_grouping_join(make_mock_client_with_manager, make_mock_response):
    mock_client, _ = make_mock_client_with_manager()

    from signify.app.grouping import Groups
    groups = Groups(client=mock_client)  # type: ignore

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

    mock_response = make_mock_response({'headers': {'content-range': 'aids 0-10/2'}})
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


