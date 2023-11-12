from labpack.protocol import base_protocol
import numpy as np
import math
import pickle
from time import sleep
import stimpack.rpc.multicall

class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

# %% # # # SIMPLE SYNTHETIC STIMS # # # # # # # # #
class OcclusionShape(BaseProtocol):
    '''
    Occluder is defined by its shape (width and height, ellipse vs rectangle)
    '''
    
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        # Set variables for convenience
        obj_ellipse = self.epoch_protocol_parameters['obj_ellipse']
        obj_start_theta = self.epoch_protocol_parameters['obj_start_theta'] #negative value starts from the opposite side of obj direction
        obj_end_theta = self.epoch_protocol_parameters['obj_end_theta']
        obj_width = self.epoch_protocol_parameters['obj_wh'][0]
        obj_height = self.epoch_protocol_parameters['obj_wh'][1]
        obj_prime_color = self.epoch_protocol_parameters['obj_prime_color']
        obj_probe_color = self.epoch_protocol_parameters['obj_probe_color']
        obj_speed = self.epoch_protocol_parameters['obj_speed']
        obj_surface_radius = self.epoch_protocol_parameters['obj_surface_radius']

        occluder_ellipse = self.epoch_protocol_parameters['occluder_ellipse']
        occluder_theta = self.epoch_protocol_parameters['occluder_theta']
        occluder_width = self.epoch_protocol_parameters['occluder_wh'][0]
        occluder_height = self.epoch_protocol_parameters['occluder_wh'][1]
        occluder_color = self.epoch_protocol_parameters['occluder_color']
        occluder_surface_radius = self.epoch_protocol_parameters['occluder_surface_radius']

        preprime_duration = self.epoch_protocol_parameters['preprime_duration']
        pause_duration = self.epoch_protocol_parameters['pause_duration']

        render_on_cylinder = self.epoch_protocol_parameters['render_on_cylinder']
        
        angle = self.epoch_protocol_parameters['angle']

        center = self.adjust_center(self.epoch_protocol_parameters['center'])
        centerX = center[0]
        centerY = center[1]

        ### Stimulus construction ###

        obj_start_theta *= np.sign(obj_speed)
        obj_end_theta *= np.sign(obj_speed)
        occluder_theta *= np.sign(obj_speed)

        # Object
        theta_distance = np.abs(obj_end_theta - obj_start_theta)
        prime_distance = np.abs(occluder_theta - obj_start_theta)
        prime_duration = prime_distance / np.abs(obj_speed)
        probe_distance = np.abs(obj_end_theta - occluder_theta)
        probe_duration = probe_distance / np.abs(obj_speed)
        obj_duration_wo_pause = theta_distance / np.abs(obj_speed)
        obj_duration_w_pause = obj_duration_wo_pause + pause_duration
        stim_duration = preprime_duration + obj_duration_w_pause

        # Object trajectory
        time =       [0,
                      preprime_duration,
                      preprime_duration+prime_duration,
                      preprime_duration+prime_duration+pause_duration,
                      stim_duration]
        x =          [obj_start_theta,
                      obj_start_theta,
                      occluder_theta,
                      occluder_theta,
                      obj_end_theta]
        obj_color =  [obj_prime_color,
                      obj_prime_color,
                      obj_prime_color,
                      obj_probe_color,
                      obj_probe_color]

        # Occluder trajectory
        occluder_time = [0, stim_duration]
        occluder_x = [occluder_theta, occluder_theta]

        ### Create stimpack.visual_stim trajectory objects ###
        obj_theta_traj      = {'name': 'TVPairs', 'tv_pairs': list(zip(time, (centerX + np.array(x)).tolist())), 'kind': 'linear'}
        obj_color_traj      = {'name': 'TVPairs', 'tv_pairs': list(zip(time, obj_color)), 'kind': 'previous'}
        occluder_theta_traj = {'name': 'TVPairs', 'tv_pairs': list(zip(occluder_time, (centerX + np.array(occluder_x)).tolist())), 'kind': 'linear'}

        # Create epoch parameters dictionary
        if render_on_cylinder:
            obj_flystim_stim_name = 'MovingEllipseOnCylinder' if obj_ellipse else 'MovingPatchOnCylinder'
            occluder_flystim_stim_name = 'MovingEllipseOnCylinder' if occluder_ellipse else 'MovingPatchOnCylinder'
            surface_dim_name = 'cylinder_radius'
        else:
            obj_flystim_stim_name = 'MovingEllipse' if obj_ellipse else 'MovingPatch'
            occluder_flystim_stim_name = 'MovingEllipse' if occluder_ellipse else 'MovingPatch'
            surface_dim_name = 'sphere_radius'
        
        obj_parameters = {'name': obj_flystim_stim_name,
                            'width': obj_width,
                            'height': obj_height,
                            'color': obj_color_traj,
                            'theta': obj_theta_traj,
                            'phi': centerY,
                            'angle': angle,
                            surface_dim_name: obj_surface_radius}
        occluder_parameters = {'name': occluder_flystim_stim_name,
                            'width': occluder_width,
                            'height': occluder_height,
                            'color': occluder_color,
                            'theta': occluder_theta_traj,
                            'phi': centerY,
                            'angle': angle,
                            surface_dim_name: occluder_surface_radius}        
        
        self.epoch_stim_parameters = [obj_parameters, occluder_parameters]
        self.epoch_protocol_parameters['stim_time'] = stim_duration

        # opto
        self.epoch_protocol_parameters['opto_stim_time'] = stim_duration + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

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
                'tail_time': 1.0,
                'loco_pos_closed_loop': 0,
            
                'obj_ellipse': True,
                'obj_start_theta': 0,
                'obj_end_theta': 210,
                'obj_wh': (35, 25),
                'obj_prime_color': 0.3,
                'obj_probe_color': 0.3,
                'obj_speed': [30, -30],
                'obj_surface_radius': 3,
                
                'occluder_ellipse': False,
                'occluder_theta': 120,
                'occluder_wh': [(0, 100), (60, 100)],
                'occluder_color': 0.0,
                'occluder_surface_radius': 2,
                
                'render_on_cylinder': True,
                'center': (0, 0),
                'angle': 0.0,
                
                'preprime_duration': 1.0,
                'pause_duration': 0.0,
                
                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,
                'opto_pulse_width': 0.01,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 240, # 12 x 20 each
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

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
        self.epoch_protocol_parameters['opto_stim_time'] = stim_time + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

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
                'velocity': [-60, -30, -15, -7.5, 7.5, 15, 30, 60],
                'angle': 0.0,
                'render_on_cylinder': False,

                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,
                'opto_pulse_width': 0.01,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'set_time_by_distance': True,
                'all_combinations': True,
                'randomize_order': True}

class LinearTrackWithTowers(BaseProtocol):
    """
    Linear track with towers. Towers can be rotating or stationary, and can be sine or square wave gratings.
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

    def start_stimuli(self, manager, append_stim_frames=False, print_profile=True, multicall=None):
        
        # locomotion setting variables
        do_loco = self.run_parameters.get('do_loco', False)
        do_loco_closed_loop = do_loco and self.epoch_protocol_parameters.get('loco_pos_closed_loop', False)
        save_pos_history = do_loco_closed_loop and self.save_metadata_flag
        
        ### pre time
        sleep(self.epoch_protocol_parameters['pre_time'])
        
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(manager)

        ### stim time
        # locomotion / closed loop
        if do_loco:
            multicall.target('locomotion').set_pos_0(loco_pos = {'x': None, 'y': None, 'z': None, 'theta': None, 'phi': None, 'roll': None}, 
                                                                  use_data_prev=True, write_log=self.save_metadata_flag)
        if do_loco_closed_loop:
            multicall.target('locomotion').loop_update_closed_loop_vars(update_x=True, update_y=True, update_z=True, update_theta=True, update_phi=True, update_roll=True)
            multicall.target('locomotion').loop_start_closed_loop()
        
        multicall.target('all').set_save_pos_history_flag(save_pos_history)
        multicall.target('all').start_stim(append_stim_frames=append_stim_frames)
        multicall.target('visual').corner_square_toggle_start()
        multicall()
        sleep(self.epoch_protocol_parameters['stim_time'])

        ### tail time
        multicall = stimpack.rpc.multicall.MyMultiCall(manager)
        multicall.target('all').stop_stim(print_profile=print_profile)
        multicall.target('visual').corner_square_toggle_stop()
        multicall.target('visual').corner_square_off()

        # locomotion / closed loop
        if do_loco_closed_loop:
            multicall.target('locomotion').loop_stop_closed_loop()
        if save_pos_history:
            multicall.target('all').save_pos_history_to_file(epoch_id=f'{self.num_epochs_completed:03d}')

        multicall()

        sleep(self.epoch_protocol_parameters['tail_time'])

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        # assert that all tower parameters are the same length
        if not (len(self.epoch_protocol_parameters['tower_radius']) \
            == len(self.epoch_protocol_parameters['tower_top_z']) \
            == len(self.epoch_protocol_parameters['tower_bottom_z']) \
            == len(self.epoch_protocol_parameters['tower_y_pos']) \
            == len(self.epoch_protocol_parameters['tower_period']) \
            == len(self.epoch_protocol_parameters['tower_angle']) \
            == len(self.epoch_protocol_parameters['tower_mean']) \
            == len(self.epoch_protocol_parameters['tower_contrast']) \
            == len(self.epoch_protocol_parameters['tower_profile_sine']) \
            == len(self.epoch_protocol_parameters['tower_rotating']) \
            == len(self.epoch_protocol_parameters['tower_on_left'])):
            print('Error: tower parameters are not the same length.')
        
        n_repeat_track = int(self.epoch_protocol_parameters['n_repeat_track'])
        n_towers = len(self.epoch_protocol_parameters['tower_radius'])

        track_width = float(self.epoch_protocol_parameters['track_width']) / 100 # m
        track_patch_width = float(self.epoch_protocol_parameters['track_patch_width']) / 100 # m
        track_length = float(self.epoch_protocol_parameters['track_length']) / 100 # m
        track_z_level = float(self.epoch_protocol_parameters['track_z_level']) / 100 # m
        
        tower_radius = np.array(self.epoch_protocol_parameters['tower_radius'], dtype=float) / 100 # m
        tower_top_z = np.array(self.epoch_protocol_parameters['tower_top_z'], dtype=float) / 100 # m
        tower_bottom_z = np.array(self.epoch_protocol_parameters['tower_bottom_z'], dtype=float) / 100 # m
        tower_y_pos = np.array(self.epoch_protocol_parameters['tower_y_pos'], dtype=float) / 100 # m
        tower_period = np.array(self.epoch_protocol_parameters['tower_period'], dtype=float) # deg
        tower_angle = np.array(self.epoch_protocol_parameters['tower_angle'], dtype=float) # deg

        tower_height = tower_top_z - tower_bottom_z
        tower_z_pos = tower_top_z/2 + tower_bottom_z/2
        tower_x_pos_l = -track_width/2 - tower_radius
        tower_x_pos_r = +track_width/2 + tower_radius

        # Create stimpack.visual_stim epoch parameters dictionary

        track = {'name':  'CheckerboardFloor',
                'mean': self.epoch_protocol_parameters['track_color_mean'],
                'contrast': self.epoch_protocol_parameters['track_color_contrast'],
                'center': (0, track_length * n_repeat_track / 2, track_z_level),
                'side_length': (track_width, track_length * n_repeat_track),
                'patch_width': track_patch_width}
        
        self.epoch_stim_parameters = [track]

        for r in range(n_repeat_track):
            for i in range(n_towers):
                tower_x_pos = tower_x_pos_l[i] if self.epoch_protocol_parameters['tower_on_left'][i] else tower_x_pos_r[i]
                tower_y_pos_r = tower_y_pos[i] + r * track_length
                tower = {'name': 'CylindricalGrating' if not self.epoch_protocol_parameters['tower_rotating'][i] else 'RotatingGrating',
                        'period': tower_period[i],
                        'mean': self.epoch_protocol_parameters['tower_mean'][i], 
                        'contrast': self.epoch_protocol_parameters['tower_contrast'][i],
                        'offset': 0.0,
                        'grating_angle': tower_angle[i],
                        'profile': 'sine' if self.epoch_protocol_parameters['tower_profile_sine'][i] else 'square',
                        'color': [1, 1, 1, 1],
                        'cylinder_radius': tower_radius[i],
                        'cylinder_location': (tower_x_pos, tower_y_pos_r, tower_z_pos[i]),
                        'cylinder_height': tower_height[i],
                        'theta': 0,
                        'phi': 0,
                        'angle': 0}
                if self.epoch_protocol_parameters['tower_rotating'][i]:
                    tower['rate'] = tower_period[i]
                self.epoch_stim_parameters.append(tower)
        
    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

        super().load_stimuli(client, multicall)

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 25.0,
                'tail_time': 1.0,
                'loco_pos_closed_loop': 1,

                'track_z_level': -5,
                'track_length': 400,
                'track_width': 40,
                'track_patch_width': 5,
                'track_color_mean': 0.3,
                'track_color_contrast': 1.0,

                'tower_radius':       ( 15,  15,   5,   5,  10,  10,  10,  10,   8,   8),
                'tower_bottom_z':     (-10, -10, -10, -10, -10, -10, -10, -10, -10, -10),
                'tower_top_z':        ( 30,  30,  40,  40,  20,  20,  40,  40,  50,  50),
                'tower_y_pos':        ( 80,  80, 160, 160, 240, 240, 320, 320, 400, 400),
                'tower_on_left':      (   1,  0,   1,   0,   1,   0,   1,   0,   1,   0),
                'tower_angle':        (   0,180,  45, -45,  90,  90,  60, -60, -30,  30),
                'tower_period':       ( 30,  30,  60,  60,  45,  45,  30,  30,  60,  60),
                'tower_mean':         (0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5),
                'tower_contrast':     (  1,   1,   1,   1, 0.6, 0.6,   1,   1,   1,   1),
                'tower_profile_sine': (  0,   0,   1,   1,   1,   1,   0,   0,   1,   1),
                'tower_rotating':     (  0,   0,   1,   1,   0,   0,   1,   1,   0,   0),

                'n_repeat_track': 2,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

class TowerLatencyMeasure(BaseProtocol):
    """
    Linear track with towers. Towers can be rotating or stationary, and can be sine or square wave gratings.
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

    def start_stimuli(self, manager, append_stim_frames=False, print_profile=True, multicall=None):
        
        # locomotion setting variables
        do_loco = self.run_parameters.get('do_loco', False)
        do_loco_closed_loop = do_loco and self.epoch_protocol_parameters.get('loco_pos_closed_loop', False)
        save_pos_history = do_loco_closed_loop and self.save_metadata_flag
        
        ### pre time
        sleep(self.epoch_protocol_parameters['pre_time'])
        
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(manager)

        ### stim time
        # locomotion / closed loop
        if do_loco:
            multicall.target('locomotion').set_pos_0(loco_pos = {'x': None, 'y': None, 'z': None, 'theta': None, 'phi': None, 'roll': None}, 
                                                                  use_data_prev=True, write_log=self.save_metadata_flag)
        if do_loco_closed_loop:
            multicall.target('locomotion').loop_update_closed_loop_vars(update_x=True, update_y=True, update_z=False, update_theta=False, update_phi=False, update_roll=False)
            multicall.target('locomotion').loop_start_closed_loop()
        
        multicall.target('all').set_save_pos_history_flag(save_pos_history)
        multicall.target('all').start_stim(append_stim_frames=append_stim_frames)
        multicall.target('visual').corner_square_toggle_start()
        multicall()
        sleep(self.epoch_protocol_parameters['stim_time'])

        ### tail time
        multicall = stimpack.rpc.multicall.MyMultiCall(manager)
        multicall.target('all').stop_stim(print_profile=print_profile)
        multicall.target('visual').corner_square_toggle_stop()
        multicall.target('visual').corner_square_off()

        # locomotion / closed loop
        if do_loco_closed_loop:
            multicall.target('locomotion').loop_stop_closed_loop()
        if save_pos_history:
            multicall.target('all').save_pos_history_to_file(epoch_id=f'{self.num_epochs_completed:03d}')

        multicall()

        sleep(self.epoch_protocol_parameters['tail_time'])

    def get_epoch_parameters(self):
        super().get_epoch_parameters()
        
        n_towers = len(self.epoch_protocol_parameters['tower_radius'])

        tower_radius = np.array(self.epoch_protocol_parameters['tower_radius'], dtype=float) / 100 # m
        tower_top_z = np.array(self.epoch_protocol_parameters['tower_top_z'], dtype=float) / 100 # m
        tower_bottom_z = np.array(self.epoch_protocol_parameters['tower_bottom_z'], dtype=float) / 100 # m
        tower_x_pos = np.array(self.epoch_protocol_parameters['tower_x_pos'], dtype=float)
        tower_y_pos = np.array(self.epoch_protocol_parameters['tower_y_pos'], dtype=float) / 100 # m
        tower_period = np.array(self.epoch_protocol_parameters['tower_period'], dtype=float) # deg
        tower_angle = np.array(self.epoch_protocol_parameters['tower_angle'], dtype=float) # deg

        tower_height = tower_top_z - tower_bottom_z
        tower_z_pos = tower_top_z/2 + tower_bottom_z/2

        # Create stimpack.visual_stim epoch parameters dictionary

        self.epoch_stim_parameters = []

        for i in range(n_towers):
            tower = {'name': 'CylindricalGrating' if not self.epoch_protocol_parameters['tower_rotating'][i] else 'RotatingGrating',
                    'period': tower_period[i],
                    'mean': self.epoch_protocol_parameters['tower_mean'][i], 
                    'contrast': self.epoch_protocol_parameters['tower_contrast'][i],
                    'offset': 0.0,
                    'grating_angle': tower_angle[i],
                    'profile': 'sine' if self.epoch_protocol_parameters['tower_profile_sine'][i] else 'square',
                    'color': [1, 1, 1, 1],
                    'cylinder_radius': tower_radius[i],
                    'cylinder_location': (tower_x_pos[i], tower_y_pos[i], tower_z_pos[i]),
                    'cylinder_height': tower_height[i],
                    'theta': 0,
                    'phi': 0,
                    'angle': 0}
            if self.epoch_protocol_parameters['tower_rotating'][i]:
                tower['rate'] = tower_period[i]
            self.epoch_stim_parameters.append(tower)
        
    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

        super().load_stimuli(client, multicall)

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 10.0,
                'tail_time': 1.0,
                'loco_pos_closed_loop': 1,

                'tower_radius':       ( 0.1, 0.1),
                'tower_bottom_z':     (-10,-10),
                'tower_top_z':        ( 10, 10),
                'tower_y_pos':        ( 0, 0),
                'tower_x_pos':        (  0,  0),
                'tower_angle':        (  0,  0),
                'tower_period':       ( 30, 30),
                'tower_mean':         (  0,  0),
                'tower_contrast':     (  0,  0),
                'tower_profile_sine': (  0,  0),
                'tower_rotating':     (  0,  0),
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 1,
                'all_combinations': True,
                'randomize_order': True}

class Tracked2DTrajectory():
    def __init__(self, t, x, y, a):
        assert len(t) == len(x) == len(y) == len(a)
        self.t = np.array(t)
        self.x = np.array(x)
        self.y = np.array(y)
        self.a = np.array(a)
    
    def __len__(self):
        return len(self.t)
    
    def duration(self):
        return self.t[-1]
    
    def to_dict(self):
        return {'t': self.t, 'x': self.x, 'y': self.y, 'a': self.a}
    
    def to_tv_pairs(self):
        return {'x': list(zip(self.t, self.x)), 
                'y': list(zip(self.t, self.y)), 
                'a': list(zip(self.t, self.a))}
        
    def rotate(self, theta_deg):
        '''
        :param theta_deg: rotation angle (in degrees)
        '''
        self.x, self.y, self.a = Tracked2DTrajectory.__rotate_trajectory(self.x, self.y, self.a, theta_deg)
    
    def translate(self, dx, dy):
        self.x += dx
        self.y += dy
        
    def repeat(self, n_repeat, continuous=True):
        n_ts = len(self)
        
        t_rep, x_rep, y_rep, a_rep = np.zeros((4, n_ts * n_repeat))
        t_rep[:n_ts] = self.t
        x_rep[:n_ts] = self.x
        y_rep[:n_ts] = self.y
        a_rep[:n_ts] = self.a
        
        for i in range(1, n_repeat):
            t_last = t_rep[i * n_ts - 1]
            x_last = x_rep[i * n_ts - 1]
            y_last = y_rep[i * n_ts - 1]
            a_last = a_rep[i * n_ts - 1]
                    
            t_rep[i * n_ts: (i+1) * n_ts] = self.t + t_last # in seconds

            if continuous:
                rotate_by = a_last - self.a[0]
                x_rot, y_rot, a_rot = Tracked2DTrajectory.__rotate_trajectory(self.x, self.y, self.a, rotate_by)
                
                x_rep[i * n_ts: (i+1) * n_ts] = x_rot + x_last
                y_rep[i * n_ts: (i+1) * n_ts] = y_rot + y_last
                a_rep[i * n_ts: (i+1) * n_ts] = a_rot
            else:
                x_rep[i * n_ts: (i+1) * n_ts] = self.x
                y_rep[i * n_ts: (i+1) * n_ts] = self.y
                a_rep[i * n_ts: (i+1) * n_ts] = self.a
        
        self.t, self.x, self.y, self.a = t_rep, x_rep, y_rep, a_rep
    
    def scale_position(self, scale_factor):
        self.x *= scale_factor
        self.y *= scale_factor
    
    def fast_forward(self, t_offset):
        self.t -= t_offset

    def scale_time(self, scale_factor):
        self.t *= scale_factor

    def __rotate_trajectory(x, y, a, theta_deg):
        '''
        :param x: x position trajectory
        :param y: y position trajectory
        :param a: angle trajectory (in degrees)
        :param theta_deg: rotation angle (in degrees)
        '''
        assert len(x) == len(y) == len(a)
        
        theta_rad = np.deg2rad(theta_deg)
        x_rot = x * np.cos(theta_rad) - y * np.sin(theta_rad)
        y_rot = x * np.sin(theta_rad) + y * np.cos(theta_rad)
        a_rot = a + theta_deg

        return x_rot, y_rot, a_rot

    def load_from_bigrig(traj_fn):
        traj_np = np.genfromtxt(traj_fn, delimiter=',')
        t, x, y, angle = traj_np.T
        return Tracked2DTrajectory(t, x, y, angle)
    
    def load_from_cowley(traj_fn):
        with open(traj_fn, 'rb') as f:
            traj = pickle.load(f)
        return Tracked2DTrajectory(traj['time'], traj['x']/1000, traj['y']/1000, traj['heading'])

class MovingEllipsoid(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
        
        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()
    
    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        stim_time = self.epoch_protocol_parameters['stim_time']
        
        x_trajectory = {'name': 'TVPairs',
                        'tv_pairs': [(0, -2), (stim_time, 2)],
                        'kind': 'linear'}
        y_trajectory = {'name': 'TVPairs',
                        'tv_pairs': [(0, 4), (stim_time, 6)],
                        'kind': 'linear'}
        z_trajectory = {'name': 'TVPairs',
                        'tv_pairs': [(0, -2), (stim_time, 2)],
                        'kind': 'linear'}

        yaw_trajectory = {'name': 'TVPairs',
                            'tv_pairs': [(0, 0), (stim_time, 90*stim_time)],
                            'kind': 'linear'}
        pitch_trajectory   = {'name': 'TVPairs',
                            'tv_pairs': [(0, 0), (stim_time, 90*stim_time)],
                            'kind': 'linear'}
        roll_trajectory = {'name': 'TVPairs',
                            'tv_pairs': [(0, 0), (stim_time, 0)],
                            'kind': 'linear'}

        self.epoch_stim_parameters = {'name': 'MovingEllipsoid',
                            'x_length': self.epoch_protocol_parameters['dimensions'][0],
                            'y_length': self.epoch_protocol_parameters['dimensions'][1],
                            'z_length': self.epoch_protocol_parameters['dimensions'][2],
                            'color': self.epoch_protocol_parameters['color'],
                            'x': x_trajectory,
                            'y': y_trajectory,
                            'z': z_trajectory,
                            'yaw': yaw_trajectory, 
                            'pitch': pitch_trajectory,
                            'roll': roll_trajectory,
                            'n_subdivisions': 6}
            
    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 4.0,
                'tail_time': 0.5,
                
                'dimensions': (2,1,1),
                'color': None,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 2,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

class FlyByFly(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
    
        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_protocol_parameters['start_x_dist'] = abs(self.epoch_protocol_parameters['start_x_dist'])

        start_x_dist = self.epoch_protocol_parameters['start_x_dist']/1000
        x_vel = self.epoch_protocol_parameters['x_vel']/1000
        y_dist = self.epoch_protocol_parameters['y_dist']/1000
        y_len = self.epoch_protocol_parameters['y_len']/1000
        z_pos = self.epoch_protocol_parameters['z_pos']/1000
        floor_z_pos = self.epoch_protocol_parameters['floor_z_pos']/1000

        stim_time = 2 * start_x_dist / abs(x_vel)
        self.epoch_protocol_parameters['stim_time'] = stim_time

        if x_vel > 0:
            x_pos = [start_x_dist, -start_x_dist]
            yaw = 90
        else:
            x_pos = [-start_x_dist, start_x_dist]
            yaw = -90

        x_traj = {'name': 'TVPairs', 'kind': 'linear', 
                  'tv_pairs': list(zip([0, stim_time], x_pos))
                 }

        # Create stimpack.visual_stim epoch parameters dictionary
        sky_stim_parameters = {'name': 'ConstantBackground',
                            'color': self.epoch_protocol_parameters['sky_color'],
                            'side_length': 6}
        floor_stim_parameters = {'name': 'Floor',
                                 'color': self.epoch_protocol_parameters['floor_color'],
                                 'z_level': floor_z_pos,
                                 'side_length': 5}
        fly_stim_parameters = {'name': 'MovingFly',
                            'size': y_len,
                            'color': self.epoch_protocol_parameters['color'],
                            'x': x_traj,
                            'y': y_dist,
                            'z': z_pos,
                            'yaw': yaw, 
                            'pitch': 0.0,
                            'roll': 0.0,
                            'n_subdivisions': 5}
        
        self.epoch_stim_parameters = [sky_stim_parameters, floor_stim_parameters, fly_stim_parameters]

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'tail_time': 0.5,
                
                'x_vel': [3, -3], # in mm/s
                'start_x_dist': 5, # in mm
                'y_dist': 5, # in mm
                'y_len': 3, # in mm, approximate
                'z_pos': 0.8, # in mm
                'color': None,
                'floor_z_pos': -0.1, # in mm
                'floor_color': (0.7, 0.7, 0.7, 1.0),
                'sky_color': (0.9, 0.9, 0.9, 1.0),
                
                'closed_loop': 0,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 1,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}
    
class TrackedFly(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
    
        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        traj_fn = self.epoch_protocol_parameters['traj_fn']
        traj = Tracked2DTrajectory.load_from_bigrig(traj_fn)

        traj.rotate(self.epoch_protocol_parameters['rotate_by'])
        traj.translate(0, 0.01) # Move the fly forward by 1 cm
        traj.repeat(n_repeat=math.ceil(self.epoch_protocol_parameters['stim_time'] / traj.duration()), continuous=True)
        
        traj_tv_paris = traj.to_tv_pairs()
        x_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':self.epoch_protocol_parameters['x_bounds'], 'tv_pairs': traj_tv_paris['x']}
        y_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':self.epoch_protocol_parameters['y_bounds'], 'tv_pairs': traj_tv_paris['y']}
        a_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':None, 'tv_pairs': traj_tv_paris['a']}

        # Create stimpack.visual_stim epoch parameters dictionary
        sky_stim_parameters = {'name': 'ConstantBackground',
                            'color': self.epoch_protocol_parameters['sky_color'],
                            'side_length': 6}
        floor_stim_parameters = {'name': 'Floor',
                                 'color': self.epoch_protocol_parameters['floor_color'],
                                 'z_level': self.epoch_protocol_parameters['floor_z_pos'],
                                 'side_length': 5}
        fly_stim_parameters = {'name': 'MovingFly',
                            'size': self.epoch_protocol_parameters['fly_y_len'],
                            'color': self.epoch_protocol_parameters['fly_color'],
                            'x': x_traj,
                            'y': y_traj,
                            'z': self.epoch_protocol_parameters['fly_z_pos'],
                            'yaw': a_traj, 
                            'pitch': 0.0,
                            'roll': 0.0,
                            'n_subdivisions': 5}
        
        self.epoch_stim_parameters = [sky_stim_parameters, floor_stim_parameters, fly_stim_parameters]

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 20.0,
                'tail_time': 0.5,
                
                'traj_fn': '/Users/minseung/data/bigrig_trajectories/trial-23-20190620-010244_traj.csv',
                'fly_y_len': 0.002, #approximate
                'fly_z_pos': 0,
                'fly_color': None,
                'floor_z_pos': -0.001,
                'floor_color': (0.7, 0.7, 0.7, 1.0),
                'sky_color': (0.9, 0.9, 0.9, 1.0),
                
                'x_bounds': None,
                'y_bounds': None,
                'rotate_by': 0,
                
                'center': (0, 0),
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 1,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}
        
class Tracked3DObject(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)
    
        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        traj_fn = self.epoch_protocol_parameters['traj_fn']
        traj = Tracked2DTrajectory.load_from_cowley(traj_fn)

        traj.fast_forward(self.epoch_protocol_parameters['fast_forward'])
        traj.rotate(self.epoch_protocol_parameters['rotate_by'])
        x_0 = self.epoch_protocol_parameters['pos_0'][0] / 1000 # mm to m
        y_0 = self.epoch_protocol_parameters['pos_0'][1] / 1000 # mm to m
        traj.translate(x_0, y_0)
        traj.repeat(n_repeat=math.ceil(self.epoch_protocol_parameters['stim_time'] / traj.duration()), continuous=True)
        
        traj_tv_paris = traj.to_tv_pairs()
        x_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':self.epoch_protocol_parameters['x_bounds'], 'tv_pairs': traj_tv_paris['x']}
        y_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':self.epoch_protocol_parameters['y_bounds'], 'tv_pairs': traj_tv_paris['y']}
        a_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':None, 'tv_pairs': traj_tv_paris['a']}

        # Create stimpack.visual_stim epoch parameters dictionary
        floor_stim_parameters = {'name': 'Floor',
                                 'color': self.epoch_protocol_parameters['floor_color'],
                                 'z_level': self.epoch_protocol_parameters['floor_z_pos'] / 1000, # mm to m
                                 'side_length': 5}
        if self.epoch_protocol_parameters['use_fly_rendering']:
            obj_stim_parameters  = {'name': 'MovingFly',
                                    'size': self.epoch_protocol_parameters['dim'][1] / 1000, # mm to m; only use y dim and ignore x and z dims
                                    'color': self.epoch_protocol_parameters['color'],
                                    'x': x_traj,
                                    'y': y_traj,
                                    'z': self.epoch_protocol_parameters['pos_0'][2] / 1000, # mm to m
                                    'yaw': a_traj, 
                                    'pitch': 0.0,
                                    'roll': 0.0,
                                    'n_subdivisions': 5}
        else:
            obj_stim_parameters  = {'name': 'MovingEllipsoid',
                                    'x_length': self.epoch_protocol_parameters['dim'][0] / 1000, # mm to m
                                    'y_length': self.epoch_protocol_parameters['dim'][1] / 1000, # mm to m
                                    'z_length': self.epoch_protocol_parameters['dim'][2] / 1000, # mm to m
                                    'color': self.epoch_protocol_parameters['color'],
                                    'x': x_traj,
                                    'y': y_traj,
                                    'z': self.epoch_protocol_parameters['pos_0'][2] / 1000, # mm to m
                                    'yaw': a_traj, 
                                    'pitch': 0.0,
                                    'roll': 0.0,
                                    'n_subdivisions': 6}
        
        self.epoch_stim_parameters = [floor_stim_parameters, obj_stim_parameters]

        # opto
        self.epoch_protocol_parameters['opto_stim_time'] = self.epoch_protocol_parameters['stim_time'] + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

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
        return {'pre_time': 0.5,
                'stim_time': 5.0,
                'tail_time': 0.5,
                
                'traj_fn': '/home/mc/data/cowley/m2f_pos_table.pkl',
                'fast_forward': 0.0, # s
                'dim': (1, 2, 0.8), # mm
                'pos_0': (0, 0, 0), #mm
                'color': (0, 0, 0, 1),
                'floor_z_pos': -1, # mm
                'floor_color': (0.7, 0.7, 0.7, 1.0),
                'use_fly_rendering': 0,
                
                'x_bounds': None,
                'y_bounds': None,
                'rotate_by': 0,
                
                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,
                'opto_pulse_width': 0.01,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 1,
                'idle_color': 0.9,
                'all_combinations': True,
                'randomize_order': True}
        
class TrackedTrajectory(BaseProtocol):
    """
    Moving patch, either rectangular or elliptical. Moves along trajectory imported from the Big Rig.
    Caveat: the trajectory is x y position in meters, but the stimulus is in degrees.
    """
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        traj_fn = self.epoch_protocol_parameters['traj_fn']
        traj = Tracked2DTrajectory.load_from_bigrig(traj_fn)

        traj.scale_position(self.epoch_protocol_parameters['xy_scaling'])
        traj.scale_time(self.epoch_protocol_parameters['time_scaling'])
        traj.rotate(self.epoch_protocol_parameters['rotate_by'])
        
        traj.repeat(n_repeat=math.ceil(self.epoch_protocol_parameters['stim_time'] / traj.duration()), continuous=True)
        
        traj_tv_paris = traj.to_tv_pairs()
        x_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':self.epoch_protocol_parameters['theta_bounds'], 'tv_pairs': traj_tv_paris['x']}
        y_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':self.epoch_protocol_parameters['phi_bounds'], 'tv_pairs': traj_tv_paris['y']}
        a_traj = {'name': 'TVPairsBounded', 'kind': 'linear', 'bounds':None, 'tv_pairs': traj_tv_paris['a']}

        # Create stimpack.visual_stim epoch parameters dictionary
        if self.epoch_protocol_parameters['render_on_cylinder']:
            flystim_stim_name = 'MovingEllipseOnCylinder' if self.epoch_protocol_parameters['ellipse'] else 'MovingPatchOnCylinder'
        else:
            flystim_stim_name = 'MovingEllipse' if self.epoch_protocol_parameters['ellipse'] else 'MovingPatch'
        
        self.epoch_stim_parameters = {'name': flystim_stim_name,
                            'width': self.epoch_protocol_parameters['width_height'][0],
                            'height': self.epoch_protocol_parameters['width_height'][1],
                            'color': self.epoch_protocol_parameters['color'],
                            'theta': x_traj,
                            'phi': y_traj,
                            'angle': a_traj}

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 20.0,
                'tail_time': 0.5,
                
                'traj_fn': '/Users/minseung/Downloads/Trajectories/trial-23-20190716-220502_traj.csv',
                'xy_scaling': 1000,
                'time_scaling': 1,
                'theta_bounds': (-30, 30),
                'phi_bounds': (-30, 30),
                'rotate_by': 0,
                
                'ellipse': True,
                'width_height': (5, 10),
                'color': 0,
                'center': (0, 0),
                'render_on_cylinder': False,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 1,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}
