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

            
def xpd_mscan(sample_list, pos_list, scanplan, repeatN=1, motor=sample_x, delay=0, det_folder=None, temp_folder = None, slack=False):
    '''
    xpd_mscan(sample_list, pos_list, scanplan, motor=sample_x,  det_folder=None, temp_folder= None, slack = False)
    
    example:
    sample spreadsheet record samples: 0: dummy, 1: Ni, 2: LaB6, 3: user samples_1, 4: user sample_2...
    sample_list = [3,4,5]
    pos_list=[100.5, 120.34, 130.39], result from sample_shift_pos()
    scanplan 0 :5 seconds images
    motor: default is sample_x
    det_folder: None 
    
    xpd_mscan(sample_list, pos_list, 0, slack=True)
    
    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list and pos_list are match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        det_folder: str, det_folder name, if it is not None, files will be saved at /tiff_base/sample_name/sub_folder
        temp_folder: str, second sub_folder name,
        slack: True will send notice to slack channel xpd_runlog, default is False
    '''
    
    if len(sample_list) == len(pos_list):
        for i,sample in enumerate(sample_list):
            print('Move sample: ', sample_list[i],'to position: ', pos_list[i])
            motor.move(pos_list[i])
            time.sleep(delay)
            for n in range(repeatN):
                if det_folder is None:
                    if temp_folder is None:
                        xrun(sample_list[i], scanplan)
                    else:
                        xrun(sample_list[i],scanplan, folder_tag_list=['sample_name','temp_key'],temp_key=temp_folder)
                else:   
                    if temp_folder is None:
                        xrun(sample_list[i], scanplan, folder_tag_list=['sample_name','det_key'],det_key=det_folder)
                    else:
                        xrun(sample_list[i], scanplan, folder_tag_list=['sample_name','det_key','temp_key'],det_key=det_folder, temp_key=temp_folder)                

                if slack == True:
                    smpl_name=db[-1].start['sample_name']
                    scanid=db[-1].start['scan_id']
                    xpd_report(f'sample_{sample}:{smpl_name}, position:{pos_list[i]}, scan ID:{scanid}, Done' )        
    else:
        print('sample list and pos_list Must have same length!')
        if slack:
            xpd_report('sample list and pos_list Must have same length!')
        return None
    if slack:
        xpd_report('All done')

def xpd_mscan_flt(sample_list, pos_list, ht_list, scanplan, motor=sample_x, delay= 0, h_thresh= None, flt_h=[1,0,0,0], flt_l=[0,0,0,0],det_folder=None, temp_folder=None, slack=False):
    '''
    xpd_mscan(sample_list, pos_list, scanplan, motor=sample_x,  det_folder=None)
    
    multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_list
        and pos_list are match
        motor: motor name which moves sample holder, default is sample_x
        scanplan: scanplan index in xpdacq scanplan
        sub_folder: str, sub_folder name, if it is not None, files will be saved 
        at /tiff_base/sample_name/sub_folder
    '''
    
    if len(sample_list) == len(pos_list):
        for i,sample in enumerate(sample_list):
            print('Move sample: ', sample_list[i],'to position: ', pos_list[i])
            motor.move(pos_list[i])
            time.sleep(delay)
            if h_thresh == None:
                continue
            else:
                if ht_list[i] <= h_thresh:
                    flt_p=flt_l
                else:
                    flt_p=flt_h
                xpd_flt_set(flt_p)               
            
            if det_folder is None:
                if temp_folder is None:
                    xrun(sample_list[i], scanplan)
                else:
                    xrun(sample_list[i], scanplan, folder_tag_list=['sample_name','temp_key'],temp_key=temp_folder)
            else:   
                if temp_folder is None:
                    xrun(sample_list[i], scanplan, folder_tag_list=['sample_name','det_key'],det_key=det_folder)
                else:
                    xrun(sample_list[i], scanplan, folder_tag_list=['sample_name','det_key','temp_key'],det_key=det_folder, temp_key=temp_folder) 
            
            if slack == True:
                smpl_name=db[-1].start['sample_name']
                xpd_report(f'sample_{sample}:{smpl_name}, position:{pos_list[i]}, Done' )            

    else:
        print('sample list and pos_list Must have same length!')
        if slack:
            xpd_report('sample list and pos_list Must have same length!')
        return None
    if slack:
        xpd_report('All done')    
    
    
def xpd_m2dscan(sample_list,pos_xlist, pos_ylist, scanplan, motor_x=sample_x, motor_y=ss_stg2_y, sub_folder=None, slack=False):
    '''
    xpd_m2dscan(sample_list,pos_xlist,pos_ylist, scanplan, motor_x=sample_x, motor_y=ss_stg2_y,sub_folder=None)
    
    example:
    smpl = [0, 1,2]
    posx=[100, 120, 130]
    posy=[37, 37.3, 37.5]
   
    5 seconds images, motor_x is sample_x, motor_y is ss_stg2_y, no sub_folder, send notice to slack
    
    xpd_m2dscan(smpl, posx, posy, 0, slack=True)
    
    2d multi-sample scan plan, parameters:
        sample_list: list of all samples in the sample holder
        pos_xlist: list of sample positions of motor_x
        pos_ylist: list of sample positions of motor_y
        double check make sure sample_list, posx_list, and posy_list are match    
        
        motor_x: motor name which moves sample holder at x direction,default is sample_x
        motor_y: motor name which moves sample holder at y direction, default is ss_stg2_y
        scanplan: scanplan index in xpdacq scanplan
        folder_name: sub_folder name, if it is not None, files will be saved 
        at /tiff_base/sample_name/folder_name
        slack: True will send notice to slack channel xpd_runlog, default is False

    ''' 
    
    length = len(sample_list)
    print('Total sample numbers:',length)
    
    if all(len(lst)==length for lst in [sample_list, pos_xlist, pos_ylist]):
        for i, sample in enumerate(sample_list):
            print('sample:',sample,'in postion: ( ',pos_xlist[i],pos_ylist[i],')')
            motor_x.move(pos_xlist[i])
            motor_y.move(pos_ylist[i])
            if sub_folder is None:
                xrun(sample_list[i], scanplan)
            else:   
                xrun(sample_list[i],scanplan,folder_tag_list=['sample_name','folder_key'], 
                     folder_key=sub_folder) 
            if slack:
                smpl_name=db[-1].start['sample_name']
                xpd_report(f'sample_{sample}:{smpl_name}, position:[{pos_xlist[i]},{pos_ylist[i]}], Done' )                                          
    else:
        print('sample list and posx_list, posy_list Must have same length')
        return None        
    
    if slack:
        xpd_report('All Done!')

def xpd_m2det_scan(sample_list, pos_list,  scanplan_pdf, scanplan_xrd, repeat_pdf=1, repeat_xrd=1, motor= sample_x,temp_folder=None, flt_pdf=None, flt_xrd=None, delay =0, slack=False):
    '''
    xpd_m2det_scan(sample_list, pos_list,  scanplan_pdf, scanplan_xrd, motor= sample_x,flt_pdf=None, flt_xrd=None, delay = delay, slack=False)
    
    first, multi-sample scan with pdf detector, data are saved at:/tiff_base/sample_name/pdf_data,
    then switch to xrd detector, repeat multi-sample scan, data are saved at: /tiff_base/sample_name/xrd_data
   
    parameters:
        sample_list: list of all samples in the sample holder
        pos_list: list of sample positions, double check make sure sample_liste
        and pos_list are match
        motor: motor name which moves sample holdersc
        scanplan_pdf: scanplan for pdf scan,  index ID in xpdacq scanplan
        scanplan_xrd: scanplan for xrd scan,  index ID in xpdacq scanplan
        flt_pdf: filter setting for pdf data, e.g. [0,0,0,0]
        flt_xrd: filter setting for xrd data, e.g. [0,0,0,0]
    '''
    
    print('pdf scan')
    pe1_z.move(250)
    pe1_x.move(-8)
    pe1_z.move(220)
    xpd_configuration['area_det']=pe1c
    glbl['frame_acq_time'] = 0.2  
    if flt_pdf is not None:
        xpd_flt_set(flt_pdf)
    if temp_folder is None:
        xpd_mscan(sample_list,pos_list, scanplan_pdf,repeatN=repeat_pdf, motor=motor, delay=delay,det_folder='pdf_data',slack=slack)
    else:
        xpd_mscan(sample_list,pos_list, scanplan_pdf,repeatN=repeat_pdf, motor=motor, delay=delay,det_folder='pdf_data', temp_folder=temp_folder,  slack=slack)
    
    print('xrd scan')    
    pe1_z.move(250)   
    pe1_x.move(392)
    xpd_configuration['area_det']=pe2c
    glbl['frame_acq_time'] = 0.2  
    if flt_pdf is not None:
        xpd_flt_set(flt_xrd)    
    if temp_folder is None:
        xpd_mscan(sample_list, pos_list, scanplan_xrd, repeatN=repeat_xrd, motor=motor, delay=delay,det_folder='xrd_data',slack=slack)
    else:
        xpd_mscan(sample_list, pos_list, scanplan_xrd, repeatN=repeat_xrd, motor=motor, delay=delay,det_folder='xrd_data',temp_folder=temp_folder, slack=slack)
 
    return None


# -----start temperature scan plans ------------------
    
def xpd_temp_list(sample_id, Temp_list, scanplan, delay=1, slcak = False):
    '''
    example
        xpd_temp_list(1, [300, 350, 400], 0, delay=1)
        sample 1, at temperature 300, 350 and 400, scanplan 0(5seconds), wait 1 second after each temperature.
        
        parameters: 
        sample_id: sample index ID in sample list
        Temp_list: temperature list
        scanplan : scanplan index ID in scanplan list 
        delay: sleep time after each temperature changes, for temperature controller to stable
        slack: True will send notice to slack channel xpd_runlog, default is False

    '''
    
    T_controller = xpd_configuration["temp_controller"] 
    for Temp in Temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        xrun(sample_id, scanplan, folder_tag_list=['sample_name','temp_key'], temp_key='Temp_'+str(Temp))
        if slack:
            smpl_name=db[-1].start['sample_name']
            xpd_report(f'sample_{sample_id}:{smpl_name}, temperature:{Temp}, Done' )          
    if slack:
        xpd_report('All Done!')
    return None        

def xpd_temp_ramp(sample_id, Tstart, Tstop, Tstep, scanplan, delay = 1, slcak = False):
    '''
    example:
        xpd_temp_list(1, 300, 400, 10, 0, delay=1)
        sample 1, from 300K to 400K, 10K steps, scanplan 0(5 seconds), wait 1 second after each temperature.
        
        parameters: 
        sample_id: sample index ID in sample list
        Tstart, Tstop, Tstep: temperature range(Tstart, Tend), step size: Tstep
        scanplan : scanplan index ID in scanplan list 
        delay: sleep time after each temperature changes, for temperature controller to stable
        slack: True will send notice to slack channel xpd_runlog, default is False

    '''
    
    T_controller = xpd_configuration["temp_controller"] 
    Tnum=int(abs(Tstart-Tstop)/Tstep)+1
    temp_list=np.linspace(Tstart,Tstop,Tnum)    
    for Temp in temp_list:
        print('temperature moving to' + str(Temp))
        T_controller.move(Temp)
        time.sleep(delay)
        xrun(sample_id, scanplan, folder_tag_list=['sample_name','temp_key'], temp_key='Temp_'+str(Temp))
        if slack:
            smpl_name=db[-1].start['sample_name']
            xpd_report(f'sample_{sample_id}:{smpl_name}, temperature:{Temp}, Done' )          

    if slack:
        xpd_report('All Done!')

    return None   
 
#------------------------------------------------------------------------------------------------------------------------
def post_to_slack(text):

    channel = "https://hooks.slack.com/services/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"

    post = {"text": "{0}".format(text)}
    try:
        json_data = json.dumps(post)
        req = request.Request(channel,
                              data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'}) 
        resp = request.urlopen(req)
    except Exception as em:
        print("EXCEPTION: " + str(em))
    return None
        
def xpd_report(text):
    post_to_slack(text)
    return None


def inner_shutter_control(msg):
    if msg.command == "trigger":
        def inner():
            yield from open_shutter_stub()
            yield msg
        return inner(), None
    elif msg.command == "save":
        return None, close_shutter_stub()
    else:
        return None, None

def save_position_to_sample_list(smpl_list, pos_list, filename):

    #file_name='300001_sample.xlsx'

    file_dir = '/nsls2/xf28id2/xpdUser/Import/'
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
    
def s2det_scan(sample, scanplan_pdf, scanplan_xrd, repeatN=1, temp_folder=None, flt_xrd=None, flt_pdf=None,slack=False):
    '''
    sample, scan with pdf detector, the switch to xrd detector, scan with xrd detector
    parameters:
        sample: index ID in xpdacq sample list
        scanplan_pdf: scanplan for pdf scan,  index ID in xpdacq scanplan list
        scanplan_xrd: scanplan for xrd scan,  index ID in xpdacq scanplan list
    
    '''
    print('pdf scan')
    pe1_z.move(250)
    pe1_x.move(-8)
    pe1_z.move(215)
    xpd_configuration['area_det']=pe1c
    if flt_pdf is not None:
        xpd_flt_set(flt_pdf)
    for r in range(repeatN):
        if temp_folder is None:
            xrun(sample,scanplan_pdf,folder_tag_list=['sample_name','det_key'],det_key='pdf_data')
        else:    
            xrun(sample,scanplan_pdf,folder_tag_list=['sample_name','det_key', 'temp_key'],det_key='pdf_data',temp_key=temp_folder)
        if slack == True:
            smpl_name=db[-1].start['sample_name']
            scanid=db[-1].start['scan_id']
            xpd_report(f'sample_{sample}:{smpl_name},scan ID:{scanid}, Done' )  
   
   
    print('xrd scan') 
    pe1_z.move(250)   
    pe1_x.move(392)
    xpd_configuration['area_det']=pe2c
    if flt_xrd is not None:
        xpd_flt_set(flt_xrd)
    if temp_folder is None:
        xrun(sample,scanplan_xrd,folder_tag_list=['sample_name','det_key'],det_key='xrd_data')
    else:
        xrun(sample,scanplan_xrd,folder_tag_list=['sample_name','det_key', 'temp_key'],det_key='xrd_data',temp_key=temp_folder)        

    if slack == True:
        smpl_name=db[-1].start['sample_name']
        scanid=db[-1].start['scan_id']
        xpd_report(f'sample_{sample}:{smpl_name},scan ID:{scanid}, Done' )  
    
    return None

def userscript1(sample_list, pos_list, temp_list, scanplan_pdf, scanplan_xrd, repeatN=1,motor=sample_x, flt_xrd=None, flt_pdf=None, slack=False):
    
    T_controller = xpd_configuration["temp_controller"]
    if len(sample_list) == len(pos_list):  
        for Temp in temp_list:
            print('temperature moving to' + str(Temp))
            T_controller.move(Temp)
            time.sleep(1)

            for i,sample in enumerate(sample_list):
                print('Move sample: ', sample_list[i],'to position: ', pos_list[i])
                motor.move(pos_list[i])
                if slack:
                    xpd_report(f'sample_{sample},position :{pos_list[i]}, temp:{Temp}')
                s2det_scan(sample, scanplan_pdf, scanplan_xrd, repeatN=repeatN, temp_folder=f'temp_{Temp}K', flt_xrd=flt_xrd, flt_pdf=flt_pdf, slack=slack)
                
    else:
        print('sample list and posx_list, posy_list Must have same length')
        return None     
    

