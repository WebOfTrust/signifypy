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
from keria.app.agenting import Agent

from signify.app.clienting import SignifyClient
from signify.core import api


def create_agent(bran, ctrlAid, url: str = '', boot_url: str = ""):
    """Creates a SignifyClient instance and boots an agent for that controller and then returns the client."""
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
        doist.recur(deeds=decking.Deck(deeds))
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