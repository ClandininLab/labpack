from labpack.protocol import base_protocol
import numpy as np
import stimpack.rpc.multicall

class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

# %% # # # SIMPLE SYNTHETIC STIMS # # # # # # # # #
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
                                      'hold_duration': self.epoch_protocol_parameters['hold_duration'],
                                      'color': [1, 1, 1, 1],
                                      'mean': self.epoch_protocol_parameters['mean'],
                                      'contrast': self.epoch_protocol_parameters['contrast'],
                                      'angle': self.epoch_protocol_parameters['angle'],
                                      'offset': np.rad2deg(np.random.uniform(0, 2*np.pi)) if self.epoch_protocol_parameters['random_offset'] else 0,
                                      'cylinder_radius': 1,
                                      'cylinder_height': 10,
                                      'profile': 'square',
                                      'theta': centerX,
                                      'phi': centerY}

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
        return {'pre_time': 10.0,
                'stim_time': 1.0,
                'tail_time': 10.0,
                'loco_pos_closed_loop': 0,
                
                'period': 60.0,
                'rate': 60.0,
                'contrast': 1.0,
                'mean': 0.5,
                'angle': 0.0,
                'hold_duration': 0.0,
                'random_offset': True,
                'center': (0, 0),

                'opto_pre_time': 11.0,
                'opto_stim_time': 1.0,
                'opto_freq': 50.0,
                'opto_amp': 5.0,
                'opto_pulse_width': 0.01,
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 40,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

