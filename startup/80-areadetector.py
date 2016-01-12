from ophyd.areadetector import (PerkinElmerDetector, ImagePlugin,
                                TIFFPlugin, StatsPlugin)
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import FileStoreTIFFIterativeWrite
from ophyd import Component as C

# from shutter import sh1

#shctl1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:ShutterMode', name='shctl1')
# shctl1 = EpicsSignal('XF:28IDC-ES:1{Sh:Exp}Cmd-Cmd', name='shctl1')

class XPDTIFFPlugin(TIFFPlugin, FileStoreTIFFIterativeWrite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.extend([(self.num_capture, 1),
                               ])

class XPDPerkinElmer(SingleTrigger, PerkinElmerDetector):
    # plugins
    image = C(ImagePlugin, 'image1:')
    tiff = C(XPDTIFFPlugin, 'TIFF1:',
                    write_path_template='G:/pe1_data/%Y/%m/%d/',
                    read_path_template='/home/xf28id1/pe1_data/%Y/%m/%d/')
    stats1 = C(StatsPlugin, 'Stats1:')
    stats2 = C(StatsPlugin, 'Stats2:')
    stats3 = C(StatsPlugin, 'Stats3:')
    stats4 = C(StatsPlugin, 'Stats4:')
    stats5 = C(StatsPlugin, 'Stats5:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.extend([(self.cam.trigger_mode, 'Internal'),
                               ])

pe1 = XPDPerkinElmer('XF:28IDC-ES:1{Det:PE1}', name='pe1')
