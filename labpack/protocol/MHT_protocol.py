#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: mhturner
"""

from labpack.protocol import base_protocol
import numpy as np
import stimpack.rpc
import pandas as pd
from stimpack.visual_stim.util import get_rgba

class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

# %% # # # SIMPLE SYNTHETIC STIMS # # # # # # # # #

class DriftingSquareGrating(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

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
                                 'theta': self.screen_center[0]}

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

class LoomingSpot(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        # adjust center to screen center
        adj_center = self.adjust_center(self.epoch_protocol_parameters['center'])

        r_traj = {'name': 'LoomGabb',
                  'rv_ratio': self.epoch_protocol_parameters['rv_ratio'] / 1e3, # msec -> sec
                  'collision_time': self.epoch_protocol_parameters['collision_time'],
                  'end_radius': self.epoch_protocol_parameters['end_radius']}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                 'radius': r_traj,
                                 'sphere_radius': 1,
                                 'color': self.epoch_protocol_parameters['intensity'],
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1,
                'stim_time': 3,
                'tail_time': 1.0,

                'intensity': 0.0,
                'center': (0, 0),
                'collision_time': 2.5,
                'end_radius': 45.0,
                'rv_ratio': [10.0, 20.0, 40.0, 80.0],  # msec
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 75,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}



class MovingRectangle(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_stim_parameters = self.get_moving_patch_parameters(color=self.epoch_protocol_parameters['intensity'])

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 3.0,
                'tail_time': 1.0,

                'width': 5.0,
                'height': 50.0,
                'intensity': [0.0, 1.0],
                'center': (0, 0),
                'speed': 80.0,
                'angle': [0.0, 180.0],
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 40,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}

class MovingSpot(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_stim_parameters = self.get_moving_spot_parameters(radius=self.epoch_protocol_parameters['diameter']/2,
                                                             color=self.epoch_protocol_parameters['intensity'],
                                                             distance_to_travel=180)

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 3.0,
                'tail_time': 1.0,

                'diameter': [5, 10, 15, 20, 25, 30],
                'intensity': [0.0, 1.0],
                'center': (0, 0),
                'speed': [80.0],
                'angle': 0.0,
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 70,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}
class BarOnGrating(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        patch_parameters = self.get_moving_patch_parameters(speed = self.epoch_protocol_parameters['bar_speed'],
                                                            width = self.epoch_protocol_parameters['bar_width'],
                                                            height = self.epoch_protocol_parameters['bar_height'],
                                                            color = self.epoch_protocol_parameters['bar_color'],
                                                            distance_to_travel = 180,
                                                            render_on_cylinder=True)


        grate_parameters = {'name': 'RotatingGrating',
                            'period': self.epoch_protocol_parameters['grate_period'],
                            'rate': self.epoch_protocol_parameters['grate_rate'],
                            'color': [1, 1, 1, 1],
                            'mean': self.run_parameters['idle_color'],
                            'contrast': self.epoch_protocol_parameters['grate_contrast'],
                            'angle': self.epoch_protocol_parameters['angle'],
                            'offset': 0.0,
                            'cylinder_radius': 1.1,
                            'cylinder_height': 20,
                            'profile': 'sine',
                            'theta': self.screen_center[0]}

        self.epoch_stim_parameters = (grate_parameters, patch_parameters)

    def load_stimuli(self, manager, multicall=None):
        grate_parameters = self.epoch_stim_parameters[0].copy()
        patch_parameters = self.epoch_stim_parameters[1].copy()

        bg = self.run_parameters.get('idle_color')
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(manager)
        multicall.target('visual').load_stim(**grate_parameters, hold=True)
        multicall.target('visual').load_stim(**patch_parameters, hold=True)
        multicall()

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 10.0,
                'tail_time': 1.0,

                'center': (0, 0),
                'bar_width': 10.0,
                'bar_height': 180.0,
                'bar_color': 0.0,
                'bar_speed': [5, 15, 25, 35],
                'grate_period': 20.0,
                'grate_rate': [-30, -20, -10, 0, 10, 20, 30],  # Note weird thing about stim params is that - grate rate corresponds to + bar speed
                'grate_contrast': 0.5,
                'angle': 0.0,
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 140,  # 28 combos x 5 each
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}


# %%

class SphericalCheckerboardWhiteNoise(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)


    def get_epoch_parameters(self):
        super().get_epoch_parameters()
        adj_center = self.adjust_center(self.protocol_parameters['center'])

        start_seed = int(np.random.choice(range(int(1e6))))

        distribution_data = {'name': 'Ternary',
                             'rand_min': self.epoch_protocol_parameters['rand_min'],
                             'rand_max': self.epoch_protocol_parameters['rand_max']}

        self.epoch_stim_parameters = {'name': 'RandomGridOnSphericalPatch',
                                 'patch_width': self.epoch_protocol_parameters['patch_size'],
                                 'patch_height': self.epoch_protocol_parameters['patch_size'],
                                 'width': self.epoch_protocol_parameters['grid_width'],
                                 'height': self.epoch_protocol_parameters['grid_height'],
                                 'start_seed': start_seed,
                                 'update_rate': self.epoch_protocol_parameters['update_rate'],
                                 'distribution_data': distribution_data,
                                 'theta': adj_center[0],
                                 'phi': adj_center[1]}

        self.epoch_protocol_parameters['start_seed'] = start_seed

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 2.0,
                'stim_time': 10.0,
                'tail_time': 2.0,

                'patch_size': 5.0,
                'update_rate': 20.0,
                'rand_min': 0.0,
                'rand_max': 1.0,
                'grid_width': 60,
                'grid_height': 60,
                'center': [0.0, 0.0]}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 10,
                'idle_color': 0.5}
# %%


class PanGlomSuite(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

        self.stim_list = ['LoomingSpot', 'MovingSpot', 'MovingRectangle', 'DriftingSquareGrating']
        n = [4, 3, 1, 1]  # weight each stim draw by how many trial types it has
        avg_per_stim = int(self.run_parameters['num_epochs'] / np.sum(n))
        all_stims = [[self.stim_list[i]] * n[i] * avg_per_stim for i in range(len(n))]

        self.stim_order = np.random.permutation(np.hstack(all_stims))


    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        stim_type = str(self.stim_order[self.num_epochs_completed])
        adj_center = self.adjust_center(self.epoch_protocol_parameters['center'])

        self.epoch_protocol_parameters['component_stim_type'] = stim_type

        if stim_type == 'LoomingSpot':
            r_traj = {'name': 'LoomGabb',
                    'rv_ratio': self.epoch_protocol_parameters['loom_rv_ratio'] / 1e3, # msec -> sec
                    'collision_time': self.epoch_protocol_parameters['loom_collision_time'],
                    'end_radius': self.epoch_protocol_parameters['loom_end_radius']}

            self.epoch_stim_parameters = {'name': 'MovingSpot',
                                    'radius': r_traj,
                                    'sphere_radius': 1,
                                    'color': self.epoch_protocol_parameters['loom_intensity'],
                                    'theta': adj_center[0],
                                    'phi': adj_center[1]}
        elif stim_type == 'MovingSpot':
            self.epoch_stim_parameters = self.get_moving_spot_parameters(radius=self.epoch_protocol_parameters['spot_diameter']/2,
                                                             color=self.epoch_protocol_parameters['spot_intensity'],
                                                             angle=self.epoch_protocol_parameters['spot_angle'],
                                                             speed=self.epoch_protocol_parameters['spot_speed'],
                                                             distance_to_travel=180)
        elif stim_type == 'MovingRectangle':
            self.epoch_stim_parameters = self.get_moving_patch_parameters(color=self.epoch_protocol_parameters['bar_intensity'],
                                                                          width=self.epoch_protocol_parameters['bar_width'],
                                                                          height=self.epoch_protocol_parameters['bar_height'],
                                                                          speed=self.epoch_protocol_parameters['bar_speed'],
                                                                          angle=self.epoch_protocol_parameters['bar_angle'],
                                                                          )
            
        elif stim_type == 'DriftingSquareGrating':
            self.epoch_stim_parameters = {'name': 'RotatingGrating',
                                 'period': self.epoch_protocol_parameters['grating_period'],
                                 'rate': self.epoch_protocol_parameters['grating_rate'],
                                 'color': [1, 1, 1, 1],
                                 'mean': self.run_parameters.get('idle_color'),
                                 'contrast': self.epoch_protocol_parameters['grating_contrast'],
                                 'angle': self.epoch_protocol_parameters['grating_angle'],
                                 'offset': 0.0,
                                 'cylinder_radius': 1,
                                 'cylinder_height': 10,
                                 'profile': 'square',
                                 'theta': self.screen_center[0]}


    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.5,
                'stim_time': 4.0,
                'tail_time': 1.5,
                'center': (0, 0),

                'loom_intensity': 0.0,
                'loom_collision_time': 2.5,
                'loom_end_radius': 45.0,
                'loom_rv_ratio': [10.0, 20.0, 40.0, 80.0],  # msec

                'spot_diameter': [10, 20, 40],
                'spot_intensity': [0.0],
                'spot_speed': [80.0],
                'spot_angle': 0.0,

                'bar_width': 5.0,
                'bar_height': 50.0,
                'bar_intensity': 0.0,
                'bar_speed': 80.0,
                'bar_angle': 0.0,

                'grating_angle': 180.0,
                'grating_period': 20.0,
                'grating_rate': 20.0,
                'grating_contrast': 1.0,
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 90,  # 90 = 9 * 10 averages each
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}


# %% Courtship-inspired stims

class MovingPatch(BaseProtocol):
    """
    Moving patch, either rectangular or elliptical. Moves along a spherical or cylindrical trajectory.
    Stim_time can be set by distance or by time.
    Opto, closed-loop options available.
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

        if self.run_parameters['set_time_by_distance']:
            self.protocol_parameters['stim_time'] = 0
        else:
            self.protocol_parameters['distance_to_travel'] = 0

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        if self.run_parameters['set_time_by_distance']:
            stim_time = self.epoch_protocol_parameters['distance_to_travel'] / abs(self.epoch_protocol_parameters['velocity'])
            self.epoch_protocol_parameters['stim_time'] = stim_time
        else:
            stim_time = self.epoch_protocol_parameters['stim_time']

        # Create stimpack.visual_stim epoch parameters dictionary
        self.epoch_stim_parameters = self.get_moving_patch_parameters(center=self.epoch_protocol_parameters['center'],
                                                                angle=self.epoch_protocol_parameters['angle'],
                                                                speed=self.epoch_protocol_parameters['velocity'],
                                                                width=self.epoch_protocol_parameters['width_height'][0],
                                                                height=self.epoch_protocol_parameters['width_height'][1],
                                                                color=self.epoch_protocol_parameters['color'])

        # opto
        self.epoch_protocol_parameters['opto_stim_time'] = self.epoch_protocol_parameters['stim_time'] + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']
        # Make pulse width half of period (50% duty cycle for a given freq)
        self.epoch_protocol_parameters['opto_pulse_width'] = (1 / self.epoch_protocol_parameters['opto_freq']) / 2
    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)

        if self.epoch_protocol_parameters['do_opto'] == 'True':

            # set up opto pulse wave
            multicall.target('daq').setup_pulse_wave_stream_out(output_channel='DAC0',
                                                freq=self.epoch_protocol_parameters['opto_freq'],
                                                amp=self.epoch_protocol_parameters['opto_amp'],
                                                pulse_width=self.epoch_protocol_parameters['opto_pulse_width'],
                                                scanRate=5000)
            multicall.target('daq').stream_with_timing(pre_time=self.epoch_protocol_parameters['opto_pre_time'],
                                        stim_time=self.epoch_protocol_parameters['opto_stim_time'],
                                        scanRate=5000, scansPerRead=1000)

        super().load_stimuli(client, multicall)


    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 1.0,
                'tail_time': 1.0,
                'loco_pos_closed_loop': 0,
                'center': (0, 0),

                'ellipse': True,
                'width_height': [(10, 7.14), (20, 14.29), (40, 28.57), (80, 57.14)],
                'color': 0.0,
                'distance_to_travel': 120,
                'velocity': [15, 30, 60, 120],
                'angle': 0.0,
                'render_on_cylinder': False,

                'do_opto': ['True', 'False'],
                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,

                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 160,
                'idle_color': 0.5,
                'set_time_by_distance': True,
                'all_combinations': True,
                'randomize_order': True}

# %%

class OptoPulseTrain(BaseProtocol):
    """

    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        # Create stimpack.visual_stim epoch parameters dictionary
        self.epoch_stim_parameters = {}

        # Make pulse width half of period (50% duty cycle for a given freq)
        self.epoch_protocol_parameters['opto_pulse_width'] = (1 / self.epoch_protocol_parameters['opto_freq']) / 2

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)

        if self.epoch_protocol_parameters['do_opto'] is True:

            bg = self.run_parameters.get('idle_color')
            multicall.target('visual').load_stim('ConstantBackground', color=get_rgba(bg), hold=True)

            # set up opto pulse wave
            multicall.target('daq').setup_pulse_wave_stream_out(output_channel='DAC0',
                                                freq=self.epoch_protocol_parameters['opto_freq'],
                                                amp=self.epoch_protocol_parameters['opto_amp'],
                                                pulse_width=self.epoch_protocol_parameters['opto_pulse_width'],
                                                scanRate=5000)
            multicall.target('daq').stream_with_timing(pre_time=self.epoch_protocol_parameters['pre_time'],
                                        stim_time=self.epoch_protocol_parameters['stim_time'],
                                        scanRate=5000, scansPerRead=1000)

            multicall()

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 2.0,
                'stim_time': 8.0,
                'tail_time': 2.0,
                'do_opto': True,
                'opto_freq': 50.0,
                'opto_amp': [0.5, 1.0, 2.0, 3.0, 4.0, 5.0],  # ~linear from 0-5. Cyclical after 5. E.g. 6 ~ 1
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 60,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}



class CourtshipDotSnippet(BaseProtocol):
    """

    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()



    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        adj_center = self.adjust_center(self.epoch_protocol_parameters['center'])

        fps = 30.03
        df = pd.read_pickle(self.epoch_protocol_parameters['trajectory_path'])

        current_angular_size = df.iloc[0, :][self.epoch_protocol_parameters['trajectory_index']]  # deg
        current_angular_speed = df.iloc[1, :][self.epoch_protocol_parameters['trajectory_index']]  # deg/sec

        time_steps = np.arange(0, len(current_angular_size)) / fps # time steps of update trajectory
        radius = current_angular_size / 2   # deg. Diam -> radius

        current_angular_speed = current_angular_speed / fps  # deg/sec -> deg/frame for cumsum
        position = adj_center[0] + np.cumsum(current_angular_speed) #  deg along azimuth

        self.epoch_protocol_parameters['stim_time'] = time_steps[-1]

        radius_traj = {'name': 'TVPairsBounded',
                       'tv_pairs': list(zip(time_steps, radius)),
                       'kind': 'linear',
                       'fill_value': 'extrapolate',
                       'bounds': None}

        theta_traj = {'name': 'TVPairsBounded',
                      'tv_pairs': list(zip(time_steps, position)),
                      'kind': 'linear',
                      'fill_value': 'extrapolate',
                      'bounds': [adj_center[0]-90, adj_center[0]+90]}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': theta_traj,
                                      'phi': adj_center[1]}

        # opto
        self.epoch_protocol_parameters['opto_stim_time'] = self.epoch_protocol_parameters['stim_time'] + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']
        # Make pulse width half of period (50% duty cycle for a given freq)
        self.epoch_protocol_parameters['opto_pulse_width'] = (1 / self.epoch_protocol_parameters['opto_freq']) / 2

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)

        if self.epoch_protocol_parameters['do_opto'] == 'True':

            # set up opto pulse wave
            multicall.target('daq').setup_pulse_wave_stream_out(output_channel='DAC0',
                                                freq=self.epoch_protocol_parameters['opto_freq'],
                                                amp=self.epoch_protocol_parameters['opto_amp'],
                                                pulse_width=self.epoch_protocol_parameters['opto_pulse_width'],
                                                scanRate=5000)
            multicall.target('daq').stream_with_timing(pre_time=self.epoch_protocol_parameters['opto_pre_time'],
                                        stim_time=self.epoch_protocol_parameters['opto_stim_time'],
                                        scanRate=5000, scansPerRead=1000)

        super().load_stimuli(client, multicall)

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 2.0,
                'stim_time': 3.0,
                'tail_time': 2.0,

                'center': (0, 0),
                'color': 0.0,
                'trajectory_index': [0, 1, 2, 3, 4],
                'trajectory_path': r'C:\Users\User\Documents\GitHub\clandinin_labpack\resources\courtship_traj_20230630.pkl',

                'do_opto': ['True', 'False'],
                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,

                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 50,
                'idle_color': 0.5,
                'randomize_order': True,
                'all_combinations': True}



# %% VR stims

class Tower2Choice(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        #TODO: end trial if fly gets close to tower

        reference_xside = np.random.choice([-1, 1])

        if self.epoch_protocol_parameters['fixed_cue'] == 'size':
            self.epoch_protocol_parameters['fix_parallax_cue'] = False
            self.epoch_protocol_parameters['fix_size_cue'] = True

        elif self.epoch_protocol_parameters['fixed_cue'] == 'parallax':
            self.epoch_protocol_parameters['fix_parallax_cue'] = True
            self.epoch_protocol_parameters['fix_size_cue'] = False

        elif self.epoch_protocol_parameters['fixed_cue'] == 'none':
            self.epoch_protocol_parameters['fix_parallax_cue'] = False
            self.epoch_protocol_parameters['fix_size_cue'] = False

        else:
            print('Unrecognized value for param fixed_cue')
            self.epoch_protocol_parameters['fix_parallax_cue'] = False
            self.epoch_protocol_parameters['fix_size_cue'] = False


        # reference location: fixed distance
        reference_location = [reference_xside * self.epoch_protocol_parameters['x_offset'],
                              self.epoch_protocol_parameters['reference_distance'],
                              self.epoch_protocol_parameters['z_level']+self.protocol_parameters['cylinder_height']/2]
        
        reference_cylinder_parameters = {'name': 'FixedDepthCueTower',
                                      'color': self.epoch_protocol_parameters['cylinder_color'],
                                      'cylinder_radius': self.epoch_protocol_parameters['cylinder_radius'], 
                                      'cylinder_height': self.epoch_protocol_parameters['cylinder_height'],
                                      'n_faces': 16,
                                      'cylinder_location': reference_location,
                                      'fix_size_cue': bool(self.epoch_protocol_parameters['fix_size_cue']),
                                      'fix_parallax_cue': bool(self.epoch_protocol_parameters['fix_parallax_cue'])
                                      }
        
        # test location: varied distance. Put it at -1 * the xoffset of the reference tower
        test_location = [-reference_xside * self.epoch_protocol_parameters['x_offset'],
                         self.epoch_protocol_parameters['test_distance'],
                         self.epoch_protocol_parameters['z_level']+self.protocol_parameters['cylinder_height']/2]
        
        if bool(self.epoch_protocol_parameters['fix_size_cue']):
            # Change the test radius so the initial angular size is the same as the reference tower
            reference_distance = np.sqrt(np.sum(np.array(reference_location)**2, axis=0))  # fly starts at [0, 0, 0]
            reference_angular_halfsize = np.arctan(self.epoch_protocol_parameters['cylinder_radius'] / reference_distance)  # radians

            test_distance = np.sqrt(np.sum(np.array(test_location)**2, axis=0))
            test_radius = test_distance * np.tan(reference_angular_halfsize)
        else:
            test_radius = self.epoch_protocol_parameters['cylinder_radius']


        test_cylinder_parameters = {'name': 'FixedDepthCueTower',
                                      'color': self.epoch_protocol_parameters['cylinder_color'],
                                      'cylinder_radius': test_radius, 
                                      'cylinder_height': self.epoch_protocol_parameters['cylinder_height'],
                                      'n_faces': 16,
                                      'cylinder_location': test_location,
                                      'fix_size_cue': bool(self.epoch_protocol_parameters['fix_size_cue']),
                                      'fix_parallax_cue': bool(self.epoch_protocol_parameters['fix_parallax_cue'])
                                      }
    

        self.epoch_stim_parameters = (reference_cylinder_parameters, test_cylinder_parameters)

        self.epoch_protocol_parameters['current_test_location'] = test_location
        self.epoch_protocol_parameters['current_reference_location'] = reference_location

    def load_stimuli(self, manager, multicall=None):
        test_parameters = self.epoch_stim_parameters[0].copy()
        ref_parameters = self.epoch_stim_parameters[1].copy()

        bg = self.run_parameters.get('idle_color')
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(manager)
        multicall.target('visual').load_stim('ConstantBackground', color=get_rgba(bg), hold=True)
        multicall.target('visual').load_stim(**test_parameters, hold=True)
        multicall.target('visual').load_stim(**ref_parameters, hold=True)
        multicall()
        
    def get_protocol_parameter_defaults(self):
        return {
                'loco_pos_closed_loop': 1,
                'pre_time': 2.0,
                'stim_time': 20.0,
                'tail_time': 2.0,

                'cylinder_color': (0, 0, 0, 1),
                'reference_distance': 0.5,  # m, fixed
                'test_distance': [0.25, 0.5, 1.0],  # m, varies
                'x_offset': 0.05,  # m
                'z_level': -0.5,
                'cylinder_radius': 0.01, 
                'cylinder_height': 1.0,

                'fixed_cue': ['size', 'parallax', 'none'],
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 40,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True,
               'do_loco': True}


class TowerWorld(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        current_seed = self.epoch_protocol_parameters['start_seed'] + self.num_epochs_completed
        np.random.seed(int(current_seed))

        cylinder_locations = []
        for tree in range(int(self.epoch_protocol_parameters['n_towers'])):
            cylinder_locations.append([np.random.uniform(-0.5, 0.5), np.random.uniform(-0.5, 0.5), self.epoch_protocol_parameters['z_level']+self.protocol_parameters['cylinder_height']/2])
        
        self.epoch_stim_parameters = {'name': 'Forest',
                                      'color': self.epoch_protocol_parameters['cylinder_color'],
                                      'cylinder_radius': self.epoch_protocol_parameters['cylinder_radius'], 
                                      'cylinder_height': self.epoch_protocol_parameters['cylinder_height'],
                                      'n_faces': 16,
                                      'cylinder_locations': cylinder_locations,
                                      }
        
        self.epoch_protocol_parameters['current_seed'] = current_seed

    def get_protocol_parameter_defaults(self):
        return {
                'loco_pos_closed_loop': 0,
                'pre_time': 1.0,
                'stim_time': 4.0,
                'tail_time': 1.0,

                'cylinder_color': (0, 0, 0, 1),
                'n_towers': 20,
                'start_seed': 0,
                'z_level': -0.20,
                'cylinder_radius': 0.02, 
                'cylinder_height': 0.5,
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 40,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}


# %% DOTS stims

class DifferentialMotionDots(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        current_seed_1 = np.random.randint(0, 10000)
        dots_1_parameters = {'name': 'UniformMovingDotField_Cylindrical',
                             'n_points': int(self.epoch_protocol_parameters['n_points_each']),
                             'point_size': int(self.epoch_protocol_parameters['point_size']),
                             'cylinder_radius': 1.0,
                             'color': self.epoch_protocol_parameters['intensity'],
                             'speed': self.epoch_protocol_parameters['speed_1'],
                             'direction': self.epoch_protocol_parameters['direction'],
                             'random_seed': current_seed_1,
                             'phi_limits': self.epoch_protocol_parameters['phi_limits']}

        current_seed_2 = np.random.randint(0, 10000)
        dots_2_parameters = dots_1_parameters.copy()
        dots_2_parameters['cylinder_radius'] = 1.1
        dots_2_parameters['speed'] = self.epoch_protocol_parameters['speed_2']
        dots_2_parameters['random_seed'] = current_seed_2

        self.epoch_stim_parameters = (dots_1_parameters, dots_2_parameters)

        self.epoch_protocol_parameters['current_seed_1'] = current_seed_1
        self.epoch_protocol_parameters['current_seed_2'] = current_seed_2

    def load_stimuli(self, manager, multicall=None):
        dots_1_parameters = self.epoch_stim_parameters[0].copy()
        dots_2_parameters = self.epoch_stim_parameters[1].copy()

        bg = self.run_parameters.get('idle_color')
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(manager)

        multicall.target('visual').load_stim(name='ConstantBackground',
                        color=[bg, bg, bg, 1.0],
                        hold=True)
        multicall.target('visual').load_stim(**dots_1_parameters, hold=True)
        multicall.target('visual').load_stim(**dots_2_parameters, hold=True)
        multicall()

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.5,
                'stim_time': 4.5,
                'tail_time': 1.5,

                'n_points_each': 100,  # More than ~200 total causes frame drops on bruker
                'point_size': 60,  # width 80 = about 15 deg in center of bruker screen
                'intensity': 0.0,
                'speed_1': [5, 15, 25, 35],
                'speed_2': [-30, -20, -10, 0, 10, 20, 30],
                'direction': 0.0,
                'phi_limits': (90, 160),
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 140,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}
