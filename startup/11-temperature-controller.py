from ophyd import PVPositioner, EpicsSignal, EpicsSignalRO, Device
from ophyd.signal import AttributeSignal
from ophyd.mixins import EpicsSignalPositioner
from ophyd import Component as C
from ophyd import Component as Cpt
from ophyd.device import DeviceStatus


class CS700TemperatureController(PVPositioner):
    readback = C(EpicsSignalRO, 'T-I')
    setpoint = C(EpicsSignal, 'T-SP')
    done = C(EpicsSignalRO, 'Cmd-Busy')
    stop_signal = C(EpicsSignal, 'Cmd-Cmd')
    targettemp = C(EpicsSignalRO, 'T:Target-I')
    def set(self, *args, timeout=None, **kwargs):
        return super().set(*args, timeout=timeout, **kwargs)

    def trigger(self):
        # There is nothing to do. Just report that we are done.
        # Note: This really should not necessary to do --
        # future changes to PVPositioner may obviate this code.
        status = DeviceStatus(self)
        status._finished()
        return status

# To allow for sample temperature equilibration time, increase
# the `settle_time` parameter (units: seconds).
cs700 = CS700TemperatureController('XF:28IDC-ES:1{Env:01}', name='cs700',
                                   settle_time=0)
cs700.done_value = 0
cs700.read_attrs = ['setpoint', 'readback','targettemp']
cs700.readback.name = 'temperature'
cs700.setpoint.name = 'temperature_setpoint'
cs700.targettemp.name = 'temperature_target'


class CS800TemperatureController(PVPositioner):
    readback = C(EpicsSignalRO, ':TEMP')
    setpoint = C(EpicsSignal, ':RTEMP')
    done = C(EpicsSignalRO, ':PHASE', string=True) #0:ramp, 1:cool, 2:flat, 3:hold, 4:end, 5:purge
    #stop_signal = C(EpicsSignal, ':STOP.PROC')
    runmode = C(EpicsSignalRO, ':RUNMODE', string=True) #0:runup OK,  2:startup OK, 3:run, 5:shutdown Ok
    #trigger signal
    trig = Cpt(EpicsSignal,':RAMP.PROC')
    coolsetpoint = C(EpicsSignal, ':CTEMP')
    cooltrig = Cpt(EpicsSignal,':COOL.PROC')
    #targettemp = C(EpicsSignalRO, 'T:Target-I')
    def set(self, *args, timeout=None, **kwargs):
        return super().set(*args, timeout=timeout, **kwargs)

    def trigger(self):
        # There is nothing to do. Just report that we are done.
        # Note: This really should not necessary to do --
        # future changes to PVPositioner may obviate this code.
        self.trig.put(1, wait=True)
        #status = DeviceStatus(self)
        #status._finished()
        return DeviceStatus(self, done = True, success=True)

    def moveto(self, position, timeout=None, move_cb=None, **kwargs):
        if self.runmode.get()!='Shutdown OK':
            self.setpoint.set(position, timeout=timeout, **kwargs)
            self.trig.put(1, wait=True)
            #wait 5 second to allow phaseID update after trigger
            time.sleep(10)
            while self.done.value != 'Hold':
                time.sleep(0.1)
            return DeviceStatus(self,done = True, success=True)
        else:
            raise ValueError('cs800 is shutdown mode, please restart it')

    def coolto(self, position, timeout=None, move_cb=None, **kwargs):
        if self.runmode.get()!='Shutdown OK':
            self.coolsetpoint.set(position, timeout=timeout, **kwargs)
            self.cooltrig.put(1, wait=True)
            #wait 5 second to allow phaseID update after trigger
            time.sleep(10)
            while self.done.value != 'Hold':
                time.sleep(0.1)
            return DeviceStatus(self,done = True, success=True)
        else:
            raise ValueError('cs800 is shutdown mode, please restart it')

    def setcoolto(self, position, timeout=None, move_cb=None, **kwargs):
        if self.runmode.get()!='Shutdown OK':
            self.coolsetpoint.set(position, timeout=timeout, **kwargs)
            self.cooltrig.put(1, wait=True)
            
            return DeviceStatus(self,done = True, success=True)
        else:
            raise ValueError('cs800 is shutdown mode, please restart it')

# To allow for sample temperature equilibration time, increase
# the `settle_time` parameter (units: seconds).
cs800 = CS800TemperatureController('XF:28IDC-ES:1{CS:800}', name='cs800',
                                   settle_time=0)
cs800.done_value = 'Hold'
cs800.read_attrs = ['setpoint', 'readback']
cs800.readback.name = 'temperature'
cs800.setpoint.name = 'temperature_setpoint'


'''
class Eurotherm(EpicsSignalPositioner):

    def set(self, *args, **kwargs):
        # override #@!$(#$ hard-coded timeouts
        return super().set(*args, timeout=1000000, **kwargs)

eurotherm = Eurotherm('XF:28IDC-ES:1{Env:04}T-I',
                                 write_pv='XF:28IDC-ES:1{Env:04}T-SP',
                                 tolerance= 1, name='eurotherm')

eurotherm_power = Eurotherm('XF:28IDC-ES:1{Env:04}Out-I',
                                 write_pv='XF:28IDC-ES:1{Env:04}Out-SP',
                                 tolerance= 1, name='eurotherm_power')

eurotherm_mode = Eurotherm('XF:28IDC-ES:1{Env:04}Mode:Man-Sts',
                                 write_pv='XF:28IDC-ES:1{Env:04}Mode:Man-Cmd',
                                 tolerance= 1, name='eurotherm_mode')
'''

class Eurotherm(Device):
    temperature = Cpt(
        EpicsSignalPositioner,
        'T-I',
        write_pv='T-SP',
        tolerance=1,
        #write_timeout=1000000
    )
    power = Cpt(
        EpicsSignalPositioner,
        'Out-I',
        write_pv='Out-SP',
        tolerance=1,
        #write_timeout=1000
    )
    mode = Cpt(
        EpicsSignal,
        'Mode:Man-Sts',
        write_pv='Mode:Man-Cmd',
        kind='config',
        string=True
    )
    ramprate = Cpt(
        EpicsSignalPositioner,
        'Rate:Ramp-RB',
        write_pv='Rate:Ramp-SP',
        tolerance=1
    )
    setread = Cpt(
        EpicsSignalPositioner,
        'Disp-Line2',
        #write_pv='Rate:Ramp-SP',
        tolerance=1
    )
eurotherm = Eurotherm('XF:28IDC-ES:1{Env:04}', name='eurotherm')
eurotherm2 = Eurotherm('XF:28IDC-ES:1{Env:06}', name='eurotherm2')
hotairblower = Eurotherm('XF:28IDC-ES:1{Env:03}', name='hotairblower')

'''

#hot air blower , add by Hui and Jianming
hotairblower=Eurotherm('XF:28IDC-ES:1{Env:03}T-I',
                                 write_pv='XF:28IDC-ES:1{Env:03}T-SP',
                                 tolerance= 1, name='hotairblower')

'''
class CryoStat(Device):
    # readback
    T = Cpt(EpicsSignalRO, ':IN1')
    # setpoint
    setpoint = Cpt(EpicsSignal, read_pv=":OUT1:SP_RBV",
                   write_pv=":OUT1:SP",
                   add_prefix=('suffix', 'read_pv', 'write_pv'))
    # heater power level
    heater = Cpt(EpicsSignal, ':HTR1')

    # configuration
    dead_band = Cpt(AttributeSignal, attr='_dead_band')
    heater_range = Cpt(EpicsSignal, ':HTR1:Range', string=True)
    scan = Cpt(EpicsSignal, ':read.SCAN', string=True)
    mode = Cpt(EpicsSignal, ':OUT1:Mode', string=True)
    cntrl = Cpt(EpicsSignal, ':OUT1:Cntrl', string=True)
    # trigger signal
    trig = Cpt(EpicsSignal, ':read.PROC')

    def trigger(self):
        self.trig.put(1, wait=True)
        return DeviceStatus(self, done=True, success=True)

    def __init__(self, *args, dead_band, read_attrs=None,
                 configuration_attrs=None, **kwargs):
        if read_attrs is None:
            read_attrs = ['T', 'setpoint']
        if configuration_attrs is None:
            configuration_attrs = ['heater_range', 'dead_band',
                                   'mode', 'cntrl']
        super().__init__(*args, read_attrs=read_attrs,
                         configuration_attrs=configuration_attrs,
                         **kwargs)
        self._target = None
        self._dead_band = dead_band
        self._sts = None

    def _sts_mon(self, value, **kwargs):
        if (self._target is None or
                 np.abs(self._target - value) < self._dead_band):
            self.T.clear_sub(self._sts_mon)
            self.scan.put('Passive', wait=True)
            if self._sts is not None:
                self._sts._finished()
                self._sts = None
            self._target = None

    def set(self, val):
        self._target = val
        self.setpoint.put(val, wait=True)
        sts = self._sts = DeviceStatus(self)
        self.scan.put('.2 second')
        self.T.subscribe(self._sts_mon)

        return sts

    def stop(self, *, success=False):
        self.setpoint.put(self.T.get())
        if self._sts is not None:
            self._sts._finished(success=success)
        self._sts = None
        self._target = None
        self.scan.put('Passive', wait=True)


cryostat = CryoStat('XF:28IDC-ES1:LS335:{CryoStat}', name='cryostat', dead_band=1)


# TODO : PV needs to be fixed for done signal
# (doesn't work on ramp down)
class LinkamFurnace(PVPositioner):
    readback = C(EpicsSignalRO, 'TEMP')
    setpoint = C(EpicsSignal, 'RAMP:LIMIT:SET')
    done = C(EpicsSignalRO, 'STATUS')
    stop_signal = C(EpicsSignal, 'RAMP:CTRL:SET')
    ramp_rate = C(EpicsSignal, 'RAMP:RATE:SET')

    def set(self, new_position, *args, timeout=None, **kwargs):
        if abs(new_position - self.setpoint.value) < 1:
            return DeviceStatus(self, done=True, success=True)
        else:
            return super().set(new_position, *args, timeout=timeout, **kwargs)

    def trigger(self):
        # There is nothing to do. Just report that we are done.
        # Note: This really should not necessary to do --
        # future changes to PVPositioner may obviate this code.
        status = DeviceStatus(self)
        status._finished()
        return status

# To allow for sample temperature equilibration time, increase
# the `settle_time` parameter (units: seconds).
linkam_furnace = LinkamFurnace('XF:28IDC-ES:2:{LINKAM}:',
                               name='linkam_furnace', settle_time=0)
linkam_furnace.done_value = 3
linkam_furnace.stop_value = 1
linkam_furnace.setpoint.kind = "normal"
linkam_furnace.readback.kind = "normal"
linkam_furnace.readback.name = 'temperature'
linkam_furnace.setpoint.name = 'temperature_setpoint'

