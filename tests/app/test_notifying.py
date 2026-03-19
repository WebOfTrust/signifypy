# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_notifying module

Testing notifying with unit tests
"""

import pytest
from mockito import mock, expect

pytestmark = pytest.mark.usefixtures("mockito_clean")


def test_notification_list(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client) # type: ignore

    mock_response = make_mock_response({'headers': {'content-range': 'notes 0-10/20'}})
    expect(mock_client, times=1).get('/notifications', headers=dict(Range=f"notes={0}-{24}")).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        ['note1', 'note2']
    )

    out = notes.list()
    assert out['start'] == 0
    assert out['end'] == 10
    assert out['total'] == 20
    assert out['notes'] == ['note1', 'note2']

def test_notification_mark_as_read(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client) # type: ignore

    mock_response = make_mock_response({'status_code': 202})
    expect(mock_client, times=1).put('/notifications/ABC123', json={}).thenReturn(mock_response)

    out = notes.markAsRead(nid="ABC123")
    assert out is True

    mock_response = make_mock_response({'status_code': 404})
    expect(mock_client, times=1).put('/notifications/DEF456', json={}).thenReturn(mock_response)

    out = notes.markAsRead(nid="DEF456")
    assert out is False

def test_notification_delete(make_mock_response):
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client)  # type: ignore

    mock_response = make_mock_response({'status_code': 202})
    expect(mock_client, times=1).delete(path='/notifications/ABC123').thenReturn(mock_response)

    out = notes.delete(nid="ABC123")
    assert out is True

    mock_response = make_mock_response({'status_code': 404})
    expect(mock_client, times=1).delete(path='/notifications/DEF456').thenReturn(mock_response)

    out = notes.delete(nid="DEF456")
    assert out is False
