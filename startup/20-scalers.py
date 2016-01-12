from ophyd import EpicsScaler


em = EpicsScaler('XF:28IDC-BI:1{IM:02}', name='em')
em.channels.read_attrs = ['chan%d' % i for i in [20, 21, 22, 23]]

# Energy Calibration Scintillator
det_sc2 = EpicsScaler('XF:28IDC-ES:1{Det:SC2}', name='det_sc2')
