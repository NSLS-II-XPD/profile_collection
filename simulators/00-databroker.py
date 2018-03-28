# simulator for databroker
from databroker import Broker

from databroker import temp_config

db = Broker.from_config(temp_config())

from bluesky import RunEngine


RE = RunEngine()
RE.subscribe(db.insert)




