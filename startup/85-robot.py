from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import Component as C


class Robot(Device):
    robot_sample_number = C(EpicsSignal, 'ID:Tgt-SP')
    robot_load_cmd = C(EpicsSignal, 'Cmd:Load-Cmd.PROC')
    robot_unload_cmd = C(EpicsSignal, 'Cmd:Unload-Cmd.PROC')
    robot_execute_cmd = C(EpicsSignal, 'Cmd:Exec-Cmd')
    robot_status = C(EpicsSignal, 'Sts-Sts')

robot = Robot('XF:28IDC-ES:1{SM}')

# old RobotPositioner code is .ipython/profile_2015_collection/startup/robot.py
