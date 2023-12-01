# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.authing module

"""
from urllib.parse import urlparse

from keri import kering
from keri.app import keeping
from keri.core import coring, eventing, serdering

from keri.end import ending
from signify.signifying import State


class Agent:
    def __init__(self, state):
        self.pre = ""
        self.delpre = ""
        self.said = ""
        self.sn = 0
        self.verfer = None

        self.parse(state)

    def parse(self, state):
        self.pre = state['i']
        self.sn = coring.Number(num=state['s']).num
        self.delpre = state['di']
        self.said = state['d']

        if len(state['k']) != 1:
            raise kering.ValidationError(f"agent inception event can only have one key")

        self.verfer = coring.Verfer(qb64=state['k'][0])


class Controller:
    def __init__(self, bran, tier, state=None):
        if hasattr(bran, "decode"):
            bran = bran.decode("utf-8")

        self.bran = coring.MtrDex.Salt_128 + 'A' + bran[:21]  # qb64 salt for seed
        self.stem = "signify:controller"
        self.tier = tier

        self.salter = coring.Salter(qb64=self.bran)
        creator = keeping.SaltyCreator(salt=self.salter.qb64, stem=self.stem, tier=tier)

        self.signer = creator.create(ridx=0, tier=tier).pop()
        self.nsigner = creator.create(ridx=0 + 1, tier=tier).pop()

        self.keys = [self.signer.verfer.qb64]
        self.ndigs = [coring.Diger(ser=self.nsigner.verfer.qb64b).qb64]

        self.serder = self.derive(state)

    @property
    def pre(self):
        return self.serder.pre

    def event(self):
        siger = self.signer.sign(ser=self.serder.raw, index=0)
        return self.serder, siger

    def derive(self, state):
        if state is None or (type(state) is dict and state['ee']['s'] == "0"):
            return eventing.incept(keys=self.keys,
                                   isith="1",
                                   nsith="1",
                                   ndigs=self.ndigs,
                                   code=coring.MtrDex.Blake3_256,
                                   toad="0",
                                   wits=[])
        elif type(state) is State:
            return serdering.SerderKERI(sad=state.controller['ee'])

    def approveDelegation(self, agent):
        seqner = coring.Seqner(sn=agent.sn)
        anchor = dict(i=agent.pre, s=seqner.snh, d=agent.said)

        self.serder = eventing.interact(pre=self.serder.pre, dig=self.serder.said, sn=self.serder.sn + 1, data=[anchor])
        return self.serder, [self.signer.sign(self.serder.raw, index=0).qb64]

    def rotate(self, nbran, aids):
        """
        Rotate passcode involves re-encrypting all saved AID salts for salty keyed AIDs and
        all signing priv keys and next pub/priv keys for randy keyed AIDs.  The controller AID salt must be re-encrypted
         too. The old salt must be encrypted and stored externally in case key re-encryption fails halfway
        through the procedure.  The presence of an encrypted old key signals that recovery is needed.  Otherwise, the
        old key encryption material is deleted and the current passcode is the only one needed.  Steps:

        1. Encrypt and save old enc salt
        2. Rotate local Controller AID and share with Agent
        3. Retrieve all AIDs
        4. For each Salty AID, decrypt AID salt with old salt, re-encrypt with new salt, save
        5. For each Randy AID, decrypt priv signing and next keys and next pub keys, re-encrypt with new passcode, save
        6. Delete saved encrypted old enc salt

        In the event of a crash half way thru a recovery will be needed.  That recovery process is triggered with the
        discovery of a saved encrypted old salt.  When found, the following steps are needed:

        1. Retrieve and decrypt the saved old salt for enc key
        2. Ensure the local Conroller AID is rotated to the current new salt
        3. Retrieve all AIDs
        4. For each Salty AID, test if the AID salt is encrypted with old salt, re-encrypt as needed.
        5. For each Randy AID, test if the priv signing and next keys and next pub keys are encrypted with old salt,
         re-encrypt as needed.
        6. Delete saved encrypted old enc salt


        Parameters:
            nbran (str):  new passcode to use for re-encryption
            aids (list): all AIDs from the agent

        """

        # First we create the new salter and then use it to encrypted the OLD salt
        nbran = coring.MtrDex.Salt_128 + 'A' + nbran[:21]  # qb64 salt for seed
        nsalter = coring.Salter(qb64=nbran)
        nsigner = self.salter.signer(transferable=False)

        # This is the previous next signer so it will be used to sign the rotation and then have 0 signing authority
        #here
        creator = keeping.SaltyCreator(salt=self.salter.qb64, stem=self.stem, tier=self.tier)
        signer = creator.create(ridx=0 + 1, tier=self.tier).pop()

        ncreator = keeping.SaltyCreator(salt=nsalter.qb64, stem=self.stem, tier=self.tier)
        self.signer = ncreator.create(ridx=0, tier=self.tier).pop()
        self.nsigner = ncreator.create(ridx=0 + 1, tier=self.tier).pop()

        self.keys = [self.signer.verfer.qb64, signer.verfer.qb64]
        self.ndigs = [coring.Diger(ser=self.nsigner.verfer.qb64b).qb64]

        # Now rotate the controller AID to authenticate the passcode rotation
        rot = eventing.rotate(pre=self.serder.pre,
                              keys=self.keys,
                              dig=self.serder.ked['d'],
                              isith=["1", "0"],
                              nsith="1",
                              ndigs=self.ndigs)

        sigs = [signer.sign(ser=rot.raw, index=1, ondex=0).qb64, self.signer.sign(ser=rot.raw, index=0).qb64]

        encrypter = coring.Encrypter(verkey=nsigner.verfer.qb64)  # encrypter for new salt
        decrypter = coring.Decrypter(seed=nsigner.qb64)  # decrypter with old salt

        # First encrypt and save old Salt in case we need a recovery
        sxlt = encrypter.encrypt(matter=coring.Matter(qb64b=self.bran)).qb64

        data = dict(
            rot=rot.ked,
            sigs=sigs,
            sxlt=sxlt,
        )

        # Not recrypt all salts and saved keys after verifying they are decrypting correctly
        keys = dict()
        for aid in aids:
            pre = aid["prefix"]
            if "salty" in aid:
                salty = aid["salty"]
                cipher = coring.Cipher(qb64=salty["sxlt"])
                dnxt = decrypter.decrypt(cipher=cipher).qb64

                # Now we have the AID salt, use it to verify against the current public keys
                acreator = keeping.SaltyCreator(dnxt, stem=salty["stem"], tier=salty["tier"])
                signers = acreator.create(codes=salty["icodes"], pidx=salty["pidx"], kidx=salty["kidx"],
                                          transferable=salty["transferable"])
                pubs = aid["state"]["k"]
                if pubs != [signer.verfer.qb64 for signer in signers]:
                    raise kering.ValidationError(f"unable to rotate, validation of salt to public keys {pubs} failed")

                asxlt = encrypter.encrypt(matter=coring.Matter(qb64=dnxt)).qb64
                keys[pre] = dict(
                    sxlt=asxlt
                )

            elif "randy" in aid:
                randy = aid["randy"]
                prxs = randy["prxs"]
                nxts = randy["nxts"]

                nprxs = []
                signers = []
                for prx in prxs:
                    cipher = coring.Cipher(qb64=prx)
                    dsigner = decrypter.decrypt(cipher=cipher, transferable=True)
                    signers.append(dsigner)
                    nprxs.append(encrypter.encrypt(matter=coring.Matter(qb64=dsigner.qb64)).qb64)

                pubs = aid["state"]["k"]
                if pubs != [signer.verfer.qb64 for signer in signers]:
                    raise kering.ValidationError(f"unable to rotate, validation of encrypted public keys {pubs} failed")

                nnxts = []
                for nxt in nxts:
                    nnxts.append(self.recrypt(nxt, decrypter, encrypter))

                keys[pre] = dict(prxs=nprxs, nxts=nxts)

        data["keys"] = keys
        return data

    @staticmethod
    def recrypt(enc, decrypter, encrypter):
        cipher = coring.Cipher(qb64=enc)
        dnxt = decrypter.decrypt(cipher=cipher).qb64
        return encrypter.encrypt(matter=coring.Matter(qb64=dnxt)).qb64


class Authenticater:
    DefaultFields = ["@method",
                     "@path",
                     "Content-Length",
                     "Signify-Resource",
                     "Signify-Timestamp"]

    def __init__(self, agent: Agent, ctrl: Controller):
        """ Create Agent Authenticator for verifying requests and signing responses

        Parameters:
            agent(Hab): habitat of Agent for signing responses
            ctrl(Controller): qb64 controller signing AID

        Returns:
              Authenicator:  the configured habery

        """
        self.agent = agent
        self.ctrl = ctrl

    def verify(self, rep, **kwargs):
        url = urlparse(rep.request.url)
        if "SIGNIFY-RESOURCE" not in rep.headers:
            raise kering.AuthNError("No valid signature from agent on response.")

        resource = rep.headers["SIGNIFY-RESOURCE"]
        if resource != self.agent.pre or not self.verifysig(rep.headers, rep.request.method, url.path):
            raise kering.AuthNError("No valid signature from agent on response.")

    def verifysig(self, headers, method, path):
        headers = headers
        if "SIGNATURE-INPUT" not in headers:
            return False

        siginput = headers["SIGNATURE-INPUT"]

        if "SIGNATURE" not in headers:
            return False

        signature = headers["SIGNATURE"]

        inputs = ending.desiginput(siginput.encode("utf-8"))
        inputs = [i for i in inputs if i.name == "signify"]

        if not inputs:
            return False

        for inputage in inputs:
            items = []
            for field in inputage.fields:
                if field.startswith("@"):
                    if field == "@method":
                        items.append(f'"{field}": {method}')
                    elif field == "@path":
                        items.append(f'"{field}": {path}')

                else:
                    key = field.upper()
                    field = field.lower()
                    if key not in headers:
                        continue

                    value = ending.normalize(headers[key])
                    items.append(f'"{field}": {value}')

            values = [f"({' '.join(inputage.fields)})", f"created={inputage.created}"]
            if inputage.expires is not None:
                values.append(f"expires={inputage.expires}")
            if inputage.nonce is not None:
                values.append(f"nonce={inputage.nonce}")
            if inputage.keyid is not None:
                values.append(f"keyid={inputage.keyid}")
            if inputage.context is not None:
                values.append(f"context={inputage.context}")
            if inputage.alg is not None:
                values.append(f"alg={inputage.alg}")

            params = ';'.join(values)

            items.append(f'"@signature-params: {params}"')
            ser = "\n".join(items).encode("utf-8")

            signages = ending.designature(signature)
            cig = signages[0].markers[inputage.name]
            if not self.agent.verfer.verify(sig=cig.raw, ser=ser):
                raise kering.AuthNError(f"Signature for {inputage} invalid")

        return True

    def sign(self, headers, method, path, fields=None):
        """ Generate and add Signature Input and Signature fields to headers

        Parameters:
            headers (dict): HTTP header to sign
            method (str): HTTP method name of request/response
            path (str): HTTP Query path of request/response
            fields (Optional[list]): Optional list of Signature Input fields to sign.

        Returns:
            headers (dict): Modified headers with new Signature and Signature Input fields

        """

        if fields is None:
            fields = self.DefaultFields

        header, qsig = ending.siginput("signify", method, path, headers, fields=fields, signers=[self.ctrl.signer],
                                       alg="ed25519", keyid=self.ctrl.pre)
        for key, val in header.items():
            headers[key] = val

        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        for key, val in ending.signature([signage]).items():
            headers[key] = val

        return headers
