# Make ophyd listen to pyepics.
import nslsii

# See docstring for nslsii.configure_base() for more details
# this command takes away much of the boilerplate for settting up a profile
# (such as setting up best effort callbacks etc)
nslsii.configure_base(
    get_ipython().user_ns,
    "xpd",
    pbar=True,
    bec=True,
    magics=True,
    mpl=True,
    epics_context=False,
)

del one_shot
del one_1d_step
del one_nd_step

# IMPORTANT : This is needed to read old data
try:
    # we need this on v0 databroker, but baked into configuration of v1, v2
    db.reg.set_root_map({"/direct/XF28ID1": "/direct/XF28ID2"})
except AttributeError:
    pass

# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved, post_run

# RE.subscribe(post_run(verify_files_saved, db), 'stop')

# Uncomment the following lines to turn on verbose messages for
# debugging.
# import logging
# ophyd.logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)


RE.md["facility"] = "NSLS-II"
RE.md["group"] = "XPD"
RE.md["beamline_id"] = "28-ID-2"

import subprocess


def show_env():
    # this is not guaranteed to work as you can start IPython without hacking
    # the path via activate
    proc = subprocess.Popen(["conda", "list"], stdout=subprocess.PIPE)
    out, err = proc.communicate()
    a = out.decode("utf-8")
    b = a.split("\n")
    print(b[0].split("/")[-1][:-1])
