from ophyd.sim import det, noisy_det
from bluesky.utils import ts_msg_hook
import bluesky.preprocessors as bpp
import time
import json
# RE.msg_hook = ts_msg_hook


## dump or read glbl["_dark_dict_list"] into or from a json file
def dark_json(json_fn, dump_or_load='dump'):
    if dump_or_load == 'dump':
        with open(json_fn, 'w') as f:
            # indent=2 is not needed but makes the file human-readable 
            # if the data is nested
            json.dump(glbl["_dark_dict_list"], f, indent=2)
            
        print(f'Dump glbl["_dark_dict_list"] to {json_fn}')

    elif dump_or_load == 'load':
        with open(json_fn, 'r') as f:
            new_dark = json.load(f)
        for dark in new_dark:
            glbl["_dark_dict_list"].append(dark)
        
        print(f'Append dark list from {os.path.basename(json_fn)} to glbl["_dark_dict_list"]')
        # return _dark_dict_list
        
    yield from bps.sleep(1)



def set_glbl_qserver(frame_acq_time=0.5, dk_window=1000, auto_load_calib=True, shutter_control=True, 
                     export_dark=False, append_dark=False, json_fn=None):
    
    glbl['frame_acq_time']=frame_acq_time
    print(f"{glbl['frame_acq_time'] = }")
    
    glbl['dk_window']=dk_window
    print(f"{glbl['dk_window'] = }")
    
    glbl['auto_load_calib'] = auto_load_calib
    print(f"{glbl['auto_load_calib'] = }")
    
    glbl['shutter_control'] = shutter_control
    print(f"{glbl['shutter_control'] = }")
    
    if export_dark:
        yield from dark_json(json_fn, dump_or_load='dump')
        
    
    if append_dark:
        yield from dark_json(json_fn, dump_or_load='load')
    
    
    print(f"{glbl['_dark_dict_list'] = }")
    
    print(f"{glbl['mask_kwargs'] = }")
    
    yield from bps.sleep(1)
    
    
def set_area_det_qserver(area_det):
    
    xpd_configuration['area_det'] = area_det
    
    print(f"The default detector: {xpd_configuration['area_det'] =  }")
    
    yield from bps.sleep(1)
    
    
    
def print_glbl_qserver():

    print(f"{glbl['frame_acq_time'] = }")
    
    print(f"{glbl['dk_window'] = }")
    
    print(f"{glbl['auto_load_calib'] = }")
    
    print(f"{glbl['shutter_control'] = }")
    
    print(f"{glbl['_dark_dict_list'] = }")
    
    print(f"{glbl['mask_kwargs'] = }")
    
    yield from bps.sleep(1)
    

def xray_uvvis_plan(det1, det2, *args, md=None, num_abs=10, num_flu=10, sample_type = 'test',
                    pump_list=None, precursor_list=None, mixer=None, note=None, **kwargs):
    """Trigger the two detctors (det1: pe1c, det2: qepro) for parallel measurements.
        
    Generate a scan containing three stream names: ['scattering', 'absorbance', 'fluorescence']

    Args:
        det1 (ophyd.Device): xray detector (example: pe1c)
        det2 (ophyd.Device): Uv-Vis detector (example: qepro)
        md (dict, optional): metadata.
        num_abs (int, optional): numbers of absorption spectra
        num_flu (int, optional): numbers of fluorescence spectra
        sample_type (str, optional): sample name
        pump_list (list, optional): list of pumps as ophyd.Device (example: [dds1_p1, dds1_p2, dds2_p1, dds2_p2])
        precursor_list (list, optional): list of precursors name (example: ['CsPbOA', 'TOABr', 'ZnI2', 'Toluene'])
        mixer (list, optional): list of mixers (example: ['30 cm', '60 cm'])
        note (str, optional): addtional info. Defaults to None.
    """
    if (pump_list != None and precursor_list != None):
        _md = {"pumps" : [pump.name for pump in pump_list],
               "precursors" : precursor_list,
               "infuse_rate" : [pump.read_infuse_rate.get() for pump in pump_list],
               "infuse_rate_unit" : [pump.read_infuse_rate_unit.get() for pump in pump_list],
               "pump_status" : [pump.status.get() for pump in pump_list],
               "uvvis" :[det2.integration_time.get(), det2.num_spectra.get(), det2.buff_capacity.get()],
               "mixer": mixer,
               "sample_type": sample_type,
               "sample_name": sample_type,
               "detectors": [det1.name, det2.name], 
               "note" : note if note else "None"}
        _md.update(md or {})

    if (pump_list == None and precursor_list == None):
        _md = { "uvvis" :[det2.integration_time.get(), det2.num_spectra.get(), det2.buff_capacity.get()],
                "mixer": ['exsitu measurement'],
                "sample_type": sample_type, 
                "sample_name": sample_type,
                "detectors": [det1.name, det2.name], 
                "note" : note if note else "None"}
        _md.update(md or {})

    
    @bpp.stage_decorator([det1, det2])
    @bpp.run_decorator(md=_md)
    def trigger_two_detectors():  # TODO: rename appropriately
        yield from bps.trigger(det1)

        ret = {}

        # TODO: write your fast procedure here, don't use bp.count/bp.scan here as they open separate runs.
        # Use `trigger_and_read` instead.
        # Tested on 2023/02/16: bps.trigger works for qepro


        # For absorbance: spectrum_type='Absorbtion', correction_type='Reference'
        # For fluorescence: spectrum_type='Corrected Sample', correction_type='Dark'

        ## Start to collecting absrobtion
        # t0 = time.time()
        spectrum_type='Absorbtion'
        correction_type='Reference'
        if LED.get()=='Low' and UV_shutter.get()=='High' and det2.correction.get()==correction_type and det2.spectrum_type.get()==spectrum_type:
            pass
        else:
            # yield from bps.abs_set(qepro.correction, correction_type, wait=True)
            # yield from bps.abs_set(qepro.spectrum_type, spectrum_type, wait=True)
            yield from bps.mv(det2.correction, correction_type, det2.spectrum_type, spectrum_type)
            yield from bps.mv(LED, 'Low', UV_shutter, 'High')
            yield from bps.sleep(2)

        for i in range(num_abs):
            yield from bps.trigger(det2, wait=True)

            yield from bps.create(name="absorbance")
            reading = (yield from bps.read(det2))
            # print(f"reading = {reading}")
            ret.update(reading)
            yield from bps.save()  # TODO: check if it's needed, most likely yes.
            # yield from bps.sleep(2)


        ## Start to collecting fluorescence
        spectrum_type='Corrected Sample'
        correction_type='Dark'
        if LED.get()=='High' and UV_shutter.get()=='Low' and det2.correction.get()==correction_type and det2.spectrum_type.get()==spectrum_type:
            pass
        else:
            # yield from bps.abs_set(qepro.correction, correction_type, wait=True)
            # yield from bps.abs_set(qepro.syield from bps.sleep(xray_time)pectrum_type, spectrum_type, wait=True)
            yield from bps.mv(det2.correction, correction_type, det2.spectrum_type, spectrum_type)
            yield from bps.mv(LED, 'High', UV_shutter, 'Low')
            yield from bps.sleep(2)

        for i in range(num_flu):  # TODO: fix the number of triggers
            yield from bps.trigger(det2, wait=True)

            yield from bps.create(name="fluorescence")
            reading = (yield from bps.read(det2))
            # print(f"reading = {reading}")
            ret.update(reading)
            yield from bps.save()  # TODO: check if it's needed, most likely yes.
            # yield from bps.sleep(2)

        yield from bps.mv(LED, 'Low', UV_shutter, 'Low')
        # t1 = time.time()
        # xray_time = det1_time-(t1-t0)
        # print(f'{xray_time = }')
        # yield from bps.sleep(xray_time)
        ...
        ###

        yield from bps.create(name="scattering")
        reading = (yield from bps.read(det1))
        print(f"reading = {reading}")
        ret.update(reading)
        yield from bps.save()

    yield from trigger_two_detectors()




def xray_uvvis_plan2(det1, det2, *args, md=None, num_abs=10, num_flu=10, sample_type = 'test',
                    pump_list=None, precursor_list=None, mixer=None, note=None, **kwargs):
    """Trigger the two detctors (det1: pe1c, det2: qepro): det2 first and then det1.
        
    Generate a scan containing three stream names: ['scattering', 'absorbance', 'fluorescence']

    Args:
        det1 (ophyd.Device): xray detector (example: pe1c)
        det2 (ophyd.Device): Uv-Vis detector (example: qepro)
        md (dict, optional): metadata.
        num_abs (int, optional): numbers of absorption spectra
        num_flu (int, optional): numbers of fluorescence spectra
        sample_type (str, optional): sample name
        pump_list (list, optional): list of pumps as ophyd.Device (example: [dds1_p1, dds1_p2, dds2_p1, dds2_p2])
        precursor_list (list, optional): list of precursors name (example: ['CsPbOA', 'TOABr', 'ZnI2', 'Toluene'])
        mixer (list, optional): list of mixers (example: ['30 cm', '60 cm'])
        note (str, optional): addtional info. Defaults to None.
    """
    
    det1 = _find_ophyd(det1)
    det2 = _find_ophyd(det2)
    
    if (pump_list != None and precursor_list != None):
        pump_list = [_find_ophyd(pump) if type(pump) is str else pump for pump in pump_list]
        _md = {"pumps" : [pump.name for pump in pump_list],
               "precursors" : precursor_list,
               "infuse_rate" : [pump.read_infuse_rate.get() for pump in pump_list],
               "infuse_rate_unit" : [pump.read_infuse_rate_unit.get() for pump in pump_list],
               "pump_status" : [pump.status.get() for pump in pump_list],
               "uvvis" :[det2.integration_time.get(), det2.num_spectra.get(), det2.buff_capacity.get()],
               "mixer": mixer,
               "sample_type": sample_type,
               "sample_name": sample_type,
               "detectors": [det1.name, det2.name], 
               "note" : note if note else "None"}
        _md.update(md or {})

    if (pump_list == None and precursor_list == None):
        _md = { "uvvis" :[det2.integration_time.get(), det2.num_spectra.get(), det2.buff_capacity.get()],
                "mixer": ['exsitu measurement'],
                "sample_type": sample_type, 
                "sample_name": sample_type,
                "detectors": [det1.name, det2.name], 
                "note" : note if note else "None"}
        _md.update(md or {})

    
    @bpp.stage_decorator([det1, det2])
    @bpp.run_decorator(md=_md)
    def trigger_two_detectors():  # TODO: rename appropriately
        ret = {}

        # TODO: write your fast procedure here, don't use bp.count/bp.scan here as they open separate runs.
        # Use `trigger_and_read` instead.
        # Tested on 2023/02/16: bps.trigger works for qepro


        # For absorbance: spectrum_type='Absorbtion', correction_type='Reference'
        # For fluorescence: spectrum_type='Corrected Sample', correction_type='Dark'

        ## Start to collecting absrobtion
        # t0 = time.time()
        spectrum_type='Absorbtion'
        correction_type='Reference'
        if LED.get()=='Low' and UV_shutter.get()=='High' and det2.correction.get()==correction_type and det2.spectrum_type.get()==spectrum_type:
            pass
        else:
            # yield from bps.abs_set(qepro.correction, correction_type, wait=True)
            # yield from bps.abs_set(qepro.spectrum_type, spectrum_type, wait=True)
            yield from bps.mv(det2.correction, correction_type, det2.spectrum_type, spectrum_type)
            yield from bps.mv(LED, 'Low', UV_shutter, 'High')
            yield from bps.sleep(2)

        for i in range(num_abs):
            yield from bps.trigger(det2, wait=True)

            yield from bps.create(name="absorbance")
            reading = (yield from bps.read(det2))
            # print(f"reading = {reading}")
            ret.update(reading)
            yield from bps.save()  # TODO: check if it's needed, most likely yes.
            # yield from bps.sleep(2)


        ## Start to collecting fluorescence
        spectrum_type='Corrected Sample'
        correction_type='Dark'
        if LED.get()=='High' and UV_shutter.get()=='Low' and det2.correction.get()==correction_type and det2.spectrum_type.get()==spectrum_type:
            pass
        else:
            # yield from bps.abs_set(qepro.correction, correction_type, wait=True)
            # yield from bps.abs_set(qepro.syield from bps.sleep(xray_time)pectrum_type, spectrum_type, wait=True)
            yield from bps.mv(det2.correction, correction_type, det2.spectrum_type, spectrum_type)
            yield from bps.mv(LED, 'High', UV_shutter, 'Low')
            yield from bps.sleep(2)

        for i in range(num_flu):  # TODO: fix the number of triggers
            yield from bps.trigger(det2, wait=True)

            yield from bps.create(name="fluorescence")
            reading = (yield from bps.read(det2))
            # print(f"reading = {reading}")
            ret.update(reading)
            yield from bps.save()  # TODO: check if it's needed, most likely yes.
            # yield from bps.sleep(2)

        yield from bps.mv(LED, 'Low', UV_shutter, 'Low')
        try:  
            yield from stop_group([pump_list[-1]])
            print(f'\nUV-Vis acquisition finished and stop infusing of {pump_list[-1].name} for toluene dilution\n')
        except (TypeError):
            print(f'\n{pump_list = }. No pump_list!! \n')
        
       
        ## Start to collecting scattering
        yield from bps.trigger(det1, wait=True)
        # yield from bps.sleep(det1_time)
        yield from bps.create(name="scattering")
        reading = (yield from bps.read(det1))
        print(f"reading = {reading}")
        ret.update(reading)
        yield from bps.save()


    yield from trigger_two_detectors()




def record_metadata(peak_emission, fwhm, plqy, md={}):
    """TEMPORARY SOLUTION!!! Implement a proper solution for saving analysis/processed data into tiled."""
    md["plan_name"] = "record_metadata"
    md["optical_property"] = {'Peak': peak_emission, 'FWHM': fwhm, 'PLQY': plqy}
    yield from bp.count([], md=md)
    
    
    
def xray_uvvis_bsui(det1, det2, exposure, *args, md=None, num_abs=10, num_flu=10, sample_type = 'test',
                    pump_list=None, precursor_list=None, mixer=None, note=None, **kwargs):
    """Trigger the two detctors (det1: pe1c, det2: qepro): det2 first and then det1.
        
    Generate a scan containing three stream names: ['scattering', 'absorbance', 'fluorescence']

    Args:
        det1 (ophyd.Device): xray detector (example: pe1c)
        det2 (ophyd.Device): Uv-Vis detector (example: qepro)
        md (dict, optional): metadata.
        num_abs (int, optional): numbers of absorption spectra
        num_flu (int, optional): numbers of fluorescence spectra
        sample_type (str, optional): sample name
        pump_list (list, optional): list of pumps as ophyd.Device (example: [dds1_p1, dds1_p2, dds2_p1, dds2_p2])
        precursor_list (list, optional): list of precursors name (example: ['CsPbOA', 'TOABr', 'ZnI2', 'Toluene'])
        mixer (list, optional): list of mixers (example: ['30 cm', '60 cm'])
        note (str, optional): addtional info. Defaults to None.
    """
    
    det1 = _find_ophyd(det1)
    det2 = _find_ophyd(det2)
    
    if (pump_list != None and precursor_list != None):
        pump_list = [_find_ophyd(pump) if type(pump) is str else pump for pump in pump_list]
        _md = {"pumps" : [pump.name for pump in pump_list],
               "precursors" : precursor_list,
               "infuse_rate" : [pump.read_infuse_rate.get() for pump in pump_list],
               "infuse_rate_unit" : [pump.read_infuse_rate_unit.get() for pump in pump_list],
               "pump_status" : [pump.status.get() for pump in pump_list],
               "uvvis" :[det2.integration_time.get(), det2.num_spectra.get(), det2.buff_capacity.get()],
               "mixer": mixer,
               "sample_type": sample_type,
               "sample_name": sample_type,
               "detectors": [det1.name, det2.name], 
               "note" : note if note else "None"}
        _md.update(md or {})

    sp_md = yield from _pre_plan([det1], exposure)

    if (pump_list == None and precursor_list == None):
        _md = { #"uvvis" :[det2.integration_time.get(), det2.num_spectra.get(), det2.buff_capacity.get()],
                "mixer": ['exsitu measurement'],
                "sample_type": sample_type, 
                "sample_name": sample_type,
                #"detectors": [det1.name, det2.name], 
                "note" : note if note else "None"}
        _md.update(md or {})
        
    _md.update(sp_md)

    @bpp.stage_decorator([det2])
    def Absorption():
        spectrum_type='Absorbtion'
        correction_type='Reference'
        if LED.get()=='Low' and UV_shutter.get()=='High' and det2.correction.get()==correction_type and det2.spectrum_type.get()==spectrum_type:
            pass
        else:
            # yield from bps.abs_set(qepro.correction, correction_type, wait=True)
            # yield from bps.abs_set(qepro.spectrum_type, spectrum_type, wait=True)
            yield from bps.mv(det2.correction, correction_type, det2.spectrum_type, spectrum_type)
            yield from bps.mv(LED, 'Low', UV_shutter, 'High')
            yield from bps.sleep(2)

        for i in range(num_abs):
            yield from bps.trigger(det2, wait=True)

            yield from bps.create(name="absorbance")
            reading = (yield from bps.read(det2))
            # print(f"reading = {reading}")
            # ret.update(reading)
            yield from bps.save()  # TODO: check if it's needed, most likely yes.
            # yield from bps.sleep(2)
            
    
    @bpp.stage_decorator([det2])
    def fluorescence():
        spectrum_type='Corrected Sample'
        correction_type='Dark'
        if LED.get()=='High' and UV_shutter.get()=='Low' and det2.correction.get()==correction_type and det2.spectrum_type.get()==spectrum_type:
            pass
        else:
            # yield from bps.abs_set(qepro.correction, correction_type, wait=True)
            # yield from bps.abs_set(qepro.syield from bps.sleep(xray_time)pectrum_type, spectrum_type, wait=True)
            yield from bps.mv(det2.correction, correction_type, det2.spectrum_type, spectrum_type)
            yield from bps.mv(LED, 'High', UV_shutter, 'Low')
            yield from bps.sleep(2)

        for i in range(num_flu):  # TODO: fix the number of triggers
            yield from bps.trigger(det2, wait=True)

            yield from bps.create(name="fluorescence")
            reading = (yield from bps.read(det2))
            # print(f"reading = {reading}")
            # ret.update(reading)
            yield from bps.save()  # TODO: check if it's needed, most likely yes.
            # yield from bps.sleep(2)

        yield from bps.mv(LED, 'Low', UV_shutter, 'Low')
        
        try:  
            yield from stop_group([pump_list[-1]])
            print(f'\nUV-Vis acquisition finished and stop infusing of {pump_list[-1].name} for toluene dilution\n')
        except (TypeError):
            print(f'\n{pump_list = }. No pump_list!! \n')
            
            
    @bpp.stage_decorator([det1])
    def scattering():
        yield from bps.trigger(det1, wait=True)
        # yield from bps.sleep(det1_time)
        yield from bps.create(name="scattering")
        reading = (yield from bps.read(det1))
        # print(f"reading = {reading}")
        # ret.update(reading)
        print('\nForce to close fast shutter in case ....\n')
        yield from bps.mv(fs, 20)
        yield from bps.save()
    
    
    # @bpp.stage_decorator([det1, det2])
    # @bpp.stage_decorator([det1])
    @bpp.run_decorator(md=_md)
    def trigger_two_detectors():  # TODO: rename appropriately
        ret = {}

        # TODO: write your fast procedure here, don't use bp.count/bp.scan here as they open separate runs.
        # Use `trigger_and_read` instead.
        # Tested on 2023/02/16: bps.trigger works for qepro


        # For absorbance: spectrum_type='Absorbtion', correction_type='Reference'
        # For fluorescence: spectrum_type='Corrected Sample', correction_type='Dark'

        ## Start to collecting absrobtion
        # t0 = time.time()
        yield from Absorption()
        
        ## Start to collecting fluorescence
        yield from fluorescence()

        ## Start to collecting scattering
        # yield from periodic_dark(scattering())
        yield from scattering()
        
    ## periodic_dark has to wrap a plan which is a complete run (where run_decorator is added).
    grand_plan = periodic_dark(trigger_two_detectors())
    # grand_plan = trigger_two_detectors()
    grand_plan = bpp.msg_mutator(grand_plan, _inject_qualified_dark_frame_uid)
    grand_plan = bpp.msg_mutator(grand_plan, _inject_calibration_md)
    grand_plan = bpp.msg_mutator(grand_plan, _inject_analysis_stage)
    # yield from trigger_two_detectors()
    return (yield from grand_plan)


## Auto generate sample name with given prefix and infuse_rate
## If prefix = None, 'Pre00', 'Pre01', 'Pre02', ... will be used.
def _auto_name_sample(infuse_rates, prefix=None):
    infuse_rates = np.asarray(infuse_rates)

    if len(infuse_rates.shape) == 1:
        infuse_rates = infuse_rates.reshape(1, infuse_rates.shape[0])

    if prefix == None:
        prefix_list = [f'Pre{i:02d}' for i in range(infuse_rates.shape[1])]
    else:
        prefix_list = prefix
    
    # prefix_array = np.asarray(prefix_list)

    sample = []
    for i in range(infuse_rates.shape[0]):
        name = ''
        # for j in range(infuse_rates.shape[1]):
        for j in range(len(prefix_list)):
            int_rate = int(round(float(infuse_rates[i][j]), 0))
            name += f'{prefix_list[j]}_{int_rate:03d}_'
        sample.append(name[:-1])
    
    return sample



# ophyd_map = {
# 	'dds2_p1': dds2_p1, 
#  	'dds2_p2': dds2_p2, 
#   	'dds3_p2': dds3_p2, 
#    	'dds3_p1': dds3_p1, 
# 	'dds1_p1': dds1_p1, 
#  	'ultra1': ultra1, 
#   	'ultra2': ultra2, 
#    	'dds1_p2': dds1_p2, 
#     'qepro': qepro, 
#     'pe1c': pe1c
# }

## Pass qsever parameters by xlsx_to_inputs
## Arrange tasks of for PQDs synthesis
def synthesis_bsui_xlsx(parameter_obj):
	"""
	Pass qsever parameters by xlsx_to_inputs
	Arrange tasks of for PQDs synthesis

	Args:
		parameter_obj (xlsx_to_inputs): parameters passing to qserver 
		(example: pump_list = parameter_obj.inputs.pump_list)
	"""
	
	qsp = parameter_obj.inputs

	syringe_list = qsp.syringe_list
	pump_list = qsp.pump_list
	auto_set_target_list = qsp.auto_set_target_list[0]
	set_target_list = qsp.set_target_list
	target_vol_list = qsp.target_vol_list
	rate_list = qsp.infuse_rates
	syringe_mater_list = qsp.syringe_mater_list
	precursor_list = qsp.precursor_list
	mixer = qsp.mixer
	resident_t_ratio = qsp.resident_t_ratio 
	prefix = qsp.prefix
	sample = qsp.sample
	wait_dilute = qsp.wait_dilute
	if_wash = qsp.if_wash
	wash_loop = qsp.wash_loop
	# wash_sapphire = qsp.wash_sapphire
	rate_unit = qsp.rate_unit[0]
	name_by_prefix = qsp.name_by_prefix[0]
	det2 = qsp.uvvis_config[0]
	num_abs = qsp.uvvis_config[1]
	num_flu = qsp.uvvis_config[2]
	det1 = qsp.perkin_config[0]
	det1_frame_rate = qsp.perkin_config[1]
	det1_time = qsp.perkin_config[2]
	pos = qsp.pos[0]
	dummy_qserver = qsp.dummy_qserver[0]
	is_iteration = qsp.is_iteration[0]
	zmq_control_addr = qsp.zmq_control_addr[0]
	zmq_info_addr = qsp.zmq_info_addr[0]


	# RM = REManagerAPI(zmq_control_addr=zmq_control_addr, zmq_info_addr=zmq_info_addr)

	if name_by_prefix:
		sample = _auto_name_sample(rate_list, prefix=prefix)
	                                                                                 
	rate_list = np.asarray(rate_list, dtype=np.float32)
	if len(rate_list.shape) == 1:
		rate_list = rate_list.reshape(1, rate_list.shape[0])
		rate_list = rate_list.tolist()
	else:
		rate_list = rate_list.tolist()

	if auto_set_target_list:
		set_target_list = np.zeros([len(rate_list), len(pump_list)]).tolist()
	
	else:
		set_target_list = np.asarray(set_target_list, dtype=np.int8)
		if len(set_target_list.shape) == 1:
			set_target_list = set_target_list.reshape(1, set_target_list.shape[0])
			set_target_list = set_target_list.tolist()
		else:
			set_target_list = set_target_list.tolist()
		
	num_pumps = int(len(wash_loop)/3)
	# 0. stop infuese for all pumps
	yield from stop_group(pump_list + [wash_loop[1+i*3] for i in range(num_pumps)])
	# flowplan = BPlan('stop_group', pump_list + [wash_loop[1+i*3] for i in range(num_pumps)])
	# RM.item_add(flowplan, pos=pos)
 
 
	for i in range(len(rate_list)):
		# for i in range(2): 
		## 1. Set i infuese rates
		rate_list2 = rate_list[i][:-1] + [60]
		for sl, pl, ir, tvl, stl, sml in zip(
											syringe_list, 
											pump_list, 
											rate_list2, 
											target_vol_list, 
											set_target_list[i], 
											syringe_mater_list
											):
			
			# ir = float(ir)
			# stl = int(stl)
			
   
			yield from set_group_infuse2([sl], [pl],
							rate_list = [ir], 
							target_vol_list = [tvl], 
							set_target_list = [stl], 
							syringe_mater_list = [sml], 
							rate_unit = rate_unit)
            # flowplan = BPlan('set_group_infuse2', [sl], [pl],
			# 				rate_list = [ir], 
			# 				target_vol_list = [tvl], 
			# 				set_target_list = [stl], 
			# 				syringe_mater_list = [sml], 
			# 				rate_unit = rate_unit)
			# RM.item_add(flowplan, pos=pos)


		# ## 2. Start infuese
		# if precursor_list[-1] == 'Toluene':
		# 	flowplan = BPlan('start_group_infuse', pump_list[:-1], rate_list[i][:-1])
		
		# else:
		# 	flowplan = BPlan('start_group_infuse', pump_list, rate_list[i])
		
  
		yield from start_group_infuse(pump_list, rate_list[i])
		# flowplan = BPlan('start_group_infuse', pump_list, rate_list[i])
		# RM.item_add(flowplan, pos=pos)


		## 3. Wait for equilibrium
		if len(mixer) == 1:
			if (precursor_list[-1] == 'Toluene') and (precursor_list[-2] == 'PF_oil'):
				mixer_pump_list = [[mixer[0], *pump_list[:-2]]]
			# if (precursor_list[-1] == 'Toluene') and ('CsPb' in precursor_list[0]):
			# 	mixer_pump_list = [[mixer[0], *pump_list[:2]]]
			# elif (len(precursor_list)==6) and (precursor_list[-1] == 'Toluene') and ('OLA' in precursor_list[3]):
			# 	mixer_pump_list = [[mixer[0], *pump_list[:4]]]
			# elif (len(precursor_list)==5) and (precursor_list[-1] == 'Toluene') and ('Cs-rich' in precursor_list[0]):
			# 	mixer_pump_list = [[mixer[0], *pump_list[:3]]]
			else:
				mixer_pump_list = [[mixer[0], *pump_list]]
		elif len(mixer) == 2:
			if precursor_list[-1] == 'Toluene':
				mixer_pump_list = [[mixer[0], *pump_list[:2]], [mixer[1], *pump_list[:-1]]]
			else:
				mixer_pump_list = [[mixer[0], *pump_list[:2]], [mixer[1], *pump_list]]
		
		if dummy_qserver:
			yield from sleep_sec_q(qsp.dummy_qserver[0])
			# restplan = BPlan('sleep_sec_q', qsp.dummy_qserver[1])
			# RM.item_add(restplan, pos=pos)
		
		else:
			if is_iteration:
				rest_time = resident_t_ratio[-1]
			
			elif len(resident_t_ratio) == 1:
				rest_time = resident_t_ratio[0]
			elif len(resident_t_ratio) > 1 and i==0:
				rest_time = resident_t_ratio[0]
			elif len(resident_t_ratio) > 1 and i>0:
				rest_time = resident_t_ratio[-1]

			
   
			yield from wait_equilibrium2(mixer_pump_list, ratio=rest_time)
            # restplan = BPlan('wait_equilibrium2', mixer_pump_list, ratio=rest_time)
			# RM.item_add(restplan, pos=pos)


		## 3.1 Wait for 30 secpnds for post dilute
		if precursor_list[-1] == 'Toluene':
			# flowplan = BPlan('start_group_infuse', [pump_list[-1]], [rate_list[i][-1]])
			
			yield from set_group_infuse2([syringe_list[-1]], [pump_list[-1]],
							rate_list = [rate_list[i][-1]], 
							target_vol_list = [target_vol_list[-1]], 
							set_target_list = [set_target_list[i][-1]], 
							syringe_mater_list = [syringe_mater_list[-1]], 
							rate_unit = rate_unit)
            # flowplan = BPlan('set_group_infuse2', [syringe_list[-1]], [pump_list[-1]],
			# 				rate_list = [rate_list[i][-1]], 
			# 				target_vol_list = [target_vol_list[-1]], 
			# 				set_target_list = [set_target_list[i][-1]], 
			# 				syringe_mater_list = [syringe_mater_list[-1]], 
			# 				rate_unit = rate_unit)
			# RM.item_add(flowplan, pos=pos)
			
			yield from sleep_sec_q(qsp.wait_dilute[0])
			# restplan = BPlan('sleep_sec_q', qsp.wait_dilute[0])
			# RM.item_add(restplan, pos=pos)
   
		
  
  		# ## 4.0 Configure area detector in Qserver
		# if det1 == 'pe1c' or det1 == 'pe2c':
		# 	scanplan = BPlan('configure_area_det', 
		# 					det=det1, 
		# 					exposure=1, 
		# 					acq_time=det1_frame_rate)
		# 	RM.item_add(scanplan, pos=pos)
		

		## 4-1. Take a fluorescence peak to check reaction
		
		yield from take_a_uvvis_csv_q(sample_type=sample[i], 
						spectrum_type='Corrected Sample', 
                        correction_type='Dark', 
						pump_list=pump_list, 
						precursor_list=precursor_list, 
                        mixer=mixer)
        # scanplan = BPlan('take_a_uvvis_csv_q', sample_type=sample[i], 
		# 				spectrum_type='Corrected Sample', 
        #                 correction_type='Dark', 
		# 				pump_list=pump_list, 
		# 				precursor_list=precursor_list, 
        #                 mixer=mixer)
		# RM.item_add(scanplan, pos=pos)
    

		# ## 4-2. Take a Absorption spectra to check reaction
        # scanplan = BPlan('take_a_uvvis_csv_q', sample_type=sample[i], 
		# 				spectrum_type='Absorbtion', 
        #                 correction_type='Reference', 
		# 				pump_list=pump_list, 
		# 				precursor_list=precursor_list, 
        #                 mixer=mixer)
        # RM.item_add(scanplan, pos=pos)


		#### Kafka check data here.

		## 5. Sleep for 5 seconds for Kafak to check good/bad data
		
		yield from sleep_sec_q(2)
        # restplan = BPlan('sleep_sec_q', 2)
		# RM.item_add(restplan, pos=pos)
		

		# ## 6.0 Print global parameters in Qserver
		# scanplan = BPlan('print_glbl_qserver')
		# RM.item_add(scanplan, pos=pos)
  
		if det1 == 'pe1c' or det1 == 'pe2c':
			## 6.1 Configure area detector in Qserver

			det1 = _find_ophyd(det1)
			yield from configure_area_det(det=det1,
							exposure=det1_time, 
							acq_time=det1_frame_rate)
            # scanplan = BPlan('configure_area_det', 
			# 				det=det1, 
			# 				exposure=det1_time, 
			# 				acq_time=det1_frame_rate)
			# RM.item_add(scanplan, pos=pos)


		## 6. Start xray_uvvis bundle plan to take real data  ('pe1c' or 'det')
  
		yield from xray_uvvis_bsui(det1, det2, det1_time, 
						num_abs=num_abs, 
						num_flu=num_flu, 
						sample_type=sample[i], 
						spectrum_type='Absorbtion', 
						correction_type='Reference', 
						pump_list=pump_list, 
						precursor_list=precursor_list, 
						mixer=mixer)
		# scanplan = BPlan('xray_uvvis_plan2', det1, det2, 
		# 				num_abs=num_abs, 
		# 				num_flu=num_flu, 
		# 				sample_type=sample[i], 
		# 				spectrum_type='Absorbtion', 
		# 				correction_type='Reference', 
		# 				pump_list=pump_list, 
		# 				precursor_list=precursor_list, 
		# 				mixer=mixer)
		# RM.item_add(scanplan, pos=pos)
        
        ## 6.1 sleep 20 seconds for stopping
        
		yield from sleep_sec_q(qsp.wait_dilute[1])
		# restplan = BPlan('sleep_sec_q', qsp.wait_dilute[1])
		# RM.item_add(restplan, pos=pos)
        

		######  Kafka analyze data here. #######

		## 7. Wash the loop and mixer
		if if_wash[0] == 1:
      
			yield from wash_tube_bsui2(pump_list, if_wash, wash_loop, rate_unit, 
							pos=[pos,pos,pos,pos,pos], 
							zmq_control_addr=zmq_control_addr,
							zmq_info_addr=zmq_info_addr)
                            
			# wash_tube_queue2(pump_list, if_wash, wash_loop, rate_unit, 
			# 				pos=[pos,pos,pos,pos,pos], 
			# 				zmq_control_addr=zmq_control_addr,
			# 				zmq_info_addr=zmq_info_addr)
		# elif wash_tube[0] == 0:
		# 	inst1 = BInst("queue_stop")
		# 	RM.item_add(inst1, pos='front')


	# 8. stop infuese for all pumps
 
	yield from stop_group(pump_list)
	# flowplan = BPlan('stop_group', pump_list)
	# RM.item_add(flowplan, pos=pos)





## wash loop with two solvents
def wash_tube_bsui2(pump_list, if_wash, wash_loop, rate_unit, 
					pos=[0,1,2,3,4], 
					zmq_control_addr='tcp://localhost:60615', 
					zmq_info_addr='tcp://localhost:60625'):

	# RM = REManagerAPI(zmq_control_addr=zmq_control_addr, zmq_info_addr=zmq_info_addr)

	### Stop all infusing pumps
 
	yield from stop_group(pump_list)
	# flowplan = BPlan('stop_group', pump_list)
	# RM.item_add(flowplan, pos=pos[0])

	num_pumps = int(len(wash_loop)/3)

	yield from set_group_infuse2([wash_loop[0+i*3] for i in range(num_pumps)], [wash_loop[1+i*3] for i in range(num_pumps)],
                    rate_list=[wash_loop[2+i*3] for i in range(num_pumps)], 
                    target_vol_list=['30 ml', '15 ml'], 
                    set_target_list=[False, False], 
                    syringe_mater_list = ['steel', 'plastic_BD'], 
                    rate_unit=rate_unit)
	# flowplan = BPlan('set_group_infuse2', [wash_loop[0+i*3] for i in range(num_pumps)], [wash_loop[1+i*3] for i in range(num_pumps)], 
	# 				rate_list=[wash_loop[2+i*3] for i in range(num_pumps)], 
	# 				target_vol_list=['30 ml', '15 ml'], 
	# 				set_target_list=[False, False], 
	# 				syringe_mater_list = ['steel', 'plastic_BD'], 
	# 				rate_unit=rate_unit)
	# RM.item_add(flowplan, pos=pos[1])	
	
	
	### Start washing tube/loop
 
	yield from start_group_infuse([wash_loop[0+i*3] for i in range(num_pumps)], [wash_loop[2+i*3] for i in range(num_pumps)])
	# flowplan = BPlan('start_group_infuse', [wash_loop[1+i*3] for i in range(num_pumps)], [wash_loop[2+i*3] for i in range(num_pumps)])
	# RM.item_add(flowplan, pos=pos[2])	


	### Wash loop/tube for xxx seconds
 
	yield from sleep_sec_q(if_wash[1])
	# restplan = BPlan('sleep_sec_q', if_wash[1])
	# RM.item_add(restplan, pos=pos[3])	
	


	### Stop washing
 
	yield from stop_group([wash_loop[1+i*3] for i in range(num_pumps)])
	# flowplan = BPlan('stop_group', [wash_loop[1+i*3] for i in range(num_pumps)])
	# RM.item_add(flowplan, pos=pos[4])

