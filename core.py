from abc import ABC
import math

from type_hints import Point2D_T, Num_T

__author__ = "Benjamin Martin"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"


class Unit(ABC):
    """A basic unit on the game field"""
    position: Point2D_T = (None, None)

    # Must be overridden/implemented!
    grid_size: Point2D_T

    def __init__(self, cell_size: Num_T=None):
        if cell_size:
            self.set_cell_size(cell_size)

    def set_cell_size(self, cell_size):
        self.size = tuple(i * cell_size for i in self.grid_size)
        self.cell_size = cell_size

    def get_bounding_box(self):
        x, y = self.position
        if x is None:
            return None

        width, height = self.size
        x0, y0 = x - width // 2, y - height // 2
        x1, y1 = x0 + width, y0 + height

        return (x0, y0), (x1, y1)


class Point2D:
    __slots__ = ['x', 'y']

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Point2D(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y

    def __sub__(self, other):
        return Point2D(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y

    def __floordiv__(self, other):
        return Point2D(self.x // other, self.y // other)

    def __truediv__(self, other):
        return Point2D(self.x / other, self.y / other)

    def __mul__(self, other):
        return Point2D(self.x * other, self.y * other)

    def __rmul__(self, other):
        return Point2D(self.x * other, self.y * other)

    def __iter__(self):
        yield self.x
        yield self.y

    def __str__(self):
        return str("Point2D({!r}, {!r})".format(self.x, self.y))

    def __gt__(self, other):
        return self.x < other.x and self.y < other.y

    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y

    def rotate(self, angle):
        """Rotates by 'angle' radians

        Parameters:
            angle (num): The angle by which to rotate
        """
        cos = math.cos(angle)
        sin = math.sin(angle)

        x = self.x
        y = self.y

        self.x = cos * x - sin * y
        self.y = sin * x + cos * y

    def tuple(self):
        """(num, num) Returns the tuple form of this point"""
        return self.x, self.y
