import math

from core import Unit, Point2D
from enemy import AbstractEnemy
from range_ import AbstractRange, CircularRange, PlusRange, DonutRange
from type_hints import Num_T
from utilities import Countdown, euclidean_distance, angular_difference, normalise_vector, rotate_point, rotate_toward, \
    angle_between

__author__ = "Benjamin Martin"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"


class AbstractTower(Unit):
    cool_down_steps: int
    cool_down: Countdown
    colour: str
    base_cost: int
    level_cost: int

    range: AbstractRange

    def __init__(self, cell_size: int, level: int = 1):
        super().__init__(cell_size)
        if self.cool_down_steps != 0:
            self.cool_down = Countdown(self.cool_down_steps)

        self.level = level

    def get_value(self):
        return self.base_cost + (self.level - 1) * self.level_cost

    def step(self):
        if self.cool_down_steps != 0:
            self.cool_down.step()

    def is_position_in_range(self, pixel_position):
        """(bool) Returns True iff 'pixel_position' exists within this range"""
        point = (Point2D(*pixel_position) - Point2D(*self.position)) / self.cell_size

        return self.range.contains(tuple(point))

    def attack(self, target):
        raise NotImplementedError("Subclasses must implement attack")


class SimpleTower(AbstractTower):
    rotation = math.pi * .25
    grid_size = (.9, .9)
    range = CircularRange(1.5)
    cool_down_steps = 0
    base_cost = 20
    level_cost = 15

    colour = 'violet red'

    def attack(self, target: AbstractEnemy):
        angle = angle_between(self.position, target.get_real_position())
        partial_angle = rotate_toward(self.rotation, angle, (1 / 6) * math.pi)
        self.rotation = partial_angle

        if partial_angle == angle:
            target.damage(1, 'projectile')

        return []


class Missile(Unit):
    grid_size = .2, 0
    speed = 0.3
    damage = 150

    def __init__(self, cell_size: Num_T, target: AbstractEnemy, rotation: int = 0):
        super().__init__(cell_size)
        self.target = target
        self.rotation = rotation

        self.pixel_speed = self.speed * cell_size

    def step(self):
        if self.target.is_dead():
            # TODO: acquire another target
            return False

        # move toward the target
        angle = angle_between(self.position, self.target.get_real_position())

        delta_angle = angular_difference(self.rotation, angle)
        radius = euclidean_distance(self.position, self.target.get_real_position())
        vector = Point2D(*self.target.get_real_position()) - Point2D(*self.position)

        if radius <= self.pixel_speed:
            print('collided')
            self.rotation = angle
            self.position = self.target.get_real_position()
            self.target.damage(self.damage, 'explosive')
            return False

        direction = 1 if delta_angle > 0 else -1
        self.rotation = rotate_toward(self.rotation, angle, (1 / 3) * math.pi)

        dx2, dy2 = tuple(self.pixel_speed * i for i in normalise_vector(vector))

        x, y = self.position
        self.position = x + dx2, y + dy2
        return True


class MissileTower(SimpleTower):
    rotation = math.pi * .25
    grid_size = (.9, .9)
    cool_down_steps = 10
    base_cost = 80
    level_cost = 60

    range = DonutRange(1.5, 4.5)

    colour = 'snow'

    def attack(self, target: AbstractEnemy):
        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, (1 / 3) * math.pi)

        to_remove = []

        self.rotation = partial_angle

        if angle == partial_angle:
            if self.cool_down.is_done():
                self.cool_down.start()

                missile = Missile(self.cell_size, target)
                missile.rotation = angle
                x, y = self.position
                diameter, _ = self.grid_size
                size = self.cell_size

                dx, dy = rotate_point((size * diameter / 2, 0), angle)

                missile.position = x + dx, y + dy

                missile.step()

                to_remove = [missile]

        return to_remove


class PulseTower(AbstractTower):
    grid_size = (.9, .9)
    cool_down_steps = 20
    base_cost = 60
    level_cost = 45

    range = PlusRange(0.5, 2.5)

    colour = '#621156'  # Spanish republican purple

    def attack(self, target: AbstractEnemy):
        if self.cool_down.is_done():
            self.cool_down.start()
            print('firing pulse')

            # TODO: send pulse
