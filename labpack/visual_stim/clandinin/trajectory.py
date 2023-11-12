import numpy as np
from scipy.interpolate import interp1d

from stimpack.visual_stim import trajectory as spv_trajectory

class TVPairsBounded(spv_trajectory.Trajectory):
    """
    List of arbitrary time-value pairs. 
    Values are optionally bounded by a lower and upper bound, and wrap around if they exceed the bounds.

    :tv_pairs: list of time, value tuples. [(t0, v0), (t1, v1), ..., (tn, vn)]
    :kind: interpolation type. See scipy.interpolate.interp1d for options.
    :bounds: lower and upper bounds for the value. (lower, upper) or None for no bounds.
    """
    def __init__(self, tv_pairs, kind='linear', fill_value='extrapolate', bounds=None):
        times, values = zip(*tv_pairs)
        values_interpolated = interp1d(times, values, kind=kind, fill_value=fill_value, axis=0)
        
        if bounds is None:
            self.getValue = values_interpolated
        else:            
            lo = min(*bounds)
            hi = max(*bounds)
            bound_range = hi - lo
            self.getValue = lambda t: np.mod(values_interpolated(t) - lo, bound_range) + lo

class LoomGabb(spv_trajectory.Trajectory):
    """
    Expanding loom trajectory defined by rv ratio and collision time
    See def'n in Gabbiani et al., 1999
    https://www.jneurosci.org/content/jneuro/19/3/1122.full.pdf

    :rv_ratio: sec. Ratio of object physical length to approach speed
    :end_radius: deg., maximum radius of spot
    :collision_time: sec., time at which object is 180 deg

    : returns radius of spot for time t
    """
    def __init__(self, rv_ratio, end_radius, collision_time):
        def get_loom_size(t):
            # note this is spot radius
            angular_size = np.rad2deg( np.arctan( rv_ratio / (collision_time - t) ) )
            # Cap the curve at end_size and have it just hang there
            if (angular_size > end_radius):
                angular_size = end_radius

            # Freeze it at the max in case there is more stim time to go
            if t > collision_time:
                angular_size = end_radius

            return angular_size
        self.getValue = get_loom_size

class LoomRV(spv_trajectory.Trajectory):
    """
    Expanding loom trajectory. Fixed loom expansion rate based on rv_ratio.

    :rv_ratio: sec
    :start_size: deg.
    :end_size: deg.
    """
    def __init__(self, rv_ratio, start_size, end_size):
        def get_loom_size(t):
            # calculate angular size at t
            d0 = rv_ratio / np.tan(np.deg2rad(start_size / 2))
            angular_size = 2 * np.rad2deg(np.arctan(rv_ratio * (1 / (d0 - t))))
            # Cap the curve at end_size and have it just hang there
            if angular_size > end_size or d0 <= t:
                angular_size = end_size
            return angular_size / 2
        self.getValue = get_loom_size
