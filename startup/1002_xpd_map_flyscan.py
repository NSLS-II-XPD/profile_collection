"""Plan to run a XRD map "fly-scan" over a large sample."""
import uuid

import numpy as np
import itertools
import bluesky.preprocessors as bpp
import bluesky.plan_stubs as bps
from bluesky.utils import short_uid

import bluesky_darkframes
from ophyd import Signal


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