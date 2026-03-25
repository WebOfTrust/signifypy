# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.app.test_coring module

Testing coring with unit tests
"""

import pytest
from mockito import mock, expect

pytestmark = pytest.mark.usefixtures("mockito_clean")


def test_operations(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ops = coring.Operations(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/operations/a_name').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ops.get("a_name")


def test_operations_list(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/operations', params=None).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn([{'name': 'op1'}])

    out = ops.list()

    assert out == [{'name': 'op1'}]


def test_operations_list_by_type(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/operations', params={'type': 'witness'}).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn([{'name': 'op1', 'type': 'witness'}])

    out = ops.list(type="witness")

    assert out == [{'name': 'op1', 'type': 'witness'}]


def test_operations_delete(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).delete('/operations/operationName').thenReturn(mock_response)

    out = ops.delete("operationName")

    assert out is None


def test_operations_wait_returns_done_operation_without_polling():
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    op = {"name": "operationName", "done": True}

    out = ops.wait(op)

    assert out is op


def test_operations_wait_polls_until_done(monkeypatch):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    responses = iter([
        {"name": "operationName", "done": False},
        {"name": "operationName", "done": True},
    ])
    calls = []
    sleeps = []

    def fake_get(name):
        calls.append(name)
        return next(responses)

    monkeypatch.setattr(ops, "get", fake_get)
    monkeypatch.setattr(coring.time, "sleep", lambda seconds: sleeps.append(seconds))

    out = ops.wait(
        {"name": "operationName", "done": False},
        interval=0.01,
        max_interval=0.01,
    )

    assert out == {"name": "operationName", "done": True}
    assert calls == ["operationName", "operationName"]
    assert sleeps == [0.01]


def test_operations_wait_waits_for_dependency(monkeypatch):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    responses = {
        "childOperation": iter([
            {"name": "childOperation", "done": True},
        ]),
        "parentOperation": iter([
            {
                "name": "parentOperation",
                "done": True,
                "metadata": {"depends": {"name": "childOperation", "done": True}},
            },
        ]),
    }
    calls = []

    def fake_get(name):
        calls.append(name)
        return next(responses[name])

    monkeypatch.setattr(ops, "get", fake_get)
    monkeypatch.setattr(coring.time, "sleep", lambda seconds: None)

    out = ops.wait(
        {
            "name": "parentOperation",
            "done": False,
            "metadata": {"depends": {"name": "childOperation", "done": False}},
        },
        interval=0.01,
        max_interval=0.01,
    )

    assert out["done"] is True
    assert calls == ["childOperation", "parentOperation"]


def test_operations_wait_raises_when_aborted(monkeypatch):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    abort_error = RuntimeError("Aborted")

    def fake_get(name):
        return {"name": name, "done": False}

    def fake_signal(current_op):
        assert current_op["name"] == "operationName"
        raise abort_error

    monkeypatch.setattr(ops, "get", fake_get)
    monkeypatch.setattr(coring.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="Aborted") as excinfo:
        ops.wait({"name": "operationName", "done": False}, check_abort=fake_signal)

    assert excinfo.value is abort_error


def test_operations_wait_raises_timeout_with_latest_operation(monkeypatch):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    def fake_get(name):
        return {"name": name, "done": False, "stage": "still waiting"}

    monotonic_values = iter([100.0, 101.0, 101.1])

    monkeypatch.setattr(ops, "get", fake_get)
    monkeypatch.setattr(coring.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(coring.time, "monotonic", lambda: next(monotonic_values))

    with pytest.raises(TimeoutError, match="timed out waiting for operation operationName") as excinfo:
        ops.wait(
            {"name": "operationName", "done": False},
            timeout=1.0,
            interval=0.25,
            max_interval=0.25,
        )

    assert "still waiting" in str(excinfo.value)


def test_operations_wait_options_compatibility_path(monkeypatch):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    ops = coring.Operations(client=client)  # type: ignore

    abort_error = RuntimeError("Aborted")

    def fake_get(name):
        return {"name": name, "done": False}

    def fake_signal():
        raise abort_error

    monkeypatch.setattr(ops, "get", fake_get)
    monkeypatch.setattr(coring.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="Aborted") as excinfo:
        ops.wait(
            {"name": "operationName", "done": False},
            options={"signal": fake_signal, "maxSleep": 10},
        )

    assert excinfo.value is abort_error


def test_config_get(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)

    from signify.app import coring
    config = coring.Config(client=client)  # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/config').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'iurls': ['http://example.com/oobi']})

    out = config.get()

    assert out == {'iurls': ['http://example.com/oobi']}

def test_oobis_get(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    oobis = coring.Oobis(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/identifiers/a_name/oobis?role=my_role').thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    oobis.get("a_name", "my_role")

def test_oobis_resolve(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    oobis = coring.Oobis(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).post('/oobis', json={'url': 'my oobi', 'oobialias': 'Harry'}).thenReturn(mock_response)

    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    oobis.resolve("my oobi", alias="Harry")

def test_key_states_get(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/states?pre=a_prefix').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.get("a_prefix")

def test_key_states_list(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/states?pre=pre1&pre=pre2').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.list(["pre1", "pre2"])

def test_key_states_query(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ks = coring.KeyStates(client=client) # type: ignore

    mock_response = make_mock_response()
     
    expect(client, times=1).post('/queries', json={'pre': 'a_prefix', 'sn': 0, 'anchor': {'my': 'anchor'}}).thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ks.query("a_prefix", sn=0, anchor={'my': 'anchor'})

def test_key_events(make_mock_response):
    from signify.app.clienting import SignifyClient
    client = mock(spec=SignifyClient, strict=True)
    
    from signify.app import coring
    ke = coring.KeyEvents(client=client) # type: ignore

    mock_response = make_mock_response()
    expect(client, times=1).get('/events?pre=my_prefix').thenReturn(mock_response)
    expect(mock_response, times=1).json().thenReturn({'some': 'json'})

    ke.get("my_prefix")
