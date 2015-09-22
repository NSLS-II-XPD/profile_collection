from __future__ import print_function
import six

import logging

from ophyd.controls import EpicsSignal
from ophyd.controls.signal import SignalGroup


class GasSwitcher(SignalGroup):
    '''Base class for Gas Switcher'''

    def __init__(self, *args, **kwargs):
        super(GasSwitcher, self).__init__(*args, **kwargs)

    def current_pos(self):
        pass

    def requested_pos(self):
        pass


class XPDGasSwitcher(GasSwitcher):
    def __init__(self, requested_pos=None, current_pos=None, gasdict = {}):
       GasSwitcher.__init__(self)
       signals = [EpicsSignal(current_pos, rw=False, alias='_current_pos',
                              name='current_gas'),
                  EpicsSignal(requested_pos, alias='_requested_pos',
                              name='requested_gas'),
                  ]
       self._gasdict = gasdict
       for sig in signals:
           self.add_signal(sig)
       return


    @property
    def current_pos(self):
        return self._current_pos.value

    @property
    def current_gas(self):
        return self._gasdict[self.current_pos]

    @property
    def requested_gas(self):
        return self._gasdict[self.requested_pos]

    @property
    def requested_pos(self):
        return self._requested_pos.value


    @requested_pos.setter
    def requested_pos(self, val):
        self._requested_pos.value = val
        return


    def define_gas(self, gas, n):
        self._gasdict[n] = gas
        return


    def print_gasses(self):
        print('Gas positions are defined as follows:')
        print('-------------------------------------')
        for k, v in self._gasdict.items():
            print(k, '-', v)
        print('-------------------------------------')
        print('switch(\'gas\') -> switch to \'gas\'')
        print('define_gas(\'gas\', n) -> define \'gas\' to be at position n')
        return


    def switch(self, newgas):
        if not newgas in self._gasdict.values():
            print(gas, 'has not been defined.')
            return
        gas_nums = [n for n, gas in self._gasdict.items() if gas == newgas]
        if len(gas_nums) > 1:
            print('Error: more than one position has been defined for this gas')
            return
        self.requested_pos = gas_nums[0]
        return


    def print_curr_gas(self):
        print('Current gas is:')
        print(self._gasdict[self.current_pos])
        return

    @property
    def lookup(self):
        return {str(k): v for k, v in six.iteritems(self._gasdict)}
