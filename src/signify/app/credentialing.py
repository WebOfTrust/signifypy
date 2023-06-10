from keri.core import coring
from keri.core.eventing import TraitDex
from keri.vdr import eventing


def registryIncept(hab, body):
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