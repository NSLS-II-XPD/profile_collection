from ophyd import EpicsScaler


class PartialEpicsScaler(EpicsScaler):
    """
    This scaler does not implement the 'gates' portion
    of the standard EPICS scaler record, so we simply
    override it here with 'None'.
    """
    gates = None


em = PartialEpicsScaler('XF:28IDC-BI:1{IM:02}', name='em')

# Energy Calibration Scintillator
det_sc2 = PartialEpicsScaler('XF:28IDC-ES:1{Det:SC2}', name='det_sc2')
