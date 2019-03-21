from ophyd import (Device,
                   Component as Cpt,
                   EpicsSignal, EpicsSignalRO, Signal)
from bluesky.preprocessors import (
    run_decorator, stage_decorator, finalize_decorator,
    monitor_during_decorator)
import bluesky.plan_stubs as bps
import pandas as pd
import time


class CurrentSetterEpicSignal(EpicsSignal):
    def stop(self):
        self.parent.enabled.put(0)


class CurrentEnable(EpicsSignal):
    def stop(self):
        self.put(0)


class FlashRampInternals(Device):
    next_sp = Cpt(EpicsSignalRO, 'I:Next-SP')
    next_min = Cpt(EpicsSignalRO, 'I:Next-Min')
    sp1 = Cpt(EpicsSignalRO, 'I:OutMain-SP1')
    sp = Cpt(EpicsSignalRO, 'I:OutMain-SP')
    scheduler = Cpt(EpicsSignalRO, 'I:Scheduler')


class FlashPower(Device):
    # stuff from PSU sorensonxg850.template
    current = Cpt(EpicsSignalRO, 'I-I', kind='hinted')
    voltage = Cpt(EpicsSignalRO, 'E-I', kind='hinted')

    current_sp = Cpt(CurrentSetterEpicSignal,
                     'I:OutMain-RB',
                     'I-Lim')
    voltage_sp = Cpt(EpicsSignal,
                     'E:OutMain-RB',
                     'E:OutMain-SP')

    enabled = Cpt(CurrentEnable,
                  'Enbl:OutMain-Sts',
                  'Enbl:OutMain-Cmd',
                  kind='omitted',
                  string=True)

    remote_lockout = Cpt(EpicsSignal,
                         'Enbl:Lock-Sts',
                         'Enbl:Lock-Cmd',
                         string=True,
                         kind='config')

    foldback_mode = Cpt(EpicsSignal,
                        'Mode:Fold-Sts',
                        'Mode:Fold-Sel',
                        string=True,
                        kind='config')

    over_volt_val = Cpt(EpicsSignal,
                        'E:OverProt-RB',
                        'E:OverProt-SP',
                        kind='config')

    protection_reset = Cpt(
        EpicsSignal, 'Reset:FoldProt-Cmd',
        kind='omitted')

    status = Cpt(EpicsSignalRO, 'Sts:Opr-Sts')

    # stuff from ramp_rate.db
    ramp_rate = Cpt(EpicsSignal,
                    'I-RampRate-RB',
                    'I-RampRate-I',
                    kind='config')

    delta = Cpt(EpicsSignalRO,
                'I-Delta',
                kind='config')

    mode = Cpt(EpicsSignal, 'UserMode-I',
               string=True,
               kind='config')

    _internals = Cpt(FlashRampInternals, '')

    def unstage(self):
        ret = super().unstage()
        self.enabled.put(0)
        return ret

    def stop(self):
        # for safety
        self.enabled.put(0)


class KeithlyMMChannel(Device):
    chanafunc = Cpt(EpicsSignal, "ChanAFunc")
    chanaresults = Cpt(EpicsSignal, "ChanAResults")
    chanatimes = Cpt(EpicsSignal, "ChanATimes")
    chanaenable = Cpt(EpicsSignal, "ChanAEnable")

    chanbfunc = Cpt(EpicsSignal, "ChanBFunc")
    chanbresults = Cpt(EpicsSignal, "ChanBResults")
    chanbtimes = Cpt(EpicsSignal, "ChanBTimes")
    chanbenable = Cpt(EpicsSignal, "ChanBEnable")


class KeithlyMM(Device):
    # these are the ones documented in the readme
    readtype = Cpt(EpicsSignal, "ReadType", kind='config')
    # the readme says you get one or the other which seems odd?
    readcurr = Cpt(EpicsSignal, "ReadCurr", kind='hinted')
    readvolt = Cpt(EpicsSignal, "ReadVolt", kind='hinted')

    synctype = Cpt(EpicsSignal, "SyncType", kind='config')

    # other records in db file, not sure what to do with
    test = Cpt(EpicsSignal, "test", kind='omitted')

    timetotal = Cpt(EpicsSignal, "TimeTotal", kind='omitted')

    # this looks like a way to buffer in device?
    scaninterval = Cpt(EpicsSignal, "ScanInterval", kind='omitted')
    numchannels = Cpt(EpicsSignal, "NumChannels", kind='omitted')
    scancount = Cpt(EpicsSignal, "ScanCount", kind='omitted')

    func = Cpt(EpicsSignal, "Func", kind='omitted')

    # these seems important?
    scanresults = Cpt(EpicsSignal, "ScanResults", kind='omitted')
    timestamp = Cpt(EpicsSignal, "Timestamp", kind='omitted')
    timestampfrac = Cpt(EpicsSignal, "TimestampFrac", kind='omitted')
    timestampint = Cpt(EpicsSignal, "TimestampInt", kind='omitted')

    readtypeseq = Cpt(EpicsSignal, "ReadTypeSeq", kind='omitted')


MM = KeithlyMM('XF:28IDC-ES{KDMM6500}',
               name='MM')
flash_power = FlashPower('XF:28ID2-ES{PSU:SRS}',
                         name='flash_power')

def _setup_mm(mm_mode):
    yield from bps.mv(MM.readtype, mm_mode)
    if mm_mode == 'Current':
        monitor_during = [MM.readcurr]
    elif mm_mode == 'Voltage':
        monitor_during = [MM.readvolt]
    else:
        raise ValueError(f'you passed mm_mode={mm_mode} '
                         'but the value must be one of '
                         '{"Current", "Voltage"}')

    return monitor_during

def flash_step_field(dets, VIT_table, md, *, delay=1, mm_mode='Current'):
    all_dets = dets + [flash_power]
    req_cols = ['I', 'V', 't']
    if not all(k in VIT_table for k in req_cols):
        raise ValueError(f"input table must have {req_cols}")

    monitor_during = yield from _setup_mm(mm_mode)

    VIT_table = pd.DataFrame(VIT_table)
    # TODO put in default meta-data


    # paranoia to be very sure we turn the PSU off
    @finalize_decorator(bps.mov(flash_power.enabled, 0))
    # this arms the detectors
    @stage_decorator(all_dets)
    # this sets up the monitors of the multi-meter
    @monitor_during_decorator(monitor_during)
    # this opens the run and puts the meta-data in it
    @run_decorator(md=md)
    def flash_step_field_inner():
        # set everything to zero at the top
        yield from bps.mv(flash_power.current_sp, 0,
                          flash_power.voltage_sp, 0)
        # put in "Duty Cycle" mode so current changes immediately
        yield from bps.mv(flash_power.mode, 'Duty Cycle')

        # take a measurement on the way in
        yield from bps.trigger_and_read(all_dets)

        # turn it on!
        yield from bps.mv(flash_power.enabled, 1)

        for _, row in VIT_table.iterrows():
            tau = row['t']
            exposure_count = max(1, tau // delay)
            yield from bps.mv(flash_power.current, row['I'],
                              flash_power.voltage, row['V'])
            deadline = time.monotonic() + tau
            for j in range(exposure_count):
                # this triggers the cameras, the PSU readings and the mm
                yield from bps.trigger_and_read(all_dets)
                # TODO account for acquisition time!
                yield from bps.sleep(delay)
                # if things get bogged down in data collection, bail early!
                if time.monotonic() > deadline:
                    break
        # turn it off!
        # there are several other places we turn this off, but better safe
        yield from bps.mv(flash_power.enabled, 0)

        # take a measurement on the way in
        yield from bps.trigger_and_read(all_dets)

    return (yield from flash_step_field_inner())


def flash_ramp(dets, start_I, stop_I, ramp_rate, md, *,
               delay=1, mm_mode='Current'):
    start_V = 200
    all_dets = dets + [flash_power, MM]
    monitor_during = yield from _setup_mm(mm_mode)

    expected_time = (stop_I - start_I) / ramp_rate
    exposure_count = max(1, expected_time // delay)

    # paranoia to be very sure we turn the PSU off
    @finalize_decorator(bps.mov(flash_power.enabled, 0))
    # this arms the detectors
    @stage_decorator(all_dets)
    # this sets up the monitors of the multi-meter
    @monitor_during_decorator(monitor_during)
    # this opens the run and puts the meta-data in it
    @run_decorator(md=md)
    def flash_step_field_inner():
        # set everything to zero at the top
        yield from bps.mv(flash_power.current_sp, 0,
                          flash_power.voltage_sp, 0,
                          flash_power.ramp_rate, ramp_rate)
        # put in "Duty Cycle" mode so current changes immediately
        yield from bps.mv(flash_power.mode, 'Duty Cycle')
        # take one shot on the way in
        yield from bps.trigger_and_read(all_dets)
        # turn it on!
        yield from bps.mv(flash_power.enabled, 1)

        # TODO
        # what voltage limit to start with ?!
        yield from bps.mv(flash_power.current_sp, start_I,
                          flash_power.voltage_sp, start_V)
        # put in "Current Ramp" to start the ramp
        yield from bps.mv(flash_power.mode, 'Duty Cycle')
        # set the target to let it go
        yield from bps.mv(flash_power.current_sp, start_I)

        for j in range(exposure_count):
            # this triggers the cameras, the PSU readings and the mm
            yield from bps.trigger_and_read(all_dets)
            # TODO account for acquisition time!
            yield from bps.sleep(delay)

        # take one shot on the way out
        yield from bps.trigger_and_read(all_dets)

        # turn it off!
        # there are several other places we turn this off, but better safe
        yield from bps.mv(flash_power.enabled, 0)
