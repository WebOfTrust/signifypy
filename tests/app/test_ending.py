# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_ending module

Testing ending with unit tests
"""

from mockito import mock, patch, unstub, verify, verifyNoUnwantedInteractions, expect, expect, when
import pytest

def test_end_role_authorizations_name():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.ending import EndRoleAuthorizations
    ends = EndRoleAuthorizations(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock(spec=Response, strict=True)

    expect(mock_client, times=1).get('/identifiers/name/endroles/role').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'output'})

    out = ends.list(name='name', role='role')

    assert out == {'some': 'output'}

def test_end_role_authorizations_aid():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.ending import EndRoleAuthorizations
    ends = EndRoleAuthorizations(client=mock_client) # type: ignore

    from requests import Response
    mock_response = mock(spec=Response, strict=True)

    expect(mock_client, times=1).get('/endroles/aid1/role').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'output'})

    out = ends.list(aid='aid1', role='role')

    assert out == {'some': 'output'}

def test_end_role_authorizations_bad():
    from signify.app.clienting import SignifyClient
    mock_client = mock(spec=SignifyClient, strict=True)

    from signify.app.ending import EndRoleAuthorizations
    ends = EndRoleAuthorizations(client=mock_client) # type: ignore

    with pytest.raises(ValueError, match='either `aid` or `name` is required'):
        ends.list()
