from keri.app.keeping import SaltyCreator, Algos, RandyCreator
from keri.core import coring
from keri.core.coring import Tiers, MtrDex


class Manager:

    def __init__(self, salter):
        self.salter = salter

    def new(self, algo, pidx, **kwargs):
        match algo:
            case Algos.salty:
                return SaltyKeeper(salter=self.salter, pidx=pidx, **kwargs)

            case Algos.group:
                return GroupKeeper(mgr=self, **kwargs)

            case Algos.randy:
                return RandyKeeper(salter=self.salter, **kwargs)

            case _:
                return ExternalKeeper()

    def get(self, aid):
        pre = coring.Prefixer(qb64=aid["prefix"])
        if Algos.salty in aid:
            kwargs = aid[Algos.salty]
            return SaltyKeeper(salter=self.salter, **kwargs)

        elif Algos.randy in aid:
            kwargs = aid[Algos.randy]
            return RandyKeeper(salter=self.salter, transferable=pre.transferable, **kwargs)

        elif Algos.group in aid:
            kwargs = aid[Algos.group]
            return GroupKeeper(mgr=self, **kwargs)


class BaseKeeper:

    @property
    def algo(self):
        if isinstance(self, SaltyKeeper):
            return Algos.salty
        elif isinstance(self, RandyKeeper):
            return Algos.randy
        elif isinstance(self, GroupKeeper):
            return Algos.group
        else:
            return Algos.extern

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


class SaltyKeeper(BaseKeeper):
    stem = "signify:aid"

    def __init__(self, salter, pidx, kidx=0, tier=Tiers.low, transferable=False, stem=None,
                 code=MtrDex.Ed25519_Seed, count=1, icodes=None,
                 ncode=MtrDex.Ed25519_Seed, ncount=1, ncodes=None, dcode=MtrDex.Blake3_256):

        self.salter = salter
        if not icodes:  # if not codes make list len count of same code
            icodes = [code] * count
        if not ncodes:
            ncodes = [ncode] * ncount

        self.tier = tier
        self.icodes = icodes
        self.ncodes = ncodes
        self.dcode = dcode
        self.pidx = pidx
        self.kidx = kidx
        self.transferable = transferable
        stem = stem if stem is not None else self.stem

        self.creator = SaltyCreator(salt=salter.qb64, stem=stem, tier=tier)

    def params(self):
        return dict(
            pidx=self.pidx,
            kidx=self.kidx,
            stem=self.stem,
            tier=self.tier,
            icodes=self.icodes,
            ncodes=self.ncodes,
            dcode=self.dcode,
            transferable=self.transferable
        )

    def incept(self, transferable):
        self.transferable = transferable
        self.kidx = 0

        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, kidx=self.kidx,
                                      transferable=transferable)
        verfers = [signer.verfer.qb64 for signer in signers]

        nsigners = self.creator.create(codes=self.ncodes, pidx=self.pidx, kidx=len(self.icodes),
                                       transferable=self.transferable)
        digers = [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]

        return verfers, digers

    def rotate(self, ncodes, transferable, **_):
        signers = self.creator.create(codes=self.ncodes, pidx=self.pidx, kidx=self.kidx + len(self.icodes),
                                      transferable=self.transferable)
        verfers = [signer.verfer.qb64 for signer in signers]

        self.kidx = self.kidx + len(self.icodes)
        nsigners = self.creator.create(codes=ncodes, pidx=self.pidx, kidx=self.kidx + len(self.icodes),
                                       transferable=transferable)
        digers = [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]

        return verfers, digers

    def sign(self, ser, indexed=True, indices=None, ondices=None):
        signers = self.creator.create(codes=self.icodes, pidx=self.pidx, kidx=self.kidx,
                                      transferable=self.transferable)

        return self.__sign__(ser, signers=signers, indexed=indexed, indices=indices, ondices=ondices)


class RandyKeeper(BaseKeeper):
    def __init__(self, salter, code=MtrDex.Ed25519_Seed, count=1, icodes=None, transferable=False,
                 ncode=MtrDex.Ed25519_Seed, ncount=1, ncodes=None, dcode=MtrDex.Blake3_256, prxs=None, nxts=None):

        self.salter = salter
        if not icodes:  # if not codes make list len count of same code
            icodes = [code] * count
        if not ncodes:
            ncodes = [ncode] * ncount

        signer = salter.signer(transferable=False)
        self.aeid = signer.verfer.qb64
        self.encrypter = coring.Encrypter(verkey=self.aeid)
        self.decrypter = coring.Decrypter(seed=signer.qb64)

        self.prxs = prxs
        self.nxts = nxts
        self.transferable = transferable

        self.icodes = icodes
        self.ncodes = ncodes
        self.dcode = dcode

        self.creator = RandyCreator()

    def params(self):
        return dict(
            prxs=self.prxs,
            nxts=self.nxts,
            transferable=self.transferable
        )

    def incept(self, transferable):
        self.transferable = transferable
        signers = self.creator.create(codes=self.icodes, transferable=transferable)
        self.prxs = [self.encrypter.encrypt(matter=signer).qb64 for signer in signers]

        verfers = [signer.verfer.qb64 for signer in signers]

        nsigners = self.creator.create(codes=self.ncodes, transferable=transferable)
        self.nxts = [self.encrypter.encrypt(matter=signer).qb64 for signer in nsigners]
        digers = [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]
        return verfers, digers

    def rotate(self, ncodes, transferable, **_):
        self.transferable = transferable
        self.prxs = self.nxts
        signers = [self.decrypter.decrypt(cipher=coring.Cipher(qb64=nxt),
                                          transferable=self.transferable) for nxt in self.nxts]
        verfers = [signer.verfer.qb64 for signer in signers]

        nsigners = self.creator.create(codes=ncodes, transferable=transferable)
        self.nxts = [self.encrypter.encrypt(matter=signer).qb64 for signer in nsigners]
        digers = [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]

        return verfers, digers

    def sign(self, ser, indexed=True, indices=None, ondices=None, **_):
        signers = [self.decrypter.decrypt(ser=coring.Cipher(qb64=prx).qb64b, transferable=self.transferable)
                   for prx in self.prxs]
        return self.__sign__(ser, signers=signers, indexed=indexed, indices=indices, ondices=ondices)


class GroupKeeper(BaseKeeper):

    def __init__(self, mgr: Manager, mhab=None, states=None, rstates=None,
                 keys=None, ndigs=None):
        self.mgr = mgr

        if states is not None:
            keys = [state['k'][0] for state in states]

        if rstates is not None:
            ndigs = [state['n'][0] for state in rstates]

        self.gkeys = keys
        self.gdigs = ndigs
        self.mhab = mhab

    def incept(self, **_):
        return self.gkeys, self.gdigs

    def rotate(self, states, rstates, **_):
        self.gkeys = [state['k'][0] for state in states]
        self.gdigs = [state['n'][0] for state in rstates]

        return self.gkeys, self.gdigs

    def sign(self, ser, indexed=True, rotate=False, **_):
        key = self.mhab['state']['k'][0]
        ndig = self.mhab['state']['n'][0]

        csi = self.gkeys.index(key)
        pni = self.gdigs.index(ndig)
        mkeeper = self.mgr.get(self.mhab)

        return mkeeper.sign(ser, indexed=indexed, indices=[csi], ondices=[pni])

    def params(self):
        return dict(
            mhab=self.mhab,
            keys=self.gkeys,
            ndigs=self.gdigs
        )


class ExternalKeeper:
    pass
