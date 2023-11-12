from labpack.protocol import base_protocol
import numpy as np
import stimpack.rpc.multicall

class BaseProtocol(base_protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

# %% # # # SIMPLE SYNTHETIC STIMS # # # # # # # # #

class Loom(BaseProtocol):
    '''
    Circle that approaches the fly
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_stim_parameters = {'name': 'LoomingCircle',
                                      'radius': self.epoch_protocol_parameters['radius'],
                                      'color': self.epoch_protocol_parameters['color'],
                                      'starting_distance': self.epoch_protocol_parameters['start_distance'],
                                      'speed': self.epoch_protocol_parameters['speed'],
                                      'n_steps': 36}
        
    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 0.5,
                'tail_time': 0.5,
                
                'radius': 0.005,
                'start_distance': 0.125,
                'speed': -0.25,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 2,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomRandomlySpaced(BaseProtocol):
    '''
    Circle that approaches the fly, randomly spaced
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

        # Calculate ITIs probabilistically (tail_time)
        # Randomly spaced ITIs, drawn from a uniform distribution between avg_iti - 1 and avg_iti + 1

        total_loom_dur = self.run_parameters['num_epochs'] * np.mean(self.protocol_parameters['stim_time'])
        num_itis = self.run_parameters['num_epochs'] - 1
        total_iti_dur = self.run_parameters['run_time'] - total_loom_dur
        avg_iti = total_iti_dur / num_itis
        iti_lo = max(avg_iti - 1, 0)
        iti_hi = min(avg_iti + 1, total_iti_dur)
        self.persistent_parameters['itis'] = np.random.uniform(iti_lo, iti_hi, int(self.run_parameters['num_epochs']))

        self.persistent_parameters['variable_protocol_parameter_names'].append('tail_time')

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        self.epoch_stim_parameters = {'name': 'LoomingCircle',
                                      'radius': self.epoch_protocol_parameters['radius'],
                                      'color': self.epoch_protocol_parameters['color'],
                                      'starting_distance': self.epoch_protocol_parameters['start_distance'],
                                      'speed': self.epoch_protocol_parameters['speed'],
                                      'n_steps': 36}
        
        # first epoch: pre_time = pre_run_time; subsequent epochs: pre_time = 0
        # tail_time = sampled iti for the epoch
        self.epoch_protocol_parameters['pre_time'] = self.run_parameters['pre_run_time'] if self.num_epochs_completed == 0 else 0
        self.epoch_protocol_parameters['tail_time'] = self.persistent_parameters['itis'][self.num_epochs_completed]

    def get_protocol_parameter_defaults(self):
        return {'stim_time': 0.5,
                
                'radius': 0.005,
                'start_distance': 0.125,
                'speed': -0.25,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 20,
                'run_time': 300.0,
                'pre_run_time': 5.0,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomRV(BaseProtocol):
    '''
    Loom defined by radius:velocity ratio
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        radius_traj = {'name': 'LoomRV',
                       'rv_ratio': self.epoch_protocol_parameters['rv_ratio'],
                       'start_size': self.epoch_protocol_parameters['radius_start'],
                       'end_size': self.epoch_protocol_parameters['radius_end']}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': 0,
                                      'phi': 0}
        
    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 0.5,
                'tail_time': 0.5,
                
                'rv_ratio': 0.04,
                'radius_start': 10,
                'radius_end': 100,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 2,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomRVRandomlySpaced(BaseProtocol):
    '''
    Loom defined by radius:velocity ratio, randomly spaced
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

        # Calculate ITIs probabilistically (tail_time)
        # Randomly spaced ITIs, drawn from a uniform distribution between avg_iti - 1 and avg_iti + 1

        total_loom_dur = self.run_parameters['num_epochs'] * np.mean(self.protocol_parameters['stim_time'])
        num_itis = self.run_parameters['num_epochs'] - 1
        total_iti_dur = self.run_parameters['run_time'] - total_loom_dur
        avg_iti = total_iti_dur / num_itis
        iti_lo = max(avg_iti - 1, 0)
        iti_hi = min(avg_iti + 1, total_iti_dur)
        self.persistent_parameters['itis'] = np.random.uniform(iti_lo, iti_hi, int(self.run_parameters['num_epochs']))

        self.persistent_parameters['variable_protocol_parameter_names'].append('tail_time')

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        radius_traj = {'name': 'LoomRV',
                       'rv_ratio': self.epoch_protocol_parameters['rv_ratio'],
                       'start_size': self.epoch_protocol_parameters['radius_start'],
                       'end_size': self.epoch_protocol_parameters['radius_end']}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': 0,
                                      'phi': 0}
        
        # first epoch: pre_time = pre_run_time; subsequent epochs: pre_time = 0
        # tail_time = sampled iti for the epoch
        self.epoch_protocol_parameters['pre_time'] = self.run_parameters['pre_run_time'] if self.num_epochs_completed == 0 else 0
        self.epoch_protocol_parameters['tail_time'] = self.persistent_parameters['itis'][self.num_epochs_completed]

    def get_protocol_parameter_defaults(self):
        return {'stim_time': 0.5,
                
                'rv_ratio': 0.04,
                'radius_start': 10,
                'radius_end': 100,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 20,
                'run_time': 300.0,
                'pre_run_time': 5.0,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomGabb(BaseProtocol):
    '''
    Loom defined by rv ratio and collision time (Gabbiani et al., 1999)
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        radius_traj = {'name': 'Loom_Gabb',
                       'rv_ratio': self.epoch_protocol_parameters['rv_ratio'],
                       'end_radius': self.epoch_protocol_parameters['radius_end'],
                       'collision_time': self.epoch_protocol_parameters['collision_time']}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': 0,
                                      'phi': 0}
        
    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 0.5,
                'tail_time': 0.5,
                
                'rv_ratio': 0.04,
                'radius_end': 100,
                'collision_time': 0.5,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 2,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomGabbRandomlySpaced(BaseProtocol):
    '''
    Loom defined by rv ratio and collision time (Gabbiani et al., 1999), randomly spaced
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

        # Calculate ITIs probabilistically (tail_time)
        # Randomly spaced ITIs, drawn from a uniform distribution between avg_iti - 1 and avg_iti + 1

        total_loom_dur = self.run_parameters['num_epochs'] * np.mean(self.protocol_parameters['stim_time'])
        num_itis = self.run_parameters['num_epochs'] - 1
        total_iti_dur = self.run_parameters['run_time'] - total_loom_dur
        avg_iti = total_iti_dur / num_itis
        iti_lo = max(avg_iti - 1, 0)
        iti_hi = min(avg_iti + 1, total_iti_dur)
        self.persistent_parameters['itis'] = np.random.uniform(iti_lo, iti_hi, int(self.run_parameters['num_epochs']))

        self.persistent_parameters['variable_protocol_parameter_names'].append('tail_time')

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        radius_traj = {'name': 'Loom_Gabb',
                       'rv_ratio': self.epoch_protocol_parameters['rv_ratio'],
                       'end_radius': self.epoch_protocol_parameters['radius_end'],
                       'collision_time': self.epoch_protocol_parameters['collision_time']}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': 0,
                                      'phi': 0}
        
        # first epoch: pre_time = pre_run_time; subsequent epochs: pre_time = 0
        # tail_time = sampled iti for the epoch
        self.epoch_protocol_parameters['pre_time'] = self.run_parameters['pre_run_time'] if self.num_epochs_completed == 0 else 0
        self.epoch_protocol_parameters['tail_time'] = self.persistent_parameters['itis'][self.num_epochs_completed]

    def get_protocol_parameter_defaults(self):
        return {'stim_time': 0.5,
                
                'rv_ratio': 0.04,
                'radius_end': 100,
                'collision_time': 0.5,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 20,
                'run_time': 300.0,
                'pre_run_time': 5.0,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomLinear(BaseProtocol):
    '''
    Circle that approaches the fly
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        radius_traj = {'name': 'TVPairs',
                       'tv_pairs': [(0, self.epoch_protocol_parameters['radius_start']), 
                                    (self.epoch_protocol_parameters['stim_time'], self.epoch_protocol_parameters['radius_end'])],
                       'kind': 'linear'}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': 0,
                                      'phi': 0}
        
    def get_protocol_parameter_defaults(self):
        return {'pre_time': 0.5,
                'stim_time': 0.5,
                'tail_time': 0.5,
                
                'radius_start': 10,
                'radius_end': 100,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 2,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}

class LoomLinearRandomlySpaced(BaseProtocol):
    '''
    Circle that expands linearly in radius (angle), randomly spaced
    '''
    
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def process_input_parameters(self):
        super().process_input_parameters()

        # Calculate ITIs probabilistically (tail_time)
        # Randomly spaced ITIs, drawn from a uniform distribution between avg_iti - 1 and avg_iti + 1
        total_loom_dur = self.run_parameters['num_epochs'] * np.mean(self.protocol_parameters['stim_time'])
        num_itis = self.run_parameters['num_epochs'] - 1
        total_iti_dur = self.run_parameters['run_time'] - total_loom_dur
        avg_iti = total_iti_dur / num_itis
        iti_lo = max(avg_iti - 1, 0)
        iti_hi = min(avg_iti + 1, total_iti_dur)
        self.persistent_parameters['itis'] = np.random.uniform(iti_lo, iti_hi, int(self.run_parameters['num_epochs']))
        
        self.persistent_parameters['variable_protocol_parameter_names'].append('tail_time')
        
    def get_epoch_parameters(self):
        super().get_epoch_parameters()
        
        radius_traj = {'name': 'TVPairs',
                       'tv_pairs': [(0, self.epoch_protocol_parameters['radius_start']), 
                                    (self.epoch_protocol_parameters['stim_time'], self.epoch_protocol_parameters['radius_end'])],
                       'kind': 'linear'}

        self.epoch_stim_parameters = {'name': 'MovingSpot',
                                      'radius': radius_traj,
                                      'sphere_radius': 1,
                                      'color': self.epoch_protocol_parameters['color'],
                                      'theta': 0,
                                      'phi': 0}
        
        # first epoch: pre_time = pre_run_time; subsequent epochs: pre_time = 0
        # tail_time = sampled iti for the epoch
        self.epoch_protocol_parameters['pre_time'] = self.run_parameters['pre_run_time'] if self.num_epochs_completed == 0 else 0
        self.epoch_protocol_parameters['tail_time'] = self.persistent_parameters['itis'][self.num_epochs_completed]

    def get_protocol_parameter_defaults(self):
        return {'stim_time': 0.5,
                
                'radius_start': 10,
                'radius_end': 100,
                'color': 0.0}

    def get_run_parameter_defaults(self):
        return {'num_epochs': 20,
                'run_time': 300.0,
                'pre_run_time': 5.0,
                'idle_color': 1.0,
                'all_combinations': True,
                'randomize_order': True}
    

class LoomWithFriends(BaseProtocol):
    '''
    Circle that approaches the fly
    Plus walking dot friends
    '''
    def __init__(self, cfg):
        super().__init__(cfg)

        self.run_parameters = self.get_run_parameter_defaults()
        self.protocol_parameters = self.get_protocol_parameter_defaults()

    def get_epoch_parameters(self):
        super().get_epoch_parameters()

        loom_parameters = {'name': 'LoomingCircle',
                            'radius': self.epoch_protocol_parameters['loom_radius'],
                            'color': self.epoch_protocol_parameters['loom_color'],
                            'starting_distance': self.epoch_protocol_parameters['loom_start_distance'],
                            'speed': self.epoch_protocol_parameters['loom_speed'],
                            'n_steps': 36}

        current_seed = np.random.randint(0, 10000)
        friends_parameters = {'name': 'IndependentDotField',
                                'n_points': self.epoch_protocol_parameters['friends_n_points'],
                                'point_size': self.epoch_protocol_parameters['friends_point_size'],
                                'sphere_radius': 1,  # meters, just has to be further out than the looming circle
                                'color': self.epoch_protocol_parameters['friends_color'],
                                'theta_trajectories': None,
                                'phi_trajectories': None,
                                'random_seed': current_seed}

        self.epoch_stim_parameters = [friends_parameters, loom_parameters]
        
    def get_protocol_parameter_defaults(self):
        return {'pre_time': 1,
                'stim_time': 2,
                'tail_time': 1,
                
                'loom_radius': 0.005,  # meters
                'loom_start_distance': 0.125,  # meters
                'loom_speed': -0.25,  # meters/sec
                'loom_color': 0.0,
                
                'friends_n_points': 100,  # over the entire sphere. Number of points in the screen will be fewer
                'friends_point_size': 40,  # PIXELS! Adjust empirically for the rig to get to the approximate right size in degrees
                'friends_color': 0.0,  # Applies to every friend
                }

    def get_run_parameter_defaults(self):
        return {'num_epochs': 20,
                'idle_color': 0.5,
                'all_combinations': True,
                'randomize_order': True}

