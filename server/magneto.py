#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import matplotlib.pyplot as plt

from stimpack.visual_stim.screen import Screen, SubScreen

from base_server import BaseServer
# from lab_package.device.daq import LabJackTSeries
# from lab_package.device.loco_managers.fictrac_managers import FtClosedLoopManager

class MagnetoServer(BaseServer):
    def __init__(self, screens=[], loco_class=None, loco_kwargs={}, daq_class=None, daq_kwargs={}):
        super().__init__(screens=screens, loco_class=loco_class, loco_kwargs=loco_kwargs, daq_class=daq_class, daq_kwargs=daq_kwargs)

    def __set_up_daq__(self, daq_class, **kwargs):
        super().__set_up_daq__(daq_class, **kwargs)

        # if issubclass(daq_class, LabJackTSeries):
        #     self.manager.register_function_on_root(self.daq_device.setup_pulse_wave_stream_out, "daq_setup_pulse_wave_stream_out")
        #     self.manager.register_function_on_root(self.daq_device.start_stream, "daq_start_stream")
        #     self.manager.register_function_on_root(self.daq_device.stop_stream, "daq_stop_stream")
        #     self.manager.register_function_on_root(self.daq_device.stream_with_timing, "daq_stream_with_timing")

    def get_subscreens(dir):
        if dir == 'l':
            viewport_ll = (-1.0, -1.0)
            viewport_width  = 2
            viewport_height = 2
            pa = (-14, -7, -2)
            pb = (0, 10, -2)
            pc = (-14, -7, 10)
        elif dir == 'r':
            viewport_ll = (-1.0, -1.0)
            viewport_width  = 2
            viewport_height = 2
            pa = (0, 10, -2)
            pb = (14, -7, -2)
            pc = (0, 10, 10)
        elif dir == 'aux':
            viewport_ll = (-1.0, -1.0)
            viewport_width  = 2
            viewport_height = 2
            pa = (-4, -2, -2)
            pb = (0, 4, -2)
            pc = (-4, -2, 2)
        else:
            raise ValueError('Invalid direction.')
        return SubScreen(pa=pa, pb=pb, pc=pc, viewport_ll=viewport_ll, viewport_width=viewport_width, viewport_height=viewport_height)

def main():
    left_screen = Screen(subscreens=[MagnetoServer.get_subscreens('l')], server_number=2, id=2, fullscreen=True, vsync=True, square_size=(0.1, 0.1), square_loc=(-0.9, -0.9), name='Left', horizontal_flip=False)
    right_screen = Screen(subscreens=[MagnetoServer.get_subscreens('r')], server_number=2, id=1, fullscreen=True, vsync=False, square_size=(0.1, 0.1), square_loc=(0.9, 0.9), name='Right', horizontal_flip=False)
    aux_screen = Screen(subscreens=[MagnetoServer.get_subscreens('aux')], server_number=2, id=0, fullscreen=False, vsync=False, square_size=(0.1, 0.1), square_loc=(-1, -1), name='Aux', horizontal_flip=False)

    screens = [left_screen, right_screen, aux_screen]

    # draw_screens(screens); plt.show()

    # loco_class = FtClosedLoopManager
    # loco_kwargs = {
    #     'host':          '127.0.0.1', 
    #     'port':          33334, 
    #     'ft_bin':           "/home/clandinin/src/fictrac211/bin/fictrac",
    #     'ft_config':        "/home/clandinin/src/fictrac211/config2x2.txt", 
    #     'ft_theta_idx':     16, 
    #     'ft_x_idx':         14, 
    #     'ft_y_idx':         15, 
    #     'ft_frame_num_idx': 0, 
    #     'ft_timestamp_idx': 21
    # }
    # daq_class = LabJackTSeries
    # daq_kwargs = {'dev':"470022145", 'trigger_channel':["FIO4", "FIO5", "FIO6"]}
    
    server = MagnetoServer(screens = screens)#, loco_class=loco_class, loco_kwargs=loco_kwargs, daq_class=daq_class, daq_kwargs=daq_kwargs)
    server.loop()

if __name__ == '__main__':
    main()
