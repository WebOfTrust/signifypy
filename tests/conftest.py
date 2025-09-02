"""
Configure PyTest

Use this module to configure pytest
https://docs.pytest.org/en/latest/pythonpath.html

"""
import json
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

import pytest
from hio.base import Doer, doing, Doist
from hio.help import decking
from keri import core, kering
from keri.app import habbing, delegating, forwarding, indirecting, agenting, keeping, oobiing, \
    grouping, notifying
from keri.app.habbing import openHby, Habery
from keri.core import coring, eventing, serdering, Salter, scheming
from keri.db import basing
from keri.help import helping
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import credentialing, verifying
from keri.vdr.credentialing import Regery
from pysodium import randombytes, crypto_sign_SEEDBYTES

from tests.keri_ops import KliGrantDoer


@pytest.fixture()
def mockHelpingNowUTC(monkeypatch):
    """
    Replace nowUTC universally with fixed value for testing
    """

    def mockNowUTC():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return helping.fromIso8601("2021-01-01T00:00:00.000000+00:00")

    monkeypatch.setattr(helping, "nowUTC", mockNowUTC)


@pytest.fixture()
def mockHelpingNowIso8601(monkeypatch):
    """
    Replace nowIso8601 universally with fixed value for testing
    """

    def mockNowIso8601():
        """
        Use predetermined value for now (current time)
        '2021-01-01T00:00:00.000000+00:00'
        """
        return "2021-06-27T21:26:21.233257+00:00"

    monkeypatch.setattr(helping, "nowIso8601", mockNowIso8601)


@pytest.fixture()
def mockCoringRandomNonce(monkeypatch):
    """ Replay randomNonce with fixed falue for testing"""

    def mockRandomNonce():
        return "A9XfpxIl1LcIkMhUSCCC8fgvkuX8gG9xK3SM-S8a8Y_U"

    monkeypatch.setattr(coring, "randomNonce", mockRandomNonce)

@dataclass
class IcpCfg:
    """
    Configuration for inception

    Constructor arguments:
    :param name: str - Name of the AID
    :param icount: int - Signing key count for the AID
    :param isith: str - Signing threshold for the AID
    :param ncount: int - Rotation key count for the AID
    :param nsith: str - Rotation threshold for the AID
    :param toad: int - Threshold of accountable duplicity for the AID
    :param wits: List[str] - List of witness AIDs for the AID
    """
    name: str = "test_aid"
    icount: int = 1
    isith: str = '1'
    ncount: int = 1
    nsith: str = '1'
    toad: int = 1
    wits: List[str] = None

class HabbingHelpers:
    @staticmethod
    @contextmanager
    def openHab(name='test', base='', salt=None, temp=True, cf=None, **kwa):
        """
        Context manager wrapper for Hab instance.
        Defaults to temporary resources
        Context 'with' statements call .close on exit of 'with' block

        Parameters:
            name(str): name of habitat to create
            base(str): the name used for shared resources i.e. Baser and Keeper The habitat specific config file will be
            in base/name
            salt(bytes): passed to habitat to use for inception raw salt not qb64
            temp(bool): indicates if this uses temporary databases
            cf(Configer): optional configer for loading configuration data
        TODO: replace this openHab fixture with one from KERIpy once https://github.com/WebOfTrust/keripy/pull/1078 is merged.
              this copy was needed in order to pass cf to Habery.makeHab() since the **kwa is not unpacking the cf arg.
        """

        salt = core.Salter(raw=salt).qb64

        with openHby(name=name, base=base, salt=salt, temp=temp, cf=cf) as hby:
            if (hab := hby.habByName(name)) is None:
                hab = hby.makeHab(name=name, icount=1, isith='1', ncount=1, nsith='1', cf=cf, **kwa)

            yield hby, hab

    @staticmethod
    def habery_doers(hby: habbing.Habery):
        """
        Return the list of Doers needed to run a controller using a Doist and the WitnessReceiptor.
        The WitnessReceiptorDoer is used to check whether there are any unprocessed cues so the
        Doist knows when to stop running.

        Useful for running a Controller in a test.
        """
        hby_doer = habbing.HaberyDoer(habery=hby)
        anchorer = delegating.Anchorer(hby=hby, proxy=None)
        postman = forwarding.Poster(hby=hby)
        mbx = indirecting.MailboxDirector(hby=hby, topics=['/receipt', '/replay', '/reply'])
        wit_rcptr = agenting.WitnessReceiptor(hby=hby)
        receiptor = agenting.Receiptor(hby=hby)
        doers = [hby_doer, anchorer, postman, mbx, wit_rcptr, receiptor]
        return doers, hby_doer, wit_rcptr

    @staticmethod
    def resolve_wit_oobi(doist: doing.Doist, wit_deeds: List[Doer], hby: habbing.Habery, oobi: str, alias: str = None):
        """Resolve an OOBI depending on a given witness for a given Habery."""
        obr = basing.OobiRecord(date=helping.nowIso8601())
        if alias is not None:
            obr.oobialias = alias
        hby.db.oobis.put(keys=(oobi,), val=obr)

        oobiery = oobiing.Oobiery(hby=hby)
        authn = oobiing.Authenticator(hby=hby)
        oobiery_deeds = doist.enter(doers=oobiery.doers + authn.doers)
        while not oobiery.hby.db.roobi.get(keys=(oobi,)):
            doist.recur(deeds=decking.Deck(wit_deeds + oobiery_deeds))
            hby.kvy.processEscrows()  # process any escrows from witness receipts

    @staticmethod
    def incept_aid(doist: doing.Doist, wit_deeds: List[Doer], hby_deeds: List[Doer], hby: habbing.Habery, icp_cfg: IcpCfg, wit_rcptr: agenting.WitnessReceiptor):
        """
        Incept an AID in the given Habery using the given inception configuration.

        Does not yet support delegation or multisig.
        """

        # perform inception
        hab = hby.makeHab(name=icp_cfg.name, isith=icp_cfg.isith, icount=icp_cfg.icount, toad=icp_cfg.toad, wits=icp_cfg.wits)

        if len(icp_cfg.wits) > 0:
            # Waiting for witness receipts...
            wit_rcptr.msgs.append(dict(pre=hab.pre))

            while not wit_rcptr.cues:
                doist.recur(deeds=decking.Deck(wit_deeds + hby_deeds)) # Use of Deck avoids type error of raw list
        return hab

    @staticmethod
    def generate_oobi(hby: habbing.Habery, alias: str = None, role: str = kering.Roles.witness):
        hab = hby.habByName(name=alias)
        oobi = ''
        if role in (kering.Roles.witness,):
            if not hab.kever.wits:
                raise kering.ConfigurationError(f"{alias} identifier {hab.pre} does not have any witnesses.")
            for wit in hab.kever.wits:
                urls = hab.fetchUrls(eid=wit, scheme=kering.Schemes.http) \
                       or hab.fetchUrls(eid=wit, scheme=kering.Schemes.https)
                if not urls:
                    raise kering.ConfigurationError(f"unable to query witness {wit}, no http endpoint")

                url = urls[kering.Schemes.https] if kering.Schemes.https in urls else urls[kering.Schemes.http]
                oobi = f"{url.rstrip("/")}/oobi/{hab.pre}/witness"
        elif role in (kering.Roles.controller,):
            urls = hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.http) \
                   or hab.fetchUrls(eid=hab.pre, scheme=kering.Schemes.https)
            if not urls:
                raise kering.ConfigurationError(f"{alias} identifier {hab.pre} does not have any controller endpoints")
            url = urls[kering.Schemes.https] if kering.Schemes.https in urls else urls[kering.Schemes.http]
            oobi = f"{url.rstrip("/")}/oobi/{hab.pre}/controller"
        elif role in (kering.Roles.mailbox,):
            for (_, _, eid), end in hab.db.ends.getItemIter(keys=(hab.pre, kering.Roles.mailbox, )):
                if not (end.allowed and end.enabled is not False):
                    continue

                urls = hab.fetchUrls(eid=eid, scheme=kering.Schemes.http) or hab.fetchUrls(eid=hab.pre,
                                                                                           scheme=kering.Schemes.https)
                if not urls:
                    raise kering.ConfigurationError(f"{alias} identifier {hab.pre} does not have any mailbox endpoints")
                url = urls[kering.Schemes.https] if kering.Schemes.https in urls else urls[kering.Schemes.http]
                oobi = f"{url.rstrip("/")}/oobi/{hab.pre}/mailbox/{eid}"
        if oobi:
            return oobi
        else:
            raise kering.ConfigurationError(f"Unable to generate OOBI for {alias} identifier {hab.pre} with role {role}")

    @staticmethod
    def create_registry(
            hby: habbing.Habery,
            hby_doer: Doer,
            regery: credentialing.Regery,
            hab: habbing.Hab,
            name: str | None = None,
            registry_nonce: str | None = None,
            additional_deeds: List[Doer] = None):
        """Single-sig registry inception helper. Multisig will require more work"""
        name = hab.name if name is None else name  # default to hab name if no name provided

        counselor = grouping.Counselor(hby=hby)
        registrar = credentialing.Registrar(hby=hby, rgy=regery, counselor=counselor)
        verifier = verifying.Verifier(hby=hby, reger=regery.reger)
        credentialer = credentialing.Credentialer(hby=hby, rgy=regery, registrar=registrar, verifier=verifier)
        regery_doer = credentialing.RegeryDoer(rgy=regery)

        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        registry_deeds = doist.enter(doers=[hby_doer, counselor, registrar, credentialer, regery_doer])

        issuer_reg = regery.makeRegistry(prefix=hab.pre, name=name, noBackers=True, nonce=registry_nonce)
        rseal = eventing.SealEvent(issuer_reg.regk, '0', issuer_reg.regd)._asdict()
        reg_anc = hab.interact(data=[rseal])
        reg_anc_serder = serdering.SerderKERI(raw=bytes(reg_anc))
        registrar.incept(iserder=issuer_reg.vcp, anc=reg_anc_serder)

        additional_deeds = additional_deeds or decking.Deck([])
        deeds = decking.Deck(registry_deeds + additional_deeds)
        while not registrar.complete(pre=issuer_reg.regk, sn=0):
            doist.recur(deeds=deeds)  # run until registry is incepted
            verifier.processEscrows()

        assert issuer_reg.regk in regery.reger.tevers
        return issuer_reg

    @staticmethod
    def add_acdc_schema(baser: basing.Baser, schema: dict):
        schemer = scheming.Schemer(
            raw=bytes(json.dumps(schema), 'utf-8'),
            typ=scheming.JSONSchema(),
            code=coring.MtrDex.Blake3_256
        )
        cache = scheming.CacheResolver(db=baser)
        cache.add(schemer.said, schemer.raw)

def random_passcode():
    return Salter(raw=randombytes(crypto_sign_SEEDBYTES)).qb64


class WitnessContext:
    """
    An instance of the doers for a witness that enable running a witness as a set of doers with the
    static context manager function `with_witness`. This facilitates debuggable testability of any
    functionality involving witnesses.
    """

    def __init__(self, name: str, hby: habbing.Habery, tcp_port: int = 6632, http_port: int = 6642):
        """
        Initialize the WitnessContext context manager with a witness name and habery.

        Args:
            name (str): The name of the witness.
            hby (habbing.Habery): The habery instance to use.
            tcp_port (int): The TCP port for the witness. Default is 6642.
            http_port (int): The HTTP port for the witness. Default is 6643.
        """
        self.name = name
        self.hby = hby
        ks = keeping.Keeper(name=name, base=hby.base, temp=True, reopen=True)

        aeid = ks.gbls.get('aeid')

        hby_doer = habbing.HaberyDoer(habery=hby)
        doers = [hby_doer]
        doers.extend(indirecting.setupWitness(alias=name, hby=hby, tcpPort=tcp_port, httpPort=http_port))
        self.doers = doers  # store doers for manual Doist.recur control in body of test

    @contextmanager
    @staticmethod
    def with_witness(name, hby, tcp_port=6632, http_port=6642):
        yield WitnessContext(name, hby, tcp_port, http_port)

class Schemas:
    """
    Using pathlib to load schema and rules files from "tests/schema" using the relative .parent path
    allows tests to be run from any working directory.
    """

    @staticmethod
    def qvi_schema_as_dict():
        schema_path = Path(__file__).parent / "schema" / "qualified-vLEI-issuer-vLEI-credential.json"
        return json.loads(schema_path.read_bytes())

    @staticmethod
    def qvi_rules_as_dict():
        rules_path = Path(__file__).parent / "schema" / "rules" / "qvi-cred-rules.json"
        return json.loads(rules_path.read_bytes())

    @staticmethod
    def le_schema_as_dict():
        schema_path = Path(__file__).parent / "schema" / "legal-entity-vLEI-credential.json"
        return json.loads(schema_path.read_bytes())

    @staticmethod
    def le_rules_as_dict():
        # reuses QVI rules file since both are the same
        rules_path = Path(__file__).parent / "schema" / "rules" / "qvi-cred-rules.json"
        return json.loads(rules_path.read_bytes())

class CredentialHelpers:
    @staticmethod
    def vc_create(
        hby: habbing.Habery,
        hby_doer: habbing.HaberyDoer,
        regery: credentialing.Regery,
        registry_name: str,
        hab: habbing.Hab,
        schema_said: str,
        subject_data: dict,
        rules_json: dict,
        source: Union[dict, list] = None,
        recp: str = None,
        private: bool = False,
        private_credential_nonce: str = None,
        private_subject_nonce: str = None,
        additional_deeds: List[doing.Doer] = None,):
        """
        This function assumes that the schema is already in the schema cache of the issuer's Regery
        and that the registry is already created for the issuer.

        Parameters:
            hby (habbing.Habery): The habery instance to use.
            hby_doer (habbing.HaberyDoer): The habery doer instance to use.
            regery (credentialing.Regery): The regery instance to use.
            registry_name (str): The registry name (registry.name). Required.
            hab (habbing.Hab): The hab instance to use for signing.
            schema_said (str): The SAID of the schema to use for the credential.
            schema_json (dict): The JSON schema to use for the credential.
            subject_data (dict): The subject data to include in the credential.
            rules_json (dict): The rules JSON to use for the credential.
            source (Union[dict, list], optional): The source data for the credential. Defaults to None.
            recp (str, optional): The recipient of the credential. Defaults to None for self-issued.
            private (bool, optional): Whether the credential is private. Defaults to False.
            private_credential_nonce (str, optional): The nonce for private credential. Defaults to None.
            private_subject_nonce (str, optional): The nonce for private subject. Defaults to None.
            additional_deeds (List[doing.Doer], optional): Additional deeds to run with the doist. Defaults to None.
        """
        registry = regery.registryByName(registry_name)
        assert registry.regk in regery.reger.tevers, f"Registry {registry_name} not found in Issuer's Regery"
        schema = hby.db.schema.get(schema_said)
        assert schema is not None, f"Schema {schema_said} not found in Issuer's schema cache"

        additional_deeds = additional_deeds or decking.deque(
            []
        )
        # Components needed for creation / issuance of credential
        counselor = grouping.Counselor(hby=hby)
        registrar = credentialing.Registrar(hby=hby, rgy=regery, counselor=counselor)
        verifier = verifying.Verifier(hby=hby, reger=regery.reger)
        credentialer = credentialing.Credentialer(hby=hby, rgy=regery, registrar=registrar, verifier=verifier)
        regery_doer = credentialing.RegeryDoer(rgy=regery)

        # set up Doist to run doers
        doist = doing.Doist(limit=1.0, tock=0.03125, real=True)
        create_deeds = doist.enter(doers=[hby_doer, counselor, registrar, credentialer, regery_doer])

        creder = credentialer.create(
            regname=registry.name,
            recp=recp,
            schema=schema_said,
            source=source,
            rules=rules_json,
            data=subject_data,
            private=private,
            private_credential_nonce=private_credential_nonce,
            private_subject_nonce=private_subject_nonce,
        )

        # Create ACDC issuance and anchor to KEL
        reg_iss_serder = registry.issue(said=creder.said, dt=creder.attrib['dt'])
        iss_seal = eventing.SealEvent(reg_iss_serder.pre, '0', reg_iss_serder.said)._asdict()
        iss_anc = hab.interact(data=[iss_seal])
        anc_serder = serdering.SerderKERI(raw=iss_anc)
        credentialer.issue(creder, reg_iss_serder)
        registrar.issue(creder, reg_iss_serder, anc_serder)

        while not credentialer.complete(said=creder.said):
            doist.recur(deeds=create_deeds + additional_deeds)
            verifier.processEscrows()
            regery.processEscrows()

        state = registry.tever.vcState(vci=creder.said)
        assert state.et == coring.Ilks.iss
        return creder, reg_iss_serder, anc_serder

class IpexHelpers:
    @staticmethod
    def kli_grant(name: str, base: str, bran: bytes, alias: str, said: str, recp: str,
                  hby: Habery,
                  regery: Regery,
                  doist: Doist,
                  additional_deeds: List[Doer] = None,
                  message: str = None,
                  timestamp: str = None):
        """
        I had to write the below function instead of using GrantDoer because the KLI command Doer
        does not allow specifying temp=True and thus puts the databases in a non-temp location.
        Right now this only supports single sig Granting. Multisig will not be too much more work.
        """
        notifier = notifying.Notifier(hby=hby)
        exc = exchanging.Exchanger(hby=hby, handlers=[])
        protocoling.loadHandlers(hby, exc, notifier)

        kli_grant_doer = KliGrantDoer(hby=hby, hab=hby.habByName(alias), regery=regery, exc=exc,
                                      said=said, recp=recp, message=message, timestamp=timestamp)
        grant_deed = doist.enter(doers=[kli_grant_doer])
        while not kli_grant_doer.done:
            doist.recur(deeds=decking.Deck([grant_deed] + additional_deeds))

    @staticmethod
    def kli_admit():
        pass


