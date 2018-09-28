### This is RGA:2 configured for ExQ new RGA connected at 10.28.2.142 #####
from ophyd import Device, Component as Cpt


class EpicsSignalOverridePrecRO(EpicsSignalRO):
    def __init__(self, *args, precision=10, **kwargs):
        self._precision = precision
        super().__init__(*args, **kwargs)

    @property
    def precision(self):
        return self._precision


class EpicsSignalOverridePrec(EpicsSignal):
    def __init__(self, *args, precision=10, **kwargs):
        self._precision = precision
        super().__init__(*args, **kwargs)

    @property
    def precision(self):
        return self._precision


class RGA(Device):
    startRGA = Cpt(EpicsSignal, 'Cmd:MID_Start-Cmd')
    stopRGA = Cpt(EpicsSignal, 'Cmd:ScanAbort-Cmd')
    mass1 = Cpt(EpicsSignalOverridePrecRO, 'P:MID1-I')
    mass2 = Cpt(EpicsSignalOverridePrecRO, 'P:MID2-I')
    mass3 = Cpt(EpicsSignalOverridePrecRO, 'P:MID3-I')
    mass4 = Cpt(EpicsSignalOverridePrecRO, 'P:MID4-I')
    mass5 = Cpt(EpicsSignalOverridePrecRO, 'P:MID5-I')
    mass6 = Cpt(EpicsSignalOverridePrecRO, 'P:MID6-I')
    mass7 = Cpt(EpicsSignalOverridePrecRO, 'P:MID7-I')
    mass8 = Cpt(EpicsSignalOverridePrecRO, 'P:MID8-I')
    mass9 = Cpt(EpicsSignalOverridePrecRO, 'P:MID9-I')

## We don't want the RGA to start and stop by any bluseky plan###

"""
    def stage(self):
        self.startRGA.put(1)

    def unstage(self):
        self.stopRGA.put(1)


    def describe(self):
        res = super().describe()
        # This precision should be configured correctly in EPICS.
        for key in res:
            res[key]['precision'] = 12
        return res
 """

rga = RGA('XF:28IDC-VA{RGA:2}',
          name='rga',
          read_attrs=['mass1', 'mass2', 'mass3', 'mass4','mass5', 'mass6', 'mass7', 'mass8', 'mass9'])
