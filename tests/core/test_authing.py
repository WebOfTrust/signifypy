# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.authing module

Testing authentication
"""
import pytest
from falcon import testing
from keri import kering
from keri.app import habbing
from keri.core import parsing, eventing, coring
from keri.core.coring import Tiers
from keri.db import dbing
from keri.end import ending

from signify.core import authing


def test_authenticater(mockHelpingNowUTC):
    bran = b'0123456789abcdefghijk'

    with habbing.openHby(name="agent", temp=True) as agentHby:

        ctrl = authing.Controller(bran=bran, tier=Tiers.low)
        agentHab = agentHby.makeHab(name="agent", icount=1, isith='1', ncount=1, nsith='1', data=[ctrl.pre], delpre=ctrl.pre)

        dgkey = dbing.dgKey(agentHab.pre, agentHab.kever.serder.said)  # get message
        raw = agentHby.db.getEvt(key=dgkey)
        serder = coring.Serder(raw=bytes(raw))

        sigs = agentHby.db.getSigs(key=dgkey)
        evt = dict(
            ked=serder.ked,
            sig=coring.Siger(qb64b=bytes(sigs[0])).qb64
        )

        agent = authing.Agent(state=evt["ked"])

        # Create authenticater with Agent and controllers AID
        authn = authing.Authenticater(agent=agent, ctrl=ctrl)

        method = "POST"
        path = "/boot"
        headers = dict([
            ("Content-Type", "application/json"),
            ("content-length", "256"),
            ("Connection", "close"),
            ("signify-resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"),
            ("signify-timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        header, qsig = ending.siginput("signify", method, path, headers, fields=authn.DefaultFields, hab=agentHab,
                                       alg="ed25519", keyid=agentHab.pre)
        headers |= header
        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers |= ending.signature([signage])

        assert dict(headers) == {'Connection': 'close',
                                 'Content-Type': 'application/json',
                                 'Signature': 'indexed="?0";signify="0BCnXc1Wz8OfYUSRFz8eSW1AkW3J4D_bJFHiOga-1KbBJ2g_LwlfaZMRqxaMDqsnY02ggwRpUTrTEE7c_lbQ0VQD"',
                                 'Signature-Input': 'signify=("@method" "@path" "content-length" '
                                                    '"signify-resource" '
                                                    '"signify-timestamp");created=1609459200;keyid="EJ-t3M9T3Sq0Xa6XmpWMoNtstEqJWvJoXD_GdIRwvINc";alg="ed25519"',
                                 'content-length': '256',
                                 'signify-resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
                                 'signify-timestamp': '2022-09-24T00:05:48.196795+00:00'}
        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))
        assert authn.verifysig(req.headers, "POST", "/boot")


def test_agent():
    salt = b'0123456789abcdef'
    anchor = "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"
    with habbing.openHab(name="agent", salt=salt, temp=True, data=[anchor], delpre=anchor) as (_, hab):
        kel = []
        assert hab.pre == "EESwpe1cY0YDPrBgVhlFwMq26hhmtl4owg3jSTd-1zP_"
        icp, sigs, _ = hab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))

        hab.rotate()
        rot, sigs, _ = hab.getOwnEvent(sn=1)
        kel.append(dict(ked=rot.ked, sig=sigs[0].qb64))
        assert rot.said == "EE97cLvSQ73H_GpsDYVyShsXxNh9EFr_qYFJ4cFz6eqq"

        hab.rotate()
        rot, sigs, _ = hab.getOwnEvent(sn=2)
        kel.append(dict(ked=rot.ked, sig=sigs[0].qb64))
        assert rot.said == "ENKtgP3irYwtGArIIUp_aerC1Ddq0scGwY2yMZBmdDDi"

        assert hab.kever.sn == 2

        agent = authing.Agent(state=icp.ked)
        assert agent.pre == hab.pre
        assert agent.delpre == anchor
        assert agent.verfer.qb64 == "DHh2g07Bl2UjV6DIOQZ4cu_82r1vuebMQTq-_waXI1ew"
        assert agent.verfer.qb64 == hab.kever.verfers[0].qb64

    # Inception event with 2 keys is invalid
    with habbing.openHby(name="agent", temp=True) as (hby):
        kel = []
        hab = hby.makeHab(name="agent", icount=2)
        assert hab.pre == "ED1l3hmrwWCCP70E2FNJoDhkbyrFY3EYr6UK_AgKt3TQ"

        icp, sigs, _ = hab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))

        with pytest.raises(kering.ValidationError) as ex:
            _ = authing.Agent(state=kel)

        assert ex.value.args[0] == "agent inception event can only have one key"

    # Inception event with 2 next keys is invalid
    with habbing.openHby(name="agent", temp=True) as (hby):
        kel = []
        hab = hby.makeHab(name="agent", ncount=2)
        assert hab.pre == "EGBs12Z55x-iiZvxLQF4ZCVkJFmQm3m-dE701Vur1STw"

        icp, sigs, _ = hab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))

        with pytest.raises(kering.ValidationError) as ex:
            _ = authing.Agent(state=kel)

        assert ex.value.args[0] == "agent inception event can only have one next key"

