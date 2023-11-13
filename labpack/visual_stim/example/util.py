import os
import numpy as np
import inspect
import labpack
from stimpack.visual_stim import util as spv_util

def get_resource_path(resource_name):
    path_to_resource = os.path.join(inspect.getfile(labpack).split('labpack')[0],
                                    'labpack',
                                    'resources',
                                    resource_name)

    assert os.path.exists(path_to_resource), 'Resource not found at {}'.format(path_to_resource)

    return path_to_resource

def rot1_scale_rot2(pts, yaw1, pitch1, roll1, scale_x, scale_y, scale_z, yaw2, pitch2, roll2):
    A = spv_util.rot_mat(yaw2, pitch2, roll2) @ np.diag([scale_x, scale_y, scale_z]) @ spv_util.rot_mat(yaw1, pitch1, roll1)
    return A @ pts

