
# dictionary of references
D_SPACINGS = {'LaB6': np.array([4.15772, 2.94676, 2.40116]),
              'Si': 5.43095 / np.array([np.sqrt(3), np.sqrt(8), np.sqrt(11), np.sqrt(27)]),
             }

# Helper functions
def peakfunc(x, amplitude, sigma, x0, slope, intercept):
    # amplitude is *not* amplitude!!! needs to be rescaled by sigma!!!!
    amplitude = amplitude*sigma*np.sqrt(2*np.pi)
    result = voigt(x=x, amplitude=amplitude, center=x0, sigma=sigma)
    result += slope*x + intercept
    return result

def guess(xdata, ydata, sigma=None):
    '''
        sigma is often hard to guess, allow it to be externally guessed
    '''
    g_average = np.average(ydata)

    # choose between a peak or dip
    dip_amp = np.min(ydata) - g_average
    peak_amp = np.max(ydata) - g_average
    if np.abs(dip_amp) > peak_amp:
        print("found a dip")
        g_amp = dip_amp
    else:
        print("found a peak")
        g_amp = peak_amp

    if sigma is None:
        # guess fwhm
        w, = np.where(np.abs(ydata-g_average) < np.abs(g_amp/2.))
        g_fwhm = np.abs(xdata[w[-1]] - xdata[w[0]])
        # guess...
        g_sigma = g_fwhm/2.
    else:
        g_sigma = sigma

    x0 = xdata[np.argmax(np.abs(ydata-g_average))]


    init_guess = {
                  'amplitude': Parameter('amplitude', value=g_amp, vary=True),
                  'sigma': Parameter('sigma', min=0, value=g_sigma, vary=True),
                  'x0' : Parameter('x0', value=x0, vary=True),
                  'intercept': Parameter('intercept', value=g_average,vary=True),
                  'slope': Parameter('slope', value=0, vary=True),
                 }
    params = Parameters(init_guess)
    return params


def ispeak(x, y, sdev=2):
    '''
        Decision making logic for if we have a peak or dip.
        sdev : number of std dev's the peak must be above noise
            sdev 2 seems to be okay...
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

def guess_theta_from_reference(wguess, D="Si"):
    '''
        Guess the theta value from the reference.

        Parameters
        ----------
        wguess : float
            the wavelength guess
        D : str
            the reference to use
    '''
    # the sample to use (use from the string supplied)
    D = D_SPACINGS[D]

    cen_guesses = np.degrees(np.arcsin(wguess/ (2 * D)))
    return cen_guesses


def wavelength_from_theta(theta, D="Si"):
    '''
        Get the wavelength from theta
    '''
    D = D_SPACINGS[D]
    return np.sin(np.radians(theta))*2*D

# New calibration scan plan
def Ecal_dips(detectors, motor, wguess, max_step, D='Si', detector_name='sc_chan1',
              theta_offset=-35.26, guessed_sigma=.002, nsigmas=10,
              output_file="result.csv"):
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

        Example
        -------
        RE(Ecal_dips([sc], motor1, wguess=.1878, max_step=.004, D='Si',
        detector_name=sc.name, theta_offset=-35.26, guessed_sigma=.002, nsigmas=15))

    '''
    # an object for passing messages
    global myresult

    # first guess the theta positions
    # TODO : do for two theta
    cen_guesses = guess_theta_from_reference(wguess, D=D)
    # now find the symmetric peaks
    left_guesses, right_guesses = (theta_offset-cen_guesses,
                                   theta_offset+cen_guesses)

    # just take first peak + symmetric for now
    peak_guesses = left_guesses[0], right_guesses[0]

    print("Trying {} +/- {} = {} and {}".format(theta_offset, cen_guesses[0],
                                                peak_guesses[0],
                                                peak_guesses[1]))


    # set up the live Plotting
    fig = plt.figure(detector_name)
    fig.clf();
    ax = plt.gca();

    #detector_name = detectors[0].name

    # set up a live plotter
    lp = LivePlot(detector_name, x=motor.name, marker='o', ax=ax)

    xdata_total = list()
    ydata_total = list()
    results_list = list()
    cnt = 0
    # TODO : this should be a plan on its own
    for theta_guess in peak_guesses:
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
        # (can use ispeak(... , sdev=2)
        # find the position c1 in terms of theta

        xdata = lp.x_data
        ydata = lp.y_data

        peakmodel = Model(peakfunc, independent_vars=['x'])
        init_guess = guess(xdata, ydata, sigma=guessed_sigma)
        res = peakmodel.fit(data=ydata, x=xdata, params=init_guess)

        print("guess: {}".format(init_guess))

        plt.figure('fitting coarse {}'.format(cnt));plt.clf()
        plt.plot(lp.x_data, lp.y_data, linewidth=0, marker='o', color='b', label="data")
        plt.plot(lp.x_data, res.best_fit, color='r', label="fit")
        plt.plot(init_guess['x0'].value, init_guess['amplitude'].value +
                 init_guess['intercept'].value, 'ro')

        # best guess of center position
        new_theta_guess = res.best_values['x0']
        print("Found center at {}, running finer scan".format(new_theta_guess))
        npoints = 120
        start, stop = new_theta_guess - guessed_sigma*nsigmas,  new_theta_guess + guessed_sigma*nsigmas
        # reverse to go negative
        start, stop = stop, start
        print("Trying to a guess. Moving {} from {} to {} in {} steps".format(motor.name, start, stop, npoints))
        yield from bpp.subs_wrapper(bp.scan(detectors, motor, start, stop, npoints), lp)

        xdata = lp.x_data
        ydata = lp.y_data

        peakmodel = Model(peakfunc, independent_vars=['x'])
        init_guess = guess(xdata, ydata, sigma=guessed_sigma)
        res = peakmodel.fit(data=ydata, x=xdata, params=init_guess)

        plt.figure('fitting fine {}'.format(cnt));plt.clf()
        plt.plot(lp.x_data, lp.y_data, linewidth=0, marker='o', color='b', label="data")
        plt.plot(lp.x_data, res.best_fit, color='r', label="fit")
        plt.plot(init_guess['x0'].value, init_guess['amplitude'].value +
                 init_guess['intercept'].value, 'ro')

        results_list.append(res)

    # now convert peak to cen 
    # just use first peak for now
    # left right doesnt mean anything by the symmetric peak pairs
    peak_left_cen = results_list[0].best_values['x0']
    peak_right_cen = results_list[1].best_values['x0']

    new_theta_offset = (peak_left_cen+peak_right_cen)*.5
    average_peak_theta = (np.abs(peak_left_cen-new_theta_offset) +
                          np.abs(peak_right_cen-new_theta_offset))
    print("new theta offset : {} deg".format(new_theta_offset))
    print("average peak theta: {} deg".format(average_peak_theta))

    fitted_wavelength = wavelength_from_theta(average_peak_theta, D="Si")
    print("Fitted wavelength is {} angs".format(fitted_wavelength))

    # in case we want access to the results list
    myresult.results_list = results_list


class MyResult:
    pass

myresult = MyResult()
