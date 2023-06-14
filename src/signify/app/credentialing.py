from collections import namedtuple

from keri.core import coring
from keri.core.eventing import TraitDex
from keri.vdr import eventing

from signify.app.clienting import SignifyClient

CredentialTypeage = namedtuple("CredentialTypeage", 'issued received')

CredentialTypes = CredentialTypeage(issued='issued', received='received')


class Registries:

    def registryIncept(self, hab, body):
        cnfg = []
        if "noBackers" in body and body["noBackers"]:
            cnfg.append(TraitDex.NoBackers)
        baks = body["baks"] if "baks" in body else None
        toad = body["toad"] if "toad" in body else None
        estOnly = body["estOnly"] if "estOnly" in body else False
        nonce = body["nonce"] if "nonce" in body else None

        regser = eventing.incept(hab.pre,
                                 baks=baks,
                                 toad=toad,
                                 nonce=nonce,
                                 cnfg=cnfg,
                                 code=coring.MtrDex.Blake3_256)


class Credentials:
    """ Domain class for accessing, presenting, issuing and revoking credentials """

    def __init__(self, aid, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                aid (str): qb64 identifier as the issuer or holder of credentials
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.aid = aid
        self.client = client

    def list(self, typ=None, schema=None):
        """

        Parameters:
            typ (str): A credential type [issued|received]
            schema (str): qb64 SAID of the schema to use as criteria for listing credentials

        Returns:
            list: list of dicts representing the listed credentials

        """
        params = dict()
        match typ:
            case CredentialTypes.issued:
                params["type"] = CredentialTypes.issued
            case CredentialTypes.received:
                params["type"] = CredentialTypes.received

        if schema is not None:
            params["schema"] = schema

        res = self.client.get(f"/aids/{self.aid}/credentials", params=params)
        return res.json()

    def export(self, said):
        headers = dict(accept="application/json+cesr")

        res = self.client.get(f"/aids/{self.aid}/credentials/{said}", headers=headers)
        return res.content