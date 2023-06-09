from stimpack.experiment import server

class BaseServer(server.BaseServer):
    def __init__(self, screens=[], loco_class=None, loco_kwargs={}, daq_class=None, daq_kwargs={}):
        super().__init__(screens=screens, loco_class=loco_class, loco_kwargs=loco_kwargs, daq_class=daq_class, daq_kwargs=daq_kwargs)
    