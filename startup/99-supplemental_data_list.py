# define supplemental data beamline would like to monitor

from ophyd import EpicsSignalRO
ring_current = EpicsSignalRO('SR:OPS-BI{DCCT:1}I:Real-I',
                             name='ring_current')
sd.baseline.extend([ss_stg2_x, ss_stg2_y, ss_stg2_z,
                    diff_x, diff_y, diff_tth_i, diff_th, 
                    em, ring_current])
#xrun.preprocessors.append(sd)

