import logging
session_mgr._logger.setLevel(logging.INFO)
from dataportal import (DataBroker as db,
                        StepScan as ss, DataBroker,
                        StepScan, DataMuxer)


from bluesky.standard_config import *
from ophyd.commands import *

gs.RE.md['config'] = {}
gs.RE.md['owner'] = 'xf28id1'
gs.RE.md['group'] = 'XPD'
gs.RE.md['beamline_id'] = 'xpd'
