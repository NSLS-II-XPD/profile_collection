#individually fit peaks
'''
    The problem is that the peak is in too narrow of a range. If we're off in
    our guess, then we're wrong. Instead, we should just fit to a peak and
    return the center.
'''
uids = ('79b54d30-7fff-4a24-80c1-1d5cb3e71373',
        'b0b7a12b-ec80-47a1-ac24-c86eb9ebf464',
        'c1e766fa-dff6-4747-877a-5a26de278ca4',
        '5de9a73c-367e-43a9-8377-80e945ad165f')

#from databroker import Broker
#db = Broker.named('xpd')

#peak1_c = db[uids[0]].table()
#peak1_f = db[uids[1]].table()
#peak2_c = db[uids[2]].table()
#peak2_f = db[uids[3]].table()
import pandas as pd
peak1_c = pd.read_csv("peak1_c.csv")
peak1_f = pd.read_csv("peak1_f.csv")
peak2_c = pd.read_csv("peak2_c.csv")
peak2_f = pd.read_csv("peak2_f.csv")

peaks_x = list(peak1_f.th_cal)
peaks_y = list(peak1_f.sc_chan1)
peaks_x.extend(list(peak2_f.th_cal))
peaks_y.extend(list(peak2_f.sc_chan1))
xdata = np.array(peaks_x)
ydata = np.array(peaks_y)
import matplotlib.pyplot as plt




def peakfunc(x, amplitude, sigma, x0, slope, intercept):
    # amplitude is *not* amplitude!!! needs to be rescaled by sigma!!!!
    amplitude = amplitude*sigma*np.sqrt(2*np.pi)
    result = voigt(x=x, amplitude=amplitude, center=x0, sigma=sigma)
    result += slope*x + intercept
    return result

def guess(x, y, sigma=None):
    '''
        sigma is often hard to guess, allow it to be externally guessed
    '''
    g_average = np.average(y)

    # choose between a peak or dip
    dip_amp = np.min(y) - g_average
    peak_amp = np.max(y) - g_average
    if np.abs(dip_amp) > peak_amp:
        print("found a dip")
        g_amp = dip_amp
    else:
        print("found a peak")
        g_amp = peak_amp

    if sigma is None:
        # guess fwhm
        w, = np.where(np.abs(y-g_average) < np.abs(g_amp/2.))
        g_fwhm = np.abs(xdata[w[-1]] - xdata[w[0]])
        # guess...
        g_sigma = g_fwhm/2.
    else:
        g_sigma = sigma

    x0 = xdata[np.argmax(np.abs(y-g_average))]


    init_guess = {
                  'amplitude': Parameter('amplitude', value=g_amp, vary=True),
                  'sigma': Parameter('sigma', min=0, value=g_sigma, vary=True),
                  'x0' : Parameter('x0', value=x0, vary=True),
                  'intercept': Parameter('intercept', value=g_average,vary=True),
                  'slope': Parameter('slope', value=0, vary=True),
                 }
    params = Parameters(init_guess)
    return params


def ispeak(x, y, sdev=3):
    '''
        Decision making logic for if we have a peak or dip.
        sdev : number of std dev's the peak must be above noise
    '''
    noise = np.std(y)
    avg = np.average(y)
    peak = np.max(np.abs(y - avg))
    return peak > sdev*noise


def guess_and_fit(xdata, ydata, sigma=None):
    '''
        Guess fit and return results.
    '''
    peakmodel = Model(peakfunc, independent_vars=['x'])
    init_guess = guess(xdata, ydata, sigma=sigma)
    return peakmodel.fit(data=ydata, x=xdata, params=init_guess)


# okay, works for all these
xdata = np.array(peak1_c.th_cal)
ydata = np.array(peak1_c.sc_chan1)
xdata = np.array(peak2_c.th_cal)
ydata = np.array(peak2_c.sc_chan1)
xdata = np.array(peak1_f.th_cal)
ydata = np.array(peak1_f.sc_chan1)
xdata = np.array(peak2_f.th_cal)
ydata = np.array(peak2_f.sc_chan1)

peakmodel = Model(peakfunc, independent_vars=['x'])
init_guess = guess(xdata, ydata, sigma=.001)

yguess = peakmodel.eval(params=init_guess, x=xdata)

result = guess_and_fit(xdata, ydata, sigma=.001)

from pylab import *
ion()
figure(10);clf();
plot(xdata, ydata)
plot(xdata, result.best_fit)
plot(xdata, yguess, color='r')
