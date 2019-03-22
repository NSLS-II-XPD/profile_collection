from ophyd import (Device,
                   Component as Cpt,
                   EpicsSignal, EpicsSignalRO, Signal)
from bluesky.preprocessors import (
    run_decorator, stage_decorator, finalize_decorator,
    monitor_during_decorator)

import bluesky.plan_stubs as bps
from bluesky.utils import short_uid
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
                     write_pv='I-Lim')
    voltage_sp = Cpt(EpicsSignal,
                     'E:OutMain-RB',
                     write_pv='E:OutMain-SP')

    enabled = Cpt(CurrentEnable,
                  'Enbl:OutMain-Sts',
                  write_pv='Enbl:OutMain-Cmd',
                  kind='omitted',
                  string=True)

    remote_lockout = Cpt(EpicsSignal,
                         'Enbl:Lock-Sts',
                         write_pv='Enbl:Lock-Cmd',
                         string=True,
                         kind='config')

    foldback_mode = Cpt(EpicsSignal,
                        'Mode:Fold-Sts',
                        write_pv='Mode:Fold-Sel',
                        string=True,
                        kind='config')

    over_volt_val = Cpt(EpicsSignal,
                        'E:OverProt-RB',
                        write_pv='E:OverProt-SP',
                        kind='config')

    protection_reset = Cpt(
        EpicsSignal, 'Reset:FoldProt-Cmd',
        kind='omitted')

    status = Cpt(EpicsSignalRO, 'Sts:Opr-Sts')

    # stuff from ramp_rate.db
    ramp_rate = Cpt(EpicsSignal,
                    'I-RampRate-RB',
                    write_pv='I-RampRate-I',
                    kind='config')

    delta = Cpt(EpicsSignalRO,
                'I-Delta',
                kind='config')

    mode = Cpt(EpicsSignal, 'UserMode-I',
               string=True,
               kind='config')

    _internals = Cpt(FlashRampInternals, '', kind='omitted')

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
    readtype = Cpt(EpicsSignal, "ReadType", kind='config',
                   string=True)
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


MM = KeithlyMM('XF:28IDC-ES{KDMM6500}', name='MM')
flash_power = FlashPower('XF:28ID2-ES:1{PSU:SRS}', name='flash_power')


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


def _inner_loop(dets, exposure_count, delay, deadline, per_step):
    for j in range(exposure_count):
        start_time = time.monotonic()
        # if things get bogged down in data collection, bail early!
        if start_time > deadline:
            print(f'{start_time} > {deadline} bail!')
            break

        # this triggers the cameras
        yield from per_step(dets, stream_name)

        stop_time = time.monotonic()
        # TODO account for acquisition time!
        exp_actual = stop_time - start_time
        sleep_time = delay - exp_actual
        if stop_time + sleep_time > deadline:
            yield from bps.sleep(deadline - stop_time)
            return
        else:
            yield from bps.sleep(delay - exp_actual)


def flash_step_field(dets, VIT_table, md, *, delay=1, mm_mode='Current',
                     per_step=bps.trigger_and_read):
    all_dets = dets + [flash_power]
    req_cols = ['I', 'V', 't']
    if not all(k in VIT_table for k in req_cols):
        raise ValueError(f"input table must have {req_cols}")

    monitor_during = yield from _setup_mm(mm_mode)

    VIT_table = pd.DataFrame(VIT_table)
    # TODO put in default meta-data

    # paranoia to be very sure we turn the PSU off
    @finalize_decorator(lambda : bps.mov(flash_power.enabled, 0))
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
        yield from bps.mv(flash_power.mode, 'Duty-Cycle')

        # take a measurement on the way in
        yield from per_step(all_dets)

        # turn it on!
        yield from bps.mv(flash_power.enabled, 1)

        for _, row in VIT_table.iterrows():
            tau = row['t']
            exposure_count = int(max(1, tau // delay))
            yield from bps.mv(flash_power.current, row['I'],
                              flash_power.voltage, row['V'])
            deadline = time.monotonic() + tau
            yield from _inner_loop(all_dets, exposure_count,
                                   delay, deadline, per_step)

        # take a measurement on the way out
        yield from per_step(all_dets)

        # turn it off!
        # there are several other places we turn this off, but better safe
        yield from bps.mv(flash_power.enabled, 0)


    return (yield from flash_step_field_inner())


def flash_ramp(dets, start_I, stop_I, ramp_rate, md, *,
               delay=1, mm_mode='Current',
               per_step=bps.trigger_and_read):
    start_V = 200
    all_dets = dets + [flash_power, MM]
    monitor_during = yield from _setup_mm(mm_mode)

    expected_time = (stop_I - start_I) / ramp_rate
    exposure_count = int(max(1, expected_time // delay))
    # paranoia to be very sure we turn the PSU off
    @finalize_decorator(lambda : bps.mov(flash_power.enabled, 0))
    # this arms the detectors
    @stage_decorator(all_dets)
    # this sets up the monitors of the multi-meter
    @monitor_during_decorator(monitor_during)
    # this opens the run and puts the meta-data in it
    @run_decorator(md=md)
    def flash_ramp_inner():
        # set everything to zero at the top
        yield from bps.mv(flash_power.current_sp, 0,
                          flash_power.voltage_sp, 0,
                          flash_power.ramp_rate, ramp_rate)
        # put in "Duty Cycle" mode so current changes immediately
        yield from bps.mv(flash_power.mode, 'Duty-Cycle')
        # take one shot on the way in
        yield from per_step(all_dets)
        # turn it on!
        yield from bps.mv(flash_power.enabled, 1)

        # TODO
        # what voltage limit to start with ?!
        yield from bps.mv(flash_power.current_sp, start_I,
                          flash_power.voltage_sp, start_V)
        # put in "Current Ramp" to start the ramp
        yield from bps.mv(flash_power.mode, 'Current Ramp')
        # set the target to let it go
        yield from bps.mv(flash_power.current_sp, stop_I)

        yield from _inner_loop(all_dets, exposure_count, delay,
                               time.monotonic() + expected_time,
                               per_step)

        # take one shot on the way out
        yield from per_step(all_dets)

        # turn it off!
        # there are several other places we turn this off, but better safe
        yield from bps.mv(flash_power.enabled, 0)


    return (yield from flash_ramp_inner())


def sawtooth_factory(motor, start, stop, step_size):
    """Generate a per-step function that move the motor in a sawtooth



    It is assumed to be near the start on the first step where this is
    called.

    The motion will look like /|/|/|/|

    Parameter
    ---------
    motor : setabble
        The motor to move.

    start, stop : float
        The range to move the motor between

    step_size : float
        The size of steps to take between the measurements

    Returns
    -------
    per_step : Callable[List[OphydObj]] -> None
    """
    if stop < start:
        start, stop = stop, start

    num_pos = int((stop - start) // step_size)
    j = itertools.count()
    last_group = None

    def x_motion_per_step(dets, stream_name):
        nonlocal last_group
        if last_group is not None:
            yield from bps.wait(last_group)
        yield from bps.trigger_and_read(dets, stream_name)
        last_group = short_uid()
        target = start + step_size * (next(j) % num_pos)
        yield from bps.abs_set(motor, target, group=last_group)

    return x_motion_per_step


def pyramid_factory(motor, start, stop, step_size):
    """Generate a per-step function that moves the motor in triangle wave

    It is assumed to be near the start on the first step where this is
    called.

    The motion will look like /\/\/\/\

    Parameter
    ---------
    motor : setabble
        The motor to move.

    start, stop : float
        The range to move the motor between

    step_size : float
        The size of steps to take between the measurements

    Returns
    -------
    per_step : Callable[List[OphydObj]] -> None
    """
    if stop < start:
        start, stop = stop, start
    last_group = None
    last_pos = start

    def x_motion_per_step(dets, stream_name):
        nonlocal last_group
        nonlocal last_pos
        nonlocal step_size

        if last_group is not None:
            yield from bps.wait(last_group)

        yield from bps.trigger_and_read(dets, stream_name)

        last_group = short_uid()

        if not start < last_pos + step_size < stop:
            step_size *= -1
        last_pos += step_size

        yield from bps.abs_set(motor, last_pos, group=last_group)

    return x_motion_per_step
