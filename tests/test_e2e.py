import threading

from hio.base import doing
from keria.app.agenting import KERIAServerConfig, setupDoers

from signify.app.clienting import SignifyClient


def test_e2e_vlei_present():
    # Helpers.remove_test_dirs()
    # set up KERIA first
    host="127.0.0.1"
    adminPort=3901
    bootPort=3903
    config = KERIAServerConfig(
        name="keria",
        base="",
        configFile="keria",
        configDir="",
        logLevel="INFO",
        adminPort=adminPort,
        httpPort=3902,
        bootPort=bootPort,
    )
    keria_doers = setupDoers(config=config)
    doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
    keria_deeds = doist.enter(doers=keria_doers)

    def run_keria_other_thread(event: threading.Event):
        keria_doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
        while not event.is_set():
            keria_doist.recur(deeds=keria_deeds)

    stop_event = threading.Event()
    keria_thread = threading.Thread(target=run_keria_other_thread, args=(stop_event,))
    keria_thread.start()

    boot_url = f"http://{host}:{bootPort}"
    connect_url = f"http://{host}:{adminPort}"
    bran = b'0123456789abcdefghijk'

    client = SignifyClient(passcode=bran, url=connect_url, boot_url=boot_url)
    client.boot()
    client.connect(url=connect_url)
    identifiers = client.identifiers()
    aids = identifiers.list()
    assert len(aids['aids']) == 0, "No identifiers should be present at this point"

    stop_event.set()
    keria_thread.join(timeout=2)







