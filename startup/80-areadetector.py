from ophyd.controls.area_detector import (AreaDetectorFileStoreHDF5,
                                          AreaDetectorFileStoreTIFF,
                                          AreaDetectorFileStoreTIFFSquashing)

from shutter import sh1

shctl1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:ShutterMode', name='shctl1')

pe1 = AreaDetectorFileStoreTIFFSquashing(
    'XF:28IDC-ES:1{Det:PE1}',
    name='pe1',
    stats=[],
    ioc_file_path = 'G:/pe1_data',
    file_path = '/home/xf28id1/pe1_data',
    shutter=shctl1,
    shutter_val=(1, 0)
)


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
