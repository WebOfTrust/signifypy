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
from signify.core.authing import Authenticater
from keria.testing.testing_helper import Helpers
from signify.core import authing

agentPre="EH1arTrTyQkrxK-cog7rzjahB0skymgrDsPbPcg45sC9"
userPub="ELI7pg979AdhmvrjDeam2eAO2SR5niCgnjAJXJHtJose"
userAid="EK35JRNdfVkO4JwhXaSTdV4qzB_ibk_tGJmSVcY4pZqx"

def test_authenticater(mockHelpingNowUTC):
    bran = b'0123456789abcdefghijk'
    ctrl = authing.Controller(bran=bran, tier=Tiers.low)
    with Helpers.openKeria(salter=ctrl.salter) as (agency, agent, app, client):

        dgkey = dbing.dgKey(agent.agentHab.pre, agent.agentHab.kever.serder.said)  # get message
        raw = agent.hby.db.getEvt(key=dgkey)
        serder = coring.Serder(raw=bytes(raw))

        sigs = agent.hby.db.getSigs(key=dgkey)
        evt = dict(
            ked=serder.ked,
            sig=coring.Siger(qb64b=bytes(sigs[0])).qb64
        )

        # signify agent
        sAgent = authing.Agent(state=evt["ked"])

        # Create authenticater with Agent and controllers AID
        authn = authing.Authenticater(agent=sAgent, ctrl=ctrl)

        method = "POST"
        path = "/boot"
        headers = dict([
            ("Content-Type", "application/json"),
            ("content-length", "256"),
            ("Connection", "close"),
            ("signify-resource", ctrl.pre),
            ("signify-timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        header, qsig = ending.siginput("signify", method, path, headers, fields=Authenticater.DefaultFields, hab=agent.agentHab,
                                       alg="ed25519", keyid=agent.pre)
        headers |= header
        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers |= ending.signature([signage])

        headd = dict(headers)
        assert headd['Connection'] == 'close'
        assert headd['Content-Type'] == 'application/json'
        assert headd['Signature'] == 'indexed="?0";signify="0BAuFfKJ-Kl7zfH5aWXDz9F0njST3t9NH4icNKpiF_NP0BnUqWx0YVIjdfQlXz-7BM2YtDJCZO5Jr4LuDyPDaucD"'
        assert headd['Signature-Input'] == f'signify=("@method" "@path" "content-length" "signify-resource" "signify-timestamp");created=1609459200;keyid="{agentPre}";alg="ed25519"'
        assert headd['content-length'] == '256'
        assert headd['signify-resource'] == ctrl.pre
        assert headd['signify-timestamp'] == '2022-09-24T00:05:48.196795+00:00'
        req = testing.create_req(method="POST", path="/boot", headers=dict(headers))
        assert authn.verifysig(req.headers, "POST", "/boot")


def test_agent():
    bran = b'0123456789abcdefghijk'
    ctrl = authing.Controller(bran=bran, tier=Tiers.low)
    with Helpers.openKeria(salter=ctrl.salter) as (agency, kAgent, app, client):
        kel = []
        ahab = kAgent.agentHab
        assert ahab.pre == f"{agentPre}"
        assert ahab.kever.verfers[0].qb64 == "DCajWNxkIK7FQWTDZpcvv3_EcRDj6HWVVx-HFEjrmBPL"
        icp, sigs, _ = ahab.getOwnEvent(sn=0)
        kel.append(dict(ked=icp.ked, sig=sigs[0].qb64))
        sAgent = authing.Agent(state=icp.ked)

        ahab.rotate()
        rot, sigs, _ = ahab.getOwnEvent(sn=1)
        kel.append(dict(ked=rot.ked, sig=sigs[0].qb64))
        assert rot.said == "EAZDlwT9z6269nmW6yjuIOYIR-GR6soqqdYvIS8FUd_m"
        assert ahab.kever.verfers[0].qb64 == "DB9RaU1cm3PcpJWcSZ_w_qFmap3fr5qgVXhQy5yXJLAo"

        ahab.rotate()
        rot, sigs, _ = ahab.getOwnEvent(sn=2)
        kel.append(dict(ked=rot.ked, sig=sigs[0].qb64))
        assert rot.said == "EI3uC6o-o9h62hjEz6i2lEWQUIPDI4GCDfF7Gw2eXPRv"

        assert ahab.kever.sn == 2

        assert kAgent.pre == ahab.pre
        assert sAgent.pre == ahab.pre
        assert kAgent.caid == userAid
        assert sAgent.delpre == userAid
        assert sAgent.verfer.qb64 == 'DCajWNxkIK7FQWTDZpcvv3_EcRDj6HWVVx-HFEjrmBPL'
        assert ahab.kever.verfers[0].qb64 == "DFzRzCjvWRuMfcCo2CiOpx-sWXEHxDByv2J907Yqb-Nq"
        # TODO: This used to be an equality check, but rotation should make it non-equal?
        assert sAgent.verfer.qb64 != ahab.kever.verfers[0].qb64

        # Inception event with 2 keys is invalid
        orig=icp.ked["k"]
        # adding agent verfer is non-sensicle but helpful for causing the exception
        badTestValue=[icp.verfers[0].qb64,coring.Verfer(qb64=ahab.kever.verfers[0].qb64).qb64]
        icp.ked["k"]=badTestValue
        with pytest.raises(kering.ValidationError) as ex:
            _ = authing.Agent(state=icp.ked)

        assert ex.value.args[0] == "agent inception event can only have one key"
        
        # reset to original value
        icp.ked["k"]=orig

        # TODO we used to validate the next key of the agent, but our Agent doesn't validate next keys
        # Inception event with 2 next keys is invalid
        # orig=icp.ked["n"]
        # # adding agent diger is non-sensicle but helpful for causing the exception
        # badTestValue=[icp.digers[0].qb64,coring.Diger(qb64=ahab.kever.digers[0].qb64).qb64]
        # icp.ked["n"]=badTestValue

        # with pytest.raises(kering.ValidationError) as ex:
        #     _ = authing.Agent(state=icp.ked)

        # assert ex.value.args[0] == "agent inception event can only have one next key"

