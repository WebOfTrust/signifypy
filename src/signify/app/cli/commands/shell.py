# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.witness module

Witness command line interface
"""
import argparse
import cmd

from hio.base import doing
from keri import kering
from keri.core import coring

from signify.app import clienting

d = "Signify Client Shell\n"
d += "\tExample:\nsignify shell\n"
parser = argparse.ArgumentParser(description=d)
parser.set_defaults(handler=lambda args: signify(args))
parser.add_argument('--agent', '-a',
                    action='store',
                    required=True,
                    help="KERIA Cloud Agent URL.")
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", required=True)  # passcode => bran
parser.add_argument('--tier', '-t', help='security threshold of generated private keys [high, med, low, temp]',
                    default="low")

DEFAULT_PROMPT = "(signify) "


def signify(args):
    kwa = dict(args=args)
    return [doing.doify(shell, **kwa)]


def shell(tymth, tock=0.0, **opts):
    _ = (yield tock)

    args = opts["args"]
    agent = args.agent
    bran = args.bran

    if len(bran) < 21:
        raise ValueError(f"Bran (passcode seed material) too short.")

    if args.tier == "temp":
        tier = coring.Tiers.low
        temp = True
    elif args.tier in coring.Tiers:
        tier = args.tier
        temp = False
    else:
        raise kering.ConfigurationError(f"invalid value {args.tier} for --tier")

    client = clienting.SignifyClient(url=agent, bran=bran, tier=tier, temp=temp)
    client.connect()
    SignifyShell(client).cmdloop()


class SignifyShell(cmd.Cmd):
    prompt = DEFAULT_PROMPT
    add_cmds = ["participant", "witness", "local"]

    def __init__(self, client):
        self.client = client
        super(SignifyShell, self).__init__()

    @property
    def intro(self):
        return 'Welcome to the Signify interactive client shell.   Type help or ? to list commands.\n\nUsing ' \
               f'Controller AID {self.client.ctrl.pre}\nAgent: {self.client.base}'

    # ----- basic multisig commands -----
    def do_show(self, _):
        """ Print the current start of the multisig group configuration file """
        print(self.client.ctrl.pre)

    def do_exit(self, _):
        """ Exit without saving """
        self.close()
        return True

    def precmd(self, line):
        if self.prompt == "\tEnter weight: ":
            self.prompt = DEFAULT_PROMPT
            return ""

        return line

    def emptyline(self) -> bool:
        return False

    @staticmethod
    def close():
        print("Closing")
