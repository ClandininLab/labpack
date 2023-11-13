#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: mhturner
"""

from labpack.protocol import base_protocol


class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

# %% Some simple visual stimulus protocol classes

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

        # Create stimpack.visual_stim epoch parameters dictionary
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

#### Set server_options['visual_stim_module_paths'] in example_config.yaml, then uncomment below.
# class MovingEllipsoid(BaseProtocol):
#     def __init__(self, cfg):
#         super().__init__(cfg)
        
#         self.run_parameters = self.get_run_parameter_defaults()
#         self.protocol_parameters = self.get_protocol_parameter_defaults()
    
#     def get_epoch_parameters(self):
#         super().get_epoch_parameters()

#         stim_time = self.epoch_protocol_parameters['stim_time']
        
#         x_trajectory = {'name': 'TVPairs',
#                         'tv_pairs': [(0, -2), (stim_time, 2)],
#                         'kind': 'linear'}
#         y_trajectory = {'name': 'TVPairs',
#                         'tv_pairs': [(0, 4), (stim_time, 6)],
#                         'kind': 'linear'}
#         z_trajectory = {'name': 'TVPairs',
#                         'tv_pairs': [(0, -2), (stim_time, 2)],
#                         'kind': 'linear'}

#         yaw_trajectory = {'name': 'TVPairs',
#                             'tv_pairs': [(0, 0), (stim_time, 90*stim_time)],
#                             'kind': 'linear'}
#         pitch_trajectory   = {'name': 'TVPairs',
#                             'tv_pairs': [(0, 0), (stim_time, 90*stim_time)],
#                             'kind': 'linear'}
#         roll_trajectory = {'name': 'TVPairs',
#                             'tv_pairs': [(0, 0), (stim_time, 0)],
#                             'kind': 'linear'}

#         self.epoch_stim_parameters = {'name': 'MovingEllipsoid',
#                             'x_length': self.epoch_protocol_parameters['dimensions'][0],
#                             'y_length': self.epoch_protocol_parameters['dimensions'][1],
#                             'z_length': self.epoch_protocol_parameters['dimensions'][2],
#                             'color': self.epoch_protocol_parameters['color'],
#                             'x': x_trajectory,
#                             'y': y_trajectory,
#                             'z': z_trajectory,
#                             'yaw': yaw_trajectory, 
#                             'pitch': pitch_trajectory,
#                             'roll': roll_trajectory,
#                             'n_subdivisions': 6}
            
#     def get_protocol_parameter_defaults(self):
#         return {'pre_time': 0.5,
#                 'stim_time': 4.0,
#                 'tail_time': 0.5,
                
#                 'dimensions': (2,1,1),
#                 'color': None,
#                 }

#     def get_run_parameter_defaults(self):
#         return {'num_epochs': 2,
#                 'idle_color': 0.5,
#                 'all_combinations': True,
#                 'randomize_order': True}
