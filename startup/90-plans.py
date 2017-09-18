import os
import numpy as np
from bluesky.plans import (scan, subs_wrapper, abs_set, pchain, count, list_scan,
                           adaptive_scan, reset_positions_wrapper)
from bluesky.callbacks import LiveTable, LivePlot, LiveFit, LiveFitPlot
from lmfit import Model, Parameter
from lmfit.models import VoigtModel, LinearModel
from lmfit.lineshapes import voigt
from bluesky.plans import adaptive_scan, subs_wrapper, stage_decorator, run_decorator, reset_positions_wrapper, one_1d_step




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

d_spacings = {'LaB6': np.array([4.15772, 2.94676, 2.40116]),
              'Si': 5.43095 / np.array([np.sqrt(3), np.sqrt(8), np.sqrt(11), np.sqrt(27)]),
             }


def Ecal(guessed_energy, mode, *, guessed_amplitude=1, margin=0.5, min_step=0.001, D='LaB6', max_n=3, md=None):
    """
    Energy calibration scan


    Parameters
    ----------
    guessed_energy : number
        units of keV
    mode : {'peaks', 'dips'}
    guessed_amplitude : number, optional
        detector units, defaults to 1000
    margin : number, optional
        how far to scan in two theta beyond the 
        guessed left and right peaks, default 0.5
    D : string or array
        Either provide the spacings literally (as an array) or
        give the name of a known spacing ('LaB6' or 'Si')
    offset : number
        Difference between crystal angle and hardware-reported angle.

    Example
    -------
    Execute an energy calibration scan with default steps.

    >>> RE(Ecal(68))
    """
    if mode == 'peaks':
        motor = tth_cal
        factor = 2
        offest = 0
    if mode == 'dips':
        motor = th_cal
        factor = 1
        offset = -35.26  # degrees
    if isinstance(D, str):
        D = d_spacings[D]
    # Based on the guessed energy, compute where the peaks should be centered
    # in theta. This will be used as an initial guess for peak-fitting.
    guessed_wavelength = 12.398 / guessed_energy  # angtroms

    theta = np.rad2deg(np.arcsin(guessed_wavelength / (2 * D)))
    guessed_centers = factor * theta  # 'factor' puts us in two-theta units if applicable
    _range = (max(guessed_centers) + offset) + factor * margin
    start, stop = -_range, +_range
    print('guessed_wavelength={} [Angstroms]'.format(guessed_wavelength))
    print('guessed_centers={} [in {}-theta DEGREES]'.format(guessed_centers, factor))
    print('will scan from {} to {}'.format(start, stop))

    if max_n > 3:
        raise NotImplementedError("I only work for n up to 3.")

    def peaks(x, c0, wavelength, a1, a2, a3, sigma):
        c0 = c0 + offset
        c1, c2, c3 = np.rad2deg(2 * np.arcsin(wavelength / (2 * D)))
        result = (voigt(x=x, amplitude=a1, center=c0 - c1, sigma=sigma) +
                  voigt(x=x, amplitude=a1, center=c0 + c1, sigma=sigma))
        if max_n > 1:
            result += (voigt(x=x, amplitude=a2, center=c0 - c2, sigma=sigma) +
                       voigt(x=x, amplitude=a2, center=c0 + c2, sigma=sigma))
        if max_n > 2:
            result += (voigt(x=x, amplitude=a3, center=c0 - c3, sigma=sigma) +
                       voigt(x=x, amplitude=a3, center=c0 + c3, sigma=sigma))
        return result
                  
    model = Model(peaks, missing='drop') + LinearModel(missing='drop')

    init_guess = {'intercept': 0,
                  'slope': 0,
                  'sigma': Parameter('sigma', value=10 * min_step, min=0, max=100 * min_step),
                  'c0': 0,
                  'wavelength': Parameter('wavelength', guessed_wavelength, min=0, max=np.min(D))}
    for i, center in enumerate(guessed_centers):
        if mode == 'peaks':
            kwargs = {'min': 0}
        elif mode == 'dips':
            kwargs = {'max': 0}
        else:
            raise ValueError("mode should be 'peaks' or 'dips'") 
        init_guess.update({'a%d' % (1 + i): Parameter('a%d' % (1 + i), guessed_amplitude, **kwargs)})
    lf = LiveFit(model, 'sc_chan1', {'x': motor.name}, init_guess,
                 update_every=100)

    fig, ax = plt.subplots()  # explitly create figure, axes to use below
    plot = LivePlot('sc_chan1', motor.name, linestyle='none', marker='o', ax=ax)
    lfp = LiveFitPlot(lf, ax=ax, color='r')
    subs = [lfp, plot]
    
    detectors = [sc]
    
    # Set up metadata -- based on the sourcecode of bluesky.plans.scan.
    _md = {'detectors': [det.name for det in detectors],
           'motors': [motor.name],
           'hints': {},
          }
    _md.update(md or {})
    try:
        dimensions = [(motor.hints['fields'], 'primary')]
    except (AttributeError, KeyError):
        pass
    else:
        _md['hints'].setdefault('dimensions', dimensions)

    initial_steps = np.arange(start, stop, min_step)
    assert initial_steps, "bad start, stop, min_step parameters"

    @stage_decorator(list(detectors) + [motor])
    @run_decorator(md=_md)
    def inner_scan():
        for step in initial_steps:
            yield from one_1d_step(detectors, motor, step)
            x_data = lf.independent_vars_data['x']
            if x_data and lf.result is not None:
                # Have we yet scanned past the third peak?
                wavelength = lf.result.values['wavelength']
                c1, c2, c3 = np.rad2deg(2 * np.arcsin(wavelength / (2 * D)))
                if np.max(x_data > -(c1 + 3 * lf.result.values['sigma'])):
                    # Stop dense scanning.
                    print('Becoming adaptive to save time....')
                    break
        sigma = 10 * lf.result.values['sigma']
        neighborhoods = [np.arange(c - sigma, c + sigma, min_step) for c in (c1, c2, c3)]
        for neighborhood in neighborhoods:
            for step in neighborhood:
                yield from one_1d_step(detectors, motor, step)

    plan = inner_scan()
    plan = subs_wrapper(plan, subs)
    plan = reset_positions_wrapper(plan, [motor])
    ret = (yield from plan)
    print(lf.result.values)
    print(lf.result)
    print('WAVELENGTH: {} [Angstroms]'.format(lf.result.values['wavelength']))
    return ret


def RockingEcal(guess_energy, offset=35.26, D='Si'):
    yield from Ecal(guess_energy, offset=offset, D=D, factor=1, motor='th_cal')
