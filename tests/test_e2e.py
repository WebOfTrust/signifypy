import json
import threading
from time import sleep

from hio.base import doing
from keri import core, kering
from keri.app import configing, habbing
from keri.core.coring import Saids, Saider
from keri.help import nowIso8601
from keri.vdr import credentialing
from keria.app.agenting import KERIAServerConfig, setupDoers, createAgency

from signify.app.clienting import SignifyClient
from tests import keria_api
from tests.conftest import HabbingHelpers, WitnessContext, IcpCfg, Schemas, \
    CredentialHelpers
from tests.keri_ops import GrantContainer
from tests.keria_api import create_agent


def test_e2e_vlei_present():
    """
    Run through a vLEI credential chain issuance flow and present to the Sally verifier.
    Components:
    - A single witness for the mailbox of KERIpy controllers to send messages to and from KERIA.
    - KERIpy controllers (like the KLI)
      - GEDA (single sig for now)
    - Signify Controllers
      - QVI (single sig for now)
      - Legal Entity (single sig for now)
    - KERIA Server
    - Sally Server
    """
    host = "127.0.0.1"
    # Set up wan witness
    wan_tcp = 6632
    wan_http = 6642
    wan_pre = 'BPwwr5VkI1b7ZA2mVbzhLL47UPjsGBX4WeO6WRv6c7H-' # hardcode this after first run with the salts below
    wan_salt = core.Salter(raw=b'abcdef0123456789').qb64
    keria_cf = configing.Configer(name='wan', temp=False, reopen=True, clear=False)
    wan_hby_conf = f"""{{
      "dt": "2022-01-20T12:57:59.823350+00:00",
      "wan": {{
        "dt": "2022-01-20T12:57:59.823350+00:00",
        "curls": ["tcp://{host}:{wan_tcp}/", "http://{host}:{wan_http}/"]}}}}"""
    keria_cf.put(json.loads(wan_hby_conf))
    wan_oobi = f'http://{host}:{wan_http}/oobi/{wan_pre}/controller?name=Wan&tag=witness'

    # set up wes witness
    wes_tcp = 6633
    wes_http = 6643
    wes_pre = 'BF_Ia6sKZTQkxBp05lYkqT8Vaz_CQvgNdNsdgoeNkEKf'  # hardcode this after first run with the salts below
    wes_salt = core.Salter(raw=b'0123456789abcdef').qb64
    wes_cf = configing.Configer(name='wes', temp=False, reopen=True, clear=False)
    wes_hby_conf = f"""{{
          "dt": "2022-01-20T12:57:59.823350+00:00",
          "wes": {{
            "dt": "2022-01-20T12:57:59.823350+00:00",
            "curls": ["tcp://{host}:{wes_tcp}/", "http://{host}:{wes_http}/"]}}}}"""
    wes_cf.put(json.loads(wes_hby_conf))
    wes_oobi = f'http://{host}:{wes_http}/oobi/{wes_pre}/controller?name=Wes&tag=witness'

    # Config of the GEDA keystore
    geda_salt = b'0ABdz_XWX22ZXj-eBTyUWQuV'
    geda_hby_conf = f"""{{
      "dt": "2022-01-20T12:57:59.823350+00:00",
      "iurls": [
        "{wan_oobi}"
      ]}}"""
    geda_cf = configing.Configer(name='geda', temp=False, reopen=True, clear=False)
    geda_cf.put(json.loads(geda_hby_conf))
    geda_registry_nonce = '0ABuNSSoCYE6BNZXJK6tFfJg'

    # Config of the GAR2 keystore (if Multisig is needed later, currently unused)
    gar2_salt = b'0AApXCjN6o8aCZPQjDRP2z3h'
    gar2_cf = configing.Configer(name='gar2', temp=False, reopen=True, clear=False)
    gar2_hby_conf = f"""{{
          "dt": "2022-01-20T12:57:59.823350+00:00",
          "iurls": [
            "{wes_oobi}"
          ]}}"""
    gar2_cf.put(json.loads(gar2_hby_conf))

    # Context managers for the witness Habery and Hab, witness Doers, GEDA Habery/Hab, and QVI Habery/Hab.
    # Uses temp=True so that the databases are not persistent and the test can be run multiple times without erroring out on a dirty context.
    with (
        # wan witness
        HabbingHelpers.openHab(salt=bytes(wan_salt, 'utf-8'), name='wan', transferable=False, temp=True, cf=keria_cf) as (wan_hby, wan_hab),
        WitnessContext.with_witness(name='wan', hby=wan_hby, tcp_port=wan_tcp, http_port=wan_http) as wan_wit,
        # wes witness
        HabbingHelpers.openHab(salt=bytes(wes_salt, 'utf-8'), name='wes', transferable=False, temp=True, cf=wes_cf) as (wes_hby, wes_hab),
        WitnessContext.with_witness(name='wes', hby=wes_hby, tcp_port=wes_tcp, http_port=wes_http) as wes_wit,
        # controllers
        habbing.openHab(salt=geda_salt, name='geda', transferable=True, temp=True, cf=geda_cf) as (geda_hby, geda_hab),
        habbing.openHab(salt=gar2_salt, name='gar2', transferable=True, temp=True, cf=gar2_cf) as (gar2_hby, gar2_hab),
    ):
        # Main Doist used throughout the test for local control, not including the threads.
        tock = 0.03125
        doist = doing.Doist(limit=0.0, tock=tock, real=True)

        # Have GEDA resolve the witness OOBI
        # Doers and deeds for witness wan
        wan_deeds = doist.enter(doers=wan_wit.doers)
        wes_deeds = doist.enter(doers=wes_wit.doers)

        # Have GEDA Hab Resolve Wan's witness OOBI
        # TODO Make OOBI resolution helper here?
        HabbingHelpers.resolve_wit_oobi(doist, wan_deeds, geda_hby, wan_oobi)

        # Incept the GEDA controller
        geda_doers, geda_hby_doer, geda_wit_rcptr = HabbingHelpers.habery_doers(hby=geda_hby)
        geda_deeds = doist.enter(doers=geda_doers)
        geda_hab_name = 'geda-aid'
        icp_cfg = IcpCfg(name=geda_hab_name, isith='1', icount=1, toad=1, wits=[wan_pre])
        HabbingHelpers.incept_aid(doist, wan_deeds, geda_deeds, geda_hby, icp_cfg, geda_wit_rcptr)

        # Have GAR2 resolve Wes' witness OOBI
        HabbingHelpers.resolve_wit_oobi(doist, wes_deeds, gar2_hby, wes_oobi)
        gar2_doers, gar2_hby_doer, gar2_wit_rcptr = HabbingHelpers.habery_doers(hby=gar2_hby)
        gar2_deeds = doist.enter(doers=gar2_doers)
        gar2_hab_name = 'gar2-aid'
        icp_cfg = IcpCfg(name=gar2_hab_name, isith='1', icount=1, toad=1, wits=[wes_pre])
        HabbingHelpers.incept_aid(doist, wes_deeds, gar2_deeds, gar2_hby, icp_cfg, gar2_wit_rcptr)

        # Have GEDA OOBI with GAR2 and GAR2 OOBI with GEDA
        geda_oobi = HabbingHelpers.generate_oobi(hby=geda_hby, alias=geda_hab_name, role=kering.Roles.witness)
        gar2_oobi = HabbingHelpers.generate_oobi(hby=gar2_hby, alias=gar2_hab_name, role=kering.Roles.witness)

        # wit_deeds = wan_deeds + wes_deeds  # run both witnesses so
        HabbingHelpers.resolve_wit_oobi(doist, wes_deeds, geda_hby, gar2_oobi)
        HabbingHelpers.resolve_wit_oobi(doist, wan_deeds, gar2_hby, geda_oobi)

        # Create the GEDA registry
        geda_regery = credentialing.Regery(hby=geda_hby, name=geda_hby.name, temp=geda_hby.temp)
        geda_reg_name = 'geda-reg'
        geda_reg = HabbingHelpers.create_registry(geda_hby, geda_hby_doer, geda_regery, geda_hab, geda_reg_name, geda_registry_nonce, wan_deeds + geda_deeds)

        # Add QVI schema to GEDA's schema cache
        HabbingHelpers.add_acdc_schema(geda_hby.db, Schemas.qvi_schema_as_dict())

        # set up KERIA
        # TODO context manager for a threaded KERIA server? Accepts KERIA deeds, returns Thread and ThreadEvent
        #      context manager would handle thread start and stop, possibly.
        adminPort=3901
        httpPort=3902
        bootPort=3903
        config = KERIAServerConfig(
            name="keria",
            base="",
            bran="0ACiLG-5zOx-LzAwewC37Hqt",
            configFile="keria",
            configDir="",
            logLevel="INFO",
            adminPort=adminPort,
            httpPort=3902,
            bootPort=bootPort,
        )
        keria_cf = configing.Configer(name='wan', temp=False, reopen=True, clear=False)
        keria_agency_cf = f"""{{
              "dt": "2022-01-20T12:57:59.823350+00:00",
              "keria": {{
                "dt": "2022-01-20T12:57:59.823350+00:00",
                "curls": ["http://{host}:{httpPort}/"]}}}}"""
        keria_cf.put(json.loads(keria_agency_cf))
        agency = createAgency(config, temp=True, cf=keria_cf)
        keria_doers = setupDoers(agency, config, temp=True)
        doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
        keria_deeds = doist.enter(doers=keria_doers)

        def run_keria_other_thread(event: threading.Event):
            keria_doist = doing.Doist(limit=0.0, tock=0.03125, real=True)
            while not event.is_set():
                keria_doist.recur(deeds=keria_deeds)

        stop_event = threading.Event()
        keria_thread = threading.Thread(target=run_keria_other_thread, args=(stop_event,))
        keria_thread.start()

        # Set up KERIA QAR
        boot_url = f"http://{host}:{bootPort}"
        connect_url = f"http://{host}:{adminPort}"
        # Add QVI schema to QVI Signify Controller
        qvi_bran = b'00123456789abcdefghij'
        qvi_ctrl_aid = 'EAE5wsF82FzIQxX7Qx9WKfHY13mSiCGzL4Tg8Y6YVSjd'
        qvi_client = create_agent(qvi_bran, qvi_ctrl_aid,
                               url=connect_url, boot_url=boot_url)
        qvi_agent = agency.get(qvi_client.ctrl.pre)
        HabbingHelpers.add_acdc_schema(qvi_agent.hby.db, Schemas.qvi_schema_as_dict())

        # Resolve OOBI of the wan witness for QVI AID
        keria_api.resolve_oobi(qvi_client, alias='wan', url=wan_oobi, agent=qvi_agent, doist=doist, deeds=wan_deeds)
        # TODO delete OOBI operation
        qvi_aid_name = 'qvi-aid'
        qvi_aid_state = keria_api.create_identifier(qvi_client, name=qvi_aid_name, agent=qvi_agent, doist=doist, deeds=wan_deeds, toad=1, wits=[wan_pre])
        # TODO delete create identifier operation
        qvi_identifiers = qvi_client.identifiers()
        qvi_aids = qvi_identifiers.list()
        qvi_aid = qvi_aids['aids'][0]
        assert len(qvi_aids['aids']) == 1, "There should be one QVI AID"

        # Have QVI OOBI with GEDA
        keria_api.resolve_oobi(qvi_client, alias=geda_hab_name, url=geda_oobi, agent=qvi_agent, doist=doist, deeds=wan_deeds)
        # TODO delete OOBI operation
        contacts = qvi_client.contacts()
        cons = contacts.list()
        assert len(cons['contacts']) == 2, "There should be two contacts for QVI AID"

        # GEDA OOBIs with QVI
        qvi_aid_oobi_resp = qvi_client.oobis().get(name=qvi_aid_name, role='agent')
        qvi_oobi = qvi_aid_oobi_resp['oobis'][0]
        HabbingHelpers.resolve_wit_oobi(doist, wan_deeds, geda_hby, qvi_oobi, qvi_aid_name)

        # Issue QVI credential from GEDA to QVI
        qvi_schema_said = 'EBfdlu8R27Fbx-ehrqwImnK-8Cm79sqbAQ4MmvEAYqao'
        qvi_acdc_data = {
            'LEI': '506700GE1G29325QX363',
            'gracePeriod': 180
        }
        qvi_creder, _, _ = CredentialHelpers.vc_create(
            hby=geda_hby,
            hby_doer=geda_hby_doer,
            regery=geda_regery,
            registry_name=geda_reg_name,
            hab=geda_hab,
            schema_said=qvi_schema_said,
            subject_data=qvi_acdc_data,
            rules_json=Schemas.qvi_rules_as_dict(),
            source=None,
            recp=qvi_aid['prefix'],
            additional_deeds=wan_deeds + geda_deeds
        )
        grant_cont_doer = GrantContainer(
            hby=geda_hby,
            hab=geda_hab,
            regery=geda_regery,
            tymth=doist.tymen()
        )
        grant_cont_doer.kli_grant(
            said=qvi_creder.said,
            recp=qvi_aid_state['prefix'],
            message="Here is the QVI credential",
            timestamp=nowIso8601()
        )
        # grant_deed = doist.enter(doers=[grant_cont_doer])
        while not grant_cont_doer.done:
            doist.recur(deeds=grant_cont_doer.deeds + wan_deeds)
        qvi_grant_notification = keria_api.wait_for_notification(qvi_client, '/exn/ipex/grant')
        keria_api.admit_credential(qvi_client, qvi_aid_name, qvi_grant_notification['a']['d'], [geda_hab.pre], qvi_agent)
        # todo mark notification as read
        # todo delete admit operation

        # Create QVI registry
        qvi_reg_name = 'qvi-reg'
        keria_api.create_registry(client=qvi_client, name=qvi_aid_name, registry_name=qvi_reg_name, agent=qvi_agent, doist=doist, deeds=wan_deeds)
        # TODO delete create registry operation

        # Set up Legal Entity
        # Add LE schema to LE Signify Controller
        le_bran = b'le023456789abcdefghij'
        le_ctrl_aid = 'EFW7wTDuSWICwgoTxdy85liV4Uzk9jnt6UIsFg0kl6wl'  # expected controller AID given le_bran
        le_client = create_agent(le_bran, le_ctrl_aid,
                                 url=connect_url, boot_url=boot_url)
        le_agent = agency.get(le_client.ctrl.pre)
        HabbingHelpers.add_acdc_schema(le_agent.hby.db, Schemas.le_schema_as_dict())
        HabbingHelpers.add_acdc_schema(le_agent.hby.db, Schemas.qvi_schema_as_dict())
        # Add LE schema to QVI
        HabbingHelpers.add_acdc_schema(qvi_agent.hby.db, Schemas.le_schema_as_dict())

        # Resolve OOBI of the wan witness for QVI AID
        keria_api.resolve_oobi(le_client, alias='wan', url=wan_oobi, agent=le_agent, doist=doist, deeds=wan_deeds)
        le_aid_name = 'le-aid'
        le_aid_state = keria_api.create_identifier(le_client, name=le_aid_name, agent=le_agent, doist=doist, deeds=wan_deeds, toad=1, wits=[wan_pre])
        # TODO delete create identifier operation
        le_identifiers = le_client.identifiers()
        le_aids = le_identifiers.list()
        assert len(le_aids['aids']) == 1, "There should be one QVI AID"

        # Have QVI and LE OOBI
        le_oobi_resp = le_client.oobis().get(name=le_aid_name, role='agent')
        le_oobi = le_oobi_resp['oobis'][0]
        keria_api.resolve_oobi(qvi_client, alias=le_aid_name, url=le_oobi, agent=qvi_agent, doist=doist, deeds=wan_deeds)
        # TODO delete OOBI operation
        keria_api.resolve_oobi(le_client, alias=qvi_aid_name, url=qvi_oobi, agent=le_agent, doist=doist, deeds=wan_deeds)
        # TODO delete OOBI operation

        # Issue vLEI from QVI to Legal Entity
        le_schema_said = 'ENPXp1vQzRF6JwIuS-mp2U8Uf1MoADoP_GqQ62VsDZWY'
        le_acdc_data = {
            'LEI': '506700GE1G29325QX363',
        }
        qvi_edge_data = {
            'd':'',
            'qvi': {
                'n': qvi_creder.sad['d'],
                's': qvi_creder.sad['s']
            }
        }
        _, qvi_edge = Saider.saidify(sad=qvi_edge_data, label=Saids.d)

        le_creder, le_iss_serder, le_iss_anc, sigs = keria_api.issue_credential(
            client=qvi_client,
            name=qvi_aid_name,
            registry_name=qvi_reg_name,
            schema=le_schema_said,
            recipient=le_aid_state['prefix'],
            data=le_acdc_data,
            agent=qvi_agent,
            doist=doist,
            deeds=wan_deeds,
            rules=Schemas.le_rules_as_dict(),
            edges=qvi_edge,
        )
        # TODO delete issue operation
        _grant = keria_api.ipex_grant(
            client=qvi_client,
            agent=qvi_agent,
            name=qvi_aid_name,
            creder=le_creder,
            iss_serder=le_iss_serder,
            iss_anc=le_iss_anc,
            sigs=sigs,
            recipient=le_aid_state['prefix'],
        )
        while qvi_agent.grants:
            sleep(0.125)
        while len(le_client.credentials().list()) == 0:
            sleep(0.25)
        # TODO delete grant operation
        le_grant_notification = keria_api.wait_for_notification(le_client, '/exn/ipex/grant')
        keria_api.admit_credential(
            client=le_client,
            name=le_aid_name,
            said=le_grant_notification['a']['d'],
            recipient=[qvi_aid['prefix']],
            agent=le_agent)
        # TODO mark notification as read
        # TODO delete admit operation

        # Set up Sally
        # Have Legal Entity OOBI with Sally
        # Have Legal Entity present vLEI to Sally
        # Assert Sally has received and validated the vLEI


        client = SignifyClient(passcode=le_bran, url=connect_url, boot_url=boot_url)
        client.boot()
        client.connect(url=connect_url)
        identifiers = client.identifiers()
        aids = identifiers.list()
        assert len(aids['aids']) == 0, "No identifiers should be present at this point"

        person_bran = b'abcdefghijk0123456789'
        client2 = create_agent(person_bran,
                               'EIIY2SgE_bqKLl2MlnREUawJ79jTuucvWwh-S6zsSUFo',
                               url=connect_url, boot_url=boot_url)
        identifiers2 = client2.identifiers()
        aids2 = identifiers2.list()
        assert len(aids2['aids']) == 0, "No identifiers should be present at this point"

        stop_event.set()
        keria_thread.join(timeout=2)







