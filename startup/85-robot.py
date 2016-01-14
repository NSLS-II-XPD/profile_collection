from ophyd import Device, EpicsSignal, EpicsSignalRO
from ophyd import Component as C
from ophyd.utils import set_and_wait

class Robot(Device):
    sample_number = C(EpicsSignal, 'ID:Tgt-SP')
    load_cmd = C(EpicsSignal, 'Cmd:Load-Cmd.PROC')
    unload_cmd = C(EpicsSignal, 'Cmd:Unload-Cmd.PROC')
    execute_cmd = C(EpicsSignal, 'Cmd:Exec-Cmd')
    status = C(EpicsSignal, 'Sts-Sts')
 
    TH_POS = {'capilary':{'load':0, 'measure': 0},
              'flat': {'load': 0, 'measure': 0}, 
              '':{}}

    DIFF_POS = {'capilary': (1,2),}

    def __init__(self, *args, theta=None, diff=None, **kwargs):
        self.theta = theta
        self.diff = diff
        super().__init__(*args, **kwargs)

    def load_sample(sample_number, sample_type):
        # self.theta.move(self.TH_POS[sample_type]['load'], wait=True)
        set_and_wait(self.sample_number, sample_number)
        set_and_wait(self.load_cmd, 1)
        self.execute_cmd.put(1)

        while self.status.get() != 'Idle':
            time.sleep(.1)
        # self.theta.move(self.TH_POS[sample_type]['measure'], wait=True)
        


# robot = Robot('XF:28IDC-ES:1{SM}', th, None)

# old RobotPositioner code is .ipython/profile_2015_collection/startup/robot.py
