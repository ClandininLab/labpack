from labpack.protocol import base_protocol
import cv2
from stimpack.experiment import protocol
from stimpack.visual_stim.util import generate_lowercase_barcode

class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method


# %% # # # SIMPLE SYNTHETIC STIMS # # # # # # # # #
class MovieFilePixMap(BaseProtocol,  protocol.SharedPixMapProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_protocol_parameters['memname'] = generate_lowercase_barcode(10)

        filepath = self.protocol_parameters['filepath']
        cap = cv2.VideoCapture(filepath)
        ret,frame = cap.read()

        frame_shape = frame.shape

        self.epoch_shared_pixmap_stim_parameters = {'name': 'StreamMovie',
                                                    'memname': self.epoch_protocol_parameters['memname'],
                                                    'filepath': self.protocol_parameters['filepath'],
                                                    'nominal_frame_rate': self.epoch_protocol_parameters['frame_rate'],
                                                    'duration': self.epoch_protocol_parameters['stim_time'],
                                                    'start_frame': self.epoch_protocol_parameters['start_frame']}

        self.epoch_stim_parameters = {'name': 'PixMap',
                                      'memname': self.epoch_protocol_parameters['memname'],
                                      'frame_size': frame_shape,
                                      'rgb_texture': True,
                                      'width': self.epoch_protocol_parameters['angular_width'],
                                      'radius': self.epoch_protocol_parameters['render_radius'],
                                      'n_steps': self.epoch_protocol_parameters['render_n_steps'],
                                      'surface': self.epoch_protocol_parameters['render_surface'],
                                      'rotation': self.epoch_protocol_parameters['rotation']}


    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 4.0,
                'tail_time': 1.0,
                'start_frame': 1000,
                'angular_width': 360,
                'filepath': '/home/dennis/Videos/jcw.mp4', 
                'frame_rate': 50.0,
                'render_n_steps': 32,
                'render_surface': 'spherical', # cylindrical, cylindrical_with_phi
                'render_radius': 1,
                'rotation': 280
               }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 1,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

class WhiteNoisePixMap(BaseProtocol, protocol.SharedPixMapProtocol):
    """
    Drifting square wave grating, painted on a cylinder
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_protocol_parameters['memname'] = generate_lowercase_barcode(10)
        # print(f"Created memname: {self.epoch_protocol_parameters['memname']}")

        frame_shape = (int(self.epoch_protocol_parameters['boxes_h']), int(self.epoch_protocol_parameters['boxes_w']), 3)

        self.epoch_shared_pixmap_stim_parameters = {'name': 'WhiteNoise',
                                                    'memname': self.epoch_protocol_parameters['memname'],
                                                    'frame_shape': frame_shape,
                                                    'nominal_frame_rate': self.epoch_protocol_parameters['frame_rate'],
                                                    'dur': self.epoch_protocol_parameters['stim_time'],
                                                    'seed': self.epoch_protocol_parameters['seed']}

        self.epoch_stim_parameters = {'name': 'PixMap',
                                      'memname': self.epoch_protocol_parameters['memname'],
                                      'frame_size': frame_shape,
                                      'rgb_texture': True,
                                      'width': self.epoch_protocol_parameters['angular_width'],
                                      'radius': self.epoch_protocol_parameters['render_radius'],
                                      'n_steps': self.epoch_protocol_parameters['render_n_steps'],
                                      'surface': self.epoch_protocol_parameters['render_surface'],
                                      'rotation': 280}


    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 4.0,
                'tail_time': 1.0,
                'angular_width': 280,
                'boxes_w': 280,
                'boxes_h': 140,
                'frame_rate': 10.0,
                'seed': 37,
                'render_n_steps': 32,
                'render_surface': 'spherical', # cylindrical, cylindrical_with_phi
                'render_radius': 1,
                'rotation': 280
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 1,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}


class DriftingSquareGrating(BaseProtocol):
    """
    Drifting square wave grating, painted on a cylinder
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()
        
        center = self.adjust_center(self.epoch_protocol_parameters['center'])
        centerX = center[0]
        centerY = center[1]

        self.epoch_stim_parameters = {'name': 'RotatingGrating',
                                      'period': self.epoch_protocol_parameters['period'],
                                      'rate': self.epoch_protocol_parameters['rate'],
                                      'color': [1, 1, 1, 1],
                                      'mean': self.epoch_protocol_parameters['mean'],
                                      'contrast': self.epoch_protocol_parameters['contrast'],
                                      'angle': self.epoch_protocol_parameters['angle'],
                                      'offset': 0.0,
                                      'cylinder_radius': 1,
                                      'cylinder_height': 10,
                                      'profile': 'square',
                                      'theta': centerX,
                                      'phi': centerY}

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 4.0,
                'tail_time': 1.0,
                
                'period': 20.0,
                'rate': 20.0,
                'contrast': 1.0,
                'mean': 0.5,
                'angle': [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0],
                'center': (0, 0),
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

# %%

class MovingPatch(BaseProtocol):
    """
    Moving patch, either rectangular or elliptical. Moves along a spherical or cylindrical trajectory
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        # Create flystim epoch parameters dictionary
        self.epoch_stim_parameters = self.get_moving_patch_parameters(center=self.epoch_protocol_parameters['center'],
                                                                angle=self.epoch_protocol_parameters['angle'],
                                                                speed=self.epoch_protocol_parameters['speed'],
                                                                width=self.epoch_protocol_parameters['width_height'][0],
                                                                height=self.epoch_protocol_parameters['width_height'][1],
                                                                color=self.epoch_protocol_parameters['intensity'])

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 3.0,
                'tail_time': 1.0,
                
                'ellipse': True,
                'width_height': [(5, 5), (10, 10), (15, 15), (20, 20), (25, 25), (30, 30)],
                'intensity': 0.0,
                'center': (0, 0),
                'speed': 80.0,
                'angle': 0.0,
                'render_on_cylinder': False,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

class SyncPulse(BaseProtocol):
    """
    Drifting square wave grating, painted on a cylinder
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()
        
        self.epoch_stim_parameters = {'name': 'SyncPulse',
                                      'color': [1.0, 1.0, 1.0, 1.0]}


    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 1.0,
                'tail_time': 1.0,
                'color': [1, 1, 1, 1]}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 5,
                'idle_color': 0.0,
                'all_combinations': True,
                'randomize_order': True}
