# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.keeping module

"""


import importlib

from keri import kering
from keri.app import keeping
from keri.core import coring
from keri.core.coring import Tiers, MtrDex


class Manager:

    def __init__(self, salter, extern_modules=None):
        self.salter = salter
        extern_modules = extern_modules if extern_modules is not None else []
        self.modules = dict()
        for module in extern_modules:
            typ = module["type"]
            name = module["name"]
            params = module["params"]

            pkg = importlib.import_module(name)
            mod = pkg.module(**params)

            self.modules[typ] = mod

    def new(self, algo, pidx, **kwargs):
        match algo:
            case keeping.Algos.salty:
                return SaltyKeeper(salter=self.salter, pidx=pidx, **kwargs)

            case keeping.Algos.group:
                return GroupKeeper(mgr=self, **kwargs)

            case keeping.Algos.randy:
                return RandyKeeper(salter=self.salter, **kwargs)

            case keeping.Algos.extern:
                typ = kwargs["extern_type"]
                if typ not in self.modules:
                    raise kering.ConfigurationError(f"unsupported external module type {typ}")
                mod = self.modules[typ]

                eargs = kwargs["extern"]
                return mod.shim(pidx=pidx, **eargs)

    def get(self, aid):
        pre = coring.Prefixer(qb64=aid["prefix"])
        if keeping.Algos.salty in aid:
            kwargs = aid[keeping.Algos.salty]
            if "pidx" not in kwargs:
                raise kering.ConfigurationError(f"missing pidx in {kwargs}")
            return SaltyKeeper(salter=self.salter, **kwargs)

        elif keeping.Algos.randy in aid:
            kwargs = aid[keeping.Algos.randy]
            return RandyKeeper(salter=self.salter, transferable=pre.transferable, **kwargs)

        elif keeping.Algos.group in aid:
            kwargs = aid[keeping.Algos.group]
            return GroupKeeper(mgr=self, **kwargs)


class BaseKeeper:

    @property
    def algo(self):
        if isinstance(self, SaltyKeeper):
            return keeping.Algos.salty
        elif isinstance(self, RandyKeeper):
            return keeping.Algos.randy
        elif isinstance(self, GroupKeeper):
            return keeping.Algos.group
        else:
            return keeping.Algos.extern

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
    """
    Keeper class for managing keys for an AID that uses a hierarchical deterministic key chain with a salt
    per AID.  The passcode is used as an encryption key to encrypt and store the AID's salt on the server.
    This class can either be instantiated with an encrypted salt or None which will create a random salt for this AID.

    """
    stem = "signify:aid"

    def __init__(self, salter, pidx, kidx=0, tier=Tiers.low, transferable=False, stem=None,
                 code=MtrDex.Ed25519_Seed, count=1, icodes=None, ncode=MtrDex.Ed25519_Seed,
                 ncount=1, ncodes=None, dcode=MtrDex.Blake3_256, bran=None, sxlt=None):
        """
        Create an instance of a SaltyKeeper for managing keys for a single AID.  This can be created from
        data saved externally to recreate keys at a given point in time or with values for a new AID.  The sxlt
        parameter can contain an existing encrypted salt to use for the HDK algorithm for this key chain or None
        to create a new random one for a new AID


        Parameters:
            salter (Salter): encryption salter used for encrypting the AID salt.  Typically user passcode
            pidx (int):  prefix relative index for this AID in a Habery of AIDs
            kidx (int): key index for the current state of the key chain
            tier (Tiers): secret derivation security tier
            transferable (bool): True if the AID for this keeper can establish new keys
            stem (str): prefix for the path generated for key creation
            code (str): derivation code for signing key creation
            count (int): number of signing keys
            icodes (list): alternate to code and count to be specific about key codes
            ncode (str): derivation code for rotation key creation
            ncount (int): number of rotation keys
            ncodes (list): alternate to ncode and ncount to be specific about rotation key codes
            dcode (str): derivation code for hashing algorithm for next key digests
            bran (str): AID specific salt to use for key generate for this AID inception
            sxlt (str): qualified base64 of cipher of AID salt.
        """

        if not icodes:  # if not codes make list len count of same code
            icodes = [code] * count
        if not ncodes:
            ncodes = [ncode] * ncount

        # Salter is the entered passcode and used for enc/dec of salts for each AID
        signer = salter.signer(transferable=False)
        self.aeid = signer.verfer.qb64
        self.encrypter = coring.Encrypter(verkey=self.aeid)
        self.decrypter = coring.Decrypter(seed=signer.qb64)

        self.tier = tier
        self.icodes = icodes
        self.ncodes = ncodes
        self.dcode = dcode
        self.pidx = pidx
        self.kidx = kidx
        self.transferable = transferable
        stem = stem if stem is not None else self.stem

        # sxlt is encrypted salt for this AID or None if incepting
        if bran is not None:
            bran = coring.MtrDex.Salt_128 + 'A' + bran[:21]
            self.creator = keeping.SaltyCreator(salt=bran, stem=stem, tier=tier)
            self.sxlt = self.encrypter.encrypt(self.creator.salt).qb64
        elif sxlt is None:
            self.creator = keeping.SaltyCreator(stem=stem, tier=tier)
            self.sxlt = self.encrypter.encrypt(self.creator.salt).qb64
        else:
            self.sxlt = sxlt
            ciph = coring.Cipher(qb64=self.sxlt)
            self.creator = keeping.SaltyCreator(self.decrypter.decrypt(cipher=ciph).qb64, stem=stem, tier=tier)

    def params(self):
        """ Get AID parameters to store externally """

        return dict(
            sxlt=self.sxlt,
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
        """ Create verfers and digers for inception event for AID represented by this Keeper

        Args:
            transferable (bool): True if the AID for this keeper can establish new keys

        Returns:
            verfers(list): qualified base64 of signing public keys
            digers(list): qualified base64 of hash of rotation public keys

        """
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
        """ Rotate and return verfers and digers for next rotation event for AID represented by this Keeper

        Args:
            ncodes (list):
            transferable (bool): derivation codes for rotation key creation

        Returns:
            verfers(list): qualified base64 of signing public keys
            digers(list): qualified base64 of hash of rotation public keys

        """
        signers = self.creator.create(codes=self.ncodes, pidx=self.pidx, kidx=self.kidx + len(self.icodes),
                                      transferable=self.transferable)
        verfers = [signer.verfer.qb64 for signer in signers]

        self.kidx = self.kidx + len(self.icodes)
        nsigners = self.creator.create(codes=ncodes, pidx=self.pidx, kidx=self.kidx + len(self.icodes),
                                       transferable=transferable)
        digers = [coring.Diger(ser=nsigner.verfer.qb64b, code=self.dcode).qb64 for nsigner in nsigners]

        return verfers, digers

    def sign(self, ser, indexed=True, indices=None, ondices=None):
        """ Sign provided data using the current signing keys for AID

        Args:
            ser (bytes): data to sign
            indexed (bool): True indicates the signatures are to be indexed signatures (indexed code)
            indices (list): specified signing indicies for each signature generated
            ondices (list): specified rotation indicies for each signature generated

        Returns:
            list: qualified b64 CESR encoded signatures

        """
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

        self.creator = keeping.RandyCreator()

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

    def sign(self, ser, indexed=True, **_):
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
