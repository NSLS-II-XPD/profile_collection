# the ttwotheta motor and detector

# test xpd sim of motor movement
import numpy as np
from ophyd.sim import SynSignal, motor1, motor2

from lmfit import Model, Parameter, Parameters
from lmfit.models import VoigtModel, LinearModel
from lmfit.lineshapes import voigt

class SynGaussPeaks(SynSignal):
    """
    Evaluate a point on a peaks based on the value of a motor.

    Parameters
    ----------
    name : string
    motor : Device
    motor_field : string
    center : number
        center of peak
    Imax : number
        max intensity of peak
    sigma : number, optional
        Default is 1.
    noise : {'poisson', 'uniform', None}, optional
        Add noise to the gaussian peak.
    noise_multiplier : float, optional
        Only relevant for 'uniform' noise. Multiply the random amount of
        noise by 'noise_multiplier'
    random_state : numpy random state object, optional
        np.random.RandomState(0), to generate random number with given seed

    Example
    -------
    motor = SynAxis(name='motor')
    det = SynGauss('det', motor, 'motor', center=0, Imax=1, sigma=1)
    """

    def __init__(self, name, motor, motor_field, centers, Imax, sigma=1,
                 noise=None, noise_multiplier=1, random_state=None, offset=None,
                 **kwargs):
        if noise not in ('poisson', 'uniform', None):
            raise ValueError("noise must be one of 'poisson', 'uniform', None")
        self._motor = motor
        if random_state is None:
            random_state = np.random

        def func():
            m = motor.read()[motor_field]['value']
            v = m*0
            for center in centers:
                v += Imax * np.exp(-(m - center) ** 2 / (2 * sigma ** 2))
            if offset is not None:
                v += offset
            if noise == 'poisson':
                v += int(random_state.poisson(np.round(v), 1))
            elif noise == 'uniform':
                v += random_state.uniform(-1, 1) * noise_multiplier
            return v

        super().__init__(func=func, name=name, **kwargs)

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

th_cal = motor1
sc = SynSignal(name="det", func=current_intensity_dips)


''' test sim motors
import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.callbacks import LivePlot
def myplan():
    yield from bps.abs_set(motor1, 0)
    yield from bp.rel_scan([det_6peaks], motor1, -10, 10, 1000)
RE(myplan(), LivePlot('det_6peaks', 'motor1'))
'''
