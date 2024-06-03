#!/usr/bin/env python
##############################################################################
#
# xpdacq            by Billinge Group
#                   Simon J. L. Billinge sb2896@columbia.edu
#                   (c) 2016 trustees of Columbia University in the City of
#                        New York.
#                   All rights reserved
#
# File coded by:    Timothy Liu
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
##############################################################################
import os
from xpdacq.xpdacq_conf import (glbl_dict, configure_device,
                                _reload_glbl, _set_glbl,
                                _load_beamline_config)

# configure experiment device being used in current version
if glbl_dict['is_simulation']:
    from xpdacq.simulation import (xpd_pe1c, db, cs700, shctl1,
                                   ring_current, fb)
    pe1c = xpd_pe1c # alias


configure_device(area_det=pe1c, shutter=shctl1,
                 temp_controller=cs700, db=db,
                 filter_bank=fb,
                 ring_current=ring_current,
                 robot=robot)

# cache previous glbl state
reload_glbl_dict = _reload_glbl()
from xpdacq.glbl import glbl

# reload beamtime
from xpdacq.beamtimeSetup import (start_xpdacq, _start_beamtime,
                                  _end_beamtime)

bt = start_xpdacq()
if bt is not None:
    print("INFO: Reload beamtime objects:\n{}\n".format(bt))
if reload_glbl_dict is not None:
    _set_glbl(glbl, reload_glbl_dict)

# import necessary modules
from xpdacq.xpdacq import *
from xpdacq.beamtime import *
from xpdacq.utils import import_sample_info

# Metadata for both 'RE' and 'xrun':
md = {}
md['beamline_id'] = glbl['beamline_id']
md['group'] = glbl['group']
md['facility'] = glbl['facility']
md.update({"cycle": "commissioning", "proposal_id": "pass-315985"})

# instantiate xrun without beamtime, like bluesky setup
xrun = CustomizedRunEngine(None)
xrun.md.update(md)

print("loading beamline config")

if is_re_worker_active():  # running in queueserver
    del Tlist
    del Tramp
    # removing human input for automating queueserver setup by setting test=True
    beamline_config = _load_beamline_config(glbl['blconfig_path'], test=True)
else:
    beamline_config = _load_beamline_config(glbl['blconfig_path'])

print("loaded beamline config")

xrun.md['beamline_config'] = beamline_config

# insert header to db, either simulated or real
xrun.subscribe(db.insert, 'all')

# We need to repeat it here for `xrun` as RE is not used here...
nslsii.configure_kafka_publisher(xrun, "xpd")

# robot command
xrun.register_command('load_sample', _load_sample)
xrun.register_command('unload_sample', _unload_sample)

if bt:
    xrun.beamtime = bt

HOME_DIR = glbl['home']
BASE_DIR = glbl['base']

print('INFO: Initializing the XPD data acquisition environment\n')
if os.path.isdir(HOME_DIR):
    os.chdir(HOME_DIR)
else:
    os.chdir(BASE_DIR)

from xpdacq.calib import *

# analysis functions, only at beamline
#from xpdan.data_reduction import *

print('OK, ready to go.  To continue, follow the steps in the xpdAcq')
print('documentation at http://xpdacq.github.io/xpdacq\n')


class MoreCustomizedRunEngine(CustomizedRunEngine):
    def __call__(self, plan, *args, **kwargs):
        super().__call__({}, plan, *args, **kwargs)


from nslsii import configure_kafka_publisher
from bluesky.utils import ts_msg_hook

RE = MoreCustomizedRunEngine(None)  # This object is like 'xrun', but with the RE API.
# RE.msg_hook = ts_msg_hook

configure_kafka_publisher(RE, beamline_name='xpd')
RE.md.update(md)

# insert header to db, either simulated or real
RE.subscribe(db.insert, "all")
RE.beamtime = bt
RE.clear_suspenders()
