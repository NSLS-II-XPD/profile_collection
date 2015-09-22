from __future__ import print_function
import epics
import logging

from ophyd.controls import EpicsSignal
from ophyd.controls.signal import SignalGroup


class Shutter(SignalGroup):
    '''Base class for shutters or valves'''

    def __init__(self, *args, **kwargs):
        super(Shutter, self).__init__(*args, **kwargs)

    def open(self):
        pass

    def close(close):
        pass


class Nsls2Shutter(Shutter):
    def __init__(self, open=None, open_status=None,
                 close=None, close_status=None):
       Shutter.__init__(self)
       signals = [EpicsSignal(open_status, write_pv=open, alias='_open'),
                  EpicsSignal(close_status, write_pv=close, alias='_close'),
                  ]

       for sig in signals:
           self.add_signal(sig)

    @property
    def open(self):
        return self._open.value == 0

    @open.setter
    def open(self, val):
        self._open.value = val

    @property
    def close(self):
        return self._close.value == 0

    @close.setter
    def close(self, val):
        self._close.value = val

# this is the fast shutter
        ret = self.read_pv
        ton_shutter
sh1 = Nsls2Shutter(open='XF:28IDC-ES:1{Sh:Exp}Cmd:Opn-Cmd',
                   open_status='XF:28IDC-ES:1{Sh:Exp}Sw:Opn1-Sts',
                   close='XF:28IDC-ES:1{Sh:Exp}Cmd:Cls-Cmd',
                   close_status='XF:28IDC-ES:1{Sh:Exp}Sw:Cls1-Sts')

class PhotonShutter(EpicsSignal):
    def __init__(self, read_pv, open_pv, open_status, close_pv, close_status,
                 *args, **kw):
        self.open_pv = epics.PV(open_pv)
        self.open_status = open_status
        self.close_pv = epics.PV(close_pv)
        self.close_status = close_status

        super(PhotonShutter, self).__init__(read_pv=read_pv, *args, **kw)

    def put(self, value, force=False, **kwargs):
        if value == 0:
            self._write_pv = self.close_pv
        else:
            self._write_pv = self.open_pv
        super(PhotonShutter, self).put(1)

    def get(self):
        rbv = self._read_pv.get()
        if rbv == 1:
            return 0
        else:
            return 1


# this is the photon shutter (the shutter at the entrance to the C hutch
photon_shutter = PhotonShutter(
        read_pv='XF:28IDA-PPS{PSh}Pos-Sts',
        open_pv='XF:28IDA-PPS{PSh}Cmd:Opn-Cmd',
        open_status='XF:28IDA-PPS{PSh}Cmd:Opn-Sts',
        close_pv='XF:28IDA-PPS{PSh}Cmd:Cls-Cmd',
        close_status='XF:28IDA-PPS{PSh}Cmd:Cls-Sts',
        name='photon_shutter')
