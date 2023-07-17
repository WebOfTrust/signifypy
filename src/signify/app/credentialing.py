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

    def __init__(self, client: SignifyClient):
        """ Create domain class for working with credentials for a single AID

            Parameters:
                client (SignifyClient): Signify client class for access resources on a KERIA service instance

        """
        self.client = client

    def list(self, name, filtr=None, sort=None, skip=None, limit=None):
        """

        Parameters:
            name (str): Alias associated with the AID
            filtr (dict): Credential filter dict
            sort(list): list of SAD Path field references to sort by
            skip (int): number of credentials to skip at the front of the list
            limit (int): total number of credentials to retrieve

        Returns:
            list: list of dicts representing the listed credentials

        """
        filtr = filtr if filtr is not None else {}
        sort = sort if sort is not None else []
        skip = skip if skip is not None else 0
        limit = limit if limit is not None else 25

        json = dict(
            filter=filtr,
            sort=sort,
            skip=skip,
            limt=limit
        )

        res = self.client.post(f"/identifiers/{name}/credentials/query", json=json)
        return res.json()

    def export(self, name, said):
        """

        Parameters:
            name (str): Name associated with the AID
            said (str): SAID of credential to export
        Returns:
            credential (bytes): exported credential

        """
        headers = dict(accept="application/json+cesr")

        res = self.client.get(f"/identifiers/{name}/credentials/{said}", headers=headers)
        return res.content
