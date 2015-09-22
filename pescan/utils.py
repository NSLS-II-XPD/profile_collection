#!/usr/bin/env python

from ophyd.controls import EpicsSignal

# Helper function for generating Epics PVs
def getEpicsPV(basename, suffix):
    rv = ''.join([basename, suffix])
    return rv

# Helper function for generating Epics Signals
def getEpicsSignal(basename, suffix, name = None, rw = False):
    pvname = getEpicsPV(basename, suffix)
    rv = EpicsSignal(pvname, rw = rw, name = name)
    return rv
