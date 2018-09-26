import bluesky.plans as bp
from xpdacq.beamtime import _configure_area_det
import os
import numpy as np
import itertools
from bluesky.plans import (scan, subs_wrapper, abs_set, count, list_scan,
                           adaptive_scan, reset_positions_wrapper)
from bluesky.callbacks import LiveTable, LivePlot
from bluesky.plan_tools import print_summary

gas.gas_list = ['He', 'N2', 'CO2', 'Air']

def Gas_Plan(gas_in = 'He', liveplot_key=None, totExpTime = 5, num_exp = 1, delay = 1):
    """
    Example
    -------
    Set the gasses. They can be in any other, nothing to do with
    the order they are used in the plan. But, should match the connections on switch.
    >>> gas.gas_list = ['He', 'N2', 'CO2']
    >>> RGA mass is set to different value, base shows 1^-13 with He 5 cc flow shows max 2^-8
    >>> RGA mass setup in mID mode: 4,18,28,31,44,79,94,32,81
    Parameters
    ----------
    gas_in : string
        e.g., 'He', default is 'He'
        These gas must be in `gas.gas_list` but they may be in any order.
    liveplot_key : str, optional
        e. g., liveplot_key = rga_mass1
        data key for LivePlot. default is None, which means no LivePlot
    totExpTime : float
        total exposure time per frame in seconds. Dafault value is 5 sec
    num_exp : int
        number of images/exposure, default is 1
    delay: float
        delay time between exposures in sec

    Execute it
    ----------
    >> %run -i /home/xf28id1/Documents/Sanjit/Scripts/GasXrun_Plan.py
    >> change all the parameters inside Gas_Plan as required
    >>> gas_plan = Gas_Plan(gas_in = 'He', liveplot_key= 'rga_mass1', totExpTime = 5, num_exp = 3, delay = 1)
    >> to run the xrun, save metadata & save_tiff run the following
    >>> run_and_save(sample_num = 0)  
    """


    ## switch gas
    yield from abs_set(gas, gas_in)

    ## configure the exposure time first
    _configure_area_det(totExpTime)   # 5 secs exposuretime

    ## ScanPlan you need
    plan = bp.count([pe1c, gas.current_gas, rga], num=num_exp, delay= delay)    

    #plan = bp.subs_wrapper(plan, LiveTable([xpd_configuration['area_det'], rga]))   # give you LiveTable
    plan = bp.subs_wrapper(plan, LiveTable([xpd_configuration['area_det'], gas.current_gas, rga]))  
    if liveplot_key and isinstance(liveplot_key, str):
        plan =  bp.subs_wrapper(plan, LivePlot(liveplot_key))
     
    yield from plan
'''
def run_and_save(sample_num = 0, folder_tag = ''):
    data_dir = "/direct/XF28ID1/pe2_data/xpdUser/tiff_base/"
    file_name = data_dir + "sample_num_" + str(sample_num) + str(folder_tag) + ".csv"
    xrun(sample_num, gas_plan, folder_tag = str(folder_tag))
'''
def run_and_save(sample_num = 0):
    data_dir = "/direct/XF28ID1/pe2_data/xpdUser/tiff_base/"
    file_name = data_dir + "sample_num_" + str(sample_num) + ".csv"
    xrun(sample_num, gas_plan, folder_tag = 'RT-des')
    h = db[-1]
    tb = h.table()
    tb.to_csv(path_or_buf =file_name, columns = ['time', 'gas_current_gas', 'rga_mass1',
                              'rga_mass2', 'rga_mass3', 'rga_mass4', 'rga_mass5',
                              'rga_mass6', 'rga_mass7', 'rga_mass8', 'rga_mass9'])

    integrate_and_save_last()
