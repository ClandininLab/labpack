from stimpack.experiment import server

class BaseServer(server.BaseServer):
    def __init__(self, host='', port=60629, visual_stim_kwargs={}, loco_class=None, loco_kwargs={}, daq_class=None, daq_kwargs={}):
        super().__init__(host=host, port=port, 
                         visual_stim_kwargs=visual_stim_kwargs, 
                         loco_class=loco_class, loco_kwargs=loco_kwargs, 
                         daq_class=daq_class, daq_kwargs=daq_kwargs)
    