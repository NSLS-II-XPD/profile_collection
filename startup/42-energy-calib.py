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

def get_energy_from_std_tth(x, y, d_spacings, ns, plot=False):
    # step 1 get the zero
    auto_corr = np.correlate(y, y[::-1], mode='same')
    plt.plot(x, auto_corr)
    plt.show()

    zero_point = np.argmax(auto_corr)
    print(len(x)/2, zero_point)
    print(x[len(x)/2], x[zero_point])
    new_x = x - x[zero_point]
    if plot:
        plt.plot(x, y, 'b')
        plt.plot(x[zero_point], y[zero_point], 'ro')
        plt.plot(new_x, y, 'g')
        plt.show()


    # step 2 get all the maxima worth looking at

    l, r, c = find_peaks(y)
    r_centers = c[c > zero_point]
    l_centers = c[c < zero_point]
    print(x[l_centers], x[r_centers])

    r_dists = np.abs(np.asarray(x[r_centers]) - zero_point)
    l_dists = np.abs(np.asarray(x[l_centers]) - zero_point)
    print(l_dists, r_dists)

    lmfit_centers = []
    for lidx, ridx, peak_center in zip(l, r, c):
        mod = VoigtModel()
        pars = mod.guess(y[lidx: ridx],
                         x=x[lidx: ridx])
        out = mod.fit(y[lidx: ridx], pars,
                      x=x[lidx: ridx])
        lmfit_centers.append(out.values['center'])

    # step 2.5 refine the zero
    r_centers = lmfit_centers[lmfit_centers > 0.0]
    l_centers = lmfit_centers[lmfit_centers < 0.0]

    r_dists = np.abs(np.asarray(r_centers) - zero_point)
    l_dists = np.abs(np.asarray(l_centers) - zero_point)
    print(r_dists, l_dists)

    if plot:
        plt.plot(new_x, y)
        plt.plot(new_x[c], y[c], 'ro')
        plt.show()
    AAA

    wavelengths = []
    for center, d, n in zip(lmfit_centers, d_spacings, ns):
        wavelengths.append(lamda_from_bragg(center, d, n))
    return np.average(wavelengths)

if __name__ == '__main__':
    import os
    directory = '/home/cwright/Downloads'
    filename='Lab6_67p8.chi'
    calibration_file = os.path.join(directory, filename)

    # step 0 load data
    d_spacings = np.loadtxt(calibration_file)
    # ns = np.ones(len(d_spacings))

    # x = np.linspace(-np.pi, np.pi, 100)
    # y = np.sin(x)
    # x = np.linspace(-np.pi+1, np.pi, 100)
    a = np.loadtxt('/home/cwright/Downloads/Lab6_67p8.chi')
    x = a[:, 0]
    x = np.hstack((np.zeros(1), x))
    x = np.hstack((-x[::-1], x))
    y = a[:, 1]
    y = np.hstack((np.zeros(1), y))
    y = np.hstack((y[::-1], y))

    x = x[10:]
    y = y[10:]
    get_energy_from_std_tth(x, y, [], [], plot=True)
