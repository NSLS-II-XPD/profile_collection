"Define all the motors on the beamline"

from ophyd import EpicsMotor

th_cal = EpicsMotor('XF:28IDC-ES:1{Dif:2-Ax:Th}Mtr', name='th_cal')
tth_cal = EpicsMotor('XF:28IDC-ES:1{Dif:2-Ax:2Th}Mtr', name='tth_cal')

# Tim test with Sanjit. Delete it if anything goes wrong
ss_stg2_x = EpicsMotor('XF:28IDC-ES:1{Stg:Smpl2-Ax:X}Mtr', name='ss_stg2_x')
# Sanjit Inlcuded this. Delete it if anything goes wrong
ss_stg2_y = EpicsMotor('XF:28IDC-ES:1{Stg:Smpl2-Ax:Y}Mtr', name='ss_stg2_y')

th = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:Th}Mtr', name='th')
tth = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:2ThI}Mtr', name='tth')

diff_x = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:X}Mtr', name='diff_x')
diff_y = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:Y}Mtr', name='diff_y')


shctl1 = EpicsMotor('XF:28IDC-ES:1{Sh2:Exp-Ax:5}Mtr', name='shctl1')
