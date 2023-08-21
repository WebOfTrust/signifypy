# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_clienting module

Testing notifying with unit tests
"""

from mockito import mock,  when, unstub


def test_notification_list():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client)

    from requests import Response
    mock_response = mock({'headers': {'content-range': 'notes 0-10/20'}}, spec=Response)
    when(mock_client).get('/notifications', headers=dict(Range=f"notes={0}-{24}")).thenReturn(mock_response)
    when(mock_response).json().thenReturn(
        ['note1', 'note2']
    )

    out = notes.list()
    assert out['start'] == 0
    assert out['end'] == 10
    assert out['total'] == 20
    assert out['notes'] == ['note1', 'note2']

    unstub()


def test_noticiation_mark_as_read():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client)

    from requests import Response
    mock_response = mock({'status': 202}, spec=Response)
    when(mock_client).put('/notifications/ABC123', json={}).thenReturn(mock_response)

    out = notes.markAsRead(nid="ABC123")
    assert out is True

    mock_response = mock({'status': 404}, spec=Response)
    when(mock_client).put('/notifications/DEF456', json={}).thenReturn(mock_response)

    out = notes.markAsRead(nid="DEF456")
    assert out is False


def test_noticiation_delete():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client)

    from requests import Response
    mock_response = mock({'status': 202}, spec=Response)
    when(mock_client).delete(path='/notifications/ABC123').thenReturn(mock_response)

    out = notes.delete(nid="ABC123")
    assert out is True

    mock_response = mock({'status': 404}, spec=Response)
    when(mock_client).delete(path='/notifications/DEF456').thenReturn(mock_response)

    out = notes.delete(nid="DEF456")
    assert out is False
