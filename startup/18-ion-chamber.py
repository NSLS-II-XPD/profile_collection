import time as ttime
from collections import deque

import numpy as np
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, Kind, Signal
from ophyd.status import SubscriptionStatus


class IonChamber(Device):
    amps = Cpt(EpicsSignalRO, "Amps", kind=Kind.omitted)
    coulombs = Cpt(EpicsSignalRO, "Coulombs", kind=Kind.omitted)
    # TODO: Update this when type of readback is fixed from string to float
    # period = Cpt(EpicsSignal, read_pv="ReadPeriod", write_pv="SetPeriod", add_prefix=("read_pv", "write_pv"), kind=Kind.config)
    period = Cpt(EpicsSignal, "SetPeriod", kind=Kind.config)
    trigger_count = Cpt(EpicsSignalRO, "TriggerCount", kind=Kind.omitted)

    initiate = Cpt(EpicsSignal, "Init", kind=Kind.omitted)  # Initiate button
    stop_signal = Cpt(EpicsSignal, "Abort", kind=Kind.omitted)  # Stop button
    save_signal = Cpt(EpicsSignal, "Save", kind=Kind.omitted)  # Save button

    max_counts = Cpt(Signal, value=0, kind=Kind.config)
    timestamps = Cpt(Signal, value=[], kind=Kind.normal)
    amps_list = Cpt(Signal, value=[], kind=Kind.normal)
    coulombs_list = Cpt(Signal, value=[], kind=Kind.normal)
    amps_mean = Cpt(Signal, value=-1, kind=Kind.hinted)
    coulombs_mean = Cpt(Signal, value=-1, kind=Kind.hinted)
    
    target_trigger_count = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stage(self, *args, **kwargs):
        if self.max_counts.get() == 0:
            raise ValueError(
                f"Set max_counts to a value greater than 0.\n"
                f"max_counts is currently {self.max_counts.get()}"
            )

        # self.stop_signal.put(1)
        #self.stop_signal.put(1)
        # self.stop_signal.put(0)
        # ttime.sleep(0.1)
        self._timestamps = deque()
        self._amps_list = deque()
        self._coulombs_list = deque()
        return super().stage(*args, **kwargs)

    def trigger(self):
        print("!!! Starting trigger")
        # TODO: perform collection of individual amps readings based on user specified period of time
        def cb(value, old_value, **kwargs):
            # print(f"{old_value} -> {value}\n{kwargs}")
            # print(f"### max_counts = {self.max_counts.get()}")
            if int(value) < self.target_trigger_count:
                if int(value) != int(old_value):
                    print(f"{value} ---- {self.target_trigger_count}")
                    print(f"{ttime.monotonic()} collecting timestamps, amps, coulombs")
                    # self._timestamps.append(ttime.time())
                    self._timestamps.append(kwargs["timestamp"])
                    self._amps_list.append(self.amps.get())
                    self._coulombs_list.append(self.coulombs.get())
                return False
            else:
                # print(f"**** {value}")
                print("last addition")
                self._timestamps.append(kwargs["timestamp"])
                self._amps_list.append(self.amps.get())
                self._coulombs_list.append(self.coulombs.get())
                print(f"{ttime.monotonic()} finished collecting")
                self.timestamps.put(list(self._timestamps))
                self.amps_list.put(list(self._amps_list))
                self.coulombs_list.put(list(self._coulombs_list))
                print(f"^^^ {len(list(self._amps_list))}")

                self.amps_mean.put(np.mean(self._amps_list))
                self.coulombs_mean.put(np.mean(self._coulombs_list))

                # self.initiate.put(0)
                # self.stop_signal.put(1)
                # self.stop_signal.put(0)
                # self.save_signal.put(0)
                print(f"{ttime.monotonic()} finished putting")
                return True

        self.target_trigger_count = self.trigger_count.get() + self.max_counts.get()

        st = SubscriptionStatus(self.trigger_count, callback=cb, run=False)

        # self.save_signal.put(1)
        #self.initiate.put(1)
        print("!!! Initiated")

        return st

    def unstage(self, *args, **kwargs):
        super().unstage(*args, **kwargs)
        #self.stop_signal.put(1)
        # self.stop_signal.put(0)


ion_chamber = IonChamber("XF:28IDC-BI{IC101}", name="ion_chamber")
