#!/usr/bin/env python
import time
from pescan.utils import getEpicsPV
from ophyd.controls import EpicsSignal

class Shutter(object):
    """Open and close fast shutter.
    """

    def __init__(self, basepvname):
        self._setEpicsShutterCommands(basepvname)
        self._setEpicsShutterStatus(basepvname)
        return


    def _setEpicsShutterCommands(self, basepvname):
        open_suffix = 'Cmd:Opn-Cmd'
        close_suffix = 'Cmd:Cls-Cmd'
        open_pv = getEpicsPV(basepvname, open_suffix)
        close_pv = getEpicsPV(basepvname, close_suffix)
        self._opencmd = EpicsSignal(open_pv, rw = True, name = '_opencmd')
        self._closecmd = EpicsSignal(close_pv, rw = True, name = '_closecmd')
        return


    def _setEpicsShutterStatus(self, basepvname):
        open_suffix = 'Sw:Opn1-Sts'
        close_suffix = 'Sw:Cls1-Sts'
        open_pv = ''.join([basepvname, open_suffix])
        close_pv = ''.join([basepvname, close_suffix])
        self._openstatus = EpicsSignal(open_pv, name = '_openstatus')
        self._closestatus = EpicsSignal(close_pv, name = '_closestatus')
        return


    def openShutter(self):
        if self._openstatus.value == 0:
            return
        self._opencmd.put(1)
        while self._openstatus.value == 1:
            time.sleep(0.01)
        return


    def closeShutter(self):
        if self._closestatus.value == 0:
            return
        self._closecmd.put(1)
        while self._closestatus.value == 1:
            time.sleep(0.01)
        return


    @property
    def shutterStatus(self):
        rv = bool(not self._openstatus.value) and bool(self._closestatus.value)
        return rv
