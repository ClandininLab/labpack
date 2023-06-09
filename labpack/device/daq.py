#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from stimpack.device import daq

import nidaqmx

# %% National instruments USB daqs
class NIUSB6001(daq.DAQ):
    """
    https://www.ni.com/en-us/support/model.usb-6001.html
    """
    def __init__(self, dev='Dev1', trigger_channel='port2/line0'):
        super().__init__()  # call the parent class init method
        self.dev = dev
        self.trigger_channel = trigger_channel

    def send_trigger(self):
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan('{}/{}'.format(self.dev, self.trigger_channel))
            task.start()
            task.write([True, False])

