#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Protocol parent class. Override any methods in here in the user protocol subclass

-protocol_parameters: user-defined params that are mapped to stimpack.visual_stim epoch params
                     *saved as attributes at the epoch run level
-epoch_protocol_parameters: epoch-specific user-defined params that are mapped to stimpack.visual_stim epoch params
                     *saved as attributes at the individual epoch level
-epoch_stim_parameters: parameter set used to define stimpack.visual_stim stimulus
                     *saved as attributes at the individual epoch level
"""
from stimpack.experiment import protocol

class BaseProtocol(protocol.BaseProtocol):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

    def get_moving_spot_parameters(self, center=None, angle=None, speed=None, radius=None, color=None, distance_to_travel=None, render_on_cylinder=None):
        if radius is None: radius = self.epoch_protocol_parameters['radius']
        return self.get_moving_patch_parameters(center=center, angle=angle, speed=speed, width=radius*2, height=radius*2, color=color, distance_to_travel=distance_to_travel, ellipse=True, render_on_cylinder=render_on_cylinder)
