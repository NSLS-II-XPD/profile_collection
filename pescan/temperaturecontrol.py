#!/usr/bin/env python

from pescan.utils import getEpicsSignal


class TemperatureController(object):
    """Control sample temperature.
    """

    def __init__(self, basepvname):
        self._ramprate = getEpicsSignal(basepvname, "T:RampRate-SP", rw = True)
        self._setpoint = getEpicsSignal(basepvname, "T-SP", rw = True)
        self._temperature = getEpicsSignal(basepvname, "T-RB")
        return


    @property
    def temperature(self):
        return self._temperature.get()


    @property
    def setpoint(self):
        return self._setpoint.get()


    @setpoint.setter
    def setpoint(self, value):
        self._setpoint.put(value)
        return


    @property
    def ramprate(self):
        return self._ramprate.get()


    @ramprate.setter
    def ramprate(self, value):
        self._ramprate.put(value)
        return
