# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 15:58:10 2020

@author: hzhong
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Aut 03 16:27:20 2020
Author: Hui zhong, Sanjit Ghose
Plan to run multiple sample under remote condition
This plan uses xpdacq protocol
"""

from xpdacq.beamtime import _configure_area_det
from xpdacq.beamtime import open_shutter_stub, close_shutter_stub
from collections import ChainMap, OrderedDict
import pandas as pd
import datetime
import functools
import time
from bluesky.callbacks import LiveFit
from bluesky.callbacks.mpl_plotting import LiveFitPlot
import numpy as np
from urllib import request
import json
from os import chmod
from pandas.core.common import flatten


def xpd_mscan(sample_list, pos_list, scanplan, motor=sample_x, delay=0, smpl_h=[], flt_h=None, flt_l=None):
    '''
    xpd_mscan(sample_list, pos_list, smpl_flt_h, scanplan, motor=sample_x, delay=0, h_thresh= None, flt_h=[1,0,0,0], flt_l=[0,0,0,0])

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list
        and pos_list are match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        delay: dalay time in between each sample
        smpl_h: list of samples which needs special filter set
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    '''

    length = len(sample_list)

    print('Total sample numbers:',length)
    if len(sample_list) == len(pos_list):
        for sample, pos in zip(sample_list, pos_list):
            print('Move sample: ', sample,'to position: ', pos)
            motor.move(pos)
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l != None:
                    xpd_flt_set(flt_l)
            time.sleep(delay)
            xrun(sample, scanplan)

    else:
        print('sample list and pos_list Must have same length!')
        return None


def xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, motorx=sample_x, motory= sample_y, delay=0, smpl_h=[], flt_h=None, flt_l=None):
    '''
    xpd_m2dscan(sample_list, posx_list, posy_list, scanplan, motorx=sample_x, motory=sample_y, delay=0, smpl_h=[], flt_h=[1,0,0,0], flt_l=[0,0,0,0])

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list
        and pos_list are match
        motorx, motory: motors which moves sample holder, default is sample_x and sample_y
        scanplan: scanplan index in xpdacq scanplan
        delay: dalay time in between each sample
        smpl_h: list of samples which needs special filter set
        flt_h: filter set for smpl_h
        flt_l: filter set for rest of the samples
    '''


    length = len(sample_list)
    print('Total sample numbers:',length)
    if all(len(lst)==length for lst in [sample_list, posx_list, posy_list]):
        for sample, posx, posy in zip(sample_list, posx_list, posy_list):
            print('Move sample: ', sample,'to position: ', posx, posy)
            motorx.move(posx)
            motory.move(posy)
            if sample in smpl_h:
                xpd_flt_set(flt_h)
            else:
                if flt_l != None:
                    xpd_flt_set(flt_l)
            time.sleep(delay)
            xrun(sample, scanplan)

    else:
        print('sample list and posx_list, posy_list Must have same length!')
        return None

def xpd_battery(smpl_list, pos_list, scanplan, cycle=1, delay=0, motor=sample_x):
    if len(smpl_list) == len(pos_list):
        for i in range(cycle):
            for smpl, pos in zip(smpl_list, pos_list):
                motor.move(pos)
                time.sleep(delay)
                xrun(smpl, scanplan)
    else:
        print('please check the lenght of sample lists and pos_list')
        return None

def xpd_batteryxy(smpl_list, posx_list, posy_list, scanplan, cycle=1, delay=0, motorx=sample_x, motory=sample_y):
    length = len(smpl_list)
    if all(len(lst)==length for lst in [smpl_list, posx_list, posy_list]):
        for i in range(cycle):
            for smpl, posx, posy in zip(smpl_list, posx_list, posy_list):
                motorx.move(posx)
                motory.move(posy)
                time.sleep(delay)
                xrun(smpl, scanplan)
    else:
        print('please check the lenght of sample lists and pos_list')
        return None

def xpd_mscan_flt(sample_list, pos_list, ht_list, scanplan, motor=sample_x, delay=0, h_thresh= None, flt_h=[1,0,0,0], flt_l=[0,0,0,0]):
    '''
    xpd_mscan_flt(sample_list, pos_list, ht_list, scanplan, motor=sample_x, delay=0, h_thresh= None, flt_h=[1,0,0,0], flt_l=[0,0,0,0])

    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list
        and pos_list are match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan

    '''

    if len(sample_list) == len(pos_list):
        for sample, pos, ht in zip(sample_list, pos_list, ht_list):
            print('Move sample: ', sample,'to position: ', pos)
            motor.move(pos)
            time.sleep(delay)
            if h_thresh == None:
                continue
            else:
                if ht <= h_thresh:
                    flt_p=flt_l
                else:
                    flt_p=flt_h
                xpd_flt_set(flt_p)

            xrun(sample, scanplan)

    else:
        print('sample list and pos_list Must have same length!')
        return None


# -----start temperature scan plans ------------------

def xpd_temp_list(smpl, Temp_list, exp_time, delay=1, dets=[]):
    '''The plan to perform a scan over temperature list.

    Parameters
    ----------

    smpl: sample index ID in sample list
    Temp_list: temperature list
    exp_time : total exposure time for each sample, in seconds
    delay: sleep time after each temperature changes, for temperature controller to stable
    dets: list of motors, temperatures controllers, which will be recorded in table.

    Examples
    --------

    >>> xpd_temp_list(1, [300, 350, 400], 5, delay=1)

    sample 1, at temperature 300, 350 and 400, exposure time 5sec, wait 1 second after each temperature.
    '''
    #RE(_configure_area_det(exp_time))
    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det=[area_det, T_controller]+dets
    starttime=time.time()
    for Temp in Temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        plan = ct_motors_plan(det, exp_time)
        xrun(smpl, plan)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime,endtime)
    return None


def xpd_temp_ramp(smpl, Tstart, Tstop, Tstep, exp_time, delay = 1, dets=[]):
    '''
    Parameters
    ----------
    smpl: sample index ID in sample list
    Tstart, Tstop, Tstep: temperature range(Tstart, Tend), step size: Tstep
    scanplan : scanplan index ID in scanplan list
    delay: sleep time after each temperature changes, for temperature controller to stable
    dets: list of motors, temperatures controllers, which will be recorded in table.

    Examples
    --------
    >>> xpd_temp_ramp(1, 300, 400, 10, 5, delay=1)

    sample 1, from 300K to 400K, 10K steps, exposure time 5sec, wait 1 second after each temperature.
    '''
    #RE(_configure_area_det(exp_time))
    T_controller = xpd_configuration["temp_controller"]
    area_det = xpd_configuration['area_det']
    det=[area_det, T_controller]+dets
    starttime=time.time()
    Tnum=int(abs(Tstart-Tstop)/Tstep)+1
    temp_list=np.linspace(Tstart,Tstop,Tnum)
    for Temp in temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        plan = ct_motors_plan(det, exp_time)
        xrun(smpl, plan)
    endtime = time.time()
    save_tb_xlsx(smpl, starttime, endtime)
    return None

#------------------------------------------------------------------------------------------------------------------------

def ct_motors_plan(det,exp_time, num=1, delay=0, md=None):
    '''

    to read temperature controller and motor position and show on LiveTable
    then we can save table to excel file

    det=[area_det, T_controller, motor...]
    '''
    (num_frame, acq_time, computed_exposure) = yield from _configure_area_det(exp_time)
    _md = {

            "sp_time_per_frame": acq_time,
            "sp_num_frames": num_frame,
            "sp_requested_exposure": exp_time,
            "sp_computed_exposure": computed_exposure,
    }

    _md.update(md or {})
    motors=det[1:]
    #yield from _configure_area_det(exp_time)
    plan = bp.count(det, num, delay, md=_md)
    plan = bpp.subs_wrapper(plan, LiveTable(motors))
    plan = bpp.plan_mutator(plan, inner_shutter_control)
    yield from plan


def save_tb_xlsx(sample_name, starttime, endtime, readable_time=False):
    data_dir = "./tiff_base/"
    if not readable_time:
        startstring = datetime.datetime.fromtimestamp(float(starttime)).strftime('%Y-%m-%d %H:%M:%S')
        endstring = datetime.datetime.fromtimestamp(float(endtime)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        startstring = starttime
        endstring = endtime
    hdrs = db(since=startstring, until=endstring)
    timestamp = time.time()
    timestring_filename = datetime.datetime.fromtimestamp(float(timestamp)).strftime('%Y%m%d_%H%M%S')
    file_name = data_dir + 'sample_' + str(sample_name) + '_' + timestring_filename + ".xlsx"
    print(len(list(hdrs)))
    for idx, hdr in enumerate(hdrs):
        tb = hdr.table()
        uid6 = hdr.start['uid'][0:6]
        tb['uid6'] = uid6
        if idx == 0:
            DBout = tb
        else:
            DBout = DBout.append(tb, sort=False)
    writer = pd.ExcelWriter(file_name)
    DBout.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    return

def save_position_to_sample_list(smpl_list, pos_list, filename):

    #file_name='300001_sample.xlsx'

    file_dir = './Import/'
    ind_list=[x+1 for x in smpl_list]
    pos_str=[str(x) for x in pos_list]
    file_name=file_dir+filename
    f_out=file_name
    f = pd.read_excel(file_name)
    tags=pd.DataFrame(f, columns=['User supplied tags']).fillna(0)
    tags=tags.values
    for i,ind in enumerate(ind_list):
        if tags[ind][0] != 0:
            tag_str= str(tags[ind][0])
            tags[ind][0]=tag_str +',pos='+ str(pos_str[i])
        else:
            tags[ind][0]='pos='+ str(pos_str[i])
    tags=list(flatten(tags))

    new_f = pd.DataFrame({'User supplied tags': tags})
    f.update(new_f)
    writer = pd.ExcelWriter(f_out)
    f.to_excel(writer, index=False)
    writer.save()
    return None

def xpd_flt_set(flt_p):
    if flt_p[0]==0:
        fb.flt1.set('Out')
    else:
        fb.flt1.set('In')
    if flt_p[1]==0:
        fb.flt2.set('Out')
    else:
        fb.flt2.set('In')
    if flt_p[2]==0:
        fb.flt3.set('Out')
    else:
        fb.flt3.set('In')
    if flt_p[3]==0:
        fb.flt4.set('Out')
    else:
        fb.flt4.set('In')

    print('filter bank setting:', fb.flt1.get(), fb.flt2.get(), fb.flt3.get(), fb.flt4.get())

    return None


def xpd_flt_read():
    flt_p=[0,0,0,0]
    if fb.flt1.get() == 'Out':
        flt_p[0]=0
    else:
        flt_p[0]=1
    if fb.flt2.get() == 'Out':
        flt_p[1]=0
    else:
        flt_p[1]=1

    if fb.flt3.get() == 'Out':
        flt_p[2]=0
    else:
        flt_p[2]=1
    if fb.flt4.get() == 'Out':
        flt_p[3]=0
    else:
        flt_p[3]=1

    return flt_p
