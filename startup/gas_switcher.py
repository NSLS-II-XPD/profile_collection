from ophyd import EpicsSignal, Device
from ophyd import Component as C


class XPDGasSwitcher(Device):
    pass
    # position = C(EpicsSignal, 'XF:28IDC-ES:1{Env:02}Pos-I',
    #              write_pv='XF:28IDC-ES:1{Env:02}Pos-SP')
    # gas = # as in Ni, O
