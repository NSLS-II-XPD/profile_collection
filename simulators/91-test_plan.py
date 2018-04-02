uids = ('79b54d30-7fff-4a24-80c1-1d5cb3e71373',
        'b0b7a12b-ec80-47a1-ac24-c86eb9ebf464',
        'c1e766fa-dff6-4747-877a-5a26de278ca4',
        '5de9a73c-367e-43a9-8377-80e945ad165f')

from databroker import Broker
db = Broker.named('xpd')

peak1_c = db[uids[0]].table()
peak1_f = db[uids[1]].table()
peak2_c = db[uids[2]].table()
peak2_f = db[uids[3]].table()

peaks_x = list(peak1_f.th_cal)
peaks_y = list(peak1_f.sc_chan1)
peaks_x.extend(list(peak2_f.th_cal))
peaks_y.extend(list(peak2_f.sc_chan1))
xdata = peaks_x
ydata = peaks_y
import matplotlib.pyplot as plt




theta_offset=-35.26

wguess=.1878;
max_step=.004;
D='Si';
detector_name='sc_chan1';
theta_offset=-35.26;
guessed_sigma=.0012;
nsigmas=15




if isinstance(D, str):
    D = D_SPACINGS[D]

guessed_wavelength = wguess

# theta-tth factor
factor = 1
offset = theta_offset # degrees
# TODO : Make a Model
#def dips(x, c0, wavelength, a1, a2, sigma):
def dips(x, c0, wavelength, a1, a2, sigma):
    sign = -1
    # x comes from hardware in [theta or two-theta] degrees
    x = np.deg2rad(x / factor - offset)  # radians
    assert np.all(wavelength < 2 * D), \
        "wavelength would result in illegal arg to arcsin"
    centers = np.arcsin(wavelength / (2 * D))
    # just look at one center for now
    c1 = centers[0]

    result = (voigt(x=x, amplitude=a1, center=c0 - c1, sigma=sigma) +
              voigt(x=x, amplitude=a2, center=c0 + c1, sigma=sigma))

    return result

model = Model(dips) + LinearModel()

guessed_average = np.max(ydata)
guessed_amplitude = -10# np.abs(np.min(ydata) - np.mean(ydata))
# Fill out initial guess.
init_guess = {'intercept': Parameter('intercept', value=guessed_average,vary=False),
              'slope': Parameter('slope', value=0, vary=False),
              'sigma': Parameter('sigma', value=np.deg2rad(guessed_sigma), vary=False),
              'c0': Parameter('c0', value=np.deg2rad(0), vary=False),
              'wavelength': Parameter('wavelength', guessed_wavelength,
                                      min=0.8 * guessed_wavelength,
                                      max=1.2 * guessed_wavelength, vary=False),
              'a1' : Parameter('a1', guessed_amplitude, vary=False),
              'a2' : Parameter('a2', guessed_amplitude, vary=False),
             }
params = Parameters(init_guess)

# fit_kwargs = dict(ftol=1)
fit_kwargs = dict()
result = model.fit(ydata, x=xdata, params=params, fit_kwargs=fit_kwargs)


plt.figure(15);plt.clf()
plt.plot(xdata,ydata)
plt.plot(xdata,result.best_fit)
plt.plot(xdata,result.best_fit)
plt.show()
