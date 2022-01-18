def show_me(my_im,per_low = 1, per_high = 99, use_colorbar=False): 
     my_low = np.percentile(my_im,per_low) 
     my_high = np.percentile(my_im,per_high) 
     plt.imshow(my_im,vmin=my_low, vmax=my_high) 
     if use_colorbar: 
         plt.colorbar() 

def show_me_db(my_id,per_low=1, per_high=99, use_colorbar=False,dark_subtract=True,return_im=False):
    my_det_probably = db[my_id].start['detectors'][0]+'_image'
    my_im = db[my_id].table(fill=True)[my_det_probably][1]
    if len(my_im) == 0:
        print ('issue... passing')
        pass
    if dark_subtract:
        if 'sc_dk_field_uid' in db[my_id].start.keys():
            my_dark_id = db[my_id].start['sc_dk_field_uid']
            dark_im = db[my_dark_id].table(fill=True)[my_det_probably][1]
            my_im = my_im - dark_im
        else:
            print ('this run has no associated dark')
    if return_im:
        return my_im

    show_me(my_im,per_low=per_low,per_high=per_high,use_colorbar=use_colorbar)



def make_me_a_name(my_id): 
    if 'sample_name' in db[my_id].start.keys(): 
        sample_name = db[my_id].start['sample_name'] 
    elif 'sp_plan_name' in db[my_id].start.keys(): 
        sample_name = db[my_id].start['sp_plan_name'] 
    else: 
        sample_name = 'NoName' 
    tot_time = str(round(db[my_id].start['sp_time_per_frame'] * db[my_id].start['sp_num_frames'],2)) 
    if len(tot_time) < 4:
        tot_time = '0'+tot_time
    #print ('sample name : '+sample_name) 
    #print ('tot time : '+tot_time) 
    my_name = sample_name+'T'+tot_time

    return my_name

def make_me_a_name2(my_id):
    #if 'sample_name' in db[my_id].start.keys(): 
    #    sample_name = db[my_id].start['sample_name'] 
    #elif 'sp_plan_name' in db[my_id].start.keys(): 
    #    sample_name = db[my_id].start['sp_plan_name'] 
    #else: 
    #    sample_name = 'NoName' 
    #tot_time = str(round(db[my_id].start['sp_time_per_frame'] * db[my_id].start['sp_num_frames'],2)) 
    
    this_delay = str(db[my_id].start['dans_md']['delay'])
    sample_name = str(db[my_id].start['dans_md']['sample'])
    tot_time = str(round(db[my_id].start['dans_md']['exposure']*1.000,2))
    
    if len(tot_time) < 4:
        tot_time = '0'+tot_time

    gridx = str(round(db[my_id].table(stream_name='baseline').loc[1,'Grid_X'],2))
    gridy = str(round(db[my_id].table(stream_name='baseline').loc[1,'Grid_Y'],2))
    gridz = str(round(db[my_id].table(stream_name='baseline').loc[1,'Grid_Z'],2))

    my_name = 'p3k_'+sample_name+'_GZ'+gridz+'_T'+tot_time

    return my_name


def make_colormap(num_colors, cmap='viridis'):
    my_cmap = plt.cm.get_cmap(cmap)
    color_list = my_cmap(np.linspace(0,1,num_colors))
    return color_list

def plot_xline(my_id, *argv, use_offset=0,use_alpha=1,use_cmap='viridis'):
     my_det_probably = db[my_id].start['detectors'][0]+'_image'
     this_im = db[my_id].table(fill=True)[my_det_probably][1]
     try:
         arg_len = len(*argv)
         plot_mode = 'typea'
     except:
         arg_len = len(argv)
         plot_mode = 'typeb'
         
     cc = make_colormap(arg_len,cmap=use_cmap)
     
     if arg_len > 1: #two or more arguments passed
         ymin = min(*argv)
         ymax = max(*argv)
         if plot_mode == 'typea':
             for i, this_one in enumerate(*argv):
                 plt.plot(this_im[this_one,:]+i*use_offset,color=cc[i],alpha=use_alpha)
         else:
             for i, this_one in enumerate(argv):
                 plt.plot(this_im[this_one,:]+i*use_offset,color=cc[i],alpha=use_alpha)
     if arg_len == 1: #only one argument passed
         my_line = argv[0]       
         plt.plot(this_im[my_line,:],'k')    

         
def plot_yline(my_id, *argv, use_offset=0,use_alpha=1,use_cmap='viridis'):
     my_det_probably = db[my_id].start['detectors'][0]+'_image'
     this_im = db[my_id].table(fill=True)[my_det_probably][1]
     try:
         arg_len = len(*argv)
         plot_mode = 'typea'
     except:
         arg_len = len(argv)
         plot_mode = 'typeb'
         
     cc = make_colormap(arg_len,cmap=use_cmap)
     
     if arg_len > 1: #two or more arguments passed
         ymin = min(*argv)
         ymax = max(*argv)
         if plot_mode == 'typea':
             for i, this_one in enumerate(*argv):
                 plt.plot(this_im[:,this_one]+i*use_offset,color=cc[i],alpha=use_alpha)
         else:
             for i, this_one in enumerate(argv):
                 plt.plot(this_im[:,this_one]+i*use_offset,color=cc[i],alpha=use_alpha)
     if arg_len == 1: #only one argument passed
         my_line = argv[0]       
         plt.plot(this_im[:,my_line],'k')    

def read_twocol_data(filename,junk=None,backjunk=None,splitchar=None, do_not_float=False, shh=True, use_idex=[0,1]):
    with open(filename,'r') as infile:
        datain = infile.readlines()
    
    if junk == None:
        for i in range(len(datain)):
            try:
                for j in range(10):
                    x1,y1 = float(datain[i+j].split(splitchar)[use_idex[0]]), float(datain[i+j].split(splitchar)[use_idex[1]])
                junk = i
                break
            except:
                pass #print ('nope')
                
    if backjunk == None:
        for i in range(len(datain),-1,-1):
            try:
                x1,y1 = float(datain[i].split(splitchar)[use_idex[0]]), float(datain[i].split(splitchar)[use_idex[1]])
                backjunk = len(datain)-i-1
                break
            except:
                pass
                #print ('nope')
    
    #print ('found junk '+str(junk))
    #print ('and back junk '+str(backjunk))
            
    if backjunk == 0:
        datain = datain[junk:]
    else:
        datain = datain[junk:-backjunk]
    
    xin = np.zeros(len(datain))
    yin = np.zeros(len(datain))
    
    if do_not_float:
        xin = []
        yin = []
    
    if shh == False:
        print ('length '+str(len(xin)))
    if do_not_float:
        if splitchar==None:
            for i in range(len(datain)):
                xin.append(datain[i].split()[use_idex[0]])
                yin.append(datain[i].split()[use_idex[1]])
        else:
            for i in range(len(datain)):
                xin.append(datain[i].split(splitchar)[use_idex[0]])
                yin.append(datain[i].split(splitchar)[use_idex[1]])    
    else:        
        if splitchar==None:
            for i in range(len(datain)):
                xin[i]= float(datain[i].split()[use_idex[0]])
                yin[i]= float(datain[i].split()[use_idex[1]])
        else:
            for i in range(len(datain)):
                xin[i]= float(datain[i].split(splitchar)[use_idex[0]])
                yin[i]= float(datain[i].split(splitchar)[use_idex[1]])   
        
    return xin,yin     


#setup pandas dataframe
def make_me_a_dataframe(found_pos):
    import glob as glob
    import pandas as pd
    
    my_excel_file = glob.glob('Import/*_sample.xlsx')
    if len(my_excel_file) >= 1:
      my_excel_file = my_excel_file[0]
    else:
      print ("I couldn't find your sample info excel sheet")
      return None

    read_xcel = pd.read_excel(my_excel_file,skiprows=1,usecols=([0,1]))

    df_sample_pos_info = pd.DataFrame(index=np.array(read_xcel.index))
    df_sample_pos_info['sample_names'] = read_xcel.iloc[:,0]
    df_sample_pos_info['position'] = np.hstack((found_pos[0],found_pos))
    df_sample_pos_info['xpd_acq_sample_number'] = np.array(read_xcel.index)                          
    df_sample_pos_info['sample_compositioin'] = read_xcel.iloc[:,1]
    df_sample_pos_info['measure_time'] = np.ones(len(read_xcel.index))    

    return df_sample_pos_info

def measure_me_this(df_sample_info, sample_num,measure_time=None): 
    print ("Preparing to measure "+str(df_sample_info.loc[sample_num,'sample_names'])) 
    print ("Moving to position "+str(df_sample_info.loc[sample_num,'position'])) 
    #move logic goes here 
    if measure_time == None: 
        print ("Measuring for "+str(df_sample_info.loc[sample_num,'measure_time'])) 
        #perform xrun here (or Re(Count)) 
    else: 
        print ("Override measuring for "+str(measure_time)) 
        #perform custom measure here 
    return None 
     

def scan_shifter_pos(motor, xmin, xmax, numx, num_samples=0, min_height=.02, min_dist = 5, peak_rad=1.5, use_det = True):
    yn_question = lambda q: input(q).lower().strip()[0] == "y" or False 
    print ("")
    print ("I'm going to move the motor: "+str(motor.name))
    print ("It's currently at position: "+str(motor.position))
    move_coord = float(xmin)-float(motor.position)
    if move_coord < 0:
        print ("So I will start by moving "+str(abs(move_coord))[:4]+" mm inboard from current location")
    elif move_coord > 0:
        print ("So I will start by moving "+str(abs(move_coord))[:4]+" mm outboard from current location")
    elif move_coord == 0:
        print ("I'm starting where I am right now :)")
    else:
        print ("I confused")
    
    if yn_question("Confirm scan? [y/n] ") == False:
        print ("Aborting operation")
        return None

    pos_list, I_list = _motor_move_scan_shifter_pos(motor=motor, xmin=xmin, xmax=xmax, numx=numx) 
    if len(pos_list)>1:
        delx = pos_list[1]-pos_list[0]    
    else:
        print ("only a single point? I'm gonna quit!")
        return None

    print ("")
    if yn_question("Move on to fitting? (if not, I'll return [pos_list, I_list]) [y/n] ") == False:
        return pos_list, I_list
    plt.close()

    go_on = False
    tmin_height = min_height
    tmin_dist = min_dist
    tpeak_rad = peak_rad
    fit_attempts = 1

    while go_on == False:    
        print ("\nI'm going to fit peaks with a min_height of "+str(tmin_height))
        print ("and min_dist [index values/real vals] of "+str(tmin_dist)+' / '+str(tmin_dist*delx))
        print ("and I'll fit a radius between each peak-center of "+str(tpeak_rad)) 
        if fit_attempts == 0:
            go_on, peak_cen_list, ht_list = _identify_peaks_scan_shifter_pos(pos_list,I_list,num_samples=num_samples,min_height=tmin_height, min_dist = tmin_dist, peak_rad=tpeak_rad)    
        else:
            go_on, peak_cen_list, ht_list = _identify_peaks_scan_shifter_pos(pos_list,I_list,num_samples=num_samples,min_height=tmin_height, min_dist = tmin_dist, peak_rad=tpeak_rad,open_new_plot=False)    
        fit_attempts += 1 
        #if yn_question("\nHappy with the fit? [y/n] ") == False:
        if go_on == False:
            qans = input("\n1. Change min_height\n2. Change min_dist\n3. Change peak-fit rad\n0. Give up\n : ")
            try:
                qans = int(qans)
                if int(qans) == 1:
                    tmin_height = float(input("\nWhat is the new min_height value? "))
                if int(qans) == 2:
                    tmin_dist = float(input("\nWhat is the new min_dist value? "))
                if int(qans) == 3:
                    tpeak_rad = float(input("\nWhat is the new peak_rad value? "))
                if int(qans) == 0:
                    print ("ok, giving up")
                    return None
            except:
                print ('what, what, whaaat?')
        else:
            print ("Ok, great.")
            go_on = True     

    return peak_cen_list, ht_list


def _identify_peaks_scan_shifter_pos(x,y,num_samples=0,min_height=.02, min_dist = 5, peak_rad=1.5,open_new_plot=True):
    from scipy.signal import find_peaks
    import matplotlib.pyplot as plt
    from scipy.optimize import curve_fit
    import numpy as np
    import pandas as pd    
    if open_new_plot:
        print ("making new figure")
        plt.figure()
    else:
        print ("clearing figure")
        this_fig = plt.gcf()
        this_fig.clf()
        plt.pause(.01)
        
    yn_question = lambda q: input(q).lower().strip()[0] == "y" or False
    ymax=y.max()
    y -= y.min()
    y /= y.max()
    print ('ymax is '+str(max(y)))
    print ('ymin is '+str(min(y)))

    def cut_data(qt,sqt,qmin,qmax):
        qcut = []
        sqcut = []
        for i in range(len(qt)):
            if qt[i] >= qmin and qt[i] <= qmax:
                qcut.append(qt[i])
                sqcut.append(sqt[i])
        qcut = np.array(qcut)
        sqcut = np.array(sqcut)
        return qcut, sqcut  
    
    #initial guess of position peaks
    print ('finding things')
    peaks, _ = find_peaks(y,height=min_height,distance=min_dist)
    
    if num_samples == 0:
        print ("I found "+str(len(peaks))+" peaks.")
    elif num_samples == len(peaks):
        print ("I think I found all "+str(num_samples)+" samples you expected.")
    else:
        print ("WARNING: I saw "+str(len(peaks))+" samples!")
    print ('doing a thing')
    this_fig = plt.gcf()
    this_fig.clf()
    
    plt.plot(x,y)
    plt.plot(x[peaks], y[peaks], "kx")
    plt.show()
    print ('done')
    plt.pause(.01)
    if yn_question("Go on? [y/n] ") == False:
        return False, [], []
    
    
    #now refine positions
    peak_cen_guess_list = x[peaks]
    peak_amp_guess_list = y[peaks]

    fit_peak_cen_list = np.zeros(len(peaks))
    fit_peak_amp_list = np.zeros(len(peaks)) 
    fit_peak_bgd_list = np.zeros(len(peaks))
    fit_peak_wid_list = np.zeros(len(peaks))

    def this_func(x,c,w,a,b):

        return a*np.exp(-((x-c)**2.)/(2.*(w**2)))+b

    this_fig = plt.gcf()
    this_fig.clf()
    for i in range(len(peaks)):
        cut_x, cut_y = cut_data(x,y,peak_cen_guess_list[i]-peak_rad, peak_cen_guess_list[i]+peak_rad)
        plt.plot(cut_x, cut_y)

        this_guess = [peak_cen_guess_list[i], 1, peak_amp_guess_list[i],0]
        low_limits = [peak_cen_guess_list[i]-peak_rad, 0.05, 0.0, 0.0]
        high_limits = [peak_cen_guess_list[i]+peak_rad, 3, 1.5, .5]

        popt, _ = curve_fit(this_func, cut_x, cut_y, p0=this_guess, bounds=(low_limits, high_limits))
        plt.plot(cut_x, this_func(cut_x, *popt),'k--')

        fit_peak_amp_list[i] = popt[2]
        fit_peak_wid_list[i] = popt[1]
        fit_peak_cen_list[i] = popt[0]
        fit_peak_bgd_list[i] = popt[3]
#        ht_list=[x*ymax for x in fit_peak_amp_list]
        
    plt.show()
    plt.pause(.01) 
    
    #finally, return this as a numpy list
    return True, fit_peak_cen_list[::-1], fit_peak_amp_list[::-1] #return flipped

def _motor_move_scan_shifter_pos(motor, xmin, xmax, numx): 
    from epics import caget
    I_list = np.zeros(numx) 
    dx = (xmax-xmin)/numx 
    pos_list = np.linspace(xmin,xmax,numx) 
    fs.set(0)
    fig1, ax1 = plt.subplots() 
    use_det = True # True = detector, False = photodiode
    for i, pos in enumerate(pos_list): 
        print ("moving to "+str(pos)) 
        try: 
            motor.move(pos) 
        except: 
            print ('well, something bad happened') 
            return None 
        
        if use_det==True:
            my_int = float(caget("XF:28IDC-ES:1{Det:PE1}Stats5:Total_RBV")) 
        else:
            my_int = float(caget("XF:28IDC-BI{IM:02}EM180:Current2:MeanValue_RBV"))
        I_list[i] = my_int 
        ax1.scatter(pos, my_int, color='k') 
        plt.pause(.01)         
    
    plt.plot(pos_list, I_list) 
    #plt.close()    
    fs.set(-47)
    return pos_list, I_list 


