from ophyd.areadetector import (PerkinElmerDetector, ImagePlugin,
                                TIFFPlugin, StatsPlugin, HDF5Plugin,
                                ProcessPlugin)
from ophyd.areadetector.trigger_mixins import SingleTrigger
from ophyd.areadetector.filestore_mixins import (FileStoreIterativeWrite,
                                                 FileStoreHDF5IterativeWrite,
                                                 FileStoreTIFFSquashing)
from ophyd import Signal
from ophyd import Component as C

# from shutter import sh1

#shctl1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:ShutterMode', name='shctl1')
# shctl1 = EpicsSignal('XF:28IDC-ES:1{Sh:Exp}Cmd-Cmd', name='shctl1')

class XPDTIFFPlugin(TIFFPlugin, FileStoreTIFFSquashing,
                    FileStoreIterativeWrite):
    pass


class XPDHDF5Plugin(HDF5Plugin, FileStoreHDF5IterativeWrite):
    pass


class XPDPerkinElmer(SingleTrigger, PerkinElmerDetector):
    image = C(ImagePlugin, 'image1:')

    tiff = C(XPDTIFFPlugin, 'TIFF1:',
             write_path_template='G:/pe1_data/%Y/%m/%d/',
             read_path_template='/home/xf28id1/pe1_data/%Y/%m/%d/',
             cam_name='cam',  # used to configure "tiff squashing"
             proc_name='proc')  # ditto

    # hdf5 = C(XPDHDF5Plugin, 'HDF1:',
    #          write_path_template='G:/pe1_data/%Y/%m/%d/',
    #          read_path_template='/home/xf28id1/pe1_data/%Y/%m/%d/')
    
    proc = C(ProcessPlugin, 'Proc1:')

    # These attributes together replace `num_images`. They control
    # summing images before they are stored by the detector (a.k.a. "tiff
    # squashing").
    images_per_set = C(Signal, value=1, add_prefix=())
    number_of_sets = C(Signal, value=1, add_prefix=())

    stats1 = C(StatsPlugin, 'Stats1:')
    stats2 = C(StatsPlugin, 'Stats2:')
    stats3 = C(StatsPlugin, 'Stats3:')
    stats4 = C(StatsPlugin, 'Stats4:')
    stats5 = C(StatsPlugin, 'Stats5:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.cam.trigger_mode, 'Internal'),
                               ])

pe1 = XPDPerkinElmer('XF:28IDC-ES:1{Det:PE1}', name='pe1', read_attrs=['tiff'],
                     configuration_attrs=['images_per_set', 'number_of_sets'])
pe1.tiff.read_attrs = []  # don't include any signals, just the image itself

# some defaults, as an example of how to use this
pe1.configure(dict(images_per_set=6, number_of_sets=10))
