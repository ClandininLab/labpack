import os
import inspect
import labpack

def get_resource_path(resource_name):
    path_to_resource = os.path.join(inspect.getfile(labpack).split('labpack')[0],
                                    'labpack',
                                    'resources',
                                    resource_name)

    assert os.path.exists(path_to_resource), 'Resource not found at {}'.format(path_to_resource)

    return path_to_resource

