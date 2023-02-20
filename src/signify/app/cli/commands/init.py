# -*- encoding: utf-8 -*-
"""
KERI
keri.kli.witness module

Witness command line interface
"""
import argparse

from keri import kering
from keri.core import coring

from signify.core import authing

d = "Initialize Signify Client\n"
d += "\tExample:\nsignify init\n"
parser = argparse.ArgumentParser(description=d)
parser.set_defaults(handler=lambda args: init(args))
parser.add_argument('--passcode', '-p', help='22 character encryption passcode for keystore (is not saved)',
                    dest="bran", required=True)  # passcode => bran
parser.add_argument('--tier', '-t', help='security threshold of generated private keys [high, med, low, temp]',
                    default="low")


def init(args):
    bran = args.bran
    if args.tier == "temp":
        tier = coring.Tiers.low
        temp = True
    elif args.tier in coring.Tiers:
        tier = args.tier
        temp = False
    else:
        raise kering.ConfigurationError(f"invalid value {args.tier} for --tier")

    if len(bran) < 21:
        raise ValueError(f"Bran (passcode seed material) too short.")

    ctrl = authing.Controller(bran=bran, tier=tier, temp=temp)

    print("Provide the following Controller AID to KERIA Cloud Agent")
    print(f"\tAID: {ctrl.pre}")


