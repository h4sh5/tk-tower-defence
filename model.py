import random

from modules.ee import EventEmitter
from modules.matrix import get_adjacent_cells

from tower import SimpleTower
from enemy import SimpleEnemy
from path import Path
from type_hints import Point2DInt_T, Tuple

__author__ = "Benjamin Martin and Brae Webb"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"

CELL_SIZE = 60
PIXEL_SIZE = (24, 12)

GRID_SIZE = (6, 6)

class GridCoordinateTranslator:
    """Translates coordinates between cells in a grid (column, row) & pixels (x, y)

    Cells are treated as square
    """
    # cell is frequently used as a shorthand for cell position, as with pixel
    cells: Point2DInt_T  # The number of (column, row) cells in the grid
    cell_size: int  # The number of pixels wide & high each cell is
    pixels: Point2DInt_T  # The number of (x, y) pixels in the grid

    def __init__(self, cells: Tuple[int, int] = PIXEL_SIZE,
                 cell_size: int = CELL_SIZE):
        """Construct a coordinate translator

        Parameters:
            cells (tuple<int, int>): Grid dimensions
            cell_size (int): The side length of the cell
        """
        self.cells = cells
        self.cell_size = cell_size

        # convert grid dimensions to pixel dimensions
        self.pixels = tuple(i * cell_size for i in cells)

    def is_cell_valid(self, cell):
        """(bool) Returns True iff 'cell' position exists in the grid"""
        column, row = cell
        columns, rows = self.cells

        return 0 <= column < columns and 0 <= row < rows

    def cell_to_pixel_centre(self, cell):
        """(int, int) Returns the pixel position at the centre of 'cell'"""
        return tuple(int((i + .5) * self.cell_size) for i in cell)

    def cell_to_pixel_corner(self, cell):
        """(int, int) Returns the pixel position at the top-left corner of 'cell'"""
        return tuple(i * self.cell_size for i in cell)

    def pixel_to_cell(self, pixel):
        """(int, int) Returns the position of the cell that contains the pixel position"""
        return tuple(int(i // self.cell_size) for i in pixel)

    def pixel_to_cell_offset(self, pixel):
        """(float, float) Returns the fractional offset of a pixel position
        from the centre of the corresponding cell

        A fractional offset is the proportion of the cell's length that each
        pixel coordinate is away from the pixel centre, and hence each value
        of the result will be in the range [-0.5, 0.5]

        I.e.
             Cell Offset  | Position
            -----------------------------------------------------------------------
             (-0.5, -0.5) | Top-left corner
             ( 0.5,  0.5) | Bottom-right corner
             (   0,    0) | Centre
             (-0.25, 0.4) | Half way between the centre and the left edge,
                          | & 80% of the way between the centre and the bottom edge
        """
        return tuple((i / self.cell_size) % 1 - .5 for i in pixel)

    def get_border_coordinates(self, include_outer=True):
        """
        Yields the pixel coordinates for every border

        Parameters:
            include_outer (bool): includes outermost borders if True
        """
        offset = 1 if include_outer else 0
        width, height = self.pixels

        columns, rows = self.cells

        for column in range(1 - offset, columns + offset):
            x = column * self.cell_size
            yield (x, 0), (x, height)

        for row in range(1 - offset, rows + offset):
            y = row * self.cell_size
            yield (0, y), (width, y)


class TowerGame(EventEmitter):
    """Model for a game of tower defence"""
    _current_step = -1

    def __init__(self, size=GRID_SIZE, cell_size=CELL_SIZE):
        """Construct a new tower defence game"""
        super().__init__()

        self.grid = GridCoordinateTranslator(cells=size, cell_size=cell_size)

        self.towers = {}

        # assign the start and end point of the enemies
        self._start, self._end = (-1, 1), (self.grid.cells[0], 1)

        # recalculate the path for enemies to travel avoiding current towers
        self.path = self.generate_path()

        self.obstacles = []

        for position, tower in self.towers.items():
            tower.position = self.grid.cell_to_pixel_centre(position)

        self.enemies = []
        self._unspawned_enemies = []

    def is_wave_over(self):
        """(bool) Returns True iff there is no wave in progress"""
        return len(self._unspawned_enemies) == 0 and len(self.enemies) == 0

    # TODO: add property for active tower to get_neighbours in generate_path & refactor this
    def generate_path(self, *extra_towers):
        """
        Determine if a valid path can be made with extra towers added.

        Parameters:
            extra_towers (set<tuple<int, int>>): Set of extra tower positions to add

        Returns:
            (bool) True iff a path can be made with towers in the extra positions
        """
        # gather all the current tower positions and include new towers
        towers = set(self.towers.keys())
        towers.update(extra_towers)

        def get_neighbours(cell, from_=True):  # pylint: disable=unused-argument
            """Yields all the positions neighbouring cell

            Parameters:
                cell (tuple<int, int>): The cell to check for neighbours
                from_ (bool): If true, searches from cell to neighbour, else from neighbour to cell
                              *not used in this implementation*
            """
            for node in get_adjacent_cells(cell):
                if (self.grid.is_cell_valid(node) and node not in towers) \
                        or node == self._start or node == self._end:
                    yield node

        # create a path from start to end avoiding towers
        path = Path(self._start, self._end, get_neighbours)
        self._start, self._end = path.start, path.end

        return path

    def remove(self, cell):
        """Removes a tower from the given 'cell' position
        
        Parameters:
            cell (tuple<int, int>): The grid position from which to remove the tower
        
        Raises:
            KeyError if no tower exists at cell
            
        Return:
            AbstractTower: The tower that was removed
        """
        if not self.grid.is_cell_valid(cell) or cell not in self.towers:
            raise KeyError(f"No tower exists at {cell}")

        tower = self.towers.pop(cell)
        self.path = self.generate_path()

        return tower

    def place(self, cell, tower_type=SimpleTower):
        """
        Attempt to place a tower in the given grid position

        Tower can not be placed if:
          the xy position cannot be mapped to a grid position
          the position already has a tower
          placing a tower at the position blocks the enemies path

        Parameters:
            cell (tuple<int, int>): The grid position at which to place the tower
            tower_type (AbstractTower): The type of tower to place

        Returns:
            (bool): True iff the tower can be placed in the position
        """
        # ensure the position is valid within the grid
        if not self.grid.is_cell_valid(cell):
            return False

        # ensure that there isn't a tower at the position
        if cell in self.towers:
            return False

        tower = tower_type(self.grid.cell_size)
        tower.position = self.grid.cell_to_pixel_centre(cell)

        # check a path can still be made
        try:
            self.generate_path(cell)
        except KeyError:
            return False

        self.towers[cell] = tower
        self.path = self.generate_path()
        return True

    def _step_obstacles(self):
        """Performs a single time step for all obstacles"""
        remaining_obstacles = []
        for obstacle in self.obstacles:
            if obstacle.step():
                remaining_obstacles.append(obstacle)

        self.obstacles = remaining_obstacles

    def _step_enemies(self):
        """Performs a single time step for all enemies"""
        remaining_enemies = []
        dead_enemies = []
        escaped_enemies = []

        for _, enemy in enumerate(self.enemies):
            # remove dead enemies
            if enemy.is_dead():
                dead_enemies.append(enemy)
                continue

            # keep enemies who are still in bounds
            if enemy.step(self.grid, self.path):
                remaining_enemies.append(enemy)
            else:
                escaped_enemies.append(enemy)

        # emit enemy events
        if len(escaped_enemies) > 0:
            self.emit("enemy_escape", escaped_enemies)
        self.emit("enemy_death", dead_enemies)

        self.enemies = remaining_enemies
        if len(remaining_enemies) == 0 and len(self._unspawned_enemies) == 0:
            self.emit("cleared")

    def _step_towers(self):
        """Performs a single time step for all towers"""
        # process tower abilities (attacks, etc.)
        for tower in self.towers.values():
            tower.step()
            for enemy in self.enemies:
                if tower.is_position_in_range(enemy.get_real_position()):

                    # TODO: replace with generic
                    obstacles = tower.attack(enemy)

                    if obstacles:
                        self.obstacles.extend(obstacles)

    def _spawn_enemies(self):
        """Spawn all the enemies to be spawned in the current time-step"""
        while len(self._unspawned_enemies):
            # gather next enemy to be spawned
            start_step, enemy = self._unspawned_enemies[-1]

            # ensure they are meant to be spawned in this step
            if start_step <= self._current_step:
                self._unspawned_enemies.pop()

                # spawn enemy
                position = self.grid.cell_to_pixel_centre(self.path.start)

                enemy.position = position
                self.enemies.append(enemy)
            else:
                break

    def step(self):
        """Performs a single time step of the game

        Returns:
            (bool): True iff the game is still running
        """
        self._current_step += 1

        if self._current_step % 2 == 0:
            # perform all step actions
            self._step_obstacles()
            self._step_enemies()
            self._step_towers()
            self._spawn_enemies()

        return len(self._unspawned_enemies) or len(self.enemies)

    def reset(self):
        self.towers = {}
        self._unspawned_enemies = []

    def queue_wave(self, wave, clear=False):
        """Queues a wave of enemies to spawn into the game

        Parameters:
            wave (iter<tuple<int, AbstractEnemy>>):
                The wave of enemies to spawn
                A list of tuples for each enemy to spawn
                The first tuple element is the step number to spawn the enemy
                The second tuple element is the enemy object
            clear (bool): Clears existing wave, iff True
        """
        wave = [(step + self._current_step, enemy) for step, enemy in wave]

        if not clear:
            wave += self._unspawned_enemies

        self._unspawned_enemies = sorted(wave, key=lambda x: x[0], reverse=True)

        if clear:
            self.enemies = []

    def send_wave(self, clear=False, enemies=20, steps=200):
        """Send a wave of randomly generated enemies
        
        Parameters:
            clear (bool): If True, clears the current enemies
            enemies (int): The number of enemies to generate
            steps (int): The number of steps over which to generate the enemies
        """
        print(enemies, steps)
        offset = self._current_step + 1

        wave = []

        # randomly generate enemies and their start steps
        for _ in range(enemies):
            step = int(offset + steps - random.triangular(0, steps, 0))
            wave.append((step, SimpleEnemy(self.grid.cell_size)))

        self.queue_wave(wave, clear=clear)

    # TODO: comment
    def attempt_placement(self, position):
        # convert mouse position to grid coordinates
        grid_position = self.grid.pixel_to_cell(position)

        # make a path and determine whether it is possible
        try:
            path = self.generate_path(grid_position)
            legal = True
        except KeyError:
            path = self.path
            legal = False

        if grid_position in self.towers:
            legal = False

        return legal, path
