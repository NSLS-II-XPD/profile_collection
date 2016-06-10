import os
import numpy as np
from bluesky.plans import scan, subs_wrapper, abs_set, pchain, reset_positions_wrapper
from bluesky.callbacks import LiveTable, LivePlot


d_spacings = np.loadtxt(os.path.join('/nfs/xf28id1/ipython_ophyd/profile_collection/startup/../../data/LaB6_d.txt'))


def Ecal(start=-4, stop=-1.5, step_size=0.01):
    """
    Energy calibration scan

    Example
    -------

    Execute an energy calibration scan with default steps.
    >>> RE(Ecal())
    """
    plan = scan([sc], tth_cal, start, stop, (stop - start)/step_size)
    # plan = pchain(abs_set(x_cal, 0), abs_set(y_cal, 0), plan) 
    # plan = reset_positions_wrapper(plan)

    # Send data documnets to cw, LiveTable, LivePlot.
    cw = ComputeWavelength('tth_cal', 'sc_chan1', d_spacings)
    subs = [cw, LiveTable(['tth_cal', 'sc_chan1']), LivePlot('sc_chan1', 'tth_cal')]
    plan = subs_wrapper(plan, subs)

    yield from plan
