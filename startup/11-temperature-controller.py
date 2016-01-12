from ophyd import PVPositioner, EpicsSignal, EpicsSignalRO
from ophyd import Component as C


class CS700TemperatureController(PVPositioner):
    setpoint = C(EpicsSignal, 'T-I.VAL')
    readback = C(EpicsSignalRO, 'T-I.RBV')
    done = C(EpicsSignalRO, 'Cmd-Busy')
    stop_signal = C(EpicsSignal, 'Cmd-Cmd')

cs700 = CS700TemperatureController('XF:28IDC-ES:1{Env:01}', name='cs700')


# old version from ophyd v0.1.x
# cs700 = PVPositioner('XF:28IDC-ES:1{Env:01}'),
#                      readback='XF:28IDC-ES:1{Env:01}T-I',
#                     #done='XF:28IDC-ES:1{Env:01}Cmd-Busy', done_val=0,
#                     stop='XF:28IDC-ES:1{Env:01}Cmd-Cmd', stop_val=13,
#                     put_complete=True, name='cs700')
