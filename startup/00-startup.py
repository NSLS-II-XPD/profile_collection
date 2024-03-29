# Make ophyd listen to pyepics.
import nslsii
import ophyd.signal
import logging

logger = logging.getLogger("startup_profile")

logger.warning("I'm loading the startup profile")

try:
    from bluesky_queueserver import is_re_worker_active
except ImportError:
    # TODO: delete this when 'bluesky_queueserver' is distributed as part of collection environment
    def is_re_worker_active():
        return False

ophyd.signal.EpicsSignal.set_defaults(connection_timeout=5)
# See docstring for nslsii.configure_base() for more details
# this command takes away much of the boilerplate for settting up a profile
# (such as setting up best effort callbacks etc)

if not is_re_worker_active():
    nslsii.configure_base(get_ipython().user_ns, 'xpd', pbar=True, bec=True,
                        magics=True, mpl=True, epics_context=False,
                        publish_documents_with_kafka=True)
else:
    nslsii.configure_base(dict(), 'xpd', configure_logging=True, publish_documents_with_kafka=True)


# #### Test config for Kafka
# from bluesky import RunEngine
# from databroker import Broker
# from bluesky.callbacks.best_effort import BestEffortCallback

# RE = RunEngine({})
# db = Broker.named("xpd")
# bec = BestEffortCallback()

# RE.subscribe(db.insert)
# RE.subscribe(bec)
# res = nslsii.configure_kafka_publisher(RE, beamline_name="xpd")



# At the end of every run, verify that files were saved and
# print a confirmation message.
from bluesky.callbacks.broker import verify_files_saved, post_run
# RE.subscribe(post_run(verify_files_saved, db), 'stop')

# Uncomment the following lines to turn on verbose messages for
# debugging.
# import logging
# ophyd.logger.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)


RE.md['facility'] = 'NSLS-II'
RE.md['group'] = 'XPD'
RE.md['beamline_id'] = '28-ID-2'

import subprocess


def show_env():
    # this is not guaranteed to work as you can start IPython without hacking
    # the path via activate
    proc = subprocess.Popen(["conda", "list"], stdout=subprocess.PIPE)
    out, err = proc.communicate()
    a = out.decode('utf-8')
    b = a.split('\n')
    print(b[0].split('/')[-1][:-1])
