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
    mock_response = mock({'headers': {'content-range': 'contents 0-10/20'}}, spec=Response, strict=True)
    expect(mock_client, times=1).get('/contacts', headers=dict(Range=f"contacts={0}-{24}")).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn(
        ['contact1', 'contact2']
    )

    out = contacts.list()
    assert out['start'] == 0
    assert out['end'] == 2
    assert out['total'] == 2
    assert out['contacts'] == ['contact1', 'contact2']

    verifyNoUnwantedInteractions()
    unstub()
