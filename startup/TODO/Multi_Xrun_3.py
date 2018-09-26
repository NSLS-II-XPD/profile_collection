# ==================================================================
# Author:S. Ghose
# Date written: 11-03-2017
# Date last updated:
# %run -i /home/xf28id1/Documents/Sanjit/Scripts/Multi_Xrun_3.py
# Function: multiple xrun with GasXrun_plan
# ==================================================================

gas_plan = Gas_Plan(gas_in = 'He', liveplot_key= 'rga_mass7', totExpTime = 300, num_exp = 48, delay = 1) 
run_and_save(sample_num = 8)

xrun(8,6, folder_tag = 'RT-DMMP-des-900s')   
integrate_and_save_last() 
time.sleep(10)

xrun(8,12, folder_tag = 'Tramp-DMMP-des')   
integrate_and_save_last() 
time.sleep(10)

xrun(8,14, folder_tag = 'HT-DMMP-des')   
integrate_and_save_last() 
time.sleep(10)

cs700.move(300)
time.sleep(120)
xrun(8,6, folder_tag = 'RT-DMMP-ades-900s')   
integrate_and_save_last() 
time.sleep(10)

