from ophyd.controls import EpicsSignal, PerkinElmerDetector


em_cnt = EpicsSignal('XF:28IDC-BI:1{IM:02}.CNT', name='em_cnt')
# write 1 for AutoCount, 0 for OneShot
em_mode = EpicsSignal('XF:28IDC-BI:1{IM:02}.CONT', name='em_mode')
em_ch1 = EpicsSignal('XF:28IDC-BI:1{IM:02}.S20', rw=False, name='em_ch1')
em_ch2 = EpicsSignal('XF:28IDC-BI:1{IM:02}.S21', rw=False, name='em_ch2')
em_ch3 = EpicsSignal('XF:28IDC-BI:1{IM:02}.S23', rw=False, name='em_ch3')
em_ch4 = EpicsSignal('XF:28IDC-BI:1{IM:02}.S23', rw=False, name='em_ch4')

# Perkin Elmer aSi x-ray detector
pe_cam = PerkinElmerDetector('XF:28IDC-ES:1{Det:PE1}')
pe_cam_trigger = EpicsSignal('XF:28IDC-ES:1{Det:PE1}cam1:Acquire_RBV',
                        write_pv='XF:28IDC-ES:1{Det:PE1}cam1:Acquire',
                        rw=True, name='pe_cam_trigger')
pe_cam_tot1 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats1:Total_RBV',
                          rw=False, name='pe_cam_tot1')
pe_cam_tot2 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats2:Total_RBV',
                          rw=False, name='pe_cam_tot2')
pe_cam_tot3 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats3:Total_RBV',
                          rw=False, name='pe_cam_tot3')
pe_cam_tot4 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats4:Total_RBV',
                          rw=False, name='pe_cam_tot4')
pe_cam_tot5 = EpicsSignal('XF:28IDC-ES:1{Det:PE1}Stats5:Total_RBV',
                          rw=False, name='pe_cam_tot5')
