import copy
import time  # for debugging and benchmarking
from math import radians

import numpy as np
from numpy.random import default_rng

from stimpack.visual_stim import shapes as spv_shapes
from stimpack.visual_stim import stimuli as spv_stimuli
from stimpack.visual_stim.stimuli import BaseProgram
from stimpack.visual_stim.trajectory import make_as_trajectory, return_for_time_t
from stimpack.visual_stim.distribution import make_as_distribution

from labpack.visual_stim.clandinin.shapes import GlIcosphere, GlFly
from labpack.visual_stim.clandinin.image import Image

class HorizonCylinder(spv_stimuli.TexturedCylinder):
    def __init__(self, screen):
        super().__init__(screen=screen)

    def configure(self, color=[1, 1, 1, 1], cylinder_radius=5, cylinder_height=5, cylinder_pitch=0, cylinder_yaw=0,
                  theta=0,
                  image_name=None, filter_name=None, filter_kwargs={}):

        super().configure(color=color, cylinder_radius=cylinder_radius, cylinder_height=cylinder_height, theta=theta, phi=0, angle=0.0)
        self.cylinder_pitch = cylinder_pitch
        self.cylinder_yaw = cylinder_yaw
        if image_name is not None:
            t0 = time.time()
            image_object = Image(image_name)
            if filter_name is not None:  # use filtered image
                if filter_name == 'whiten':
                    texture_img = image_object.whiten_image()
                else:
                    texture_img = image_object.filter_image(filter_name, filter_kwargs)
            else:  # use original image
                texture_img = image_object.load_image()

            print('LOADED TEXTURE IMAGE FROM {}. \n SHAPE={}, FILTER={} ({:.2f} sec)'.format(image_object.image_path,
                                                                                             texture_img.shape,
                                                                                             filter_name,
                                                                                             time.time()-t0))

        else:
            # use a dummy texture
            np.random.seed(0)
            face_colors = np.random.uniform(size=(128, 128))
            texture_img = (255*face_colors).astype(np.uint8)

            print('USING DUMMY TEXTURE. SHAPE = {}'.format(texture_img.shape))

        self.add_texture_gl(texture_img, texture_interpolation='LINEAR')

        self.stim_template = spv_shapes.GlCylinder(cylinder_height=self.cylinder_height,
                                                cylinder_radius=self.cylinder_radius,
                                                cylinder_location=(0, 0, 0),
                                                color=self.color,
                                                texture=True).rotz(np.radians(180))
    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        theta = return_for_time_t(self.theta, t)
        cyl_position = subject_position.copy()  # cylinder moves with the fly, so fly is always in the center
        self.stim_object = copy.copy(self.stim_template).translate(cyl_position).rotz(np.radians(theta)).roty(np.radians(self.cylinder_yaw)).rotx(np.radians(self.cylinder_pitch))

class IndependentDotField(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)
        self.draw_mode = 'POINTS'

    def make_random_walk(self, origin=0, duration=1, step_size=np.pi/8, nsteps=100):

        """
        origin (position, radians)
        duration (sec)
        nsteps
        """

        time_steps = np.linspace(0, duration, nsteps)
        steps = np.random.choice(a=[-step_size, 0, step_size], size=nsteps-1)
        path = np.cumsum(np.append(origin, steps))

        return {'name': 'TVPairs',
                'TVPairs': list(zip(time_steps, path)),
                'kind': 'linear'}

    def configure(self, n_points=100, point_size=40, sphere_radius=1, color=[1, 1, 1, 1],
                  theta_trajectories=None, phi_trajectories=None, random_seed=0):
        """
        Collection of moving points. Independent trajectories

        Note that points are all the same size, so no area correction is made for perspective
        """
        self.n_points = n_points
        self.point_size = point_size
        self.sphere_radius = sphere_radius
        self.color = color
        self.random_seed = random_seed

        # Set random seed
        rng = default_rng(self.random_seed)

        if theta_trajectories is None:
            self.theta_trajectories = [make_as_trajectory(self.make_random_walk(origin=rng.uniform(0, 2*np.pi),
                                                                                           duration=4,
                                                                                           step_size=np.pi/32,
                                                                                           nsteps=50)) for x in range(self.n_points)]
        else:
            self.theta_trajectories = [make_as_trajectory(x) for x in theta_trajectories] 

        if phi_trajectories is None:
            self.phi_trajectories = [make_as_trajectory(self.make_random_walk(origin=rng.uniform(-np.pi/2, +np.pi/2),
                                                                              duration=4,
                                                                              step_size=np.pi/32,
                                                                              nsteps=50)) for x in range(self.n_points)]
        else:
            self.phi_trajectories = [make_as_trajectory(x) for x in phi_trajectories] 

        self.stim_object = spv_shapes.GlVertices()

        self.stim_object_template = spv_shapes.GlSphericalPoints(sphere_radius=self.sphere_radius,
                                                                color=self.color,
                                                                theta=[0],
                                                                phi=[0])
        
    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):

        self.stim_object = spv_shapes.GlVertices()
        for pt in range(self.n_points):
            new_theta = return_for_time_t(self.theta_trajectories[pt], t)
            # Bounce phi back from pi to 0. Shift by pi/2 because of offset in where point is rendered in stimpack.visual_stim.shapes
            new_phi = return_for_time_t(self.phi_trajectories[pt], t) % np.pi - np.pi/2
            self.stim_object.add(copy.copy(self.stim_object_template).rotate(new_theta,  # yaw
                                                                             new_phi,  # pitch
                                                                             0))

class MovingDotField(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)
        self.draw_mode = 'POINTS'

    def configure(self, n_points=20, point_size=20, sphere_radius=1, color=[1, 1, 1, 1],
                  speed=40, signal_direction=0, coherence=1.0, random_seed=0, sphere_pitch=0):
        """
        Collection of moving points. Tunable coherence.

        Note that points are all the same size, so no area correction is made for perspective
        """
        self.n_points = n_points
        self.point_size = point_size
        self.sphere_radius = sphere_radius
        self.color = color
        self.speed = speed  # Deg/sec
        self.signal_direction = signal_direction  # In theta/phi plane. [0, 360] degrees
        self.coherence = coherence  # [0-1]
        self.random_seed = random_seed
        self.sphere_pitch = sphere_pitch  # Degrees. Pitch to the entire sphere on which dots move. Shifts signal direction axes

        self.stim_object = spv_shapes.GlVertices()

        self.stim_object_template = spv_shapes.GlSphericalPoints(sphere_radius=self.sphere_radius,
                                                      color=self.color,
                                                      theta=[0],
                                                      phi=[0])

        # Set random seed
        rng = default_rng(self.random_seed)

        self.starting_theta = rng.uniform(0, 2*np.pi, self.n_points)
        self.starting_phi = rng.uniform(-np.pi/2, +np.pi/2, self.n_points)

        # Make velocity vectors for each point
        self.velocity_vectors = []
        is_signal = rng.choice([False, True], self.n_points, p=[1-self.coherence, self.coherence])
        for pt in range(self.n_points):
            if is_signal[pt]:
                dir = self.signal_direction
            else:
                dir = rng.uniform(0, 360)

            vec = self.speed*np.array([np.cos(np.deg2rad(dir)), np.sin(np.deg2rad(dir))])
            self.velocity_vectors.append(vec)

    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        sphere_pitch_rad = np.radians(self.sphere_pitch)

        self.stim_object = spv_shapes.GlVertices()
        for pt in range(self.n_points):
            d_xy = self.velocity_vectors[pt] * t  # Change in (theta, phi) position, in degrees
            new_theta = self.starting_theta[pt] + np.radians(d_xy[0])
            # Bounce phi back from pi to 0. Shift by pi/2 because of offset in where point is rendered in stimpack.visual_stim.shapes
            new_phi = (self.starting_phi[pt] + np.radians(d_xy[1])) % np.pi - np.pi/2
            self.stim_object.add(copy.copy(self.stim_object_template).rotate(new_theta,  # yaw
                                                                             new_phi,  # pitch
                                                                             0).rotate(0, sphere_pitch_rad, 0))

class MovingDotField_Cylindrical(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)
        self.draw_mode = 'POINTS'

    def configure(self, n_points=20, point_size=20, cylinder_radius=1, color=[1, 1, 1, 1],
                  speed=40, signal_direction=0, coherence=1.0, random_seed=0,
                  cylinder_pitch=0, phi_limits=[0, 180]):
        """
        Collection of moving points that move on a rotating cylinder. Tunable coherence.

        Note that points are all the same size, so no area correction is made for perspective
        """
        self.n_points = n_points
        self.point_size = point_size
        self.cylinder_radius = cylinder_radius
        self.color = color
        self.speed = speed  # Deg/sec
        self.signal_direction = signal_direction  # In theta/phi plane. [0, 360] degrees
        self.coherence = coherence  # [0-1]
        self.random_seed = random_seed
        # Pitch to the entire cylinder on which dots move. Shifts signal direction axes
        # Note this pitch happens after the phi limits, so ultimate phi limits are changed by pitch
        self.cylinder_pitch = cylinder_pitch  # Degrees.
        self.phi_limits = phi_limits  # [lower, upper], degrees. Default = entire elevation range (0, 180)

        self.stim_object = spv_shapes.GlVertices()

        # Set random seed
        rng = default_rng(self.random_seed)
        self.starting_theta = rng.uniform(0, 360, self.n_points)  # degrees
        self.starting_phi = rng.uniform(self.phi_limits[0], self.phi_limits[1], self.n_points)  # degrees

        self.stim_object_list = []
        self.dir_list = []
        is_signal = rng.choice([False, True], self.n_points, p=[1-self.coherence, self.coherence])
        for pt in range(self.n_points):
            if is_signal[pt]:
                self.dir_list.append(np.radians(self.signal_direction))
            else:
                self.dir_list.append(np.radians(rng.uniform(0, 360)))

            self.stim_object_list.append(spv_shapes.GlCylindricalPoints(cylinder_radius=self.cylinder_radius,
                                                             color=self.color,
                                                             theta=[self.starting_theta[pt]],
                                                             phi=[self.starting_phi[pt]]))

    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        cyl_pitch = np.radians(self.cylinder_pitch)
        dtheta = np.radians(self.speed * t)
        self.stim_object = spv_shapes.GlVertices()
        for pt in range(self.n_points):
            self.stim_object.add(self.stim_object_list[pt].rotz(dtheta).roty(self.dir_list[pt]).rotx(cyl_pitch))

class MovingDotField_MotionPulse_Cylindrical(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)
        self.draw_mode = 'POINTS'

    def configure(self, n_points=20, point_size=20, cylinder_radius=1, color=[1, 1, 1, 1],
                  speed=40, signal_direction=0, coherence=1.0, random_seed=0,
                  cylinder_pitch=0, phi_limits=[0, 180]):
        """
        Collection of moving points that move on a rotating cylinder. Tunable coherence.

        Note that points are all the same size, so no area correction is made for perspective
        """
        self.n_points = n_points
        self.point_size = point_size
        self.cylinder_radius = cylinder_radius
        self.color = color
        self.speed = speed  # Deg/sec
        self.signal_direction = signal_direction  # In theta/phi plane. [0, 360] degrees
        self.coherence = coherence  # [0-1]
        self.random_seed = random_seed
        # Pitch to the entire cylinder on which dots move. Shifts signal direction axes
        # Note this pitch happens after the phi limits, so ultimate phi limits are changed by pitch
        self.cylinder_pitch = cylinder_pitch  # Degrees.
        self.phi_limits = phi_limits  # [lower, upper], degrees. Default = entire elevation range (0, 180)

        self.stim_object = spv_shapes.GlVertices()

        # Set random seed
        rng = default_rng(self.random_seed)
        #self.starting_theta = rng.uniform(0, 360, self.n_points)  # degrees
        self.starting_theta = [0]* self.n_points  # degrees

        self.starting_phi = rng.uniform(self.phi_limits[0], self.phi_limits[1], self.n_points)  # degrees

        self.stim_object_list = []
        self.dir_list = []
        is_signal = rng.choice([False, True], self.n_points, p=[1-self.coherence, self.coherence])
        for pt in range(self.n_points):
            if is_signal[pt]:
                self.dir_list.append(np.radians(self.signal_direction))
            else:
                self.dir_list.append(np.radians(rng.uniform(0, 360)))

            self.stim_object_list.append(spv_shapes.GlCylindricalPoints(cylinder_radius=self.cylinder_radius,
                                                             color=self.color,
                                                             theta=[self.starting_theta[pt]],
                                                             phi=[self.starting_phi[pt]]))

    def eval_at(self, t, fly_position=[0, 0, 0], fly_heading=[0, 0]):
        cyl_pitch = np.radians(self.cylinder_pitch)
        dtheta = np.radians(self.speed * t)
        self.stim_object = spv_shapes.GlVertices()
        for pt in range(self.n_points):
            self.stim_object.add(self.stim_object_list[pt].rotz(dtheta).roty(self.dir_list[pt]).rotx(cyl_pitch))

class UniformMovingDotField_Cylindrical(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)
        self.draw_mode = 'POINTS'

    def configure(self, n_points=20, point_size=20, cylinder_radius=1, color=[1, 1, 1, 1],
                  speed=40, direction=0, random_seed=0, cylinder_pitch=0, phi_limits=[0, 180]):
        """
        Collection of moving points that move on a rotating cylinder. Tunable coherence.

        Note that points are all the same size, so no area correction is made for perspective
        """
        self.n_points = n_points
        self.point_size = point_size
        self.cylinder_radius = cylinder_radius
        self.color = color
        self.speed = speed  # Deg/sec
        self.direction = direction  # In theta/phi plane. [0, 360] degrees
        self.random_seed = random_seed
        # Pitch to the entire cylinder on which dots move. Shifts direction axes
        # Note this pitch happens after the phi limits, so ultimate phi limits are changed by pitch
        self.cylinder_pitch = cylinder_pitch  # Degrees.
        self.phi_limits = phi_limits  # [lower, upper], degrees. Default = entire elevation range (0, 180)

        self.stim_object = spv_shapes.GlVertices()

        # Set random seed
        rng = default_rng(self.random_seed)
        self.starting_theta = rng.uniform(0, 360, self.n_points)  # degrees
        self.starting_phi = rng.uniform(self.phi_limits[0], self.phi_limits[1], self.n_points)  # degrees

        self.stim_object_list = []
        self.direction_rad = np.radians(self.direction)
        self.stim_object_template = spv_shapes.GlCylindricalPoints(cylinder_radius=self.cylinder_radius,
                                                                color=self.color,
                                                                theta=self.starting_theta,
                                                                phi=self.starting_phi)


    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        cyl_pitch = np.radians(self.cylinder_pitch)
        dtheta = np.radians(self.speed * t)
        self.stim_object = copy.copy(self.stim_object_template).rotz(dtheta).roty(self.direction_rad).rotx(cyl_pitch)

class ProgressiveStarfield(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)
        self.draw_mode = 'POINTS'

    def configure(self, point_size=20, color=[1, 1, 1, 1],
                  point_locations=[[+5, 0, 0]],
                  y_offset=0):
        """

        Note that points are all the same size, so no area correction is made for perspective
        """
        self.point_size = point_size
        self.color = color
        self.point_locations = point_locations  # list of (x, y, z) meters for each dot
        self.y_offset = make_as_trajectory(y_offset)  # Can pass Y offset as trajectory to specify approach

        self.stim_template = spv_shapes.GlPointCollection(locations=self.point_locations,
                                                        color=self.color)

        self.stim_object = copy.copy(self.stim_template)

    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        y_position = return_for_time_t(self.y_offset, t)
        self.stim_object = copy.copy(self.stim_template).translate([0, y_position, 0])

class MovingEllipsoid(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=1000)

    def configure(self, x_length=1, y_length=1, z_length=1, color=(1, 1, 1, 1), x=0, y=0, z=0, yaw=0, pitch=0, roll=0, n_subdivisions=6):
        """
        Stimulus consisting of a rectangular patch on the surface of a sphere. Patch is rectangular in spherical coordinates.

        :param x_length: meters, x length of ellipsoid
        :param y_length: meters, y length of ellipsoid
        :param z_length: meters, z length of ellipsoid
        :param color: (r,g,b,a) or mono. Color of the ellipsoid
        :param x: meters, x position of center of ellipsoid
        :param y: meters, y position of center of ellipsoid
        :param z: meters, z position of center of ellipsoid
        :param yaw: degrees, rotation around z axis
        :param pitch: degrees, rotation around y axis
        :param roll: degrees, rotation around x axis
        *Any of these params can be passed as a trajectory dict to vary these as a function of time elapsed
        """
        self.x_length = make_as_trajectory(x_length)
        self.y_length = make_as_trajectory(y_length)
        self.z_length = make_as_trajectory(z_length)
        self.color = make_as_trajectory(color) if color is not None else None
        self.x = make_as_trajectory(x)
        self.y = make_as_trajectory(y)
        self.z = make_as_trajectory(z)
        self.yaw = make_as_trajectory(yaw)
        self.pitch = make_as_trajectory(pitch)
        self.roll = make_as_trajectory(roll)
        
        self.stim_object_template = GlIcosphere(return_for_time_t(self.color, 0), n_subdivisions).scale(0.5)
        
    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        x_length = return_for_time_t(self.x_length, t)
        y_length = return_for_time_t(self.y_length, t)
        z_length = return_for_time_t(self.z_length, t)
        color    = return_for_time_t(self.color, t)
        x        = return_for_time_t(self.x, t)
        y        = return_for_time_t(self.y, t)
        z        = return_for_time_t(self.z, t)
        yaw    = return_for_time_t(self.yaw, t)
        pitch      = return_for_time_t(self.pitch, t)
        roll    = return_for_time_t(self.roll, t)

        self.stim_object = copy.copy(self.stim_object_template
                                    ).scale(np.array((x_length, y_length, z_length)).reshape(3,1)
                                    ).rotate(radians(yaw), radians(pitch), radians(roll)
                                    ).translate((x, y, z))
        # if self.color is not None: #TODO: fix coloring
        #     self.stim_object.set_color(util.get_rgba(color))

class MovingFly(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen, num_tri=10000)

    def configure(self, size=1, color=(1, 1, 1, 1), x=0, y=0, z=0, yaw=0, pitch=0, roll=0, n_subdivisions=6):
        """
        Stimulus consisting of a rectangular patch on the surface of a sphere. Patch is rectangular in spherical coordinates.

        :param size: meters, body scaling
        :param color: (r,g,b,a) or mono. Color of the box
        :param x: meters, x position of center of ellipsoid
        :param y: meters, y position of center of ellipsoid
        :param z: meters, z position of center of ellipsoid
        :param yaw: degrees, rotation around z axis
        :param pitch: degrees, rotation around y axis
        :param roll: degrees, rotation around x axis
        *Any of these params can be passed as a trajectory dict to vary these as a function of time elapsed
        """
        self.size = make_as_trajectory(size)
        self.color = make_as_trajectory(color) if color is not None else None
        self.x = make_as_trajectory(x)
        self.y = make_as_trajectory(y)
        self.z = make_as_trajectory(z)
        self.yaw = make_as_trajectory(yaw)
        self.pitch = make_as_trajectory(pitch)
        self.roll = make_as_trajectory(roll)
        
        self.stim_object_template = GlFly(size=1, color=return_for_time_t(self.color, 0))
        
    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        size     = return_for_time_t(self.size, t)
        color    = return_for_time_t(self.color, t)
        x        = return_for_time_t(self.x, t)
        y        = return_for_time_t(self.y, t)
        z        = return_for_time_t(self.z, t)
        yaw      = return_for_time_t(self.yaw, t)
        pitch    = return_for_time_t(self.pitch, t)
        roll     = return_for_time_t(self.roll, t)

        self.stim_object = copy.copy(self.stim_object_template
                                    ).scale(size
                                    ).rotate(radians(yaw), radians(pitch), radians(roll)
                                    ).translate((x, y, z))
        # if self.color is not None: #TODO: fix coloring
        #     self.stim_object.set_color(util.get_rgba(color))


class FixedDepthCueTower(BaseProgram):
    def __init__(self, screen):
        super().__init__(screen=screen)

    def configure(self, color=[1, 0, 0, 1], cylinder_radius=0.5, cylinder_height=0.5, cylinder_location=[+5, 0, 0], n_faces=16, 
                  fix_size_cue=False, fix_parallax_cue=False):
        """
        Cylindrical tower object in arbitrary x, y, z coords.

        :param color: [r,g,b,a] color of cylinder. Applied to entire texture, which is monochrome
        :param cylinder_radius: meters
        :param cylinder_height: meters
        :param cylinder_location: [x, y, z] location of the center of the cylinder, meters
        :param n_faces: number of quad faces to make the cylinder out of
        """
        self.color = color
        self.cylinder_radius = cylinder_radius
        self.cylinder_height = cylinder_height
        self.cylinder_location = cylinder_location
        self.n_faces = n_faces
        self.fix_size_cue = fix_size_cue
        self.fix_parallax_cue = fix_parallax_cue

        subject_xyz = np.array([0, 0, 0])
        self.starting_distance = np.sqrt(np.sum((self.cylinder_location-subject_xyz)**2, axis=0))
        # Half-angular width of cylinder from starting position given cylinder_radius and cylinder_location
        self.starting_angular_halfsize = np.arctan(self.cylinder_radius / self.starting_distance)  # radians

        self.stim_object_template = spv_shapes.GlCylinder(cylinder_height=self.cylinder_height,
                                            cylinder_radius=self.cylinder_radius,
                                            color=self.color,
                                            n_faces=self.n_faces)
        
    def eval_at(self, t, subject_position={'x':0, 'y':0, 'z':0, 'theta':0, 'phi':0, 'roll':0}):
        subject_xyz = np.array([subject_position['x'], subject_position['y'], subject_position['z']])
        current_distance = np.sqrt(np.sum((self.cylinder_location-subject_xyz)**2, axis=0))
        
        if self.fix_size_cue:
            new_radius = current_distance * np.tan(self.starting_angular_halfsize)
            size_scale_factor = new_radius / self.cylinder_radius
        else:
            size_scale_factor = 1.0

        if self.fix_parallax_cue:
            new_translation = subject_xyz
            # Introduce a scale factor to size the towers as if the distance was changing
            desired_angular_halfsize = np.arctan(np.tan(self.starting_angular_halfsize) * self.starting_distance/current_distance)
            new_radius = self.starting_distance * np.tan(desired_angular_halfsize)
            parallax_scale_factor = new_radius / self.cylinder_radius
        else:
            new_translation = [0, 0, 0]
            parallax_scale_factor = 1.0


        self.stim_object = copy.copy(self.stim_object_template
                                    ).scale(size_scale_factor * parallax_scale_factor
                                    ).translate(np.array(self.cylinder_location) + np.array(new_translation))
