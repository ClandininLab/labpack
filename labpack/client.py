#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from stimpack.visual_stim.stim_server import launch_stim_server
from stimpack.rpc.transceiver import MySocketClient
from stimpack.visual_stim.screen import Screen
from stimpack.visual_stim.draw import draw_screens

from stimpack.experiment import client


class Client(client.BaseClient):
    def __init__(self, cfg):
        super().__init__(cfg)  # call the parent class init method

     