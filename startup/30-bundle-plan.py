from ophyd.sim import det, noisy_det
from bluesky.utils import ts_msg_hook
import bluesky.preprocessors as bpp
import time
import json

from xpdacq.beamtime import configure_area_det
from xpdacq.xpdacq import _inject_qualified_dark_frame_uid, _inject_calibration_md, _inject_analysis_stage
import bluesky.preprocessors as bpp

# RE.msg_hook = ts_msg_hook


def open_shutter_stub():
    """simple function to return a generator that yields messages to
    open the shutter"""
    # yield from bps.abs_set(
    #     xpd_configuration["shutter"], XPD_SHUTTER_CONF["open"], wait=True
    # )
    yield from bps.mv(fs, -20)
    yield from bps.sleep(glbl["shutter_sleep"])
    yield from bps.checkpoint()
    
    
def close_shutter_stub():
    """simple function to return a generator that yields messages to
    close the shutter"""
    # yield from bps.abs_set(
    #     xpd_configuration["shutter"], XPD_SHUTTER_CONF["close"], wait=True
    # )
    yield from bps.mv(fs, 20)
    yield from bps.checkpoint()
    
    
    
def take_dark():
    """a plan for taking a single dark frame"""
    print("INFO: closing shutter...")
    yield from close_shutter_stub()
    print("INFO: taking dark frame....")
    # upto this stage, area_det has been configured to so exposure time is
    # correct
    area_det = xpd_configuration["area_det"]
    acq_time = area_det.cam.acquire_time.get()
    if hasattr(area_det, 'images_per_set'):
        num_frame = area_det.images_per_set.get()
    else:
        num_frame = 1
    computed_exposure = acq_time * num_frame
    # update md
    _md = {
        "sp_time_per_frame": acq_time,
        "sp_num_frames": num_frame,
        "sp_computed_exposure": computed_exposure,
        "sp_type": "ct",
        "sp_plan_name": "dark_{}".format(computed_exposure),
        "dark_frame": True,
    }
    c = bp.count([area_det], md=_md)
    yield from bpp.subs_wrapper(c, {"stop": [_update_dark_dict_list]})
    print("opening shutter...")



def periodic_dark(plan):
    """
    a plan wrapper that takes a plan and inserts `take_dark`

    The `take_dark` plan is inserted on the fly before the beginning of
    any new run after a period of time defined by glbl['dk_window'] has passed.
    """
    need_dark = True

    def insert_take_dark(msg):
        nonlocal need_dark
        qualified_dark_uid = _validate_dark(expire_time=glbl["dk_window"])
        area_det = xpd_configuration["area_det"]

        if (not need_dark) and (not qualified_dark_uid):
            need_dark = True
        if need_dark and (not qualified_dark_uid) and msg.command == "open_run" and (
            "dark_frame" not in msg.kwargs
        ):
            # We are about to start a new 'run' (e.g., a count or a scan).
            # Insert a dark frame run first.
            need_dark = False
            # Annoying detail: the detector was probably already staged.
            # Unstage it (if it wasn't staged, nothing will happen) and
            # then take_dark() and then re-stage it.
            return (
                bpp.pchain(
                    bps.unstage(area_det),
                    take_dark(),
                    bps.stage(area_det),
                    bpp.single_gen(msg),
                    open_shutter_stub(),
                ),
                None,
            )
        elif msg.command == "open_run" and "dark_frame" not in msg.kwargs:
            return (
                bpp.pchain(
                    bpp.single_gen(msg),
                    open_shutter_stub()
                ),
                None,
            )
        else:
            # do nothing if (not need_dark)
            return None, None

    return (yield from bpp.plan_mutator(plan, insert_take_dark))



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
    
    print(f"{glbl['inbound_proxy_address'] = }")
    
    print(f"{glbl['outbound_proxy_address'] = }")
    
    yield from bps.sleep(1)
    
    
    
    
def print_pump_server(pump_list):

    for p in pump_list:
        print(f"{p.name = }")
        
        print(f"{p.read_infuse_rate.get() = }")
    
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



            
            

def xray_uvvis_plan3(det1, det2, *args, md=None, num_abs=10, num_flu=10, sample_type = 'test',
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
            
            
            
    def scattering():
        yield from bps.trigger(det1, wait=True)
        # yield from bps.sleep(det1_time)
        yield from bps.create(name="scattering")
        reading = (yield from bps.read(det1))
        # print(f"reading = {reading}")
        # ret.update(reading)
        yield from bps.save()
        print('\nForce to close fast shutter in case ....\n')
        yield from bps.mv(fs, 20)
    
    
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
        yield from Absorption()
        
        ## Start to collecting fluorescence
        yield from fluorescence()

        ## Start to collecting scattering
        return (yield from scattering())
        
        
    ## periodic_dark has to wrap a plan which is a complete run (where run_decorator is added).
    grand_plan = periodic_dark(trigger_two_detectors())
    grand_plan = bpp.msg_mutator(grand_plan, _inject_qualified_dark_frame_uid)
    grand_plan = bpp.msg_mutator(grand_plan, _inject_calibration_md)
    grand_plan = bpp.msg_mutator(grand_plan, _inject_analysis_stage)
    return (yield from grand_plan)





def record_metadata(peak_emission, fwhm, plqy, md={}):
    """TEMPORARY SOLUTION!!! Implement a proper solution for saving analysis/processed data into tiled."""
    md["plan_name"] = "record_metadata"
    md["optical_property"] = {'Peak': peak_emission, 'FWHM': fwhm, 'PLQY': plqy}
    yield from bp.count([], md=md)
