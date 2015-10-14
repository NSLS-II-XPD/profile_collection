from ophyd.controls import EpicsMotor, PVPositioner
from ophyd.controls.positioner import MoveStatus,Positioner
from ophyd.controls.signal import EpicsSignal
from robot import RobotPositioner
from gas_switcher import XPDGasSwitcher
import time as ttime


robot_sample_number = EpicsSignal('XF:28IDC-ES:1{SM}ID:Tgt-SP',
        rw = True, name = 'robot_sample_number')
robot_load_cmd = EpicsSignal('XF:28IDC-ES:1{SM}Cmd:Load-Cmd.PROC',
        rw = True, name = 'robot_load_cmd')
robot_unload_cmd = EpicsSignal('XF:28IDC-ES:1{SM}Cmd:Unload-Cmd.PROC',
        rw = True, name = 'robot_unload_cmd')
robot_execute_cmd = EpicsSignal('XF:28IDC-ES:1{SM}Cmd:Exec-Cmd',
        rw = True, name = 'robot_execute_cmd')
robot_status = EpicsSignal('XF:28IDC-ES:1{SM}Sts-Sts', name = 'robot_status')

robot = RobotPositioner(robot_sample_number, robot_load_cmd, robot_unload_cmd,
        robot_execute_cmd, robot_status)

THETA_MEASURE = 176.0
THETA_LOAD = 86.0

TWO_THETA_DIODE_IN = 100.0
TWO_THETA_DIODE_OUT = 60.0

X_HOME = 11.0
Y_HOME = 41.0

gas = XPDGasSwitcher(requested_pos='XF:28IDC-ES:1{Env:02}Pos-SP',
        current_pos='XF:28IDC-ES:1{Env:02}Pos-I',
        gasdict = {1: 'O2', 2: 'N2', 3: 'He'})


th_cal = EpicsMotor('XF:28IDC-ES:1{Dif:2-Ax:Th}Mtr', name='th_cal')
tth_cal = EpicsMotor('XF:28IDC-ES:1{Dif:2-Ax:2Th}Mtr', name='tth_cal')

th = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:Th}Mtr', name='th')
tth = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:2ThI}Mtr', name='tth')
diff_x = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:X}Mtr', name='diff_x')
diff_y = EpicsMotor('XF:28IDC-ES:1{Dif:1-Ax:Y}Mtr', name='diff_y')

cs700 = PVPositioner('XF:28IDC-ES:1{Env:01}T-SP',
                     readback='XF:28IDC-ES:1{Env:01}T-I',
                     #done='XF:28IDC-ES:1{Env:01}Cmd-Busy', done_val=0,
                     stop='XF:28IDC-ES:1{Env:01}Cmd-Cmd', stop_val=13,
                     put_complete=True, name='cs700')

def thetaLoad():
    th.move(THETA_LOAD)
    return


def thetaMeasure():
    th.move(THETA_MEASURE)
    return


def diodeIn():
    tth.move(TWO_THETA_DIODE_IN)
    return


def diodeOut():
    tth.move(TWO_THETA_DIODE_OUT)
    return


def diffHome():
    diff_x.move(X_HOME)
    diff_y.move(Y_HOME)
    return


def loadSample(samplenum, sampledict, userobot = False):
    diodeIn()
    emptydict = sampledict.copy()
    emptydict['Empty'] = True
    ct(sample=emptydict)
    diffHome()
    if userobot:
        thetaLoad()
        robot.sample = samplenum
        robot.loadsample()
    thetaMeasure()
    if userobot: ct(sample=sampledict)
    return


def unloadSample():
    thetaLoad()
    diffHome()
    robot.unloadsample()
    return
