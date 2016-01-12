"Define all the motors on the beamline"

from ophyd import EpicsMotor

th_cal = EpicsMotor('XF:28IDC-ES:1{Dif:2-Ax:Th}Mtr', name='th_cal')
tth_cal = EpicsMotor('XF:28IDC-ES:1{Dif:2-Ax:2Th}Mtr', name='tth_cal')

th = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:Th}Mtr', name='th')
tth = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:2ThI}Mtr', name='tth')

diff_x = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:X}Mtr', name='diff_x')
diff_y = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:Y}Mtr', name='diff_y')
