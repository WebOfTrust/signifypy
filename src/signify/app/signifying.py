# -*- encoding: utf-8 -*-
"""
KERI
signify.app.signifying module

"""
import json

import falcon
from falcon import media
from hio.base import doing
from keri import kering
from keri.app import configing, keeping, habbing
from keri.core import coring

from signify.core import httping
from src.signify.core import authing


def setup(name, base, bran, controller, configFile=None, configDir=None):
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

    app = falcon.App(middleware=falcon.CORSMiddleware(
        allow_origins='*', allow_credentials='*', expose_headers=['cesr-attachment', 'cesr-date', 'content-type']))
    app.add_middleware(httping.SignatureValidationComponent(hby=None, pre=controller))
    app.req_options.media_handlers.update(media.Handlers())
    app.resp_options.media_handlers.update(media.Handlers())

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
            name (str): keystore name for Signify Agent
            base (str): optional directory path segment inserted before name
                        that allows further hierarchical differentiation of databases.
                        "" means optional.
            temp (bool): True for testing:
                temporary storage of databases and config file
                weak resources for stretch of salty key
            configFile (str):  name of config file to load
            configDir (str): name of base for directory to load
            headDirPath (str): root path

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
        if not self.btl.booted:
            rep.status = falcon.HTTP_417
            rep.data = json.dumps({'msg': f'system agent AEID not loaded'}).encode("utf-8")
            return
        
        body = dict(aaid=self.agent.pre, caid=c)

        rep.content_type = "application/json"
        rep.data = json.dumps(body).encode("utf-8")
        rep.status = falcon.HTTP_200

    def on_post(self, req, rep):
        """ POST endpoint for creating a new environment (keystore and database)

        Post creates a new database with aeid encryption key generated from passcode.  Fails
        if database already exists.

        Args:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Create KERI environment (database and keystore)
        description: Creates the directories for database and keystore for vacuous KERI instance
                     using name and aeid key or passcode to encrypt datastore.  Fails if directory
                     already exists.
        tags:
           - Boot
        requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   name:
                     type: string
                     description: human readable nickname for this agent
                     example: alice
                   aeid:
                     type: string
                     description: qualified base64 encoded non-transferable identifier as AEID
                     example: BKlt39DHsSyqKb6ZYW8BnhSYWJnBniB78egviLLYeVmo
                   ndig:
                     type: string
                     description: qualified base64 encoded Blake3 digest of prior next AEID (AEID')
        responses:
           200:
              description: JSON object containing status message

        """
        body = req.get_media()

        name = body["name"]
        aeid = body["aeid"]
        ndig = body["ndig"]

        try:
            rep.status = falcon.HTTP_200
            body = dict(name=name, msg="Keystore created")
            rep.content_type = "application/json"
            rep.data = json.dumps(body).encode("utf-8")

        except Exception as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]

    def on_put(self, req, rep):
        """ PUT endpoint for rotating an existing keystore

        Put updates an existing keystore with a new AEID and encrypted keys.

        Args:
            req: falcon.Request HTTP request
            rep: falcon.Response HTTP response

        ---
        summary: Create KERI environment (database and keystore)
        description: Creates the directories for database and keystore for vacuous KERI instance
                     using name and aeid key or passcode to encrypt datastore.  Fails if directory
                     already exists.
        tags:
           - Boot
        requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 properties:
                   name:
                     type: string
                     description: human readable nickname for this agent
                     example: alice
                   passcode:
                     type: string
                     description: passcode for encrypting and securing this agent
                     example: RwyY-KleGM-jbe1-cUiSz-p3Ce
        responses:
           200:
              description: JSON object containing status message

        """
        body = req.get_media()
        rep.status = falcon.HTTP_200
        rep.content_type = "application/json"
        rep.data = json.dumps(body).encode("utf-8")


class HabEnd:
    """ Resource class for Signify client signing at the edge """

    def __init__(self, btl: authing.Authenticater):
        self.btl = btl
        pass

    def on_post(self, req, rep):
        """ Inception event POST endpoint

        Parameters:
            req (Request): falcon.Request HTTP request object
            rep (Response): falcon.Response HTTP response object

        """
        if self.btl.booted is None:
            rep.status = falcon.HTTP_423
            rep.data = json.dumps({'msg': f'system agent AEID not loaded'}).encode("utf-8")
            return

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

            self.btl.hby.makeSignifyHab(name, serder=serder, sigers=sigers, ipath=ipath, npath=npath, tier=tier,
                                        temp=temp)

            rep.status = falcon.HTTP_200
            rep.content_type = "application/json"
            rep.data = serder.raw

        except (kering.AuthError, ValueError) as e:
            rep.status = falcon.HTTP_400
            rep.text = e.args[0]
