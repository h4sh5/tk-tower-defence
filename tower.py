"""
Tower classes for simple tower defence game

All towers should inherit from AbstractTower (either directly or from one of its subclasses)
"""

import math
from typing import Union

from core import Unit, Point2D, UnitManager
from enemy import AbstractEnemy
from range_ import AbstractRange, CircularRange, PlusRange, DonutRange
from utilities import Countdown, euclidean_distance, rotate_toward, angle_between, polar_to_rectangular, \
    rectangles_intersect


__author__ = "Benjamin Martin"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.1.1"


class AbstractTower(Unit):
    """Abstract representation for a tower"""
    name: str
    colour: str

    cool_down_steps: int
    cool_down: Countdown

    base_cost: int
    level_cost: int

    base_damage: int

    range: AbstractRange

    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=1, level: int = 1):
        super().__init__(None, grid_size, cell_size)

        self.rotation = rotation
        self.grid_size = grid_size

        self.cool_down = Countdown(self.cool_down_steps)

        self.base_damage = base_damage
        self.level = level

    def get_damage(self):
        """(int) Returns the amount of damage this tower can deal"""
        return self.level * self.base_damage

    def get_value(self):
        """(int) Returns the value of this tower (i.e. coin cost)"""
        return self.base_cost + (self.level - 1) * self.level_cost

    def is_position_in_range(self, pixel_position):
        """(bool) Returns True iff 'pixel_position' exists within this range"""
        point = (Point2D(*pixel_position) - Point2D(*self.position)) / self.cell_size

        return self.range.contains(tuple(point))

    def step(self, data):
        """Performs time step for tower
        Generally, time step involves attacking choice of target(s) from 'units.enemies'
        """

    def get_units_in_range(self, enemies: UnitManager, limit=0):
        """(AbstractEnemy) Yields enemies that are in-range of this tower
        
        Parameters:
            enemies (UnitManager): All enemies in the game
            
        Note:
            For efficiency, method could be extended to first convert to potentially
            valid buckets, and only search those rather than iterating through every enemy.
        """

        count = 0
        for enemy in enemies.get_closish(self.position):
            if self.is_position_in_range(enemy.position):
                yield enemy
                count += 1
                if limit == count:
                    break

    def get_unit_in_range(self, units) -> Union[AbstractEnemy, None]:
        """(AbstractEnemy) Returns an enemy that is in-range of this tower, else None if no
        such enemy is in range.
        
        Enemy is not guaranteed to be the closest to tower."""
        for unit in self.get_units_in_range(units, limit=1):
            return unit

        return None

    def _get_target(self, units) -> Union[AbstractEnemy, None]:
        """Returns previous target, else selects new one if previous is invalid
        
        Invalid target is one of:
            - dead
            - out-of-range
        
        Return:
            AbstractEnemy: Returns previous target, unless it is non-existent or invalid (see above),
                           Otherwise, selects & returns new target if a valid one can be found,
                           Otherwise, returns None
        """
        if self._target is None \
                or self._target.is_dead() \
                or not self.is_position_in_range(self._target.position):
            self._target = self.get_unit_in_range(units)

        return self._target


class SimpleTower(AbstractTower):
    """A simple tower with short range that rotates towards enemies and shoots projectiles at them"""
    name = 'Simple Tower'
    colour = '#E94A1F'  # Coquelicot

    range = CircularRange(1.5)
    cool_down_steps = 0

    base_cost = 30
    level_cost = 20

    rotation_threshold = (1 / 6) * math.pi

    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=5, level: int = 1):
        super().__init__(cell_size, grid_size, rotation, base_damage, level)

    def step(self, data):
        """Rotates toward 'target' and attacks if possible"""
        self.cool_down.step()

        target = self.get_unit_in_range(data.enemies)

        if target is None:
            return

        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, self.rotation_threshold)
        self.rotation = partial_angle

        if partial_angle == angle:
            target.damage(self.get_damage(), 'projectile')


class AbstractObstacle(Unit):
    """An obstacle created by a tower"""
    speed = None

    def __init__(self, position, grid_size, cell_size, grid_speed: Union[int, float] = 0, rotation=0, damage=0):
        self.grid_speed = grid_speed

        super().__init__(position, grid_size, cell_size)

        self.rotation = rotation
        self.damage = damage

    def set_cell_size(self, cell_size: int):
        """Sets the cell size for this unit to 'cell_size'"""
        super().set_cell_size(cell_size)
        self.speed = cell_size * self.grid_speed

    def step(self, units):
        """Performs a time step for this obstacle
        
        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from
            
        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        raise NotImplementedError("step must be implemented by a subclass")


class Missile(AbstractObstacle):
    """A simple projectile fired from a MissileTower"""
    name = "Missile"
    colour = '#F5F0E5'  # Eburnean

    rotation_threshold = (1 / 3) * math.pi

    def __init__(self, position, cell_size, target: AbstractEnemy, size=.2,
                 rotation: Union[int, float] = 0, grid_speed=.1, damage=10):
        super().__init__(position, (size, 0), cell_size, grid_speed=grid_speed, rotation=rotation, damage=damage)
        self.target = target


    def step(self, units):
        """Performs a time step for this missile
        
        Moves towards target and damages if collision occurs
        If target is dead, this missile expires
        
        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from
            
        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        if self.target.is_dead():
            return False, None

        # move toward the target
        radius = euclidean_distance(self.position, self.target.position)

        if radius <= self.speed:
            self.target.damage(self.damage, 'explosive')
            return False, None

        # Rotate toward target and move
        angle = angle_between(self.position, self.target.position)
        self.rotation = rotate_toward(self.rotation, angle, self.rotation_threshold)

        dx, dy = polar_to_rectangular(self.speed, self.rotation)
        x, y = self.position
        self.position = x + dx, y + dy

        return True, None


class MissileTower(SimpleTower):
    """A tower that fires missiles that track a target"""
    name = 'Missile Tower'
    colour = 'snow'

    cool_down_steps = 10

    base_cost = 150
    level_cost = 60

    range = DonutRange(1.5, 4.5)

    rotation_threshold = (1 / 3) * math.pi

    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=150, level: int = 1):
        super().__init__(cell_size, grid_size=grid_size, rotation=rotation, base_damage=base_damage, level=level)

        self._target: AbstractEnemy = None

    def _get_target(self, units) -> Union[AbstractEnemy, None]:
        """Returns previous target, else selects new one if previous is invalid
        
        Invalid target is one of:
            - dead
            - out-of-range
        
        Return:
            AbstractEnemy: Returns previous target, unless it is non-existent or invalid (see above),
                           Otherwise, selects & returns new target if a valid one can be found,
                           Otherwise, returns None
        """
        if self._target is None \
                or self._target.is_dead() \
                or not self.is_position_in_range(self._target.position):
            self._target = self.get_unit_in_range(units)

        return self._target

    def step(self, units):
        """Rotates toward 'target' and fires missile if possible"""
        self.cool_down.step()

        target = self._get_target(units.enemies)

        if target is None:
            return None

        # Rotate toward target
        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, self.rotation_threshold)

        self.rotation = partial_angle

        if angle != partial_angle or not self.cool_down.is_done():
            return None

        self.cool_down.start()

        # Spawn missile on tower
        missile = Missile(self.position, self.cell_size, target, rotation=self.rotation,
                          damage=self.get_damage(), grid_speed=.3)

        # Move missile to outer edge of tower
        radius = self.grid_size[0] / 2
        delta = polar_to_rectangular(self.cell_size * radius, partial_angle)
        missile.move_by(delta)

        return [missile]



class Pulse(AbstractObstacle):
    """A projectile fired from a PulseTower that damages all enemies it collides with"""
    name = "Pulse"
    colour = '#7F191C'  # Falu

    NORTH = (0, -1)
    SOUTH = (0, 1)
    EAST = (1, 0)
    WEST = (-1, 0)

    DIRECTIONS = [NORTH, EAST, SOUTH, WEST]

    base_damage = 30

    def __init__(self, position, cell_size, direction, size=.04,
                 rotation: Union[int, float] = 0, grid_speed=.35, damage=30, hits=20):
        super().__init__(position, (size, 0), cell_size, grid_speed=grid_speed, rotation=rotation, damage=damage)

        self.direction = direction
        self._damaged = set()
        self._hit_count = hits

    def step(self, units):
        """Performs a time step for this pulse

        Moves according to direction, damaging any enemies that are collided with along the way
        If hits is non-zero, this pulse expires if it has the number of enemies hit is at least 'hits',
        else continues until off the grid

        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from

        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        dx, dy = tuple(self.speed * i for i in self.direction)

        x, y = old_position = self.position
        self.position = new_position = x + dx, y + dy

        try:
            old_bucket = units.enemies.get_bucket_for_position(old_position)
            new_bucket = units.enemies.get_bucket_for_position(self.position)
        except IndexError:
            return False, None

        for enemy in old_bucket.union(new_bucket):
            if enemy in self._damaged:
                continue

            x1, y1 = old_position
            x2, y2 = new_position

            if x2 < x1:
                x1, x2 = x2, x1

            if y2 < y1:
                y1, y2 = y2, y1

            tl1, br1 = (x1, y1), (x2, y2)
            tl2, br2 = enemy.get_bounding_box()

            if rectangles_intersect(tl1, br1, tl2, br2):
                enemy.damage(self.damage, 'pulse')
                self._damaged.add(enemy)

                if self._hit_count and len(self._damaged) >= self._hit_count:
                    return False, None

        return True, None


class SlowTower(SimpleTower):
    '''a tower that slows down enemies'''
    name = 'Slow Tower'
    colour = '#6183B4'
    base_cost = 100
    level_cost = 120

    def step(self, data):
        """Rotates toward 'target' and attacks if possible"""
        self.cool_down.step()

        target = self.get_unit_in_range(data.enemies)

        if target is None:
            return

        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, self.rotation_threshold)
        self.rotation = partial_angle

        if partial_angle == angle:
            target.grid_speed = 1/12 / (self.get_damage()/1.8) 


class PulseTower(AbstractTower):
    """A tower that sends slow moving pulses out that damage all enemies in their path"""
    name = 'Pulse Tower'
    colour = '#6183B4'  # Glaucous

    cool_down_steps = 20

    base_cost = 60
    level_cost = 45


    range = PlusRange(0.5, 1.5)

    def step(self, units):
        """Fires pulses"""
        self.cool_down.step()

        if not self.cool_down.is_done():
            return None

        target = self.get_unit_in_range(units.enemies)

        if target is None:
            return None

        self.cool_down.start()

        pulses = []

        for direction in Pulse.DIRECTIONS:
            pulse = Pulse(self.position, self.cell_size, direction)
            pulse.move_by(Point2D(*direction) * (.4 * self.cell_size))
            pulses.append(pulse)

        return pulses



class Laser(AbstractObstacle):
    """A laser fired from a LaserTower"""


    name = "Laser"
    #colour = "#00FFFF" #Aqua
    colour = 'red'
    rotation_threshold = (1 / 3) * math.pi


    def __init__(self, position, cell_size, target: AbstractEnemy, size=30,
                 rotation: Union[int, float] = 0, grid_speed=.5, damage=10):
        
        super().__init__(position, (size, 0), cell_size, grid_speed=grid_speed, rotation=rotation, damage=damage)
        self.target = target
        self._rotation = rotation


    def step(self, units):
        """Performs a time step for this missile
        
        Moves towards target and damages if collision occurs
        If target is dead, this missile expires
        
        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from
            
        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        
        if self.target == None:
            return False, None

        if self.target.is_dead():
            return False, None

        
        # move toward the target
        #for enemy in units.enemies:
         #   radius = euclidean_distance(self.position, enemy.position)

            #if radius <= self.speed:
                #enemy.damage(self.damage, 'energy')
                #return False, None

        # new approach to laser
        x, y = old_position = self.position
        dx, dy = polar_to_rectangular(self.speed, self._rotation)
        self.position = new_position = x + dx, y + dy

        self._hit_count = 1000 


        try:
            old_bucket = units.enemies.get_bucket_for_position(old_position)
            new_bucket = units.enemies.get_bucket_for_position(self.position)
        except IndexError:
            return False, None

        for enemy in old_bucket.union(new_bucket):
            if -0.5 <= euclidean_distance(self.position, enemy.position) >= 0.5:
                enemy.damage(self.damage, 'energy')


        return True, None


class LaserTower(SimpleTower):
    """A tower that fires lasers at a target"""
    name = 'Laser Tower'
    colour = '#6600FF' # purple-ish

    cool_down_steps = 1 #insanely fast

    base_cost = 500
    level_cost = 400 

    range = CircularRange(4)

    rotation_threshold = (1 / 3) * math.pi

    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=2, level: int = 1):
        super().__init__(cell_size, grid_size=grid_size, rotation=rotation, base_damage=base_damage, level=level)

        self._target: AbstractEnemy = None

    def _get_target(self, units) -> Union[AbstractEnemy, None]:
        """Returns previous target, else selects new one if previous is invalid
        
        Invalid target is one of:
            - dead
            - out-of-range
            - off the map
        
        Return:
            AbstractEnemy: Returns previous target, unless it is non-existent or invalid (see above),
                           Otherwise, selects & returns new target if a valid one can be found,
                           Otherwise, returns None
        """
        if self._target is None \
                or self._target.is_dead() \
                or not self.is_position_in_range(self._target.position) \
                or self._target.position[0] > 400:
            self._target = self.get_unit_in_range(units)

        return self._target

    def step(self, units):
        """Rotates toward 'target' and fires laser if possible"""
        self.cool_down.step()

        target = self._get_target(units.enemies)

        # if there's no target or if the target is out of the map
        if target is None:
            return None

        
        # Rotate toward target
        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, self.rotation_threshold)

        self.rotation = partial_angle

        if angle != partial_angle or not self.cool_down.is_done():
            return None

        self.cool_down.start()

        # Spawn laser on tower
        laser = Laser(self.position, self.cell_size, target, rotation=self.rotation,
                          damage=self.get_damage(), grid_speed=.5)

        # Move laser to outer edge of tower
        radius = self.grid_size[0] / 2
        delta = polar_to_rectangular(self.cell_size * radius, partial_angle)
        laser.move_by(delta)


        return [laser]

class Inferno(Pulse):
    '''a pulse that deals energy damage'''

    colour = 'orange'
    name = 'Inferno'
    base_damage = 20


    def step(self, units):
        """Performs a time step for this pulse

        Moves according to direction, damaging any enemies that are collided with along the way
        If hits is non-zero, this pulse expires if it has the number of enemies hit is at least 'hits',
        else continues until off the grid

        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from

        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        dx, dy = tuple(self.speed * i for i in self.direction)

        x, y = old_position = self.position
        self.position = new_position = x + dx, y + dy

        try:
            old_bucket = units.enemies.get_bucket_for_position(old_position)
            new_bucket = units.enemies.get_bucket_for_position(self.position)
        except IndexError:
            return False, None

        for enemy in old_bucket.union(new_bucket):
            if enemy in self._damaged:
                continue

            x1, y1 = old_position
            x2, y2 = new_position

            if x2 < x1:
                x1, x2 = x2, x1

            if y2 < y1:
                y1, y2 = y2, y1

            tl1, br1 = (x1, y1), (x2, y2)
            tl2, br2 = enemy.get_bounding_box()

            if rectangles_intersect(tl1, br1, tl2, br2):
                enemy.damage(self.damage, 'energy')
                self._damaged.add(enemy)

                if self._hit_count and len(self._damaged) >= self._hit_count:
                    return False, None

        return True, None

class InfernoTower(PulseTower):
    '''a pulse tower that shoots infernos'''
    name = "Inferno Tower"
    colour = 'orange'
    cool_down_steps = 5
    base_cost = 100
    level_cost = 80

    range = PlusRange(0.5, 1.5)


    def step(self, units):
        """Fires pulses"""
        self.cool_down.step()

        if not self.cool_down.is_done():
            return None

        target = self.get_unit_in_range(units.enemies)

        if target is None:
            return None

        self.cool_down.start()

        infernos = []

        for direction in Inferno.DIRECTIONS:
            inferno = Inferno(self.position, int(self.cell_size), direction)
            inferno.move_by(Point2D(*direction) * (.4 * self.cell_size))
            infernos.append(inferno)

        return infernos



    

class Bullet(AbstractObstacle):
    """A simple projectile fired from a BulletTower"""
    name = "Bullet"
    colour = 'orange'  # Eburnean

    rotation_threshold = (1 / 3) * math.pi

    def __init__(self, position, cell_size, target: AbstractEnemy, size=.2,
                 rotation: Union[int, float] = 0, grid_speed=.1, damage=80):
        super().__init__(position, (size, 0), cell_size, grid_speed=grid_speed, rotation=rotation, damage=damage)
        self.target = target
        self.rotation = rotation

    def step(self, units):
        """Performs a time step for this missile
        
        Moves towards target and damages if collision occurs
        If target is dead, this missile expires
        
        Parameters:
            units.enemies (UnitManager): The unit manager to select targets from
            
        Return:
            (persist, new_obstacles) pair, where:
                - persist (bool): True if the obstacle should persist in the game (else will be removed)
                - new_obstacles (list[AbstractObstacle]): A list of new obstacles to add to the game, or None
        """
        if self.target.is_dead():
            return False, None

        # move toward the target
        radius = euclidean_distance(self.position, self.target.position)

        if radius <= self.speed:
            self.target.damage(self.damage, 'explosive')
            return False, None



        dx, dy = polar_to_rectangular(self.speed, self.rotation)
        x, y = self.position
        self.position = x + dx, y + dy

        return True, None

    

class GunTower(SimpleTower):
    '''a tower that shoots bullets but is better than simple tower'''
    name = "Gun Tower"
    colour = "grey"
    cool_down_steps = 4
    base_cost = 30

    def __init__(self, cell_size: int, grid_size=(.9, .9), rotation=math.pi * .25, base_damage=40, level: int = 1):
        super().__init__(cell_size, grid_size, rotation, base_damage, level)
        self._target = None


    def step(self, units):
        """Rotates toward 'target' and fires missile if possible"""
        self.cool_down.step()

        target = self._get_target(units.enemies)

        if target is None:
            return None

        # Rotate toward target
        angle = angle_between(self.position, target.position)
        partial_angle = rotate_toward(self.rotation, angle, self.rotation_threshold)

        self.rotation = partial_angle

        if angle != partial_angle or not self.cool_down.is_done():
            return None

        self.cool_down.start()

        # Spawn missile on tower
        bullet = Bullet(self.position, self.cell_size, target, rotation=self.rotation,
                          damage=self.get_damage(), grid_speed=.4)

        # Move missile to outer edge of tower
        radius = self.grid_size[0] / 2
        delta = polar_to_rectangular(self.cell_size * radius, partial_angle)
        bullet.move_by(delta)

        return [bullet]

