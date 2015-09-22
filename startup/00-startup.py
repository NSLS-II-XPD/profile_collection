import logging
session_mgr._logger.setLevel(logging.INFO)
from ophyd.userapi import *
from dataportal import (DataBroker as db,
                        StepScan as ss, DataBroker,
                        StepScan, DataMuxer)
