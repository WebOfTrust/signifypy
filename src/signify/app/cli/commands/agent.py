# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.witness module

Witness command line interface
"""
import argparse
import logging

from keri import __version__
from keri import help
from keri.app import directing, indirecting, habbing, keeping
from keri.app.cli.common import existing

from src.signify.app import signifying

d = "Runs KERI Signify Agent\n"
d += "\tExample:\nkli agent\n"
parser = argparse.ArgumentParser(description=d)
parser.set_defaults(handler=lambda args: launch(args))
parser.add_argument('-V', '--version',
                    action='version',
                    version=__version__,
                    help="Prints out version of script runner.")
parser.add_argument('-a', '--admin-http-port',
                    action='store',
                    default=5623,
                    help="Admin port number the HTTP server listens on. Default is 5623.")
parser.add_argument('-H', '--http',
                    action='store',
                    default=5632,
                    help="Local port number the HTTP server listens on. Default is 5631.")
parser.add_argument('-c', '--controller', required=True,
                    help="Identifier prefix to accept control messages from.")
parser.add_argument('-n', '--name',
                    action='store',
                    default="agent",
                    help="Name of controller. Default is witness.")
parser.add_argument('--base', '-b', help='additional optional prefix to file location of KERI keystore',
                    required=False, default="")
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran
parser.add_argument('--config-file',
                    dest="configFile",
                    action='store',
                    default="",
                    help="configuration filename")
parser.add_argument("--config-dir",
                    dest="configDir",
                    action="store",
                    default=None,
                    help="directory override for configuration data")


def launch(args):
    help.ogler.level = logging.CRITICAL
    help.ogler.reopen(name=args.name, temp=True, clear=True)

    logger = help.ogler.getLogger()

    logger.info("\n******* Starting Agent for %s listening: http/%s, tcp/%s "
                ".******\n\n", args.name, args.http, args.tcp)

    runAgent(args.controller, name=args.name,
             base=args.base,
             bran=args.bran,
             admin=args.adminHttpPort,
             http=int(args.http),
             configFile=args.configFile,
             configDir=args.configDir)

    logger.info("\n******* Ended Agent for %s listening: http/%s, tcp/%s"
                ".******\n\n", args.name, args.http, args.tcp)


def runAgent(controller, *, name="agent", base="", bran="", admin=5623, http=5632, configFile=None,
             configDir=None, expire=0.0):
    """
    Setup and run one witness
    """

    doers = []
    doers.extend(signifying.setup(name=name, base=base, bran=bran,
                                  controller=controller,
                                  adminPort=admin,
                                  httpPort=http,
                                  configFile=configFile,
                                  configDir=configDir))

    directing.runController(doers=doers, expire=expire)
