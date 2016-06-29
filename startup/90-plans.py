import os
import numpy as np
from bluesky.plans import scan, subs_wrapper, abs_set, pchain, reset_positions_wrapper, count, list_scan
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.plan_tools import print_summary


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


def MED(init_gas, other_gas, minT, maxT, num_steps, num_steady, num_trans, num_loops=2):
    """
    1. Start flowing the initial gas.
    2. Scan the temperature from minT to maxT in `num_steps` evenly-spaced steps.
    3. Hold temperature at maxT and take  `num_steady` images.
    4. Repeat (2) and (3) `num_loops` times.
    5. Switch the gas to `other_gas` and take `num_trans` acquisitions.
    6. Switch it back and take another `num_trans` acquisitions.

    Example
    -------
    Set the gasses. They can be in any other, nothing to do with
    the order they are used in the plan.
    >>> gas.gas_list = ['O2', 'CO2']

    Optionally, preview the plan.
    >>> print_summary(MED('O2', 'C02', 200, 300, 21, 20, 60))

    Execute it.
    >>> RE(MED('O2', 'C02', 200, 300, 21, 20, 60))

    """
    # Step 1
    yield from abs_set(gas, init_gas)
    # Steps 2 and 3 in a loop.
    for _ in range(num_loops):
        yield from subs_wrapper(scan([pe1, gas.current_gas], eurotherm, minT, maxT, num_steps),
                            LiveTable([eurotherm, gas.current_gas]))
        yield from subs_wrapper(count([pe1], num_steady), LiveTable([]))
    # Step 4
    yield from abs_set(gas, other_gas)
    yield from subs_wrapper(count([pe1], num_steady), LiveTable([]))
    # Step 6
    yield from abs_set(gas, init_gas)
    yield from subs_wrapper(count([pe1], num_steady), LiveTable([]))
