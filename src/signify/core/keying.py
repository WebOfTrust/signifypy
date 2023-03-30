from keri.app.keeping import SaltyCreator, Algos
from keri.core import coring


class Manager:

    def __init__(self, salter):
        self.salter = salter

    def _signer(self, aid):
        if Algos.salty in aid:
            signer = SaltySigner(salter=self.salter, aid=aid)

        elif Algos.group in aid:
            signer = GroupSigner(aid=aid)

        elif Algos.randy in aid:
            signer = RandySigner()
        else:
            signer = ExternalSigner()

        return signer

    def keys(self, kidx, aid):
        return self._signer(aid).keys(kidx)

    def ndigs(self, aid):
        return self._signer(aid).ndigs()

    def sign(self, ser, aid):
        return self._signer(aid).sign(ser)


class SaltySigner:

    def __init__(self, salter, aid):
        self.salter = salter
        salt = aid[Algos.salty]
        stem = salt["stem"]
        tier = salt["tier"]
        self.icodes = salt["icodes"]
        self.ncodes = salt["ncodes"]
        self.dcode = salt["dcode"]
        self.pidx = salt["pidx"]

        state = aid["state"]
        self.transferable = aid["transferable"]

        self.count = len(state['k'])
        self.ridx = int(state["ee"]["s"], 16)

        self.creator = SaltyCreator(salt=salter.qb64, stem=stem, tier=tier)

    def keys(self, kidx):
        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, ridx=self.ridx, kidx=kidx,
                                      transferable=self.transferable)
        return [signer.verfer.qb64 for signer in signers]

    def ndigs(self):
        nsigners = self.creator.create(codes=self.ncodes, pidx=self.pidx, ridx=self.ridx + 1, kidx=len(self.icodes),
                                       transferable=self.transferable)
        return [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]

    def sign(self, ser, rotate=False):
        ridx = self.ridx
        if rotate:
            ridx = ridx + 1

        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, ridx=ridx, kidx=0,
                                      transferable=self.transferable)
        sigs = [signer.sign(ser=ser, index=idx).qb64 for idx, signer in enumerate(signers)]

        return sigs


class RandySigner:
    pass


class ExternalSigner:
    pass


class GroupSigner:
    def __init__(self, salter, aid):
        group = aid[Algos.group]
        self.smids = group["smids"]
        self.rmids = group["rmids"]



    def keys(self, kidx):
        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, ridx=self.ridx, kidx=kidx,
                                      transferable=self.transferable)
        return [signer.verfer.qb64 for signer in signers]

    def ndigs(self):
        nsigners = self.creator.create(codes=self.ncodes, pidx=self.pidx, ridx=self.ridx + 1, kidx=len(self.icodes),
                                       transferable=self.transferable)
        return [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]

    def sign(self, ser, rotate=False):
        ridx = self.ridx
        if rotate:
            ridx = ridx + 1

        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, ridx=ridx, kidx=0,
                                      transferable=self.transferable)
        sigs = [signer.sign(ser=ser, index=idx).qb64 for idx, signer in enumerate(signers)]

        return sigs
