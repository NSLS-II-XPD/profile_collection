from ophyd import (Device,
                   Component as Cpt,
                   EpicsSignal, EpicsSignalRO)


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

    current_sp = Cpt(EpicsSignal,
                     'I:OutMain-RB',
                     'I-Lim')
    voltage_sp = Cpt(EpicsSignal,
                     'E:OutMain-RB',
                     'E:OutMain-SP')

    enabled = Cpt(EpicsSignal,
                  'Enbl:OutMain-Sts',
                  'Enbl:OutMain-Cmd',
                  kind='omitted')

    remote_lockout = Cpt(EpicsSignal,
                         'Enbl:Lock-Sts',
                         'Enbl:Lock-Cmd',
                         kind='config')

    foldback_mode = Cpt(EpicsSignal,
                        'Mode:Fold-Sts',
                        'Mode:Fold-Sel',
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
               kind='config')

    _internals = Cpt(FlashRampInternals, '')

    def unstage(self):
        ret = super().unstage()
        self.enabled.put(0)
        return ret

    def stop(self):
        # for safety
        self.enabled.put(0)


flash_power = FlashPower('XF:28ID2-ES{PSU:SRS}',
                         name='flash_power')
