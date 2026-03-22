# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_contacting module

Testing contacting with unit tests
"""

from mockito import mock, unstub, expect, verifyNoUnwantedInteractions


def test_contact_list():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/contacts', params=None).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        ['contact1', 'contact2']
    )

    out = contacts.list()
    assert out == ['contact1', 'contact2']

    verifyNoUnwantedInteractions()
    unstub()


def test_contact_list_with_filters():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).get(
        '/contacts',
        params={'group': 'mygroup', 'filter_field': 'company', 'filter_value': 'mycompany'},
    ).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(['contact1'])

    out = contacts.list(group='mygroup', filter_field='company', filter_value='mycompany')
    assert out == ['contact1']

    verifyNoUnwantedInteractions()
    unstub()


def test_contact_list_legacy_range():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({'headers': {'content-range': 'contents 0-10/20'}}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/contacts', headers=dict(Range="contacts=0-24")).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(['contact1', 'contact2'])

    out = contacts.list(start=0, end=24)
    assert out['start'] == 0
    assert out['end'] == 2
    assert out['total'] == 2
    assert out['contacts'] == ['contact1', 'contact2']

    verifyNoUnwantedInteractions()
    unstub()


def test_contact_get():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/contacts/E123').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'id': 'E123', 'alias': 'bob'})

    out = contacts.get('E123')
    assert out == {'id': 'E123', 'alias': 'bob'}

    verifyNoUnwantedInteractions()
    unstub()


def test_contact_add():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    info = {'name': 'John Doe', 'company': 'My Company'}
    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).post('/contacts/E123', json=info).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'id': 'E123', **info})

    out = contacts.add('E123', info)
    assert out == {'id': 'E123', **info}

    verifyNoUnwantedInteractions()
    unstub()


def test_contact_update():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    info = {'name': 'John Doe', 'company': 'My Company'}
    from requests import Response
    mock_response = mock({}, spec=Response, strict=True)
    expect(mock_client, times=1).put('/contacts/E123', json=info).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'id': 'E123', **info})

    out = contacts.update('E123', info)
    assert out == {'id': 'E123', **info}

    verifyNoUnwantedInteractions()
    unstub()


def test_contact_delete():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient)

    from signify.app.contacting import Contacts
    contacts = Contacts(client=mock_client)  # type: ignore

    from requests import Response
    mock_response = mock({'status_code': 202}, spec=Response, strict=True)
    expect(mock_client, times=1).delete('/contacts/E123').thenReturn(mock_response)

    out = contacts.delete('E123')
    assert out is True

    verifyNoUnwantedInteractions()
    unstub()
