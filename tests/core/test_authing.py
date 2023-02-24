# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.authing module

Testing authentication
"""
import falcon
import pytest
from falcon import testing
from hio.help import Hict
from keri import kering
from keri.app import habbing
from keri.core import parsing, eventing

from signify.core import authing


def test_authenticater(mockHelpingNowUTC):
    salt = b'0123456789abcdef'
    with habbing.openHab(name="controller", salt=salt, temp=True) as (controllerHby, controller), \
            habbing.openHab(name="agent", salt=salt, temp=True) as (agentHby, agent):

        # Create authenticater with Agent and controllers AID
        authn = authing.Authenticater(agent=agent, ctrl=controller)
        signer = authing.Authenticater(agent=controller)

        rep = falcon.Response()
        with pytest.raises(kering.AuthNError):  # Should fail if Agent hasn't resolved controller's KEL
            authn.verify(rep)

        agentKev = eventing.Kevery(db=agent.db, lax=True, local=False)
        icp = controller.makeOwnInception()
        parsing.Parser().parse(ims=bytearray(icp), kvy=agentKev)

        assert controller.pre in agent.kevers

        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", "256"),
            ("Connection", "close"),
            ("Signify-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        headers = signer.sign(headers, method="POST", path="/boot")
        assert dict(headers) == {'Connection': 'close',
                                 'Content-Length': '256',
                                 'Content-Type': 'application/json',
                                 'Signature': 'indexed="?0";signify="0BBuKkeizz5dM7MurQd7i3PyYh5kariHlZ0id01UJJfYfl5gKr'
                                              'Bg5BPsTKyIySCnQfBgEiCaDvC5NCC0kon_8QEI"',
                                 'Signature-Input': 'signify=("signify-resource" "@method" "@path" '
                                                    '"signify-timestamp");created=1609459200;keyid="EAM6vT0VYoaEWxRTgr'
                                                    '24g0nZHmPSUBgs19WB43zEKHnz";alg="ed25519"',
                                 'Signify-Resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
                                 'Signify-Timestamp': '2022-09-24T00:05:48.196795+00:00'}

        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))
        assert authn.verify(req)


def test_agent():
    salt = b'0123456789abcdef'
    anchor = "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"
    with habbing.openHab(name="agent", salt=salt, temp=True, data=[anchor]) as (_, hab):
        kel = []
        assert hab.pre == "EMxaZwqassOlnl33B8MqsYZfm-_uVaAEdyOf_uZuAK8B"
        icp, sigs, _ = hab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))

        hab.rotate()
        rot, sigs, _ = hab.getOwnEvent(sn=1)
        kel.append(dict(ked=rot.ked, sig=sigs[0].qb64))
        assert rot.said == "EB3J34zJS_BfIaaO_N2Efulk5GF8ZI2BGzOD2HbX9wiR"

        hab.rotate()
        rot, sigs, _ = hab.getOwnEvent(sn=2)
        kel.append(dict(ked=rot.ked, sig=sigs[0].qb64))
        assert rot.said == "ECgCwYVemBbwFZ5YqanWX9RowsnBFjn7kMdxSVwJa5AN"

        assert hab.kever.sn == 2

        agent = authing.Agent(kel=kel)
        assert agent.pre == hab.pre
        assert agent.anchor == anchor
        assert agent.verfer.qb64 == "DIhwCPtuYnIudD4Kqd8tZ9B6XvTSbGkjXGMA38u1K4tu"
        assert agent.verfer.qb64 == hab.kever.verfers[0].qb64

    # Inception event with 2 keys is invalid
    with habbing.openHby(name="agent", temp=True) as (hby):
        kel = []
        hab = hby.makeHab(name="agent", icount=2)
        assert hab.pre == "ED1l3hmrwWCCP70E2FNJoDhkbyrFY3EYr6UK_AgKt3TQ"

        icp, sigs, _ = hab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))

        with pytest.raises(kering.ValidationError) as ex:
            _ = authing.Agent(kel=kel)

        assert ex.value.args[0] == "agent inception event can only have one key"

    # Inception event with 2 next keys is invalid
    with habbing.openHby(name="agent", temp=True) as (hby):
        kel = []
        hab = hby.makeHab(name="agent", ncount=2)
        assert hab.pre == "EGBs12Z55x-iiZvxLQF4ZCVkJFmQm3m-dE701Vur1STw"

        icp, sigs, _ = hab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))

        with pytest.raises(kering.ValidationError) as ex:
            _ = authing.Agent(kel=kel)

        assert ex.value.args[0] == "agent inception event can only have one next key"

