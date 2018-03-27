import matplotlib.pyplot as plt
plt.ion()
from bluesky.utils import install_qt_kicker
install_qt_kicker()

import os
import numpy as np
#from bluesky.plans import (scan, subs_wrapper, bps.abs_set, pchain, count, list_scan,
                           #adaptive_scan, reset_positions_wrapper)
import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
from bluesky.callbacks import LiveTable, LivePlot, LiveFit, LiveFitPlot
from lmfit import Model, Parameter
from lmfit.models import VoigtModel, LinearModel
from lmfit.lineshapes import voigt
#from bluesky.plans import adaptive_scan, subs_wrapper, stage_decorator, run_decorator, reset_positions_wrapper, one_1d_step




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
    yield from bps.abs_set(gas, init_gas)
    # Steps 2 and 3 in a loop.
    for _ in range(num_loops):
        yield from bpp.subs_wrapper(scan([pe1, gas.current_gas], eurotherm, minT, maxT, num_steps),
                            LiveTable([eurotherm, gas.current_gas]))
        yield from bpp.subs_wrapper(bp.count([pe1], num_steady), LiveTable([]))
    # Step 4
    yield from bps.abs_set(gas, other_gas)
    yield from bpp.subs_wrapper(bp.count([pe1], num_steady), LiveTable([]))
    # Step 6
    yield from bps.abs_set(gas, init_gas)
    yield from bpp.subs_wrapper(bp.count([pe1], num_steady), LiveTable([]))

D_SPACINGS = {'LaB6': np.array([4.15772, 2.94676, 2.40116]),
              'Si': 5.43095 / np.array([np.sqrt(3), np.sqrt(8), np.sqrt(11), np.sqrt(27)]),
             }

import numpy as np

#def gaussian(theta, center, width):
#    return 1500 / (np.sqrt(2*np.pi) * width) * np.exp(-((theta - center) / width)**2 / 2)

def intensity(theta, amplitude, width, wavelength):
    result = np.clip(5 * np.random.randn(), 0, None)  # Gaussian noise
    for d in D_SPACINGS['LaB6']:
        assert wavelength < 2 * d, \
            "wavelength would result in illegal arg to arcsin"
        try:
            center = np.arcsin(wavelength / (2 * d))
        except Exception:
            print("DEAD"); center = 0
        result += voigt(theta, amplitude, center, width)
        result += voigt(-theta, amplitude, center, width)
    return result

#from bluesky.examples import Reader, Mover


def current_intensity_peaks():
    amplitude = 0.5
    width = 0.004  # degrees
    wavelength = 12.398 / 66.4 # angtroms
    two_theta = motor1.read()['motor1']['value']  # degrees
    theta = np.deg2rad(two_theta / 2)  # radians
    return intensity(theta, amplitude, np.deg2rad(width), wavelength)

def current_intensity_dips():
    amplitude = 0.5
    width = 0.004  # degrees
    wavelength = 12.398 / 66.4 # angtroms
    hw_theta = motor1.read()['motor1']['value']  # degrees
    theta = np.deg2rad(hw_theta + 35.26)  # radians
    return -intensity(theta, amplitude, np.deg2rad(width), wavelength)

# SIMULATED HARDWARE FOR TESTING ONLY
#sc = Reader('sc', {'sc_chan1': lambda: current_intensity_peaks()})
# sc = Reader('sc', {'sc_chan1': lambda: current_intensity_dips()})



def Ecal(detectors, motor, guessed_energy, mode, *,
         guessed_amplitude=0.5, guessed_sigma=0.004, min_step=0.001, D='LaB6',
         max_n=3, margin=0.5, md=None):
    """
    Energy calibration scan


    Parameters
    ----------
    detectors : detectors
    motor : the motor
    guessed_energy : number
        units of keV
    mode : {'peaks', 'dips'}
    guessed_amplitude : number, optional
        detector units, defaults to 1500
    guessed_sigma : number, optional
        in units of degrees, defaults to 0.004
    min_step : number, optional
        step size in degrees, defaults to 0.001
    D : string or array, optional
        Either provide the spacings literally (as an array) or
        give the name of a known spacing ('LaB6' or 'Si')
    max_n : integer, optional
        how many peaks (on one side of 0), default is 3
    margin : number, optional
        how far to scan in two theta beyond the 
        guessed left and right peaks, default 0.5

    Example
    -------
    Execute an energy calibration scan with default steps.

    >>> RE(Ecal(68))
    """
    if mode == 'peaks':
        #motor = tth_cal
        factor = 2
        offset = 0
        sign = 1
    if mode == 'dips':
        #motor = th_cal
        factor = 1
        # theta_hardware = theta_theorhetical + offset
        offset = -35.26  # degrees
        sign = -1
    if isinstance(D, str):
        D = D_SPACINGS[D]
    # Based on the guessed energy, compute where the peaks should be centered
    # in theta. This will be used as an initial guess for peak-fitting.
    guessed_wavelength = 12.398 / guessed_energy  # angtroms

    theta = np.rad2deg(np.arcsin(guessed_wavelength / (2 * D)))
    guessed_centers = factor * theta  # 'factor' puts us in two-theta units if applicable
    _range = max(guessed_centers) + (factor * margin)
    # Scan from positive to negative because that is the direction
    # that the th_cal and tth_cal motors move without backlash.
    start, stop = _range + offset, -_range + offset
    print('guessed_wavelength={} [Angstroms]'.format(guessed_wavelength))
    print('guessed_centers={} [in {}-theta DEGREES]'.format(guessed_centers, factor))
    print('will scan from {} to {} in hardware units'.format(start, stop))

    if max_n > 3:
        raise NotImplementedError("I only work for n up to 3.")

    def peaks(x, c0, wavelength, a1, a2, a3, sigma):
        # x comes from hardware in [theta or two-theta] degrees
        x = np.deg2rad(x / factor - offset)  # radians
        assert np.all(wavelength < 2 * D), \
            "wavelength would result in illegal arg to arcsin"
        c1, c2, c3 = np.arcsin(wavelength / (2 * D))
        result = (voigt(x=x, amplitude=sign*a1, center=c0 - c1, sigma=sigma) +
                  voigt(x=x, amplitude=sign*a1, center=c0 + c1, sigma=sigma))
        if max_n > 1:
            result += (voigt(x=x, amplitude=sign*a2, center=c0 - c2, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a2, center=c0 + c2, sigma=sigma))
        if max_n > 2:
            result += (voigt(x=x, amplitude=sign*a3, center=c0 - c3, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a3, center=c0 + c3, sigma=sigma))
        return result
                  
    model = Model(peaks) + LinearModel()

    # Fill out initial guess.
    init_guess = {'intercept': Parameter('intercept', value=0, min=-100, max=100),
                  'slope': Parameter('slope', value=0, min=-100, max=100),
                  'sigma': Parameter('sigma', value=np.deg2rad(guessed_sigma)),
                  'c0': Parameter('c0', value=np.deg2rad(0), min=-0.2, max=0.2),
                  'wavelength': Parameter('wavelength', guessed_wavelength,
                                          min=0.8 * guessed_wavelength,
                                          max=1.2 * guessed_wavelength)}
                                          # min=0, max=np.min(2 * D))}
    kwargs = {'min': 0.5 * guessed_amplitude,
              'max': 2 * guessed_amplitude}
    for i, center in enumerate(guessed_centers):
        init_guess.update(
            {'a%d' % (1 + i): Parameter('a%d' % (1 + i), guessed_amplitude, **kwargs)})
    print(init_guess)
    lf = LiveFit(model, detectors[0].name, {'x': motor.name}, init_guess,
                 update_every=100)

    fig, ax = plt.subplots()  # explitly create figure, axes to use below
    plot = LivePlot(detectors[0].name, motor.name, linestyle='none', marker='o', ax=ax)
    lfp = LiveFitPlot(lf, ax=ax, color='r')
    subs = [lfp, plot]
    
    #detectors = [det]#[sc]
    
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

    initial_steps = np.arange(start, stop, -min_step)
    assert len(initial_steps), "bad start, stop, min_step parameters"
    size = factor * 0.05  # region around each predicted peak location

    @bpp.stage_decorator(list(detectors) + [motor])
    @bpp.run_decorator(md=_md)
    def inner_scan():
        wavelength=guessed_wavelength
        for step in initial_steps:
            yield from bps.one_1d_step(detectors, motor, step)
            x_data = lf.independent_vars_data['x']
            if x_data and lf.result is not None:
                # Have we yet scanned past the third peak?
                wavelength = lf.result.values['wavelength']
                # Convert c's to hardware units here for comparison with x_data.
                c1, c2, c3 = factor * np.rad2deg(np.arcsin(wavelength / (2 * D))) + offset
                if np.min(x_data) < (c1 - 1):
                    # Stop dense scanning.
                    print('Preliminary result:\n', lf.result.values)
                    print('Becoming adaptive to save time....')
                    break
        # left of zero peaks
        c1, c2, c3 = -factor * np.rad2deg(np.arcsin(wavelength / (2 * D))) + offset
        neighborhoods = [np.arange(c + size, c - size, -min_step) for c in (c1, c2, c3)]
        for neighborhood in neighborhoods:
            for step in neighborhood:
                yield from bps.one_1d_step(detectors, motor, step)

    plan = inner_scan()
    plan = bpp.subs_wrapper(plan, subs)
    plan = bpp.reset_positions_wrapper(plan, [motor])
    ret = (yield from plan)
    print(lf.result.values)
    print('WAVELENGTH: {} [Angstroms]'.format(lf.result.values['wavelength']))
    return ret


def RockingEcal(guess_energy, offset=35.26, D='Si'):
    yield from Ecal(guess_energy, offset=offset, D=D, factor=1, motor='th_cal')


# simulated sc detector
#tth = SynSignal('tth', func = intensity_peaks)
#th = SynSignal('th', func = intensity_dips)
# simulated two theta detector
# for intensity_peaks/dips simulation
# for intensity_peaks/dips simulation
sc_peaks = SynSignal(name="det", func=current_intensity_peaks)
sc_dips = SynSignal(name="det", func=current_intensity_dips)

from bluesky.plans import adaptive_scan

lp = LivePlot('det', x='motor1', marker='o')
def myplan():
    yield from bpp.subs_wrapper(adaptive_scan([sc_dips],'det', motor1, 6-35.26,
                                              -6-35.26,
                                              min_step=.001, max_step=.5,
                                              target_delta=.1,
                                              backstep=True, threshold=.8),
                                lp)

lp = LivePlot(y='det', x='motor1', marker='o')

def myplan_withfit_peaks():
    global lp

    mode = 'peaks'
    guessed_wavelength = 12.398/66.
    guessed_sigma = .01
    guessed_amplitude = 800
    D ='LaB6'
    max_n = 3
    if isinstance(D, str):
        D = D_SPACINGS[D]
    if mode == 'peaks':
        #motor = tth_cal
        factor = 2
        offset = 0
        sign = 1
    if mode == 'dips':
        #motor = th_cal
        factor = 1
        # theta_hardware = theta_theorhetical + offset
        offset = -35.26  # degrees
        sign = -1

    def peaks(x, c0, wavelength, a1, a2, a3, sigma):
        # x comes from hardware in [theta or two-theta] degrees
        x = np.deg2rad(x / factor - offset)  # radians
        assert np.all(wavelength < 2 * D), \
            "wavelength would result in illegal arg to arcsin"
        c1, c2, c3 = np.arcsin(wavelength / (2 * D))
        result = (voigt(x=x, amplitude=sign*a1, center=c0 - c1, sigma=sigma) +
                  voigt(x=x, amplitude=sign*a1, center=c0 + c1, sigma=sigma))
        if max_n > 1:
            result += (voigt(x=x, amplitude=sign*a2, center=c0 - c2, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a2, center=c0 + c2, sigma=sigma))
        if max_n > 2:
            result += (voigt(x=x, amplitude=sign*a3, center=c0 - c3, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a3, center=c0 + c3, sigma=sigma))
        return result

    model = Model(peaks) + LinearModel()
    init_guess = {'intercept': Parameter('intercept', value=0, min=-100, max=100),
                  'slope': Parameter('slope', value=0, min=-100, max=100),
                  'sigma': Parameter('sigma', value=np.deg2rad(guessed_sigma)),
                  'c0': Parameter('c0', value=np.deg2rad(0), min=-0.2, max=0.2),
                  'wavelength': Parameter('wavelength', guessed_wavelength,
                                          min=0.8 * guessed_wavelength,
                                          max=1.2 * guessed_wavelength),
                  'a1' : Parameter('a1', guessed_amplitude, min=0),
                  'a2' : Parameter('a2', guessed_amplitude, min=0),
                  'a3' : Parameter('a3', guessed_amplitude, min=0),}
                                          # min=0, max=np.min(2 * D))}

    kwargs = {'min': 0.5 * guessed_amplitude,
              'max': 2 * guessed_amplitude}

    print(init_guess)
    lf = LiveFit(model, 'det', {'x': 'motor1'}, init_guess,
                 update_every=100)
    lfp = LiveFitPlot(lf, color='r')

    yield from bpp.subs_wrapper(adaptive_scan([sc_peaks],'det', motor1, 6, -6,
                                              min_step=.001, max_step=1,
                                              target_delta=.01,
                                              backstep=.01, threshold=.001),
                                [lp])

def myplan_withfit_dips():
    global lp

    mode = 'peaks'
    guessed_wavelength = 12.398/66.
    guessed_sigma = .01
    guessed_amplitude = 800
    D ='LaB6'
    max_n = 3
    if isinstance(D, str):
        D = D_SPACINGS[D]
    if mode == 'peaks':
        #motor = tth_cal
        factor = 2
        offset = 0
        sign = 1
    if mode == 'dips':
        #motor = th_cal
        factor = 1
        # theta_hardware = theta_theorhetical + offset
        offset = -35.26  # degrees
        sign = -1

    def peaks(x, c0, wavelength, a1, a2, a3, sigma):
        # x comes from hardware in [theta or two-theta] degrees
        x = np.deg2rad(x / factor - offset)  # radians
        assert np.all(wavelength < 2 * D), \
            "wavelength would result in illegal arg to arcsin"
        c1, c2, c3 = np.arcsin(wavelength / (2 * D))
        result = (voigt(x=x, amplitude=sign*a1, center=c0 - c1, sigma=sigma) +
                  voigt(x=x, amplitude=sign*a1, center=c0 + c1, sigma=sigma))
        if max_n > 1:
            result += (voigt(x=x, amplitude=sign*a2, center=c0 - c2, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a2, center=c0 + c2, sigma=sigma))
        if max_n > 2:
            result += (voigt(x=x, amplitude=sign*a3, center=c0 - c3, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a3, center=c0 + c3, sigma=sigma))
        return result

    model = Model(peaks) + LinearModel()
    init_guess = {'intercept': Parameter('intercept', value=0, min=-100, max=100),
                  'slope': Parameter('slope', value=0, min=-100, max=100),
                  'sigma': Parameter('sigma', value=np.deg2rad(guessed_sigma)),
                  'c0': Parameter('c0', value=np.deg2rad(0), min=-0.2, max=0.2),
                  'wavelength': Parameter('wavelength', guessed_wavelength,
                                          min=0.8 * guessed_wavelength,
                                          max=1.2 * guessed_wavelength),
                  'a1' : Parameter('a1', guessed_amplitude, min=0),
                  'a2' : Parameter('a2', guessed_amplitude, min=0),
                  'a3' : Parameter('a3', guessed_amplitude, min=0),}
                                          # min=0, max=np.min(2 * D))}

    kwargs = {'min': 0.5 * guessed_amplitude,
              'max': 2 * guessed_amplitude}

    print(init_guess)
    lf = LiveFit(model, 'det', {'x': 'motor1'}, init_guess,
                 update_every=100)
    lfp = LiveFitPlot(lf, color='r')

    yield from bpp.subs_wrapper(adaptive_scan([sc_dips],'det', motor1, 6, -6,
                                              min_step=.001, max_step=1,
                                              target_delta=.01,
                                              backstep=.01, threshold=.001),
                                [lp])
