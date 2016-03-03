# Configure bluesky default detectors with this:
# These are the new "default detectors"
gs.DETS = [em]
gs.TABLE_COLS.append('em_chan21')
gs.PLOT_Y = 'em_chan21'
gs.TEMP_CONTROLLER = cs700
gs.TH_MOTOR = th
gs.TTH_MOTOR = tth


import time as ttime
# We probably already have these imports, but we use them below
# so I'm importing here to be sure.
from databroker import DataBroker as db, get_events

# 
from bluesky.broker_callbacks import verify_files_saved, post_run
gs.RE.subscribe('stop', post_run(verify_files_saved))


# Alternatively,
# gs.RE(my_scan, verify_files_accessible)
# or
# ct(verify_files_accessible)
