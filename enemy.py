from core import Unit
from type_hints import Point2D_T, Num_T
from utilities import inherit_docstrings, rectangles_intersect

__author__ = "Benjamin Martin and Brae Webb"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"


class AbstractEnemy(Unit):
    """An enemy for the towers to defend against"""
    position: Point2D_T
    size: Point2D_T
    health: int

    # Must be overridden/implemented!
    max_health: int
    colour: str
    points: int

    def __init__(self, cell_size: Num_T=None):
        """Construct an abstract enemy

        Note: Do not construct directly as class is abstract

        Parameters:
            cell_size (tuple<int, int>): The width,height of the enemy in pixels
        """
        super().__init__(cell_size=cell_size)
        self.health = self.max_health

    def is_dead(self):
        """(bool) True iff the enemy is dead i.e. health below zero"""
        return self.health <= 0

    def percentage_health(self):
        """(float) percentage of current health over maximum health"""
        return self.health / self.max_health

    # TODO: is this required?
    def get_real_position(self):
        return self.position

    def damage(self, damage: int, type_: str):
        """Inflict damage on the current enemy

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        raise NotImplementedError("damage method must be implemented by subclass")


@inherit_docstrings
class SimpleEnemy(AbstractEnemy):
    """Basic type of enemy"""
    max_health = 100
    grid_size = (.25, .25)
    speed = 5
    points = 5

    colour = 'indian red'

    def damage(self, damage, type_):
        self.health -= damage
        if self.health < 0:
            self.health = 0

    def step(self, grid, path):
        """Move the enemy forward a single time-step

        Parameters:
            grid (GridCoordinateTranslator): Grid the enemy is currently on
            path (Path): The path the enemy is following

        Returns:
            bool: True iff the new location of the enemy is within the grid
        """
        x, y = self.position

        position = grid.pixel_to_cell(self.position)
        grid_dx, grid_dy = path.get_best_delta(position)
        internal_x, internal_y = grid.pixel_to_cell_offset(self.position)

        # TODO: Simplify?
        if internal_x > 0:
            internal_x = 1
        elif internal_x < 0:
            internal_x = -1
        if internal_y > 0:
            internal_y = 1
        elif internal_y < 0:
            internal_y = -1

        if (internal_x, internal_y) not in ((0, 0), (grid_dx, grid_dy)):
            grid_dx, grid_dy = -internal_x, -internal_y

        # assumes grid_delta is a unit vector
        # would need to be normalised otherwise
        dx = grid_dx * self.speed
        dy = grid_dy * self.speed

        self.position = x + dx, y + dy
        intersects = rectangles_intersect(*self.get_bounding_box(), (0, 0), grid.pixels)

        return intersects or grid.pixel_to_cell(self.position) in path.deltas


@inherit_docstrings
class SteelEnemy(SimpleEnemy):
    max_health = 250
    colour = 'light sky blue'
    points = 100

    def damage(self, damage, type_):
        if type_ not in ('projectile',):
            super().damage(damage, type_)


@inherit_docstrings
class InvincibleEnemy(SimpleEnemy):
    colour = 'slate gray'

    def damage(self, damage, type_):
        return
