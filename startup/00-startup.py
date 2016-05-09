import logging

# Import these things for convenience.
from databroker import DataBroker as db, get_images, get_table, get_events
# 0304 test
from databroker import process
import ophyd
from ophyd.commands import *
# install callback trampoline
setup_ophyd()
from bluesky.standard_config import *

gs.RE.md['owner'] = 'xf28id1'
gs.RE.md['group'] = 'XPD'
gs.RE.md['beamline_id'] = 'xpd'

# This makes the plots update live.
import bluesky.qt_kicker
bluesky.qt_kicker.install_qt_kicker()
del bluesky.qt_kicker
