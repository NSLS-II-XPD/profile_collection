from ophyd import Signal, EpicsSignalWithRBV, Component as Cpt
from ophyd.areadetector import ADBase, ADComponent as ADCpt
from ophyd import QuadEM
from nslsii.ad33 import StatsPluginV33


class QuadEMPort(ADBase):
    port_name = Cpt(Signal, value="")

    def __init__(self, port_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port_name.put(port_name)


class ESMQuadEM(QuadEM):
    conf = Cpt(QuadEMPort, port_name="EM180")
    em_range = Cpt(EpicsSignalWithRBV, "Range", string=True)

    current1 = ADCpt(StatsPluginV33, 'Current1:')
    current2 = ADCpt(StatsPluginV33, 'Current2:')
    current3 = ADCpt(StatsPluginV33, 'Current3:')
    current4 = ADCpt(StatsPluginV33, 'Current4:')
    sum_all = ADCpt(StatsPluginV33, 'SumAll:')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stage_sigs.update([(self.acquire_mode, "Single")])  # single mode
        self.configuration_attrs = [
            "integration_time",
            "averaging_time",
            "em_range",
            "num_averaged",
            "values_per_read",
        ]

    def set_primary(self, n, value=None):
        name_list = []
        if "All" in n:
            for k in self.read_attrs:
                getattr(self, k).kind = "normal"
            return

        for channel in n:
            cur = getattr(self, f"current{channel}")
            cur.kind |= Kind.normal
            cur.mean_value = Kind.hinted


qem1 = ESMQuadEM("XF:28IDC-BI{IM:02}EM180:", name="qem1")
for det in [qem1]:
    det.read_attrs = ['current2', 'current2.mean_value']
_
