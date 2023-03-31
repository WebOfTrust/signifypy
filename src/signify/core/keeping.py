from keri.app.keeping import SaltyCreator, Algos
from keri.core import coring


class Manager:

    def __init__(self, salter):
        self.salter = salter

    def _signer(self, aid):
        if Algos.salty in aid:
            signer = SaltySigner(salter=self.salter, aid=aid)

        elif Algos.group in aid:
            signer = GroupSigner(mgr=self, aid=aid)

        elif Algos.randy in aid:
            signer = RandySigner()

        else:
            signer = ExternalSigner()

        return signer

    def keys(self, kidx, aid):
        return self._signer(aid).keys(kidx)

    def ndigs(self, aid):
        return self._signer(aid).ndigs()

    def sign(self, ser, aid, indexed=True, indices=None, ondices=None, rotate=False):
        return self._signer(aid).sign(ser, indexed=indexed, indices=indices, ondices=ondices, rotate=rotate)


class BaseSigner:

    @staticmethod
    def __sign__(ser, signers, indexed=False, indices=None, ondices=None):
        if indexed:
            sigers = []
            for j, signer in enumerate(signers):
                if indices:  # not the default get index from indices
                    i = indices[j]  # must be whole number
                    if not isinstance(i, int) or i < 0:
                        raise ValueError(f"Invalid signing index = {i}, not "
                                         f"whole number.")
                else:  # the default
                    i = j  # same index as database

                if ondices:  # not the default get ondex from ondices
                    o = ondices[j]  # int means both, None means current only
                    if not (o is None or
                            isinstance(o, int) and not isinstance(o, bool) and o >= 0):
                        raise ValueError(f"Invalid other signing index = {o}, not "
                                         f"None or not whole number.")
                else:  # default
                    o = i  # must both be same value int
                # .sign assigns .verfer of siger and sets code of siger
                # appropriately for single or dual indexed signatures
                sigers.append(signer.sign(ser,
                                          index=i,
                                          only=True if o is None else False,
                                          ondex=o))
            return [siger.qb64 for siger in sigers]

        else:
            cigars = []
            for signer in signers:
                cigars.append(signer.sign(ser))  # assigns .verfer to cigar
            return [cigar.qb64 for cigar in cigars]


class SaltySigner(BaseSigner):

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

    def sign(self, ser, indexed=False, indices=None, ondices=None, rotate=False):
        ridx = self.ridx
        if rotate:
            ridx = ridx + 1

        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, ridx=ridx, kidx=0,
                                      transferable=self.transferable)

        return self.__sign__(ser, signers=signers, indexed=indexed, indices=indices, ondices=ondices)


class RandySigner:
    pass


class ExternalSigner:
    pass


class GroupSigner:
    def __init__(self, mgr: Manager, aid):
        self.mgr = mgr
        group = aid[Algos.group]
        self.gkeys = group["keys"]
        self.gdigs = group["ndigs"]
        self.mhab = group["mhab"]

    def keys(self, kidx):
        return self.gkeys

    def ndigs(self):
        return self.gdigs

    def sign(self, ser, indexed=True, rotate=False, **kwargs):
        key = self.mhab['state']['k'][0]
        ndig = self.mhab['state']['n'][0]

        csi = self.gkeys.index(key)
        pni = self.gdigs.index(ndig)
        return self.mgr.sign(ser, self.mhab, indexed=indexed, indices=[csi], ondices=[pni], rotate=rotate)
