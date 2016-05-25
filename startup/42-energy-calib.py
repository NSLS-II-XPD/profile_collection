from __future__ import division, print_function
import numpy as np
from lmfit.models import VoigtModel
from scipy.signal import argrelmax
import matplotlib.pyplot as plt


def lamda_from_bragg(th, d, n):
    return 2 * d * np.sin(th / 2.) / n


def find_peaks(chi, sides=6, intensity_threshold=0):
    # Find all potential peaks
    preliminary_peaks = argrelmax(chi, order=20)[0]

    # peaks must have at least sides pixels of data to work with
    preliminary_peaks2 = preliminary_peaks[
        np.where(preliminary_peaks < len(chi) - sides)]

    # make certain that a peak has a drop off which causes the peak height to
    # be more than twice the height at sides pixels away
    criteria = chi[preliminary_peaks2] >= 2 * chi[preliminary_peaks2 + sides]
    criteria *= chi[preliminary_peaks2] >= 2 * chi[preliminary_peaks2 - sides]
    criteria *= chi[preliminary_peaks2] >= intensity_threshold

    peaks = preliminary_peaks[np.where(criteria)]

    left_idxs = peaks - sides
    right_idxs = peaks + sides
    peak_centers = peaks
    left_idxs[left_idxs < 0] = 0
    right_idxs[right_idxs > len(chi)] = len(chi)
    return left_idxs, right_idxs, peak_centers


def get_wavelength_from_std_tth(x, y, d_spacings, ns, plot=False):
    """
    Return the wavelength from a two theta scan of a standard

    Parameters
    ----------
    x: ndarray
        the two theta coordinates
    y: ndarray
        the detector intensity
    d_spacings: ndarray
        the dspacings of the standard
    ns: ndarray
        the multiplicity of the reflection
    plot: bool
        If true plot some of the intermediate data
    Returns
    -------
    float:
        The average wavelength
    float:
        The standard deviation of the wavelength
    """
    l, r, c = find_peaks(y)
    lmfit_centers = []
    for lidx, ridx, peak_center in zip(l, r, c):
        mod = VoigtModel()
        pars = mod.guess(y[lidx: ridx],
                         x=x[lidx: ridx])
        out = mod.fit(y[lidx: ridx], pars,
                      x=x[lidx: ridx])
        lmfit_centers.append(out.values['center'])
    lmfit_centers = np.asarray(lmfit_centers)
    if plot:
        plt.plot(x, y)
        plt.plot(x[c], y[c], 'ro')
        plt.show()

    wavelengths = []
    l_peaks = lmfit_centers[lmfit_centers < 0.]
    r_peaks = lmfit_centers[lmfit_centers > 0.]
    for peak_set in [r_peaks, l_peaks[::-1]]:
        for peak_center, d, n in zip(peak_set, d_spacings, ns):
            tth = np.deg2rad(np.abs(peak_center))
            print(tth, d)
            wavelengths.append(lamda_from_bragg(tth, d, n))
    print(wavelengths)
    return np.average(wavelengths), np.std(wavelengths)


if __name__ == '__main__':
    import os

    calibration_file = os.path.join('../../data/LaB6_d.txt')

    # step 0 load data
    d_spacings = np.loadtxt(calibration_file)
    a = np.loadtxt('../../data/Lab6_67p8.chi')
    wavechange = []
    b = np.linspace(.1, 3, 100)
    for dx in b:
        x = a[:, 0]
        x = np.hstack((np.zeros(1), x))
        x = np.hstack((-x[::-1], x))
        y = a[:, 1]
        y = np.hstack((np.zeros(1), y))
        y = np.hstack((y[::-1], y))

        x = x[:] + dx
        y = y[:]
        wavechange.append(get_energy_from_std_tth(x, y, d_spacings,
                                                  np.ones(d_spacings.shape),
                                                  )[0])
    plt.plot(b, wavechange)
    plt.show()
