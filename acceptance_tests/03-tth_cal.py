from bluesky.plans import scan

# the 'em' reports not connected because many channels are not implemented
assert em.channels.chan22.connected
assert sc.channels.chan1.connected
assert tth_cal.connected


RE(scan([em, sc, pe1], tth_cal, 0, 1, 5), LiveTable([tth_cal, 'em_chan22', sc, pe1]))
