# the ttwotheta motor and detector

# test xpd sim of motor movement
import numpy as np
from ophyd.sim import SynSignal, motor1

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


# simulated sc detector
sc = SynGaussPeaks("det_6peaks", motor1, motor_field='motor1',
                             centers=[-5, -3,-1, 1, 3, 5], Imax=100, sigma=.2)
# simulated two theta detector
tth = motor1

''' test sim motors
import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.callbacks import LivePlot
def myplan():
    yield from bps.abs_set(motor1, 0)
    yield from bp.rel_scan([det_6peaks], motor1, -10, 10, 1000)
RE(myplan(), LivePlot('det_6peaks', 'motor1'))
'''
