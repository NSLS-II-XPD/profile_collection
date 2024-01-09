"""Plan to run a XRD map "fly-scan" over a large sample."""
import datetime
import pprint
import time as ttime
import uuid

import numpy as np
import itertools
import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
import bluesky.plans as bp
from bluesky.utils import short_uid

import bluesky_darkframes
from ophyd import Signal
from ophyd.status import Status


# vendored, simplified, and made public from bluesky_darkframes
class SnapshotShell:
    """
    Shell to hold snapshots
    This enables us to hot-swap Snapshot instances in the middle of a Run.
    We hand this object to the RunEngine, so it sees one consistent
    instance throughout the Run.
    """

    def __init__(self):
        self.__snapshot = None

    def set_snaphsot(self, snapshot):
        self.__snapshot = snapshot

    def __getattr__(self, key):
        return getattr(self.__snapshot, key)


def _extarct_motor_pos(mtr):
    ret = yield from bps.read(mtr)
    if ret is None:
        return None
    return next(
        itertools.chain(
            (ret[k]["value"] for k in mtr.hints.get("fields", [])),
            (v["value"] for v in ret.values()),
        )
    )


def xrd_map(
    dets,
    shutter,
    fly_motor,
    fly_start,
    fly_stop,
    fly_pixels,
    step_motor,
    step_start,
    step_stop,
    step_pixels,
    dwell_time,
    *,
    dark_plan=None,
    md=None,
    backoff=0,
    snake=True,
):
    """
    Collect a 2D XRD map by "flying" in one direction.
    Parameters
    ----------
    dets : List[OphydObj] area_det is the xpd_configuration['area_det']
    shutter : Movable  xpd: fs
        Assumed to have "Open" and "Close" as the commands
        open : bps.mv(fs, -20)
        close: bps.mv(fs, 20)
    fly_motor : Movable
       The motor that will be moved continuously during collection
       (aka "flown")
    fly_start, fly_stop : float
       The start and stop position of the "fly" direction
    fly_pixels : int
       The target number of pixels in the "fly" direction
    step_motor : Movable
       The "slow" axis
    step_start, stop_stop : float
       The first and last position for the slow direction
    step_pixels : int
       How many pixels in the slow direction
    dwell_time : float
       How long in s to dwell in each pixel.  combined with *fly_pixels*
       this will be used to compute the motor velocity
    dark_plan : Plan or None
       The expected signature is ::
          def dp(det : Detector, shell : SnapshotShell):
             ...
        It only needs to handle one detector and is responsible for generating
        the messages to generate events.  The logic of _if_ a darkframe should
        be taken is handled else where.
    md : Optional[Dict[str, Any]]
       User-supplied meta-data
    backoff : float
       How far to move beyond the fly dimensions to get up to speed
    snake : bool
       If we should "snake" or "typewriter" the fly axis
    """
    # TODO input validation
    # rename here to use better internal names (!!)
    req_dwell_time = dwell_time
    del dwell_time
    acq_time = glbl['frame_acq_time']


    plan_args_cache = {
        k: v
        for k, v in locals().items()
        if k not in ("dets", "fly_motor", "step_motor", "dark_plan", "shutter")
    }

    (ad,) = (d for d in dets if hasattr(d, "cam"))
    (num_frame, acq_time, computed_dwell_time) = yield from configure_area_det(
        ad, req_dwell_time,acq_time
    )
    #(num_frame, acq_time, computed_dwell_time) = yield from _configure_area_det(
    #    req_dwell_time)
    # set up metadata

    sp = {
        "time_per_frame": acq_time,
        "num_frames": num_frame,
        "requested_exposure": req_dwell_time,
        "computed_exposure": computed_dwell_time,
        "type": "ct",
        "uid": str(uuid.uuid4()),
        "plan_name": "map_scan",
    }
    _md = {
        "detectors": [det.name for det in dets],
        "plan_args": plan_args_cache,
        "map_size": (fly_pixels, step_pixels),
        "hints": {},
        "sp": sp,
        "extents": [(fly_start, fly_stop), (step_stop, step_start)],
        **{f"sp_{k}": v for k, v in sp.items()},
    }
    _md.update(md or {})
    _md["hints"].setdefault(
        "dimensions",
        [((f"start_{fly_motor.name}",), "primary"), ((step_motor.name,), "primary")],
    )
    #_md["hints"].setdefault(
    #    "extents", [(fly_start, fly_stop), (step_stop, step_start)],
    #)

    # soft signal to use for tracking pixel edges
    # TODO put better metadata on these
    px_start = Signal(name=f"start_{fly_motor.name}", kind="normal")
    px_stop = Signal(name=f"stop_{fly_motor.name}", kind="normal")

    # TODO either think more carefully about how to compute this
    # or get the gating working below.
    #current_fly_motor_speed=fly_motor.velocity.get()
    speed = abs(fly_stop - fly_start) / (fly_pixels * computed_dwell_time)
    print(speed)
    shell = SnapshotShell()

    @bpp.reset_positions_decorator([fly_motor.velocity])
    @bpp.set_run_key_decorator(f"xrd_map_{uuid.uuid4()}")
    @bpp.stage_decorator(dets)
    @bpp.run_decorator(md=_md)
    def inner():
        _fly_start, _fly_stop = fly_start, fly_stop
        _backoff = backoff

        # yield from bps.mv(fly_motor.velocity, speed)
        for step in np.linspace(step_start, step_stop, step_pixels):
            yield from bps.checkpoint()
            # TODO maybe go to a "move velocity here?
            yield from bps.mv(fly_motor.velocity, 10)
            pre_fly_group = short_uid("pre_fly")
            yield from bps.abs_set(step_motor, step, group=pre_fly_group)
            yield from bps.abs_set(
                fly_motor, _fly_start - _backoff, group=pre_fly_group
            )

            # take the dark while we might be waiting for motor movement
            if dark_plan:
                #yield from bps.mv(shutter, "Close")
                yield from bps.mv(shutter, 20)
                yield from bps.sleep(0.5)
                yield from dark_plan(ad, shell)
            # wait for the pre-fly motion to stop
            yield from bps.wait(group=pre_fly_group)
            #yield from bps.mv(shutter, "Open")
            yield from bps.mv(shutter, -20)
            yield from bps.sleep(0.5)
            yield from bps.mv(fly_motor.velocity, speed)
            fly_group = short_uid("fly")
            yield from bps.abs_set(fly_motor, _fly_stop + _backoff, group=fly_group)
            # TODO gate starting to take data on motor position
            for j in range(fly_pixels):
                print(time.time())
                fly_pixel_group = short_uid("fly_pixel")
                for d in dets:
                    yield from bps.trigger(d, group=fly_pixel_group)

                # grab motor position right after we trigger
                start_pos = yield from _extarct_motor_pos(fly_motor)
                yield from bps.mv(px_start, start_pos)
                # wait for frame to finish
                yield from bps.wait(group=fly_pixel_group)

                # grab the motor position
                stop_pos = yield from _extarct_motor_pos(fly_motor)
                yield from bps.mv(px_stop, stop_pos)
                # generate the event
                yield from bps.create("primary")
                for obj in dets + [px_start, px_stop, step_motor]:
                    yield from bps.read(obj)
                yield from bps.save()
                print(time.time)
            yield from bps.checkpoint()
            #yield from bps.mv(shutter, "Close")
            yield from bps.mv(shutter, 20)
            yield from bps.wait(group=fly_group)
            yield from bps.checkpoint()
            if snake:
                # if snaking, flip these for the next pass through
                _fly_start, _fly_stop = _fly_stop, _fly_start
                _backoff = -_backoff

    yield from inner()


def dark_plan(detector, shell, *, stream_name="dark"):
    # Restage to ensure that dark frames goes into a separate file.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)

    # The `group` parameter passed to trigger MUST start with
    # bluesky-darkframes-trigger.
    grp = short_uid("bluesky-darkframes-trigger")
    yield from bps.trigger(detector, group=grp)
    yield from bps.wait(grp)
    yield from bps.read(detector)
    snapshot = bluesky_darkframes.SnapshotDevice(detector)
    shell.set_snaphsot(snapshot)

    # emit the event to the dark stream
    yield from bps.stage(shell)
    yield from bps.trigger_and_read(
        [shell], name=stream_name,
    )
    yield from bps.unstage(shell)

    # Restage.
    yield from bps.unstage(detector)
    yield from bps.stage(detector)


import itertools
from collections import deque
from pathlib import Path
from event_model import compose_resource


class XPDFlyer:
    def __init__(self, det, motor, motor_start, motor_stop, name="XPDFlyer", stats_key="stats1", **kwargs):
        self.name = name

        self.det = det
        self.motor = motor
        self.motor_start = motor_start
        self.motor_stop = motor_stop
        self.stats_key = stats_key

        # Objects needed for the bluesky documents generation:
        self._asset_docs_cache = None
        self._resource_document = None
        self._datum_factory = None

    def get_images_counter(self):
        return self.det.cam.num_images_counter.get()

    def kickoff(self):
        print("Kickoff method")
        self._asset_docs_cache = deque()
        self._counter = itertools.count()

        # Used for events generation:
        self._datum_docs = deque()
        self._det_stats = deque()
        self._motor_positions = deque()
        self._timestamps = deque()

        # Unstage the detector first from previous potential failure, then stage the detector:
        self.det.unstage()
        self.det.stage()

        # We need the following information as in the document stream produced by bp.count([det]):

        # ('resource',
        # {'spec': 'AD_TIFF',
        # 'root': '/nsls2/data/xpd-new/legacy/raw',
        # 'resource_path': 'pe1_data/2023/06/20',
        # 'resource_kwargs': {
        #   'template': '%s%s_%6.6d.tiff',
        #   'filename': '69e4ea31-849c-49cd-836e',
        #   'frame_per_point': 1},
        # 'path_semantics': 'posix',
        # 'uid': '63c5d72f-c393-47a8-a028-ff89ed3e5ccb',
        # 'run_start': 'a6ecf54d-ab06-4ed3-bf07-68a03d194380'})
        #
        # ('datum',
        # {'datum_id': '63c5d72f-c393-47a8-a028-ff89ed3e5ccb/0',
        # 'datum_kwargs': {'point_number': 0},
        # 'resource': '63c5d72f-c393-47a8-a028-ff89ed3e5ccb'})

        # Initial "done" status for the detector:
        self._trigger_status = Status()
        self._trigger_status.set_finished()

        # For Resource doc:
        self._filestore_spec = self.det.tiff.filestore_spec  # string

        self._root_dir = str(self.det.tiff.reg_root)  # pathlib.Path object
        self._resource_path = str(Path(self.det.tiff.read_path_template).relative_to(self._root_dir))

        ## For resource_kwargs:
        self._file_template = self.det.tiff.file_template.get()
        self._file_name = self.det.tiff.file_name.get()
        self._frame_per_point = self.det.cam.num_exposures.get()

        # For Datum doc:
        self._file_number = self.det.tiff.file_number.get()

        # Optional parameters:
        self._file_write_status = self.det.tiff.write_file.get(as_string=True)  # e.g., 'Done'

        # Prepare 'resource' factory.

        date = datetime.datetime.now()
        resource_path = date.strftime(self._resource_path)
        self._resource_document, self._datum_factory, _ = compose_resource(
            start={"uid": "needed for compose_resource() but will be discarded"},
            spec=self._filestore_spec,
            root=self._root_dir,
            resource_path=resource_path,
            resource_kwargs=dict(
                template=self._file_template,
                filename=self._file_name,
                frame_per_point=self._frame_per_point,
            ),
        )
        # now discard the start uid, a real one will be added later
        self._resource_document.pop("run_start")
        self._asset_docs_cache.append(("resource", self._resource_document))

        # Move the motor to the start position in a blocking fashion.
        # Then, start moving the motor to the stop position and subscribe the watch function.
        st = self.motor.move(self.motor_start)
        # Example of 'st':
        #   MoveStatus(done=True, pos=sample_x, elapsed=9.3, success=True, settle_time=0.0)

        self.motor_status = self.motor.set(self.motor_stop)

        return st  # it should have the 'done' status already

    def _watch(self, *args, **kwargs):
        print(args)
        print(kwargs)
        if self._trigger_status.done:
            self._timestamps.append(self._now())

            self._trigger_status = self.det.trigger()
            self._det_stats.append(getattr(self.det, self.stats_key).total.get())

            datum_document = self._datum_factory(datum_kwargs={"point_number": next(self._counter)})
            self._asset_docs_cache.append(("datum", datum_document))
            self._datum_docs.append(datum_document)

            print(f"\ndatum_document:\n{datum_document}")

            if "current" in kwargs:
                motor_pos = kwargs["current"]
            else:
               # Final callback does not have the 'current' field, using the motor_stop value:
               motor_pos = self.motor_stop
            self._motor_positions.append(motor_pos)

    def complete(self):
        print("Complete method")

        self.motor_status.watch(self._watch)

        return self.motor_status

    def _now(self):
        return ttime.time()

    def collect(self):
        print("Collect method")

        self.det.unstage()

        self._resource_document = None
        self._datum_factory = None

        for i, (motor_pos, datum_doc, det_stat, timestamp) in enumerate(zip(self._motor_positions, self._datum_docs, self._det_stats, self._timestamps)):
            print(f"{i:02d}  motor_pos={motor_pos}  datum_doc={datum_doc}  det_stat={det_stat}  timestamp={timestamp}")
            data_dict = {
                f"{self.det.name}_image": datum_doc["datum_id"],
                f"{getattr(self.det, self.stats_key).total.name}": det_stat,
                f"{self.motor.name}": motor_pos,
            }

            filled_dict = {}
            for key in data_dict:
                if key == f"{self.det.name}_image":
                    # We need to fill the detector image data via RunRouter:
                    filled = False
                else:
                    # We do not need to fill the other readings (i.e., motor positions, etc.):
                    filled = True
                filled_dict[key] = filled

            yield {
                "data": data_dict,
                "timestamps": {key: timestamp for key in data_dict},
                "time": timestamp,
                "filled": filled_dict,
            }

    def describe_collect(self):
        print("Descrbe_collect method")
        # TODO: implement
        return_dict = {"primary": {k: v for k, v in self.det.describe().items()
                                   if k in [f"{self.det.name}_image",
                                            f"{getattr(self.det, self.stats_key).total.name}",
                                            ]}}
        return_dict["primary"].update({k: v for k, v in self.motor.describe().items()
                                       if k == f"{self.motor.name}"})

        return return_dict

    def collect_asset_docs(self):
        items = list(self._asset_docs_cache)
        self._asset_docs_cache.clear()
        for item in items:
            yield item


# Example of a flyer object:
#   xpd_flyer = XPDFlyer(pe2c, sample_x, 8, 80)

def fly_stream(flyers, *, md=None, stream=False, return_payload=True):
    """
    Perform a fly scan with one or more 'flyers'.

    Parameters
    ----------
    flyers : collection
        objects that support the flyer interface
    md : dict, optional
        metadata

    Yields
    ------
    msg : Msg
        'kickoff', 'wait', 'complete, 'wait', 'collect' messages

    See Also
    --------
    :func:`bluesky.preprocessors.fly_during_wrapper`
    :func:`bluesky.preprocessors.fly_during_decorator`
    """
    uid = yield from bps.open_run(md)
    for flyer in flyers:
        yield from bps.kickoff(flyer, wait=True)
    for flyer in flyers:
        yield from bps.complete(flyer, wait=True)
    for flyer in flyers:
        yield from bps.collect(flyer, stream=stream, return_payload=return_payload)
    yield from bps.close_run()
    return uid


def step_and_fly(step_motor, step_start, step_stop, step_num_steps, det, fly_motor, fly_start, fly_stop):
    """Perform 2-D scan with a step scan in one dimension and fly scan in another one.

    Example of execution:

        RE(step_and_fly(sample_y, 17, 20, 3, pe2c, sample_x, 8, 80))

    Args:
        step_motor (_type_): _description_
        step_start (_type_): _description_
        step_stop (_type_): _description_
        step_num_steps (_type_): _description_
        det (_type_): _description_
        fly_motor (_type_): _description_
        fly_start (_type_): _description_
        fly_stop (_type_): _description_

    Yields:
        _type_: _description_
    """

    # TODO: add dark frame collection here - will result in a separate run/uid.

    for i, step_pos in enumerate(np.linspace(step_start, step_stop, step_num_steps)):
        yield from bps.mv(step_motor, step_pos)
        if i % 2 == 0:
            start = fly_start
            stop = fly_stop
        else:
            start = fly_stop
            stop = fly_start
        xpd_flyer = XPDFlyer(det, fly_motor, start, stop)
        yield from fly_stream([xpd_flyer], stream=True, return_payload=True)


# from pdfstream.callbacks.analysis import AnalysisConfig, AnalysisStream
# ac = AnalysisConfig()
# ac.read(os.path.expanduser("~/.pdfstream/xpd_server_xpd_beamline.ini"))
# anstr = AnalysisStream(config=ac)


# In [6]: hdr = db["1851deea-56dc-4678-8ddd-22ff3b3d7548"]

# In [7]: hdr = db[-1]

# In [8]: for name, doc in hdr.documents(fill=True):
#    ...:     print(name)
#    ...:     anstr(name, doc)
#    ...:
# start
# [10/06/2023 05:23:16 PM] Receive the start of '20b45453-a4ba-48a8-a39e-4862cae02c70'.
# [10/06/2023 05:23:17 PM] Read the calibration data in the start.
# descriptor
# [10/06/2023 05:23:17 PM] Find the data key 'pe2_image' in the stream 'primary'.
# resource
# datum
# datum
# datum
# datum
# datum
# datum
# event
# [10/06/2023 05:23:17 PM] Start processing the event 1.
# [10/06/2023 05:23:20 PM] Save the PDF data in '/nsls2/data/xpd-new/legacy/processed/xpdUser/tiff_base/Setup' using file name 'Setup_20231006-172247_20b454_0001'.
# [10/06/2023 05:23:20 PM] Finish processing the event 1.
# event
# [10/06/2023 05:23:20 PM] Start processing the event 2.
# [10/06/2023 05:23:21 PM] Save the PDF data in '/nsls2/data/xpd-new/legacy/processed/xpdUser/tiff_base/Setup' using file name 'Setup_20231006-172247_20b454_0002'.
# [10/06/2023 05:23:21 PM] Finish processing the event 2.
# event
# [10/06/2023 05:23:21 PM] Start processing the event 3.
# [10/06/2023 05:23:23 PM] Save the PDF data in '/nsls2/data/xpd-new/legacy/processed/xpdUser/tiff_base/Setup' using file name 'Setup_20231006-172247_20b454_0003'.
# [10/06/2023 05:23:23 PM] Finish processing the event 3.
# event
# [10/06/2023 05:23:23 PM] Start processing the event 4.
# [10/06/2023 05:23:24 PM] Save the PDF data in '/nsls2/data/xpd-new/legacy/processed/xpdUser/tiff_base/Setup' using file name 'Setup_20231006-172247_20b454_0004'.
# [10/06/2023 05:23:24 PM] Finish processing the event 4.
# event
# [10/06/2023 05:23:24 PM] Start processing the event 5.
# [10/06/2023 05:23:25 PM] Save the PDF data in '/nsls2/data/xpd-new/legacy/processed/xpdUser/tiff_base/Setup' using file name 'Setup_20231006-172247_20b454_0005'.
# [10/06/2023 05:23:25 PM] Finish processing the event 5.
# event
# [10/06/2023 05:23:25 PM] Start processing the event 6.
# [10/06/2023 05:23:27 PM] Save the PDF data in '/nsls2/data/xpd-new/legacy/processed/xpdUser/tiff_base/Setup' using file name 'Setup_20231006-172247_20b454_0006'.
# [10/06/2023 05:23:27 PM] Finish processing the event 6.
# stop
# [10/06/2023 05:23:27 PM] Receive the stop of '20b45453-a4ba-48a8-a39e-4862cae02c70'.

# In [9]: hdr.table()
# Out[9]:
#                                  time                               pe2_image  pe2_stats1_total    sample_x
# seq_num
# 1       2023-10-06 21:22:49.411360025  c0be55e2-8b2e-4cd1-b12f-94e99019fb3c/0      6.432940e+09  104.014375
# 2       2023-10-06 21:22:49.639249563  c0be55e2-8b2e-4cd1-b12f-94e99019fb3c/1      6.430192e+09  105.136875
# 3       2023-10-06 21:22:49.883318186  c0be55e2-8b2e-4cd1-b12f-94e99019fb3c/2      6.428717e+09  107.088750
# 4       2023-10-06 21:22:50.205786467  c0be55e2-8b2e-4cd1-b12f-94e99019fb3c/3      6.430590e+09  109.677188
# 5       2023-10-06 21:22:50.420942545  c0be55e2-8b2e-4cd1-b12f-94e99019fb3c/4      6.429063e+09  111.392500
# 6       2023-10-06 21:22:50.684250593  c0be55e2-8b2e-4cd1-b12f-94e99019fb3c/5      6.432263e+09  113.457500

