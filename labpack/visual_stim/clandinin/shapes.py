import numpy as np
from math import radians
from stimpack.visual_stim import shapes as spv_shapes
from stimpack.visual_stim import util as spv_util
import icosphere

class GlVertices(spv_shapes.GlVertices):
    def rot1_scale_rot2(self, yaw1, pitch1, roll1, scale_x, scale_y, scale_z, yaw2, pitch2, roll2):
        '''
        rot2 @ scale @ rot1 @ vertices
        '''
        return GlVertices(vertices=spv_util.rot1_scale_rot2(self.vertices, yaw1, pitch1, roll1, scale_x, scale_y, scale_z, yaw2, pitch2, roll2), colors=self.colors, tex_coords=self.tex_coords)

class GlIcosphere(GlVertices):
    def __init__(self, colors=(1, 1, 1, 1), n_subdivisions=6):
        '''
        :param colors: list of colors, one for each face or a single color for all faces; None for default colors
        :param n_subdivisions: number of subdivisions of each edge of the icosahedron. 
                                nr_vertex = 12 + 10 * (nu**2 -1) (e.g. 1=12, 2=42, 3=92, 4=162, 5=252, 6=362)
                                nr_face = 20 * nu**2 (e.g. 1 = 20, 2 = 80, 3 = 180, 4 = 320, 5 = 500, 6 = 720)
        '''
        super().__init__()

        vertices, faces = icosphere.icosphere(n_subdivisions)
        
        if colors is None:
            colors = np.linspace(0, 1, len(faces))
        elif isinstance(colors, tuple):
            colors = [colors] * len(faces)
        elif isinstance(colors, (int, float)):
            colors = [(colors, colors, colors, 1.0)] * len(faces)
        else:
            assert len(colors) == len(faces), 'Number of colors must match number of faces'
        
        for face, color in zip(faces, colors):
            self.add(spv_shapes.GlTri(vertices[face[0]], vertices[face[1]], vertices[face[2]], spv_util.get_rgba(color)))
            
class GlFly(GlVertices):
    '''
    Fly facing +y axis, thorax at origin.
    Y-length is roughly about 1m.
    '''
    
    class Head(GlVertices):
        class Eye(GlVertices):
            def __init__(self, color=(1,0,0,1), n_subdivisions=5):
                super().__init__()
                self.add(GlIcosphere(colors=color, n_subdivisions=n_subdivisions
                                    ).scale(np.asarray([0.75, 0.5, 1]).reshape(3,1)
                                    ))

        def __init__(self, head_color=(0,0,0,1), eye_color=(1,0,0,1), n_subdivisions=5):
            super().__init__()
            # Head
            self.add(GlIcosphere(colors=head_color, n_subdivisions=n_subdivisions
                                 ).scale(np.asarray([0.5625, 0.5, 0.625]).reshape(3,1)
                                 ))

            # Eyes (left, right)
            self.add(GlFly.Head.Eye(color=eye_color, n_subdivisions=n_subdivisions
                                    ).scale(0.5).rotz(radians(+20)).translate((+0.175, 0.225, 0)))
            self.add(GlFly.Head.Eye(color=eye_color, n_subdivisions=n_subdivisions
                                    ).scale(0.5).rotz(radians(-20)).translate((-0.175, 0.225, 0)))
    
    class Thorax(GlVertices):
        class Wing(GlVertices):
            def __init__(self, color=(0.5,0.5,0.5,1)):
                super().__init__()
                # Wing
                self.add(spv_shapes.GlCircle(color=color, center=(0, 0, 0), radius=1.0, n_steps=36
                                    ).scale(np.asarray([0.25, 0.5, 0.5]).reshape(3,1)
                                    ).rotx(np.pi/2
                                    ))
        def __init__(self, thorax_color=(0.2,0.2,0.2,1), wing_color=(0.5,0.5,0.5,1), n_subdivisions=5):
            super().__init__()
            # color = getColorTuple(color)

            # Thorax
            self.add(GlIcosphere(colors=thorax_color, n_subdivisions=n_subdivisions
                                 ).scale(np.asarray([0.67, 0.5, 0.5]).reshape(3,1)
                                 ))
            
            # Wings (L, R)
            self.add(GlFly.Thorax.Wing(color=wing_color
                                ).scale(2
                                ).rotate(np.deg2rad(+5), np.deg2rad(5), np.deg2rad(-10)
                                ).translate((-0.265, -0.83, 0.33)))
            self.add(GlFly.Thorax.Wing(color=wing_color
                                ).scale(2
                                ).rotate(np.deg2rad(-5), np.deg2rad(5), np.deg2rad(+10)
                                ).translate((+0.265, -0.83, 0.33)))
    
    class Abdomen(GlVertices):
        def __init__(self, color=(0,0,0,1), n_subdivisions=5):
            super().__init__()
            self.add(GlIcosphere(colors=color, n_subdivisions=n_subdivisions
                                ).scale(np.asarray([0.35, 0.5, 0.27]).reshape(3,1)
                                ))

    def __init__(self, size=1, color=None, n_subdivisions=5):
        super().__init__()
        
        if color is None:
            color = {}
        elif isinstance(color, tuple):
            color = {'head':color, 
                     'thorax':color, 
                     'abdomen':color, 
                     'wing':color, 
                     'eye':color}
        
        if 'head' not in color:
            color['head'] = (0.1,0.1,0.1,1)
        if 'thorax' not in color:
            color['thorax'] = (0.2,0.2,0.2,1)
        if 'abdomen' not in color:
            color['abdomen'] = (0.1,0.1,0.1,1)
        if 'wing' not in color:
            color['wing'] = (0.3,0.3,0.3,0.5)
        if 'eye' not in color:
            color['eye'] = (1,0,0,1)
        
        # Head
        self.add(GlFly.Head(head_color=color['head'], eye_color=color['eye'], n_subdivisions=n_subdivisions
                            ).scale(0.28
                            ).rotx(np.deg2rad(-20)
                            ).translate((0, 0.25, 0)))

        # Thorax
        self.add(GlFly.Thorax(thorax_color=color['thorax'], wing_color=color['wing'], n_subdivisions=n_subdivisions
                            ).scale(0.375
                            ).translate((0, 0, 0.025)))

        # Abdomen
        self.add(GlFly.Abdomen(color=color['abdomen'], n_subdivisions=n_subdivisions
                            ).scale(0.7
                            ).rotx(np.deg2rad(20)
                            ).translate((0, -0.25, -0.0375)))
        
        self.vertices = spv_util.scale(spv_util.translate(self.vertices, (0, 0.1, 0)), size)
