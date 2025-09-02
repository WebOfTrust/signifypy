# -*- encoding: utf-8 -*-
"""
SIGNIFY
test.keria_api module

Contains helper functions for integration tests against a KERIA server running in a separate
thread for the end to end integration tests in test_e2e.py.
"""
from time import sleep
from typing import List

from hio.base import Doer, Doist
from hio.help import decking
from keri.app import signing
from keri.core import coring, signing as csigning, eventing
from keri.core.serdering import SerderACDC, SerderKERI
from keri.help import helping
from keria.app.agenting import Agent

from signify.app.clienting import SignifyClient
from signify.core import api

def _create_timestamp():
    return helping.nowIso8601()


def create_agent(bran: bytes, ctrlAid: str, url: str = '', boot_url: str = ""):
    """
    Creates a SignifyClient instance and boots an agent for that controller and then returns the client.
    Parameters:
        bran: passcode for the controller
        ctrlAid: expected identifier prefix of the controller (run test first to determine what this should be)
        url: URL of the KERIA server to connect to
        boot_url: URL of the KERIA boot server to use to bootstrap the controller's agent
    """
    client = SignifyClient(passcode=bran, url=url, boot_url=boot_url)
    assert client.controller == ctrlAid
    client.boot()
    client.connect(url=url)
    assert client.agent is not None
    assert client.agent.delpre == ctrlAid
    return client

def resolve_oobi(client, alias, url, agent, doist: Doist, deeds: List[Doer]):
    """
    Resolves an OOBI for the specified client. Expects the deeds of either a witness or agent
    to be passed in so that doist.recur will process the OOBI resolution call for whatever the component
    hosting the target KEL is.
    """
    oobis = client.oobis()
    operations = client.operations()

    op = oobis.resolve(oobi=url, alias=alias)
    op = api.Operation(**op)
    while not agent.monitor.get(op.name).done:
        if deeds:
            doist.recur(deeds=decking.Deck(deeds))
        else:
            sleep(0.25)
    op = operations.get(op.name)
    return op["response"]


def create_identifier(client: SignifyClient, name: str, agent: Agent, doist: Doist, deeds: List[Doer], toad: int = None, wits: List[str] = None):
    """
    Creates an identifier in the agent with the specified witnesses and threshold.
    Waits for completion and then assigns the "agent" endpoint role to the agent for this identifier.
    Returns the result of identifiers().get().
    """
    wits = [] if not wits else wits
    toad = str(len(wits)) if toad is None else str(toad)
    icp_srdr, sigs, op = client.identifiers().create(name, toad=toad, wits=wits)

    op = api.Operation(**op)
    while not agent.monitor.get(op.name).done:
        doist.recur(deeds=decking.Deck(deeds))

    hab = client.identifiers().get(name)
    client.identifiers().addEndRole(name=name, eid=client.agent.pre)
    return hab


def create_registry(client: SignifyClient, name: str, registry_name: str, agent: Agent, doist: Doist, deeds: List[Doer]):
    """
    Creates a registry under the specified identifier name with the specified registry name.
    Waits for completion and then returns the result of registries().get().
    """
    hab = client.identifiers().get(name)
    regser, serder, sigs, op = client.registries().create(hab=hab, registryName=registry_name)

    op = api.Operation(**op)
    while not agent.monitor.get(op.name).done:
        doist.recur(deeds=decking.Deck(deeds))

    registry = client.registries().get(name=name, registryName=registry_name)
    return registry

def issue_credential(client: SignifyClient, name: str, registry_name: str, schema: str, recipient: str, data, agent: Agent, doist: Doist, deeds: List[Doer], rules: dict = None, edges: list = None):
    """
    Parameters:
        client: SignifyClient instance
        name: name of the issuer's identifier
        registry_name: name of the credential registry to use
        schema: SAID of the schema to use for the credential
        recipient: qb64 identifier prefix of the recipient of the credential
        data: dict of the credential subject data
        agent: Agent instance for the controller of the issuer
        doist: Doist instance used to process the deeds
        deeds: List of Doer instances needed to process the issuance
    """
    hab = client.identifiers().get(name)
    registry = client.registries().get(name, registryName=registry_name)
    creder, iserder, anc, sigs, op = client.credentials().create(
        hab, registry=registry, data=data, schema=schema,
        recipient=recipient, rules=rules, edges=edges, timestamp=_create_timestamp())

    op = api.Operation(**op)
    while not agent.monitor.get(op.name).done:
        doist.recur(deeds=decking.Deck(deeds))
    return creder, iserder, anc, sigs

def ipex_grant(client: SignifyClient, agent: Agent, name: str, creder: SerderACDC, iss_serder: SerderKERI, iss_anc: SerderKERI, sigs: List[str], recipient: str):
    """
    Performs an IPEX Grant for a given credential.
    Parameters:
        client: SignifyClient instance
        name: name of the identifier in the client to use as the issuer
        creder: SerderACDC instance of the credential to grant
        iss_serder: SerderKERI anchor of the credential issuance
        iss_anc: SerderKERI instance of the issuer's last event (to anchor the grant)
        sigs: List of signatures (siger.qb64 per sig) over the credential by the issuer
        recipient: qb64 identifier prefix of the recipient of the credential
    """
    hab = client.identifiers().get(name)
    prefixer = coring.Prefixer(qb64=iss_serder.pre)
    seqner = coring.Seqner(sn=iss_serder.sn)
    acdc = signing.serialize(creder, prefixer, seqner, coring.Saider(qb64=iss_serder.said))
    iss = client.registries().serialize(iss_serder, iss_anc)

    grant, sigs, end = client.ipex().grant(
        hab, recp=recipient, acdc=acdc, iss=iss, message="",
        anc=eventing.messagize(serder=iss_anc,
                               sigers=[csigning.Siger(qb64=sig) for sig in sigs]),
        dt=_create_timestamp(),)

    op = client.ipex().submitGrant(
        name=name, exn=grant, sigs=sigs, atc=end, recp=[recipient]
    )
    op = api.Operation(**op)
    while not agent.monitor.get(op.name).done:
        sleep(0.25)

    # response = client.exchanges().sendFromEvents(
    #     name=name, topic="credential", exn=grant, sigs=sigs, atc=end,
    #     recipients=[recipient])
    return grant

def wait_for_notification(client: SignifyClient, route: str):
    while True:
        notifications = client.notifications().list()
        for notif in notifications['notes']:
            if notif['a']['r'] == route:
                return notif
        sleep(0.25)

def admit_credential(client: SignifyClient, name: str, said: str, recipient: List[str], agent: Agent):
    dt = _create_timestamp()
    hab = client.identifiers().get(name)

    admit, sigs, end = client.ipex().admit(hab, '', said, dt)

    op = client.ipex().submitAdmit(name=name, exn=admit, sigs=sigs, atc=end, recp=recipient)
    op = api.Operation(**op)
    while not agent.monitor.get(op.name).done:
        sleep(0.25)
    return admit
