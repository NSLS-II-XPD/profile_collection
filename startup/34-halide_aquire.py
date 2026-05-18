"""
Acquisition plan for the halide perovskite QueueserverAgent.

This plan follows the Blop AcquisitionPlan protocol signature::

    def __call__(suggestions, actuators, sensors, md=None) -> uid

It performs the full synthesis + measurement sequence for one optimization step,
mirroring the order of plans that synthesis_queue_xlsx previously submitted to
the queueserver queue:

1. Stop all pumps
2. Set pump infusion rates
3. Start pumps
4. Wait for flow equilibrium (hardware read via wait_equilibrium2)
5. Optionally start toluene dilution pump and wait
6. Collect absorbance spectra
7. Collect fluorescence spectra
8. Return the run UID

This file is loaded into the queueserver environment via startup. All devices
(qepro, LED, UV_shutter, pump objects) and helper plans (stop_group,
set_group_infuse2, start_group_infuse, wait_equilibrium2, sleep_sec_q) are
available as globals from earlier startup files.
"""

import bluesky.plan_stubs as bps
import bluesky.preprocessors as bpp


# ---------------------------------------------------------------------------
# Static configuration (physical setup — update per beamtime)
# ---------------------------------------------------------------------------

# Syringe sizes (mL) for each pump, in order matching DOF order
SYRINGE_LIST = [50, 50, 50]

# Syringe materials
SYRINGE_MATER_LIST = ["steel", "steel", "steel"]

# Target volumes (format: "value unit")
TARGET_VOL_LIST = ["30 ml", "30 ml", "30 ml"]

# Whether to auto-set target for each pump
SET_TARGET_LIST = [True, True, True]

# Rate unit
RATE_UNIT = "ul/min"

# Mixer tubing: single segment of 30 cm (matches historical xlsx config).
# Format matches what wait_equilibrium2 expects: "value unit".
MIXER_LENGTHS_CM = [30.0]

# Residence time multiplier (wait this many multiples of the residence time)
RESIDENT_T_RATIO = 1.0

# Number of absorbance and fluorescence spectra per measurement
NUM_ABS = 10
NUM_FLU = 10

# Precursor names (for metadata only)
PRECURSOR_LIST = ["CsPbOA", "TOABr", "ZnI2"]

# Post-dilution with toluene
POST_DILUTE = False
POST_DILUTE_RATIO = 1.0  # toluene rate = sum(active_rates) * ratio
POST_DILUTE_WAIT_SEC = 30  # wait time after starting toluene pump (seconds)

# Default mapping: DOF name -> pump device name in queueserver namespace
DOF_TO_PUMP = {
    "infusion_rate_CsPb": "dds2_p1",
    "infusion_rate_Br": "dds2_p2",
    "infusion_rate_I2": "dds3_p1",
    "infusion_rate_Cl": "dds1_p1",
    "infusion_rate_OAm": "dds1_p2",
}

# Toluene dilution pump device name
DILUTE_PUMP_NAME = "dds1_p2"


# ---------------------------------------------------------------------------
# Acquisition plan
# ---------------------------------------------------------------------------


def halide_acquire(
    suggestions: list[dict],
    actuators,
    sensors=None,
    md=None,
    *,
    syringe_list=None,
    syringe_mater_list=None,
    target_vol_list=None,
    set_target_list=None,
    rate_unit=None,
    mixer_lengths_cm=None,
    resident_t_ratio=None,
    num_abs=None,
    num_flu=None,
    precursor_list=None,
    post_dilute=None,
    post_dilute_ratio=None,
    post_dilute_wait_sec=None,
    dof_to_pump=None,
    dilute_pump_name=None,
):
    """Acquire UV-Vis data for halide perovskite optimization.

    Mirrors the plan sequence that synthesis_queue_xlsx previously submitted
    to the queueserver queue, now expressed as a single coherent Bluesky plan.

    Parameters
    ----------
    suggestions : list[dict]
        List of suggestions from the optimizer. Each dict contains DOF names
        as keys with their suggested values. Typically len == 1.
    actuators : list[str]
        Pump device names (may be empty if DOFs have no actuator field).
    sensors : list[str] | None
        Sensor device names (e.g., ["QEPro"]).
    md : dict | None
        Metadata dict (contains blop_correlation_uid for tracking).
    syringe_list : list[float] | None
        Syringe sizes in mL for each pump, in DOF order.
    syringe_mater_list : list[str] | None
        Syringe materials for each pump.
    target_vol_list : list[str] | None
        Target volumes (e.g. ``["30 ml", ...]``) for each pump.
    set_target_list : list[bool] | None
        Whether to auto-set the target volume for each pump.
    rate_unit : str | None
        Flow-rate unit string passed to ``set_group_infuse2``.
    mixer_lengths_cm : list[float] | None
        Lengths of mixer tubing segments in cm.
    resident_t_ratio : float | None
        Multiplier of the residence time to wait for equilibrium.
    num_abs : int | None
        Number of absorbance spectra to collect.
    num_flu : int | None
        Number of fluorescence spectra to collect.
    precursor_list : list[str] | None
        Precursor names stored in run metadata.
    post_dilute : bool | None
        Whether to perform toluene post-dilution.
    post_dilute_ratio : float | None
        Toluene rate = sum(active_rates) * ratio.
    post_dilute_wait_sec : float | None
        Seconds to wait after starting the toluene pump.
    dof_to_pump : dict[str, str] | None
        Mapping of DOF name → pump device name in the queueserver namespace.
    dilute_pump_name : str | None
        Device name of the toluene dilution pump.

    Yields
    ------
    Msg
        Bluesky messages.

    Returns
    -------
    str
        The UID of the Bluesky run.
    """
    # Resolve all configuration, falling back to module-level defaults
    syringe_list = syringe_list if syringe_list is not None else SYRINGE_LIST
    syringe_mater_list = (
        syringe_mater_list if syringe_mater_list is not None else SYRINGE_MATER_LIST
    )
    target_vol_list = (
        target_vol_list if target_vol_list is not None else TARGET_VOL_LIST
    )
    set_target_list = (
        set_target_list if set_target_list is not None else SET_TARGET_LIST
    )
    rate_unit = rate_unit if rate_unit is not None else RATE_UNIT
    mixer_lengths_cm = (
        mixer_lengths_cm if mixer_lengths_cm is not None else MIXER_LENGTHS_CM
    )
    resident_t_ratio = (
        resident_t_ratio if resident_t_ratio is not None else RESIDENT_T_RATIO
    )
    num_abs = num_abs if num_abs is not None else NUM_ABS
    num_flu = num_flu if num_flu is not None else NUM_FLU
    precursor_list = precursor_list if precursor_list is not None else PRECURSOR_LIST
    post_dilute = post_dilute if post_dilute is not None else POST_DILUTE
    post_dilute_ratio = (
        post_dilute_ratio if post_dilute_ratio is not None else POST_DILUTE_RATIO
    )
    post_dilute_wait_sec = (
        post_dilute_wait_sec
        if post_dilute_wait_sec is not None
        else POST_DILUTE_WAIT_SEC
    )
    dof_to_pump = dof_to_pump if dof_to_pump is not None else DOF_TO_PUMP
    dilute_pump_name = (
        dilute_pump_name if dilute_pump_name is not None else DILUTE_PUMP_NAME
    )

    suggestion = suggestions[0]

    # Extract rates from suggestion — DOF names like "infusion_rate_CsPb"
    dof_names = sorted(k for k in suggestion.keys() if k.startswith("infusion_rate"))
    rate_list = [float(suggestion[name]) for name in dof_names]

    # Resolve pump devices
    pump_list = _resolve_pumps_from_dofs(dof_names, dof_to_pump)

    sample_type = _make_sample_name(rate_list)

    # Build metadata
    _md = {
        "sample_type": sample_type,
        "infuse_rates": rate_list,
        "dof_names": dof_names,
        "precursors": precursor_list[: len(pump_list)],
        "pumps": [p.name for p in pump_list],
        "pump_status": [p.status.get() for p in pump_list],
        "detectors": ["qepro"],
    }
    _md.update(md or {})

    # --- Step 0: Stop all pumps ---
    yield from stop_group(pump_list)

    # --- Step 1: Set pump infusion rates ---
    yield from set_group_infuse2(
        syringe_list[: len(pump_list)],
        pump_list,
        set_target_list=set_target_list[: len(pump_list)],
        target_vol_list=target_vol_list[: len(pump_list)],
        rate_list=rate_list,
        syringe_mater_list=syringe_mater_list[: len(pump_list)],
        rate_unit=rate_unit,
    )

    # --- Step 2: Start pumps ---
    yield from start_group_infuse(pump_list, rate_list)

    # --- Step 3: Wait for equilibrium via hardware read ---
    mixer_pump_list = [[f"{mixer_lengths_cm[0]} cm", *pump_list]]
    yield from wait_equilibrium2(mixer_pump_list, ratio=resident_t_ratio)

    # --- Step 4: Optional toluene post-dilution ---
    if post_dilute:
        dilute_pump = _resolve_pumps([dilute_pump_name])[0]
        toluene_rate = sum(rate_list) * post_dilute_ratio
        print(
            f"\nStarted toluene dilution at {toluene_rate:.1f} uL/min, "
            f"waiting {post_dilute_wait_sec}s"
        )
        yield from set_group_infuse2(
            [50],
            [dilute_pump],
            set_target_list=[True],
            target_vol_list=["30 ml"],
            rate_list=[toluene_rate],
            syringe_mater_list=["steel"],
            rate_unit=rate_unit,
        )
        yield from sleep_sec_q(post_dilute_wait_sec)

    # --- Step 5: Collect absorbance + fluorescence in a single run ---
    uid = yield from _acquire_uvvis(_md, num_abs=num_abs, num_flu=num_flu)

    return uid


# ---------------------------------------------------------------------------
# UV-Vis collection
# ---------------------------------------------------------------------------


def _acquire_uvvis(md, *, num_abs=NUM_ABS, num_flu=NUM_FLU):
    """Collect absorbance and fluorescence spectra in a single Bluesky run.

    Produces two streams: 'absorbance' and 'fluorescence'.
    Mirrors xray_uvvis_plan2 (startup/32-bundle-plan.py) without the X-ray
    detector, including the hardware state guard before each mode switch.

    Parameters
    ----------
    md : dict
        Run metadata.
    num_abs : int
        Number of absorbance frames to collect.
    num_flu : int
        Number of fluorescence frames to collect.
    """

    @bpp.stage_decorator([qepro])
    @bpp.run_decorator(md=md)
    def _inner():
        # --- Absorbance ---
        if (
            LED.get() == "Low"
            and UV_shutter.get() == "High"
            and qepro.correction.get() == "Reference"
            and qepro.spectrum_type.get() == "Absorbtion"
        ):
            pass
        else:
            yield from bps.mv(
                qepro.correction,
                "Reference",
                qepro.spectrum_type,
                "Absorbtion",
            )
            yield from bps.mv(LED, "Low", UV_shutter, "High")
            yield from bps.sleep(2)

        for _ in range(num_abs):
            yield from bps.trigger(qepro, wait=True)
            yield from bps.create(name="absorbance")
            yield from bps.read(qepro)
            yield from bps.save()

        # --- Fluorescence ---
        if (
            LED.get() == "High"
            and UV_shutter.get() == "Low"
            and qepro.correction.get() == "Dark"
            and qepro.spectrum_type.get() == "Corrected Sample"
        ):
            pass
        else:
            yield from bps.mv(
                qepro.correction,
                "Dark",
                qepro.spectrum_type,
                "Corrected Sample",
            )
            yield from bps.mv(LED, "High", UV_shutter, "Low")
            yield from bps.sleep(2)

        for _ in range(num_flu):
            yield from bps.trigger(qepro, wait=True)
            yield from bps.create(name="fluorescence")
            yield from bps.read(qepro)
            yield from bps.save()

        # --- Lights off ---
        yield from bps.mv(LED, "Low", UV_shutter, "Low")

    return (yield from _inner())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample_name(rate_list):
    """Generate a sample name from pump rates."""
    parts = [f"{r:.1f}" for r in rate_list]
    return "_".join(parts)


def _resolve_pumps(pump_names):
    """Resolve pump device objects from their string names in the startup namespace."""
    pumps = []
    for name in pump_names:
        device = globals().get(name)
        if device is None:
            raise ValueError(f"Pump device '{name}' not found in queueserver namespace")
        pumps.append(device)
    return pumps


def _resolve_pumps_from_dofs(dof_names, dof_to_pump=None):
    """Map DOF names to pump devices via DOF_TO_PUMP mapping."""
    if dof_to_pump is None:
        dof_to_pump = DOF_TO_PUMP
    pump_names = []
    for dof in dof_names:
        pname = dof_to_pump.get(dof)
        if pname is None:
            raise ValueError(f"No pump mapping for DOF '{dof}'")
        pump_names.append(pname)
    return _resolve_pumps(pump_names)
