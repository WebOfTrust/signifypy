# -*- encoding: utf-8 -*-
"""
SIGNIFY
signify.core.httping module

Testing httping utils
"""
from base64 import urlsafe_b64decode as decodeB64

from hio.help import Hict
from http_sfv import Dictionary
from keri.app import habbing
from keri.end import ending
from signify.core import httping


def test_siginput(mockHelpingNowUTC):
    print()
    with habbing.openHab(name="test", base="test", temp=True) as (hby, hab):
        headers = Hict([
            ("Content-Type", "application/json"),
            ("Content-Length", "256"),
            ("Connection", "close"),
            ("Signift-Resource", "EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs"),
            ("Signify-Timestamp", "2022-09-24T00:05:48.196795+00:00"),
        ])

        header, unq = httping.siginput(hab, "sig0", "POST", "/signify", headers, fields=["Signify-Resource", "@method",
                                                                                         "@path",
                                                                                         "Signify-Timestamp"],
                                       alg="ed25519", keyid=hab.pre)

        headers.extend(header)
        signage = ending.Signage(markers=dict(sig0=unq), indexed=False, signer=None, ordinal=None, digest=None,
                                 kind=None)
        headers.extend(ending.signature([signage]))

        assert dict(headers) == {'Connection': 'close',
                                 'Content-Length': '256',
                                 'Content-Type': 'application/json',
                                 'Signify-Resource': 'EWJkQCFvKuyxZi582yJPb0wcwuW3VXmFNuvbQuBpgmIs',
                                 'Signify-Timestamp': '2022-09-24T00:05:48.196795+00:00',
                                 'Signature': 'indexed="?0";sig0="1G-ItA3IPA8g30--svDMxlWW7YG_6PFf1VsUaV445PLXDDM9tTL7P'
                                              'vnEW9Uv8y2mwaGOdpIojvBbGMOzdVccCg=="',
                                 'Signature-Input': 'sig0=("signify-resource" "@method" "@path" '
                                                    '"signify-timestamp");created=1609459200;keyid="EIaGMMWJFPmtXznY1IIiK'
                                                    'DIrg-vIyge6mBl2QV8dDjI3";alg="ed25519"'}

        siginput = headers["Signature-Input"]
        signature = headers["Signature"]

        inputs = httping.desiginput(siginput.encode("utf-8"))
        assert len(inputs) == 1
        inputage = inputs[0]

        assert inputage.name == 'sig0'
        assert inputage.fields == ['signify-resource', "@method", "@path", "signify-timestamp"]
        assert inputage.created == 1609459200
        assert inputage.alg == "ed25519"
        assert inputage.keyid == hab.pre
        assert inputage.expires is None
        assert inputage.nonce is None
        assert inputage.context is None

        items = []
        for field in inputage.fields:
            if field.startswith("@"):
                if field == "@method":
                    items.append(f'"{field}": POST')
                elif field == "@path":
                    items.append(f'"{field}": /signify')

            else:
                field = field.lower()
                if field not in headers:
                    continue

                value = httping.normalize(headers[field])
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
        assert hab.kever.verfers[0].verify(sig=raw, ser=ser) is True
