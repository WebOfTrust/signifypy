# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.commands module

"""
import argparse
import sys

from hio import help
from hio.base import doing
from keri.app.cli.common import terming
from keri.core.coring import Tiers

from signify.app import clienting

logger = help.ogler.getLogger()

parser = argparse.ArgumentParser(description='View status of a local AID')
parser.set_defaults(handler=lambda args: handler(args),
                    transferable=True)
parser.add_argument('--url', '-u', help='Agent URL, defaults to "http://localhost:3901"',
                    default="http://localhost:3901")
parser.add_argument('--alias', '-a', help='human readable alias for the new identifier prefix', default=None)
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", default=None)  # passcode => bran

parser.add_argument("--verbose", "-V", help="print JSON of all current events", action="store_true")


def handler(args):
    kwa = dict(args=args)
    return [doing.doify(status, **kwa)]


def status(tymth, tock=0.0, **opts):
    """ Command line status handler

    """
    _ = (yield tock)
    args = opts["args"]
    alias = args.alias
    bran = args.bran

    url = args.url
    tier = Tiers.low

    client = clienting.SignifyClient(passcode=bran, tier=tier, url=url)
    identifiers = client.identifiers()

    aid = identifiers.get(alias)

    printIdentifier(aid)


def printIdentifier(aid, label="Identifier"):

    state = aid["state"]

    print(f"Alias: \t{aid['name']}")
    print("{}: {}".format(label, aid["prefix"]))
    print("Seq No:\t{}".format(state['s']))
    if state['di']:
        anchor = True
        print("Delegated Identifier")
        sys.stdout.write(f"    Delegator:  {state['di']} ")
        if anchor:
            print(f"{terming.Colors.OKGREEN}{terming.Symbols.CHECKMARK} Anchored{terming.Colors.ENDC}")
        else:
            print(f"{terming.Colors.FAIL}{terming.Symbols.FAILED} Not Anchored{terming.Colors.ENDC}")
        print()

    if "group" in aid:
        group = aid["group"]
        accepted = True
        print("Group Identifier")
        sys.stdout.write(f"    Local Indentifier:  {group['mhab']['prefix']} ")
        if accepted:
            print(f"{terming.Colors.OKGREEN}{terming.Symbols.CHECKMARK} Fully Signed{terming.Colors.ENDC}")
        else:
            print(f"{terming.Colors.FAIL}{terming.Symbols.FAILED} Not Fully Signed{terming.Colors.ENDC}")

    print("\nWitnesses:")
    print("Count:\t\t{}".format(len(state['b'])))
    print("Receipts:\t{}".format(len(aid['windexes'])))
    print("Threshold:\t{}".format(state['bt']))
    print("\nPublic Keys:\t")
    for idx, key in enumerate(state['k']):
        print(f'\t{idx+1}. {key}')

    print()

