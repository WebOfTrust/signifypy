
from requests import Response
from signify.app.aiding import Identifiers
from signify.app.clienting import SignifyClient
from mockito import when, unstub

def test_aiding_list():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client=client)

    res = Response()
    res.headers["content-range"] = "aids 0-10/2"
    
    when(client).get("/identifiers", headers=dict(Range=f"aids={0}-{24}")).thenReturn(res)
    when(res).json().thenReturn(
        ["aid1", "aid2"]
    )

    out = ids.list()
    assert out['start'] == 0
    assert out['end'] == 10
    assert out['total'] == 2
    assert out['aids'] == ["aid1", "aid2"]

    unstub()

def test_aiding_get():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    id = Identifiers(client=client)

    res = Response()

    when(client).get("/identifiers/aid1").thenReturn(res)
    when(res).json().thenReturn({"name": "aid1"})

    out = id.get(name="aid1")

    assert out["name"] == "aid1"

    unstub()


def test_aiding_create():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client=client)

    # ids.create(name="new_aid")

    unstub()

def test_aiding_update():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_delete():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_interact():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_rotate():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_add_end_role():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_sign():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_member():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()

def test_aiding_make_end_role():
    client = SignifyClient(passcode="abcdefghijklmnop01234")
    ids = Identifiers(client)

    unstub()
