from typing import List

from hio.base import doing
from keri.app import notifying, signing, forwarding
from keri.app.habbing import Habery, Hab
from keri.core import serdering, coring, parsing
from keri.peer import exchanging
from keri.peer.exchanging import Exchanger
from keri.vc import protocoling
from keri.vdr import credentialing
from keri.vdr.credentialing import Regery


class GrantContainer(doing.DoDoer):
    def __init__(self, hby: Habery, hab: Hab, regery: Regery, tymth, timeout: float=5.0):
        self.always = False
        self.done=False
        self.hby = hby
        self.hab = hab
        self.rgy = regery
        self.tymth = tymth
        self.timeout = timeout

        notifier = notifying.Notifier(hby=hby)
        exc = exchanging.Exchanger(hby=hby, handlers=[])
        protocoling.loadHandlers(hby, exc, notifier)
        self.exc = exc
        self.grants: List[str] = []
        super(GrantContainer, self).__init__(tymth=self.tymth)  # have to pass tymth through or it fails

    def kli_grant(self, said: str, recp: str, message: str = None, timestamp: str = None):
        grant_doer = KliGrantDoer(
            grant_cont=self,
            hby=self.hby,
            hab=self.hab,
            regery=self.rgy,
            exc=self.exc,
            said=said,
            recp=recp,
            message=message,
            timestamp=timestamp
        )
        self.grants.append(said)
        self.extend([grant_doer])

    def _remove_grant(self, said):
        self.grants.remove(said)
        if not self.grants:
            self.done = True

    def recur(self, tyme, deeds=None):
        if not self.grants:
            return True
        super(GrantContainer, self).recur(tyme, deeds)
        return False


class KliGrantDoer(doing.Doer):
    """
    This is a simple single-sig IPEX Grant Doer for use in tests.
    """
    def __init__(self, grant_cont: GrantContainer, hby: Habery, hab: Hab, regery: Regery, exc: Exchanger,
                 said: str, recp: str, message: str = None, timestamp: str = None, tock=0.0, **kwa):
        self.parent = grant_cont
        self.hby = hby
        self.hab = hab
        self.rgy = regery
        self.exc = exc
        self.said = said
        self.recp = recp
        self.message = message
        self.timestamp = timestamp
        super(KliGrantDoer, self).__init__(tock=tock, **kwa)

    def grant(self):
        recp = self.recp
        if recp is None:
            raise ValueError("recipient is required")
        creder, prefixer, seqner, saider = self.rgy.reger.cloneCred(said=self.said)
        if creder is None:
            raise ValueError(f"invalid credential SAID to grant={self.said}")

        acdc = signing.serialize(creder, prefixer, seqner, saider)

        iss = self.rgy.reger.cloneTvtAt(creder.said)

        iserder = serdering.SerderKERI(raw=bytes(iss))
        seqner = coring.Seqner(sn=iserder.sn)

        serder = self.hby.db.fetchLastSealingEventByEventSeal(creder.sad['i'],
                                                              seal=dict(i=iserder.pre, s=seqner.snh, d=iserder.said))
        anc = self.hby.db.cloneEvtMsg(pre=serder.pre, fn=0, dig=serder.said)

        exn, atc = protocoling.ipexGrantExn(hab=self.hab, recp=recp, message=self.message, acdc=acdc, iss=iss, anc=anc,
                                            dt=self.timestamp)
        msg = bytearray(exn.raw)
        msg.extend(atc)

        parsing.Parser().parseOne(ims=bytes(msg), exc=self.exc)

        sender = self.hab
        postman = forwarding.StreamPoster(hby=self.hby, hab=sender, recp=recp, topic="credential")

        sources = self.rgy.reger.sources(self.hby.db, creder)
        credentialing.sendArtifacts(self.hby, self.rgy.reger, postman, creder, recp)
        for source, atc in sources:
            credentialing.sendArtifacts(self.hby, self.rgy.reger, postman, source, recp)
            postman.send(serder=source, attachment=atc)

        atc = exchanging.serializeMessage(self.hby, exn.said)
        del atc[:exn.size]
        postman.send(serder=exn, attachment=atc)

        cred_poster_doer = doing.DoDoer(doers=postman.deliver())
        self.parent.extend([cred_poster_doer])

        while not cred_poster_doer.done:
            yield self.tock
        self.parent.remove([cred_poster_doer])
        self.parent._remove_grant(self.said)

    def recur(self, tock=0.0, **opts):
        yield from self.grant()
        return True
