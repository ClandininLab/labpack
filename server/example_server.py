from stimpack.visual_stim.screen import Screen, SubScreen
from base_server import BaseServer

class ExampleServer(BaseServer):
    def __init__(self, visual_stim_kwargs={}, loco_class=None, loco_kwargs={}, daq_class=None, daq_kwargs={}):
        super().__init__(visual_stim_kwargs=visual_stim_kwargs, 
                         loco_class=loco_class, loco_kwargs=loco_kwargs, 
                         daq_class=daq_class, daq_kwargs=daq_kwargs)

def create_subscreen(name):
    if name == 'aux':
        viewport_ll = (-1.0, -1.0)
        viewport_width  = 2
        viewport_height = 2
    elif name == 'another_aux':
        viewport_ll = (-1.0, -1.0)
        viewport_width  = 2 
        viewport_height =1 
    else:
        raise ValueError('Invalid subscreen name.')

    return SubScreen(viewport_ll=viewport_ll, viewport_width=viewport_width, viewport_height=viewport_height)

def main():
    # Define screen(s) for the rig. 
    aux_screen      = Screen(subscreens=[create_subscreen('aux')],         x_display=None, display_index=0,
                             fullscreen=False, vsync=True, square_size=(0.25, 0.25))
    another_screen  = Screen(subscreens=[create_subscreen('another_aux')], x_display=None, display_index=1,
                             fullscreen=False, vsync=True, square_size=(0.25, 0.25))
    visual_stim_kwargs = {'screens': [aux_screen, another_screen]}

    # Initialize server object, inheriting BaseServer. Define locomotion and daq classes and kwargs as desired.
    server = ExampleServer(visual_stim_kwargs=visual_stim_kwargs, 
                           loco_class=None, loco_kwargs={}, 
                           daq_class=None, daq_kwargs={})

    # Register any server-side functions to be called from the client.
    server.register_function_on_root(lambda: print("Hello, Server! From Client"), "hello_server")

    # Start the server loop.
    server.loop()

if __name__ == '__main__':
    main()
