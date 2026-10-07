import maya.cmds as cmds
import math

"""
Control creation and configuration utilities for the Prop Rigging Toolkit.

Provides methods for creating control shapes and configuring control properties.
"""

class Controls:

    def __init__(self):
        pass

    def create_control(self, name, shape="circle", size=1.0):
        """Create an animator control."""
        pass

    def create_circle(self, name, size=1.0):
        """Create a circular control."""
        return cmds.circle(
            name=name,
            radius=size,
            normal=(0, 1, 0),
            constructionHistory=False
        )[0]

    def create_square(self, name, size=1.0):
        """Create a square control."""
        points = [
            (-size, 0, -size),
            (-size, 0, size),
            (size, 0, size),
            (size, 0, -size),
            (-size, 0, -size)
        ]

        return cmds.curve( name=name, degree=1, point=points )


    def create_sphere(self, name, size=1.0):
        """Create a sphere control."""
        pass


    def create_box(self, name, size=1.0):
        """Create a box-shaped control."""
        points = [
            (-size, -size, -size),
            (-size, -size, size),
            (-size, size, size),
            (-size, size, -size),
            (-size, -size, -size),

            (size, -size, -size),
            (size, -size, size),
            (size, size, size),
            (size, size, -size),
            (size, -size, -size),

            (-size, -size, size),
            (-size, size, size),
            (size, size, size),
            (size, -size, size),

            (-size, size, -size),
            (size, size, -size)
        ]

        return cmds.curve(name=name, degree=1, point=points)


    def create_triangle(self, name, size=1.0):
        """ Create a triangular control. """
        height = size * math.sqrt(3)

        points = [
            (-size, 0, -size / 2),
            (size, 0, -size / 2),
            (0, 0, height / 2),
            (-size, 0, -size / 2)
        ]

        return cmds.curve(
            name=name,
            degree=1,
            point=points
        )

    def create_arrow(self, name, size=1.0):
        points = [
            (-size, 0, 0),
            (0, 0, 0),
            (0, 0, size),
            (size * 0.5, 0, size * 0.5),
            (0, 0, size),
            (-size * 0.5, 0, size * 0.5),
            (0, 0, size),
        ]

        return cmds.curve(name=name, degree=1, point=points)


    def create_cross(self, name, size=1.0):
        """Create a cross-shaped control."""

        thickness = size * 0.35

        points = [
            (-size, 0, -thickness),
            (-thickness, 0, -thickness),
            (-thickness, 0, -size),
            (thickness, 0, -size),
            (thickness, 0, -thickness),
            (size, 0, -thickness),
            (size, 0, thickness),
            (thickness, 0, thickness),
            (thickness, 0, size),
            (-thickness, 0, size),
            (-thickness, 0, thickness),
            (-size, 0, thickness),
            (-size, 0, -thickness)
        ]

        return cmds.curve(name=name, degree=1, point=points)


    def freeze_transforms(self, control):
        """Freeze the transforms on a control."""
        pass

    def color_control(self, control, color):
        """Set the viewport color of a control."""

        shapes = cmds.listRelatives(control, shapes=True, noIntermediate=True)

        if not shapes:
            return

        for shape in shapes:
            cmds.setAttr(f"{shape}.overrideEnabled", True)
            cmds.setAttr(f"{shape}.overrideColor", color)