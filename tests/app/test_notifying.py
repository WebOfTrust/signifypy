# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_notifying module

Testing notifying with unit tests
"""

from mockito import mock, unstub, expect, verifyNoUnwantedInteractions


def test_notification_list():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock({'headers': {'content-range': 'notes 0-10/20'}}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/notifications', headers=dict(Range=f"notes={0}-{24}")).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        ['note1', 'note2']
    )

    out = notes.list()
    assert out['start'] == 0
    assert out['end'] == 10
    assert out['total'] == 20
    assert out['notes'] == ['note1', 'note2']

    verifyNoUnwantedInteractions()
    unstub()


def test_noticiation_mark_as_read():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock({'status': 202}, spec=Response, strict=True)
    expect(mock_client, times=1).put('/notifications/ABC123', json={}).thenReturn(mock_response)

    out = notes.markAsRead(nid="ABC123")
    assert out is True

    mock_response = mock({'status': 404}, spec=Response, strict=True)
    expect(mock_client, times=1).put('/notifications/DEF456', json={}).thenReturn(mock_response)

    out = notes.markAsRead(nid="DEF456")
    assert out is False

    verifyNoUnwantedInteractions()
    unstub()


def test_noticiation_delete():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.notifying import Notifications
    notes = Notifications(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({'status': 202}, spec=Response, strict=True)
    expect(mock_client, times=1).delete(path='/notifications/ABC123').thenReturn(mock_response)

    out = notes.delete(nid="ABC123")
    assert out is True

    mock_response = mock({'status': 404}, spec=Response, strict=True)
    expect(mock_client, times=1).delete(path='/notifications/DEF456').thenReturn(mock_response)

    out = notes.delete(nid="DEF456")
    assert out is True

    verifyNoUnwantedInteractions()
    unstub()
