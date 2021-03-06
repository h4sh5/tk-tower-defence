"""Enemy classes for a simple tower defence game

All enemies should inherit from AbstractEnemy (either directly or from one of its subclasses)
"""

from core import Unit
from utilities import rectangles_intersect, get_delta_through_centre
import random

__author__ = "Benjamin Martin and Brae Webb"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.1.0"


class AbstractEnemy(Unit):
    """An enemy for the towers to defend against"""
    speed = None

    # Must be overridden/implemented!
    name: str
    colour: str
    points: int
    live_damage = 1

    def __init__(self, grid_size=(.2, .2), grid_speed=1 / 12, health=100):
        """Construct an abstract enemy

        Note: Do not construct directly as class is abstract

        Parameters:
            grid_size (tuple<int, int>): The relative (width, height) within a cell
            grid_speed (float): The relative speed within a grid cell
            health (int): The maximum health of the enemy
        """
        self.grid_speed = grid_speed
        self.health = self.max_health = health

        super().__init__(None, grid_size, 0)  # allow enemy's to be position- & sizeless initially

    def set_cell_size(self, cell_size: int):
        """Sets the cell size for this unit to 'cell_size'"""
        super().set_cell_size(cell_size)
        self.speed = cell_size * self.grid_speed

    def is_dead(self):
        """(bool) True iff the enemy is dead i.e. health below zero"""
        return self.health <= 0

    def percentage_health(self):
        """(float) percentage of current health over maximum health"""
        return self.health / self.max_health

    def damage(self, damage: int, type_: str):
        """Inflict damage on the enemy

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        raise NotImplementedError("damage method must be implemented by subclass")

    def __repr__(self):
        return self.name


class SimpleEnemy(AbstractEnemy):
    """Basic type of enemy"""
    name = "Simple Enemy"
    colour = '#E23152'  # Amaranth

    points = 5
    live_damage = 1

    def __init__(self, grid_size=(.2, .2), grid_speed=5/60, health=100):
        super().__init__(grid_size, grid_speed, health)


    def damage(self, damage, type_):
        """Inflict damage on the enemy

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        #debug

        self.health -= damage
        if self.health < 0:
            self.health = 0

    def step(self, data):
        """Move the enemy forward a single time-step

        Parameters:
            grid (GridCoordinateTranslator): Grid the enemy is currently on
            path (Path): The path the enemy is following

        Returns:
            bool: True iff the new location of the enemy is within the grid
        """
        grid = data.grid
        path = data.path

        # Repeatedly move toward next cell centre as much as possible
        movement = self.grid_speed
        while movement > 0:
            cell_offset = grid.pixel_to_cell_offset(self.position)

            # Assuming cell_offset is along an axis!
            offset_length = abs(cell_offset[0] + cell_offset[1])

            if offset_length == 0:
                partial_movement = movement
            else:
                partial_movement = min(offset_length, movement)

            cell_position = grid.pixel_to_cell(self.position)
            try:
                delta = path.get_best_delta(cell_position)
            except KeyError:
                return None

            # Ensures enemy will move to the centre before moving toward delta
            dx, dy = get_delta_through_centre(cell_offset, delta)

            speed = partial_movement * self.cell_size
            self.move_by((speed * dx, speed * dy))
            self.position = tuple(int(i) for i in self.position)

            movement -= partial_movement

        intersects = rectangles_intersect(*self.get_bounding_box(), (0, 0), grid.pixels)
        return intersects or grid.pixel_to_cell(self.position) in path.deltas


class SwarmEnemy(SimpleEnemy):
    """A type of enemy that is faster and smaller than SimpleEnemy,
    but comes in a swarm. Has a random blue or yellow colour to mimic python"""

    name = 'Swarm Enemy'
    points = 1
    live_damage = 1

    def __init__(self, grid_size=(.15, .15), grid_speed=5.1/60, health=80):
        super().__init__(grid_size, grid_speed, health)


class InvincibleEnemy(SimpleEnemy):
    """An enemy that cannot be killed; not useful, just a proof of concept"""
    name = "Invincible Enemy"
    colour = '#4D4C5B'  # Porpoise

    def damage(self, damage, type_):
        """Enemy never takes damage

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        return

class HardenedEnemy(AbstractEnemy):
    """An enemy that is immune to projectile and explosive damage"""
    name = "Hardened Enemy"
    colour = "orange"

    points = 7
    live_damage = 2

    def __init__(self, grid_size=(.3, .3), grid_speed=3/60, health=100):
        super().__init__(grid_size, grid_speed, health)

    def damage(self, damage, type_):
        """Inflict damage on the enemy

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """
        if type_ == "projectile" or type_ == "explosive":
            return

        self.health -= damage
        if self.health < 0:
            self.health = 0

    def step(self, data):
        """Move the enemy forward a single time-step

        Parameters:
            grid (GridCoordinateTranslator): Grid the enemy is currently on
            path (Path): The path the enemy is following

        Returns:
            bool: True iff the new location of the enemy is within the grid
        """
        grid = data.grid
        path = data.path


        # Repeatedly move toward next cell centre as much as possible
        movement = self.grid_speed
        while movement > 0:
            cell_offset = grid.pixel_to_cell_offset(self.position)

            # Assuming cell_offset is along an axis!
            offset_length = abs(cell_offset[0] + cell_offset[1])

            if offset_length == 0:
                partial_movement = movement
            else:
                partial_movement = min(offset_length, movement)

            cell_position = grid.pixel_to_cell(self.position)
            delta = path.get_best_delta(cell_position)

            # Ensures enemy will move to the centre before moving toward delta
            dx, dy = get_delta_through_centre(cell_offset, delta)

            speed = partial_movement * self.cell_size
            self.move_by((speed * dx, speed * dy))
            self.position = tuple(int(i) for i in self.position)

            movement -= partial_movement



        intersects = rectangles_intersect(*self.get_bounding_box(), (0, 0), grid.pixels)
        return intersects or grid.pixel_to_cell(self.position) in path.deltas


class SuperRichardEnemy(AbstractEnemy):
    """A super boss enemy.
    Upon half health he will start spawing swarm enemies.
    This enemy does not follow the path but head straight to the goal.
    """
    name = "Super Richard"
    colour = "red"

    points = 15
    health = 1500
    live_damage = 5
    id = 0


    def __init__(self, game, grid_size=(.6, .6), grid_speed=2.5/60, health=health):
        '''
        parameters:
            spawned_step (int): the number of steps when it is spawned
            game (TowerGame): instance of the game
        '''
        super().__init__(grid_size, grid_speed, health)
        self.spawn_swarm = game.queue_wave
        self.game = game

        self.swarm_count = 0

        SuperRichardEnemy.id += 1
        self.id = SuperRichardEnemy.id




    def damage(self, damage, type_):
        """Inflict damage on the enemy

        Parameters:
            damage (int): The amount of damage to inflict
            type_ (str): The type of damage to do i.e. projectile, explosive
        """

        self.health -= damage
        if self.health < 0:
            self.health = 0

    def step(self, data):
        """Move the enemy forward a single time-step

        Parameters:
            grid (GridCoordinateTranslator): Grid the enemy is currently on
            path (Path): The path the enemy is following

        Returns:
            bool: True iff the new location of the enemy is within the grid
        """
        grid = data.grid
        path = data.path


        #starts generating swarm enemies if below half life
        if self.health/SuperRichardEnemy.health <= 0.5: 

            swarm = [(5,  SwarmEnemy())]
            
            if self.swarm_count < 10:
                for i in range(5):
                    
                    for step, enemy in swarm:
                        enemy.set_cell_size(self.game.grid.cell_size)

                    self.spawn_swarm(swarm)
                    self.swarm_count += 1

        # Repeatedly move toward next cell centre as much as possible
        movement = self.grid_speed
        while movement > 0:
            cell_offset = grid.pixel_to_cell_offset(self.position)

            # Assuming cell_offset is along an axis!
            offset_length = abs(cell_offset[0] + cell_offset[1])

            if offset_length == 0:
                partial_movement = movement
            else:
                partial_movement = min(offset_length, movement)

            cell_position = grid.pixel_to_cell(self.position)
            delta = path.get_best_delta(cell_position)

            # Ensures enemy will move to the centre before moving toward delta
            dx, dy = get_delta_through_centre(cell_offset, delta)

            speed = partial_movement * self.cell_size
            self.move_by((speed * dx, speed * dy))
            self.position = tuple(int(i) for i in self.position)

            movement -= partial_movement

        intersects = rectangles_intersect(*self.get_bounding_box(), (0, 0), grid.pixels)
        return intersects or grid.pixel_to_cell(self.position) in path.deltas

