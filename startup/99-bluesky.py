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


def verify_files_accessible(name, doc):
    "This is a brute-force approach. We retrieve all the data."
    ttime.sleep(0.1)  # Wati for data to be saved.
    if name != 'stop':
        return
    print("  Verifying that run was saved to broker...")
    try:
        header = db[doc['run_start']]
    except Exception as e:
        print("  Verification Failed! Error: {0}".format(e))
        return
    else:
        print('\x1b[1A\u2713')
    print("  Verifying that all data is accessible on the disk...")
    try:
        list(get_events(header, fill=True))
    except Exception as e:
        print("  Verification Failed! Error: {0}".format(e))
    else:
        print('\x1b[1A\u2713')


gs.RE.subscribe('stop', verify_files_accessible)


# Alternatively,
# gs.RE(my_scan, verify_files_accessible)
# or
# ct(verify_files_accessible)
