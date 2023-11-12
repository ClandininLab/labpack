from labpack.protocol import base_protocol
import numpy as np
import math
import stimpack.rpc.multicall

class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

# %% # # # SIMPLE SYNTHETIC STIMS # # # # # # # # #
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
        multicall.daq_setup_pulse_wave_stream_out(output_channel='DAC0', 
                                              freq=self.epoch_protocol_parameters['opto_freq'], 
                                              amp=self.epoch_protocol_parameters['opto_amp'], 
                                              pulse_width=self.epoch_protocol_parameters['opto_pulse_width'], 
                                              scanRate=5000)
        multicall.daq_stream_with_timing(pre_time=self.epoch_protocol_parameters['opto_pre_time'], 
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


#%%
class StationaryPatches(BaseProtocol):
    """
    Stationary patch, either rectangular or elliptical.
    Opto, closed-loop options available.
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
        self.epoch_stim_parameters = []

        current_position = self.epoch_protocol_parameters['position']
        if not isinstance(current_position, list):
            current_position = [current_position]

        center = self.adjust_center(self.epoch_protocol_parameters['center'])
        centerX = center[0]
        centerY = center[1]

        # Create one stationary patch for each position

        if self.epoch_protocol_parameters['render_on_cylinder']:
            flystim_stim_name = 'MovingEllipseOnCylinder' if self.epoch_protocol_parameters['ellipse'] else 'MovingPatchOnCylinder'
        else:
            flystim_stim_name = 'MovingEllipse' if self.epoch_protocol_parameters['ellipse'] else 'MovingPatch'
        
        for pos in current_position:
            self.epoch_stim_parameters.append(
                {
                    'name': flystim_stim_name,
                    'width': centerX + self.epoch_protocol_parameters['width_height'][0],
                    'height': centerY + self.epoch_protocol_parameters['width_height'][1],
                    'color': self.epoch_protocol_parameters['color'],
                    'theta': pos[0],
                    'phi': pos[1],
                    'angle': self.epoch_protocol_parameters['angle']
                }
            )
        
        # opto
        self.epoch_protocol_parameters['opto_stim_time'] = self.epoch_protocol_parameters['stim_time'] + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

        # set up opto pulse wave
        multicall.daq_setup_pulse_wave_stream_out(output_channel='DAC0', 
                                              freq=self.epoch_protocol_parameters['opto_freq'], 
                                              amp=self.epoch_protocol_parameters['opto_amp'], 
                                              pulse_width=self.epoch_protocol_parameters['opto_pulse_width'], 
                                              scanRate=5000)
        multicall.daq_stream_with_timing(pre_time=self.epoch_protocol_parameters['opto_pre_time'], 
                                       stim_time=self.epoch_protocol_parameters['opto_stim_time'],
                                       scanRate=5000, scansPerRead=1000)

        super().load_stimuli(client, multicall)

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 2.0,
                'tail_time': 1.0,
                'loco_pos_closed_loop': 0,
                'center': (0, 0),

                'ellipse': True,
                'width_height': (15, 179),
                'color': 0.0,
                'position': [(-10, 0), (10, 0), [(-10, 0), (10, 0)]],
                'angle': 0.0,
                'render_on_cylinder': True,

                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,
                'opto_pulse_width': 0.01,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

#%%
class StationaryPatchRandomTheta(BaseProtocol):
    """
    Stationary patch, either rectangular or elliptical.
    Opto, closed-loop options available.
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

        center = self.adjust_center(self.epoch_protocol_parameters['center'])
        centerX = center[0]
        centerY = center[1]

        if self.epoch_protocol_parameters['render_on_cylinder']:
            flystim_stim_name = 'MovingEllipseOnCylinder' if self.epoch_protocol_parameters['ellipse'] else 'MovingPatchOnCylinder'
        else:
            flystim_stim_name = 'MovingEllipse' if self.epoch_protocol_parameters['ellipse'] else 'MovingPatch'
        
        self.epoch_protocol_parameters['theta'] = np.random.uniform(*self.epoch_protocol_parameters['theta_range'])

        self.epoch_stim_parameters = {'name': flystim_stim_name,
                                    'width': centerX + self.epoch_protocol_parameters['width_height'][0],
                                    'height': centerY + self.epoch_protocol_parameters['width_height'][1],
                                    'color': self.epoch_protocol_parameters['color'],
                                    'theta': self.epoch_protocol_parameters['theta'],
                                    'phi': self.epoch_protocol_parameters['phi'],
                                    'angle': self.epoch_protocol_parameters['angle']
                                    }
        
        # opto
        self.epoch_protocol_parameters['opto_stim_time'] = self.epoch_protocol_parameters['stim_time'] + self.epoch_protocol_parameters['pre_time'] - self.epoch_protocol_parameters['opto_pre_time']

    def load_stimuli(self, client, multicall=None):
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(client)
        
        params_to_print = {k:self.epoch_protocol_parameters[k] for k in self.persistent_parameters['variable_protocol_parameter_names']}
        multicall.print_on_server(f'{params_to_print}')

        # set up opto pulse wave
        multicall.daq_setup_pulse_wave_stream_out(output_channel='DAC0', 
                                              freq=self.epoch_protocol_parameters['opto_freq'], 
                                              amp=self.epoch_protocol_parameters['opto_amp'], 
                                              pulse_width=self.epoch_protocol_parameters['opto_pulse_width'], 
                                              scanRate=5000)
        multicall.daq_stream_with_timing(pre_time=self.epoch_protocol_parameters['opto_pre_time'], 
                                       stim_time=self.epoch_protocol_parameters['opto_stim_time'],
                                       scanRate=5000, scansPerRead=1000)

        super().load_stimuli(client, multicall)

    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1.0,
                'stim_time': 2.0,
                'tail_time': 1.0,
                'loco_pos_closed_loop': 0,
                'center': (0, 0),

                'ellipse': True,
                'width_height': (15, 30),
                'color': 0.0,
                'phi': 0,
                'theta_range': (-60, 60),
                'angle': 0.0,
                'render_on_cylinder': True,

                'opto_pre_time': 0.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,
                'opto_pulse_width': 0.01,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

# %% DOTS stims

class MovingDotField_MotionPulse_Cylindrical(BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        dots_parameters = {'name': 'MovingDotField_Cylindrical',
                             'n_points': int(self.epoch_protocol_parameters['n_points_each']),
                             'point_size': int(self.epoch_protocol_parameters['point_size']),
                             'cylinder_radius': 1.0,
                             'color': self.epoch_protocol_parameters['intensity'],
                             'speed': self.epoch_protocol_parameters['speed'],
                             'signal_direction': self.epoch_protocol_parameters['signal_direction'],
                             'coherence': self.epoch_protocol_parameters['coherence'],
                             'phi_limits': self.epoch_protocol_parameters['phi_limits']}
        
        if self.num_epochs_completed % 2 == 0:
            dots_parameters['coherence'] = .5
        else:
            dots_parameters['coherence'] = .4

        self.epoch_stim_parameters = dots_parameters.copy()

    def load_stimuli(self, manager, multicall=None):
        dots_parameters = self.epoch_stim_parameters.copy()

        bg = self.run_parameters.get('idle_color')
        if multicall is None:
            multicall = stimpack.rpc.multicall.MyMultiCall(manager)

        multicall.load_stim(name='ConstantBackground',
                        color=[bg, bg, bg, 1.0],
                        hold=True)
        multicall.load_stim(**dots_parameters, hold=True)
        multicall()

    def get_protocol_parameter_defaults(self):
        seed = 0 #np.random.randint(0, 10000)
        return {'pre_time': 0,
                'stim_time': 1,
                'tail_time': 0,

                'n_points_each': 100,  # More than ~200 total causes frame drops on bruker
                'point_size': 60,  # width 80 = about 15 deg in center of bruker screen
                'intensity': 0.0,
                'speed': [5],#[-30, -20, -10, 0, 10, 20, 30],
                'signal_direction': 0.0,
                'coherence': 0.0,
                'seed': seed,
                'phi_limits': (90, 160),
                }

    def get_run_parameter_defaults(self):
       return {'num_epochs': 140,
               'idle_color': 0.5,
               'all_combinations': True,
               'randomize_order': True}
