import logging
from databroker import DataBroker as db


from bluesky.standard_config import *
from ophyd.commands import *

gs.RE.md['owner'] = 'xf28id1'
gs.RE.md['group'] = 'XPD'
gs.RE.md['beamline_id'] = 'xpd'


import bluesky.qt_kicker
bluesky.qt_kicker.install_qt_kicker()
