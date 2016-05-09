from bluesky.plans import relative_inner_product_scan
from bluesky.callbacks import LiveTable

assert slt_mb2.connected

RE(relative_inner_product_scan([em], 5, slt_mb2.o, 0, 1, slt_mb2.i, 0, 1),
   LiveTable([slt_mb2.o, slt_mb2.i, em]))
