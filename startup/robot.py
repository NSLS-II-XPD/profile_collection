import time

class RobotPositioner(object):

    WAIT_TIME = 0.1
    ROBOT_IDLE = "Idle"
    ROBOT_LOADING = "Loading Sample"
    ROBOT_UNLOADING = "Unloading Sample"

    def __init__(self, sample, load, unload, execute, status):
        self._sample_number_pv = sample
        self._load_pv = load
        self._unload_pv = unload
        self._execute_pv = execute
        self._status = status
        return


    @property
    def sample(self):
        return self._sample_number_pv.value


    @sample.setter
    def sample(self, value):
        self._sample_number_pv.put(value)
        return


    def _busy(self):
        return self._status.value != self.ROBOT_IDLE


    def _loading(self):
        return self._status.value == self.ROBOT_LOADING


    def _unloading(self):
        return self._status.value == self.ROBOT_UNLOADING


    def loadsample(self):
        if self._busy():
            print("Robot is busy.")
            return
        self._load_pv.put(1)
        self._execute_pv.put(1)
        while not self._loading():
            time.sleep(self.WAIT_TIME)
        while self._busy():
            time.sleep(self.WAIT_TIME)
        return


    def unloadsample(self):
        if self._busy():
            print("Robot is busy.")
            return
        self._unload_pv.put(1)
        self._execute_pv.put(1)
        while not self._unloading():
            time.sleep(self.WAIT_TIME)
        while self._busy():
            time.sleep(self.WAIT_TIME)
        return
