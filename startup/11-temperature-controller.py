from ophyd import PVPositioner, EpicsSignal, EpicsSignalRO
from ophyd import Component as C
from ophyd.device import DeviceStatus


class CS700TemperatureController(PVPositioner):
    setpoint = C(EpicsSignal, 'T-SP')
    readback = C(EpicsSignalRO, 'T-I')
    done = C(EpicsSignalRO, 'Cmd-Busy')
    stop_signal = C(EpicsSignal, 'Cmd-Cmd')

    def trigger(self):
        # There is nothing to do. Just report that we are done.
        # Note: This really should not necessary to do --
        # future changes to PVPositioner may obviate this code.
        status = DeviceStatus()
        status._finished()
        return status

cs700 = CS700TemperatureController('XF:28IDC-ES:1{Env:01}', name='cs700',
                                   settle_time=10)
cs700.done_value = 0
