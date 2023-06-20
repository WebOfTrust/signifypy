from collections import namedtuple
from time import sleep

from keri import kering
from keri.app.keeping import Algos
from keri.core import coring
from keri.core.eventing import TraitDex, SealEvent
from keri.vdr import eventing

from signify.app.clienting import SignifyClient

CredentialTypeage = namedtuple("CredentialTypeage", 'issued received')

CredentialTypes = CredentialTypeage(issued='issued', received='received')


class Registries:
    """ Domain class for creating and accessing credential registries. """

    def __init__(self, client: SignifyClient):
        self.client = client

    def registryIncept(self, pre=None, alias=None, name=None, body=None, algo=Algos.salty, **kwargs):
        # other option
        if pre is None:
            raise kering.ValidationError(f"Hab AID prefix required in order to make a registry")
        if alias is None:
            raise kering.ValidationError(f"AID alias required in order to make a registry")

        baks = body["baks"] if "baks" in body else None
        toad = body["toad"] if "toad" in body else None
        nonce = body["nonce"] if "nonce" in body else None
        estOnly = body["estOnly"] if "estOnly" in body else False

        cnfg = []
        if "noBackers" in body and body["noBackers"]:
            cnfg.append(TraitDex.NoBackers)
        if estOnly:
            cnfg.append(TraitDex.EstOnly)

        regser = eventing.incept(pre,
                                 baks=baks,
                                 toad=toad,
                                 nonce=nonce,
                                 cnfg=cnfg,
                                 code=coring.MtrDex.Blake3_256)

        keeper = self.client.manager.new(algo, self.client.pidx, **kwargs)
        sigs = keeper.sign(regser.raw)

        rseal = SealEvent(regser.pre, "0", regser.said)
        rseal = dict(i=rseal.i, s=rseal.s, d=rseal.d)

        identifiers = self.client.identifiers()
        operations = self.client.operations()
        op = identifiers.interact(alias, data=[rseal])

        while not op["done"]:
            op = operations.get(op["name"])
            sleep(1)
        ixn = op["response"]

        json = dict(
            name=name,
            alias=alias,
            sigs=sigs,
            vcp=regser.ked,
            ixn=ixn
        )
        json[algo] = keeper.params()

        self.client.pidx = self.client.pidx + 1

        res = self.client.post("/registries", json=json)
        return res.json()


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
