# -*- encoding: utf-8 -*-
"""
KERI
signify.core.authing module

"""
from hio.help import Hict
from base64 import urlsafe_b64decode as decodeB64
from http_sfv import Dictionary
from keri import kering
from keri.end import ending

from signify.core import httping


class Authenticater:

    DefaultFields = ["Signify-Resource",
                     "@method",
                     "@path",
                     "Signify-Timestamp"]

    def __init__(self, agent, caid):
        """ Create Agent Authenticator for verifying requests and signing responses

        Parameters:
            agent(Hab): habitat of Agent for signing responses
            caid(str): qb64 controller signing AID

        Returns:
              Authenicator:  the configured habery

        """
        self.agent = agent
        self.caid = caid

    def verify(self, request):
        if self.caid not in self.agent.kevers:
            raise kering.AuthNError("controller AID not in kevers")

        ckever = self.agent.kevers[self.caid]
        headers = request.headers
        siginput = headers["SIGNATURE-INPUT"]
        signature = headers["SIGNATURE"]

        inputs = httping.desiginput(siginput.encode("utf-8"))
        inputs = [i for i in inputs if i.name == "signify"]

        for inputage in inputs:
            items = []
            for field in inputage.fields:
                if field.startswith("@"):
                    if field == "@method":
                        items.append(f'"{field}": {request.method}')
                    elif field == "@path":
                        items.append(f'"{field}": {request.path}')

                else:
                    key = field.upper()
                    field = field.lower()
                    if key not in headers:
                        continue

                    value = httping.normalize(headers[key])
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

            signage = Dictionary()
            signage.parse(signature.encode("utf-8"))

            raw = decodeB64(signage["indexed"].params[inputage.name])
            if not ckever.verfers[0].verify(sig=raw, ser=ser):
                raise kering.AuthNError(f"Signature for {inputage} invalid")

            return True

    def sign(self, headers, method, path, fields=None):
        """ Generate and add Signature Input and Signature fields to headers

        Parameters:
            headers (Hict): HTTP header to sign
            method (str): HTTP method name of request/response
            path (str): HTTP Query path of request/response
            fields (Optional[list]): Optional list of Signature Input fields to sign.

        Returns:
            headers (Hict): Modified headers with new Signature and Signature Input fields

        """

        if fields is None:
            fields = self.DefaultFields

        header, unq = httping.siginput(self.agent, "signify", method, path, headers, fields=fields,
                                       alg="ed25519", keyid=self.agent.pre)
        headers.extend(header)
        signage = ending.Signage(markers=dict(signify=unq), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        return headers
