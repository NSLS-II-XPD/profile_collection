from bluesky.plans import scan

assert pe1.connected
assert cs700.connected

RE(scan([pe1], cs700, 296, 300, 5), LiveTable([cs700]))
