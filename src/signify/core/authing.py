# -*- encoding: utf-8 -*-
"""
KERI
signify.core.authing module

"""

import falcon
from keri import kering
from keri.app.keeping import SaltyCreator
from keri.core import coring, eventing
from keri.core.coring import Salter

from keri.end import ending


class Agent:
    def __init__(self, kel):
        self.pre = ""
        self.anchor = ""
        self.verfer = None

        self.parse(kel)

    def parse(self, kel):
        if len(kel) < 1:
            raise kering.ConfigurationError("invalid empty KEL")

        serder, verfer, diger = self.event(kel[0])
        if not serder.ked['t'] in (coring.Ilks.icp,):
            raise kering.ValidationError(f"invalid inception event type {serder.ked['t']}")

        self.pre = serder.pre
        if not serder.ked['a']:
            raise kering.ValidationError("no anchor to controller AID")
        self.anchor = serder.ked['a'][0]

        for evt in kel[1:]:
            rot, nverfer, ndiger = self.event(evt)
            if not rot.ked['t'] in (coring.Ilks.rot,):
                raise kering.ValidationError(f"invalid rotation event type {serder.ked['t']}")

            if coring.Diger(ser=nverfer.qb64b).qb64b != diger.qb64b:
                raise kering.ValidationError(f"next key mismatch error on rotation event {serder.said}")

            verfer = nverfer
            diger = ndiger

        self.verfer = verfer

    @staticmethod
    def event(evt):
        serder = coring.Serder(ked=evt["ked"])
        siger = coring.Siger(qb64=evt["sig"])

        if len(serder.verfers) != 1:
            raise kering.ValidationError(f"agent inception event can only have one key")

        if not serder.verfers[0].verify(sig=siger.raw, ser=serder.raw):
            raise kering.ValidationError(f"invalid signature on evt {serder.ked['d']}")

        verfer = serder.verfers[0]

        if len(serder.digers) != 1:
            raise kering.ValidationError(f"agent inception event can only have one next key")

        diger = serder.digers[0]

        tholder = coring.Tholder(sith=serder.ked["kt"])
        if tholder.num != 1:
            raise kering.ValidationError(f"invalid threshold {tholder.num}, must be 1")
        ntholder = coring.Tholder(sith=serder.ked["nt"])

        if ntholder.num != 1:
            raise kering.ValidationError(f"invalid next threshold {ntholder.num}, must be 1")

        return serder, verfer, diger


class Controller:
    def __init__(self, bran, tier, temp, ridx=0):
        if hasattr(bran, "decode"):
            bran = bran.decode("utf-8")

        self.bran = coring.MtrDex.Salt_128 + 'A' + bran[:21]  # qb64 salt for seed
        self.stem = "signify:controller"
        self.tier = tier
        self.temp = temp

        salter = coring.Salter(qb64=self.bran)
        creator = SaltyCreator(salt=salter.qb64, stem=self.stem, tier=tier)

        self.signer = creator.create(ridx=ridx, tier=tier, temp=temp).pop()
        self.nsigner = creator.create(ridx=ridx + 1, tier=tier, temp=temp).pop()

        keys = [self.signer.verfer.qb64]
        ndigs = [coring.Diger(ser=self.nsigner.verfer.qb64b)]

        self.serder = eventing.incept(keys=keys,
                                      isith="1",
                                      nsith="1",
                                      ndigs=[diger.qb64 for diger in ndigs],
                                      code=coring.MtrDex.Blake3_256,
                                      toad="0",
                                      wits=[])

    @property
    def pre(self):
        return self.serder.pre

    def event(self):
        siger = self.signer.sign(ser=self.serder.raw, index=0)
        return self.serder, siger

    @property
    def verfers(self):
        return self.signer.verfers

    @property
    def salter(self):
        return Salter(qb64=self.bran)


class Authenticater:
    DefaultFields = ["@method",
                     "@path",
                     "Content-Length"
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

    def verify(self, headers, method, path):
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
            headers (Hict): Modified headers with new Signature and Signature Input fields

        """

        if fields is None:
            fields = self.DefaultFields

        header, qsig = ending.siginput("signify", method, path, headers, fields=fields, signers=[self.ctrl.signer],
                                       alg="ed25519", keyid=self.agent.pre)
        for key, val in header.items():
            headers[key] = val

        signage = ending.Signage(markers=dict(signify=qsig), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        for key, val in ending.signature([signage]).items():
            headers[key] = val

        return headers


class SignatureValidationComponent(object):
    """ Validate Signature and Signature-Input header signatures """

    def __init__(self, authn: Authenticater):
        """

        Parameters:
            authn (Authenticater): Authenticator to validate signature headers on request
        """
        self.authn = authn

    def process_request(self, req, resp):
        """ Process request to ensure has a valid signature from controller

        Parameters:
            req: Http request object
            resp: Http response object


        """
        # Use Authenticater to verify the signature on the request
        if not self.authn.verify(req):
            resp.complete = True  # This short-circuits Falcon, skipping all further processing
            resp.status = falcon.HTTP_401
            return

