# -*- encoding: utf-8 -*-
"""
KERI
signify.app.grouping module

"""
from math import ceil

from keri.core import coring, eventing
from keri.core.coring import MtrDex

from signify.app.clienting import SignifyClient


class Groups:
    """ """

    def __init__(self, client: SignifyClient):
        """"""
        self.client = client

    @staticmethod
    def incept(states, rstates, isith=None, nsith=None, code=MtrDex.Blake3_256, toad="0", wits=None,
               estOnly=False, DnD=False, delpre=None, data=None):

        wits = wits if wits is not None else []
        keys = []
        for state in states:
            keys.append(state['k'][0])

        ndigs = []

        for state in rstates:
            ndigs.append(state['n'][0])

        if isith is None:  # compute default
            isith = f"{max(1, ceil(len(keys) / 2)):x}"
        if nsith is None:  # compute default
            nsith = f"{max(0, ceil(len(ndigs) / 2)):x}"
        isith = coring.Tholder(sith=isith).sith  # current signing threshold
        nsith = coring.Tholder(sith=nsith).sith  # next signing threshold

        cnfg = []
        if estOnly:
            cnfg.append(eventing.TraitCodex.EstOnly)
        if DnD:
            cnfg.append(eventing.TraitCodex.DoNotDelegate)

        if delpre is not None:
            return eventing.delcept(delpre=delpre,
                                    keys=keys,
                                    isith=isith,
                                    ndigs=ndigs,
                                    nsith=nsith,
                                    code=code,
                                    toad=toad,
                                    wits=wits,
                                    cnfg=cnfg,
                                    data=data)
        else:
            return eventing.incept(keys=keys,
                                   isith=isith,
                                   ndigs=ndigs,
                                   nsith=nsith,
                                   code=code,
                                   toad=toad,
                                   wits=wits,
                                   cnfg=cnfg,
                                   data=data)

    def join(self, states, rstates, serder, sigers):
        pass
