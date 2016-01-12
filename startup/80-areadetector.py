from ophyd.areadetector import PerkinElmerDetector
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import FileStoreBase

# from shutter import sh1

#shctl1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:ShutterMode', name='shctl1')
shctl1 = EpicsSignal('XF:28IDC-ES:1{Sh:Exp}Cmd-Cmd', name='shctl1')


class XPDPerkinElmer(SingleTrigger, PerkinElmerDetector):
    pass

pe1 = XPDPerkinElmer('XF:28IDC-ES:1{Det:PE1}', name='pe1')

class XPDTiffPlugin:
    pass

#                     read_file_path='/home/xf28id1/pe1_data',
#                     write_file_path='H:/pe1_data')


# Perkin Elmer aSi x-ray detector
#pe_cam = PerkinElmerDetector('XF:28IDC-ES:1{Det:PE1}')
#pe_cam_trigger = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:Acquire_RBV',
#                        write_pv='XF:28IDC-ES:1{Det:PE1}cam1:Acquire',
#                        rw=True, name='pe_cam_trigger')
#pe_cam_tot1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats1:Total_RBV',
#                          rw=False, name='pe_cam_tot1')
#pe_cam_tot2 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats2:Total_RBV',
#                          rw=False, name='pe_cam_tot2')
#pe_cam_tot3 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats3:Total_RBV',
#                          rw=False, name='pe_cam_tot3')
#pe_cam_tot4 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats4:Total_RBV',
#                          rw=False, name='pe_cam_tot4')
#pe_cam_tot5 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats5:Total_RBV',
#                          rw=False, name='pe_cam_tot5')


# Dan and Sanjit commented this out in June.

#shctl2 = EpicsSignal('XF:28IDC-ES:1{Det:PE2}cam1:ShutterMode', name='shctl2')
#pe2 = AreaDetectorFileStoreTIFFSquashing(
#    'XF:28IDC-ES:1{Det:PE2}',
#    name='pe2',
#    stats=[],
#    ioc_file_path = 'G:/pe2_data',
#    file_path = '/home/xf28id1/pe2_data',
#    shutter=shctl2,
#    shutter_val=(1,0))
