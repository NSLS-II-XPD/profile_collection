from ophyd.userapi.scan_api import Scan, AScan, DScan, Count

ascan = AScan()
ascan.default_triggers = [em_cnt]
ascan.default_detectors = [em_ch1, em_ch2, em_ch3, em_ch4]
dscan = DScan()

# Use ct as a count which is a single scan.

ct = Count()
