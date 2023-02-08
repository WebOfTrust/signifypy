# -*- encoding: utf-8 -*-
"""
KERI
signify.app.signifying module

"""
import json

import falcon
from falcon import media
from hio.base import doing
from hio.core import http
from hio.help import decking
from keri import kering
from keri.app import configing, keeping, habbing, indirecting, storing, signaling, notifying
from keri.app.indirecting import HttpEnd
from keri.core import coring, parsing
from keri.peer import exchanging
from keri.vc import protocoling
from keri.vdr import verifying, credentialing

from signify.core.authing import Authenticater
from src.signify.core import authing


def setup(name, base, bran, controller, adminPort, configFile=None, configDir=None, httpPort=None):
    """ Set up an agent in Signify mode """
    ks = keeping.Keeper(name=name,
                        base=base,
                        temp=False,
                        reopen=True)

    aeid = ks.gbls.get('aeid')

    cf = None
    if aeid is None and configFile is not None:  # Load config file if creating database
        cf = configing.Configer(name=configFile,
                                base="",
                                headDirPath=configDir,
                                temp=False,
                                reopen=True,
                                clear=False)

    # Create the Hab for the Agent with only 2 AIDs
    agentHby = habbing.Habery(name=name, base=base, bran=bran)

    # Create Agent AID if it does not already exist
    hab = agentHby.habByName(name) is None
    if hab:
        hab = agentHby.makeHab(name, transferable=True)
        print(f"Created Agent AID {hab.pre}")
    else:
        print(f"Loading Agent AID {hab.pre}")

    # Create the Hab for the Controller AIDs.
    ctrlHby = habbing.Habery(name=controller, base=base, cf=cf)
    doers = [habbing.HaberyDoer(habery=agentHby), habbing.HaberyDoer(habery=ctrlHby)]

    # Create Authenticater for verifying signatures on all requests
    authn = Authenticater(agent=hab, caid=controller)

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*', expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))
    app.add_middleware(authing.SignatureValidationComponent(authn=authn))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

    cues = decking.Deck()
    mbx = storing.Mailboxer(name=ctrlHby.name)
    rep = storing.Respondant(hby=ctrlHby, mbx=mbx)
    rgy = credentialing.Regery(hby=ctrlHby, name=name, base=base)
    verifier = verifying.Verifier(hby=ctrlHby, reger=rgy.reger)

    signaler = signaling.Signaler()
    notifier = notifying.Notifier(hby=ctrlHby, signaler=signaler)
    issueHandler = protocoling.IssueHandler(hby=ctrlHby, rgy=rgy, notifier=notifier)
    requestHandler = protocoling.PresentationRequestHandler(hby=ctrlHby, notifier=notifier)
    applyHandler = protocoling.ApplyHandler(hby=ctrlHby, rgy=rgy, verifier=verifier, name=ctrlHby.name)
    proofHandler = protocoling.PresentationProofHandler(notifier=notifier)

    handlers = [issueHandler, requestHandler, proofHandler, applyHandler]
    exchanger = exchanging.Exchanger(db=ctrlHby.db, handlers=handlers)
    mbd = indirecting.MailboxDirector(hby=ctrlHby,
                                      exc=exchanger,
                                      verifier=verifier,
                                      rep=rep,
                                      topics=["/receipt", "/replay", "/multisig", "/credential", "/delegate",
                                              "/challenge", "/oobi"],
                                      cues=cues)

    adminServer = http.Server(port=adminPort, app=app)
    adminServerDoer = http.ServerDoer(server=adminServer)
    doers.extend([exchanger, mbd, rep, adminServerDoer])

    if httpPort is not None:
        parser = parsing.Parser(framed=True,
                                kvy=mbd.kvy,
                                tvy=mbd.tvy,
                                exc=exchanger,
                                rvy=mbd.rvy)

        httpEnd = HttpEnd(rxbs=parser.ims, mbx=mbx)
        app.add_route("/", httpEnd)

        server = http.Server(port=httpPort, app=app)
        httpServerDoer = http.ServerDoer(server=server)
        doers.append(httpServerDoer)

    doers += loadEnds(app=app, agent=hab, controller=ctrlHby)

    return doers


def loadEnds(app, agent, controller):
    bootEnd = BootEnd(agent, controller)
    app.add_route("/boot", bootEnd)

    habEnd = HabEnd(agent)
    app.add_route("/aids}", habEnd)

    return [bootEnd]


class BootEnd(doing.DoDoer):
    """ Resource class for creating datastore in cloud agent """

    def __init__(self, agent, controller):
        """ Provides endpoints for initializing and unlocking an agent

        Parameters:
            agent (Hab): Hab for Signify Agent
            controller (str): qb64 of controller AID

        """
        self.agent = agent
        self.controller = controller
        doers = []
        super(BootEnd, self).__init__(doers=doers)

    def on_get(self, _, rep):
        """ GET endpoint for Keystores

        Get keystore status

        Args:
            _: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Query KERI environment for keystore name
        tags:
           - Boot
        parameters:
          - in: path
            name: name
            schema:
              type: string
            required: true
            description: predetermined name of keep keystore
            example: alice
        responses:
           202:
              description: Keystore exists
           404:
              description: No keystore exists

        """
        if self.controller not in self.agent.kevers:
            rep.status = falcon.HTTP_417
            rep.data = json.dumps({'msg': f'system agent AEID not loaded'}).encode("utf-8")
            return
        
        body = dict(aaid=self.agent.pre, caid=self.controller)

        rep.content_type = "application/json"
        rep.data = json.dumps(body).encode("utf-8")
        rep.status = falcon.HTTP_200


class HabEnd:
    """ Resource class for creating and managing identifiers """

    def __init__(self, hby):
        """

        Parameters:
            hby (HAbery): Controller database and keystore environment
        """
        self.hby = hby
        pass

    def on_post(self, req, rep):
        """ Inception event POST endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """
        try:
            body = req.get_media()
            icp = body.get("icp")
            if icp is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'icp' missing from request"}).encode("utf-8")
                return

            name = body.get("name")
            if name is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'name' missing from request"}).encode("utf-8")
                return
            
            ipath = body.get("ipath")
            if ipath is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'ipath' missing from request"}).encode("utf-8")
                return
            
            npath = body.get("npath")
            if npath is None:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'npath' missing from request"}).encode("utf-8")
                return
            
            sigs = body.get("sigs")
            if sigs is None or len(sigs) == 0:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'sigs' missing from request"}).encode("utf-8")
                return

            tier = body.get("tier")
            if tier not in coring.Tiers:
                rep.status = falcon.HTTP_423
                rep.data = json.dumps({'msg': f"required field 'tier' missing from request"}).encode("utf-8")
                return

            temp = body.get("temp") == "true"
            serder = coring.Serder(ked=icp)
            sigers = [coring.Siger(qb64=sig) for sig in sigs]

            self.hby.makeSignifyHab(name, serder=serder, sigers=sigers, ipath=ipath, npath=npath, tier=tier,
                                    temp=temp)

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
