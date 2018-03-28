import matplotlib.pyplot as plt
plt.ion()
from bluesky.utils import install_qt_kicker
install_qt_kicker()

import os
import numpy as np


import bluesky.plan_stubs as bps
import bluesky.plans as bp
import bluesky.preprocessors as bpp
from bluesky.callbacks import LiveTable, LivePlot, LiveFit, LiveFitPlot
from lmfit import Model, Parameter, Parameters
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

# for the simulation
SIMULATED_D = "Si"
def intensity(theta, amplitude, width, wavelength):
    result = np.clip(5 * np.random.randn(), 0, None)  # Gaussian noise
    for d in D_SPACINGS['Si']:
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

    # todo : make a model and sum them
    def peaks(x, c0, wavelength, a1, a2, sigma):
        # x comes from hardware in [theta or two-theta] degrees
        x = np.deg2rad(x / factor - offset)  # radians
        assert np.all(wavelength < 2 * D), \
            "wavelength would result in illegal arg to arcsin"
        cs = np.arcsin(wavelength / (2 * D))
        c1 = cs[0]
        c2 = cs[1]
        #c3 = cs[2]
        # first peak
        result = (voigt(x=x, amplitude=sign*a1, center=c0 - c1, sigma=sigma) +
                  voigt(x=x, amplitude=sign*a1, center=c0 + c1, sigma=sigma))

        # second peak
        result += (voigt(x=x, amplitude=sign*a2, center=c0 - c2, sigma=sigma) +
                       voigt(x=x, amplitude=sign*a2, center=c0 + c2, sigma=sigma))

        # third peak
        #result += (voigt(x=x, amplitude=sign*a3, center=c0 - c3, sigma=sigma) +
                       #voigt(x=x, amplitude=sign*a3, center=c0 + c3, sigma=sigma))
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
#tth_cal = SynSignal('tth', func = intensity_peaks)
th_cal = motor1
# simulated two theta detector
# for intensity_peaks/dips simulation
# for intensity_peaks/dips simulation
#sc_peaks = SynSignal(name="det", func=current_intensity_peaks)
# sc is dips
sc = SynSignal(name="det", func=current_intensity_dips)

from bluesky.plans import adaptive_scan

def Ecal_dips(detectors, motor, start, stop, min_step, max_step, target_delta,
              threshold, Eguess=None, D="Si", detector_name="sc_chan1", fignum=None):
    '''
        Run Ecal

        Parameters
        ----------
        detectors: list of detectors to scan on 
            will only fit for the first detector's result
        motor : the motor to scan on
        start : motor start
        stop : motor stop

        Eguess : float, optional
            The guessed energy
            If set, will try fitting
    '''
    if isinstance(D, str):
        D = D_SPACINGS[D]

    if fignum is not None:
        fig = plt.figure(fignum)
        fig.clf();
        ax = plt.gca();
    else:
        ax = None
    #detector_name = detectors[0].name
    lp = LivePlot(detector_name, x=motor.name, marker='o', ax=ax)
    # TODO : make limits settable from outside
    #yield from bpp.subs_wrapper(adaptive_scan(detectors, detector_name, motor, start,
                                              #stop,
                                              #min_step=min_step, max_step=max_step,
                                              #target_delta=target_delta,
                                              #backstep=True, threshold=threshold),
                                #lp)
    # Just do small step plot for now
    num = int(abs((stop-start)/max_step))
    yield from bpp.subs_wrapper(bp.scan(detectors, motor, start, stop, num), lp)
    if Eguess is not None:
        # get th data
        xdata = lp.x_data
        ydata = lp.y_data
        result = fit_Ecal_dips(xdata, ydata, guessed_energy=Eguess, D=D)
    return lp




#lp = LivePlot(y='det', x='motor1', marker='o')

# RE(Ecal_dips(66))
# RE(Ecal_dips([sc], th_cal, -33.4, -37, 0.001, 0.02, 5000, 50000, Eguess=66.8, D='Si'))


'''
    New idea for calibration scan:
        Input:
            Eguess : guessed energy
            max_step: max step we take to find peak
            theta_guesses : approx guess of peaks from left to right
            theta_interval : starting interval for scanning in theta

        Start a fine scan in theta.
            If no peak found, scan larger interval

'''

#Ecal2_dips([-36.91, -33.5], 66., max_step=.04, Npoints=20, D="Si", fignum=2):
def Ecal2_dips(detectors, motor, wguess, max_step, D='Si', detector_name='sc_chan1',
               theta_offset=-35.26, guessed_sigma=.002, nsigmas=10):
    '''
        This is the new Ecal scan for dips.
            We should treat peaks separately to simplify matters (leaves for
            easier tweaking)


        This algorithm will search for a peak within a certain theta range
            The theta range is determined from the wavelength guess

        Parameters
        ----------
        detectors : list
            list of detectors
        motor : motor
            the motor to scan on (th_cal)
        wguess : the guessed wavelength
        max_step : the max_step to scan on. This is the step size we use for
            the coarse initial scan
        D : string
            the reference sample to use for the calculation of the d spacings
        detector_name : str, optional
            the name of the detector
        theta_offset : the offset of theta zero estimated from the sample
        guessed_sigma : the guessed sigma of the sample
        nsigmas: int
            the number of sigmas to scan for the fine scan

    '''
    global myresult

    # the sample to use (use from the string supplied)
    if isinstance(D, str):
        D = D_SPACINGS[D]
    cen_guesses = np.degrees(np.arcsin(wguess/ (2 * D)))
    # only use the first center as a guess
    cen_guess = cen_guesses[0]

    theta_guess1, theta_guess2  = theta_offset + cen_guess, theta_offset - cen_guess
    print("Trying {} + {} = {}".format(theta_offset, cen_guess, theta_offset+cen_guess))
    print("Trying {} - {} = {}".format(theta_offset, cen_guess, theta_offset-cen_guess))


    # set up the live Plotting
    fig = plt.figure(detector_name)
    fig.clf();
    ax = plt.gca();

    #detector_name = detectors[0].name

    # set up a live plotter
    global lp
    lp = LivePlot(detector_name, x=motor.name, marker='o', ax=ax)

    xdata_total = list()
    ydata_total = list()
    cnt = 0
    for theta_guess in [theta_guess1, theta_guess2]:
        cnt += 1
        # scan the first peak
        # the number of points for each side
        npoints = 30
        start, stop = theta_guess - max_step*npoints, theta_guess + max_step*npoints
        # reverse to go negative
        start, stop = stop, start
        print("Trying to a guess. Moving {} from {} to {} in {} steps".format(motor.name, start, stop, npoints))
        yield from bpp.subs_wrapper(bp.scan(detectors, motor, start, stop, npoints), lp)
        # TODO : check if a peak was found here
        # find the position c1 in terms of theta

        c1 = lp.x_data[np.argmin(lp.y_data)]
        res_one = fit_Ecal_onedip(lp.x_data, lp.y_data, c1,
                                  guessed_sigma=guessed_sigma)
        plt.figure('fitting coarse {}'.format(cnt));plt.clf()
        plt.plot(lp.x_data, lp.y_data, linewidth=0, marker='o', color='b', label="data")
        plt.plot(lp.x_data, res_one.best_fit, color='r', label="fit")

        c1_fit = res_one.best_values['c1']
        theta_guess = c1_fit
        print("Found center at {}, running finer scan".format(c1_fit))
        npoints = 120
        start, stop = theta_guess - guessed_sigma*nsigmas,  theta_guess + guessed_sigma*nsigmas
        # reverse to go negative
        start, stop = stop, start
        print("Trying to a guess. Moving {} from {} to {} in {} steps".format(motor.name, start, stop, npoints))
        yield from bpp.subs_wrapper(bp.scan(detectors, motor, start, stop, npoints), lp)
        # add to total
        xdata_total.extend(lp.x_data)
        ydata_total.extend(lp.y_data)

        plt.figure('fine scan {}'.format(cnt));plt.clf()
        plt.plot(lp.x_data, lp.y_data, linewidth=0, marker='o', color='b', label="data")


    myresult.result = fit_Ecal_dips2(xdata_total, ydata_total, wguess=wguess, D=D)


class MyResult:
    pass

def fit_Ecal_onedip(xdata, ydata, c1, guessed_sigma=.01):
    '''
        This just fits one dip, a PseudoVoigt with inverse amplitude.
            Useful for getting peak COM.
    '''
    # just fit the first
    global myresult

    # theta-tth factor
    factor = 1
    # TODO : a1, a2 the number of peaks (this makes 2*2 = 4)
    # TODO : Make a Model
    #def dips(x, c0, wavelength, a1, a2, sigma):
    def dips(x, c1, a1, sigma):
        sign = -1
        result = voigt(x=x, amplitude=sign*a1, center=c1, sigma=sigma)
        return result

    model = Model(dips) + LinearModel()

    guessed_amplitude = np.abs(np.min(ydata) - np.average(ydata))
    # Fill out initial guess.
    init_guess = {'c1': Parameter('intercept', value=c1),
                  'sigma': Parameter('sigma', value=guessed_sigma),
                  'a1' : Parameter('a1', guessed_amplitude, min=0),
                  'intercept' : Parameter("intercept", 0),
                  'slope' : Parameter("slope", 0),
                 }
    params = Parameters(init_guess)

    # fit_kwargs = dict(ftol=1)
    fit_kwargs = dict()
    result = model.fit(ydata, x=xdata, params=params, fit_kwargs=fit_kwargs)
    print("Found center to be at theta : {}".format(result.best_values['c1']))

    plt.figure(2);plt.clf();
    plt.plot(xdata, ydata, linewidth=0, marker='o', color='b', label="data")
    plt.plot(xdata, result.best_fit, color='r', label="best fit")
    plt.legend()
    return result


def fit_Ecal_dips2(xdata, ydata, guessed_sigma=.01, wguess=66., D="Si", theta_offset=-35.26):
    '''
        This fits for two peaks.

        Parameters
        ----------
        xdata : the xdata (usually theta)
        ydata : the counts measured
        guessed_sigma: float, optional
            the guessed sigma of the peaks (supplied to initial guess)
        wguess :
                the guessed wavelength
        D : str
            The str identifier for the reference sample (usually just "Si")
        theta_offset :
            The offset in theta of the theta motor
    '''
    # this is a cludge used to pass result around.
    # TODO : remove this when we finally agree on a method on how to scan...
    global myresult

    if isinstance(D, str):
        D = D_SPACINGS[D]

    guessed_wavelength = wguess

    # theta-tth factor
    factor = 1
    offset = theta_offset # degrees
    # TODO : Make a Model
    #def dips(x, c0, wavelength, a1, a2, sigma):
    def dips(x, c0, wavelength, a1, sigma):
        sign = -1
        # x comes from hardware in [theta or two-theta] degrees
        x = np.deg2rad(x / factor - offset)  # radians
        assert np.all(wavelength < 2 * D), \
            "wavelength would result in illegal arg to arcsin"
        centers = np.arcsin(wavelength / (2 * D))
        # just look at one center for now
        c1 = centers[0]

        result = (voigt(x=x, amplitude=sign*a1, center=c0 - c1, sigma=sigma) +
                  voigt(x=x, amplitude=sign*a1, center=c0 + c1, sigma=sigma))

        return result

    model = Model(dips) + LinearModel()

    guessed_amplitude = np.abs(np.min(ydata) - np.average(ydata))
    # Fill out initial guess.
    init_guess = {'intercept': Parameter('intercept', value=0, min=-100, max=100),
                  'slope': Parameter('slope', value=0, min=-100, max=100),
                  'sigma': Parameter('sigma', value=np.deg2rad(guessed_sigma)),
                  'c0': Parameter('c0', value=np.deg2rad(0)),
                  'wavelength': Parameter('wavelength', guessed_wavelength,
                                          min=0.8 * guessed_wavelength,
                                          max=1.2 * guessed_wavelength),
                  'a1' : Parameter('a1', guessed_amplitude, min=0),
                 }
    params = Parameters(init_guess)

    # fit_kwargs = dict(ftol=1)
    fit_kwargs = dict()
    myresult.result = model.fit(ydata, x=xdata, params=params, fit_kwargs=fit_kwargs)
    print('WAVELENGTH: {} [Angstroms]'.format(myresult.result.values['wavelength']))

    plt.figure(2);plt.clf();
    plt.plot(xdata, ydata, linewidth=0, marker='o', color='b', label="data")
    plt.plot(xdata, myresult.result.best_fit, color='r', label="best fit")
    plt.legend()

myresult = MyResult()
