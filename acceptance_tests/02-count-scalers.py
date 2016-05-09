from bluesky.plans import count 
from bluesky.callbacks import LiveTable

# the 'em' reports not connected because many channels are not implemented
assert em.channels.chan22.connected
assert sc.channels.chan1.connected


RE(count([em, sc]), LiveTable([em, sc]))
