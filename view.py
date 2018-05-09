"""GUI Elements for a Tower Defence game"""

import tkinter as tk
import math

from utilities import rotate_point
from tower_view import TowerView
from range_view import RangeView

__author__ = "Benjamin Martin and Brae Webb"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"


class GameView(tk.Canvas):
    """Game view which displays the user interface for the Towers game"""

    def __init__(self, master, size=(6, 6), cell_size=40, **kwargs):
        """
        Constructs a GameView inside the tkinter master widget

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget
            size (tuple<int, int>): The (row, column) size of the grid
            cell_size (int): The size of each cell in the game, in pixels
            **kwargs: Any other keyword arguments for the Canvas constructor
        """

        self.size = size
        self.cell_size = cell_size

        self.width, self.height = width, height = tuple(i * self.cell_size
                                                        for i in self.size)

        tk.Canvas.__init__(self, master, width=width, height=height, **kwargs,
                           highlightthickness=0)

    @staticmethod
    def calculate_bounds(position, size):
        """
        Calculate the top left and bottom right coordinates of a position with
        a given size

        Parameters:
            position (tuple<int, int>): The middle position to calculate for
            size (tuple<int, int>): The width and height of the item

        Returns:
            tuple<tuple<int, int>,
                  tuple<int, int>>: The top left and bottom right positions
        """
        x, y = position
        width, height = size

        top_left = x - width // 2, y - height // 2
        bottom_right = x + width // 2, y + height // 2

        return top_left, bottom_right

    def draw_borders(self, borders, fill='old lace'):
        """
        Draw the border lines of the game view

        Parameters:
            borders (iter<tuple<int, int>,
                          tuple<int, int>>): A series of pixel positions for
                                             laying out the borders of the view
            fill (str): The colour of the borders to draw
        """
        for start, end in borders:
            self.create_line(start, end, fill=fill, tag='border')

    def draw_enemies(self, enemies):
        """
        Draw a list of enemies to the view, simultaneously removing previous
        enemies

        Parameters:
            enemies (list<AbstractEnemy>): A list of enemies to draw to the view
        """
        self.delete('enemy')
        for enemy in enemies:
            top_left, bottom_right = self.calculate_bounds(enemy.position,
                                                           enemy.size)

            # create
            self.create_oval(top_left, bottom_right, tags='enemy',
                             fill='white smoke')
            extent = enemy.percentage_health() * 360
            if extent == 360:  # because tkinter is lame
                extent = 359.9999

            self.create_arc(top_left, bottom_right, tags='enemy',
                            fill=enemy.colour, start=45, extent=-extent,
                            outline='')

    def draw_towers(self, towers):
        """
        Draw a list of towers to the view, simultaneously removing previous
        towers

        Parameters:
            towers (list<AbstractTower>): A list of towers to draw to the view
        """
        self.delete('tower')
        for tower in towers.values():
            TowerView.draw(self, tower, cell_size=self.cell_size)

        self.tag_raise('shadow')

    def draw_obstacles(self, obstacles):
        """
        Draw a list of obstacles to the view, simultaneously removing previous
        obstacles

        Parameters:
            obstacles (list<Unit>): A list of obstacles to draw to the view
        """
        self.delete('obstacle')
        # assuming missile
        for missile in obstacles:
            x, y = missile.position

            length, width = missile.size

            dx, dy = rotate_point((length / 2, width / 2), missile.rotation)

            head = x + dx, y + dy
            tail = x - dx, y - dy

            self.create_line(head, tail, tag='obstacle')

    def draw_path(self, coordinates):
        """
        Draws a path on the game view
        Useful to preview where the enemies will travel after placing a tower
        
        Parameters:
            coordinates (list[tuple[int, int]]): A list of (x, y) coordinate pairs
        """

        self.delete('path')
        tag = self.create_line(coordinates, tag='path', dash=(2, 4))
        self.tag_lower(tag)
        self.tag_lower('border')

    def draw_preview(self, tower, legal=True):
        """
        Draws a shadow of a tower over the game view
        Used for visual aid when placing a tower

        Parameter:
            tower (AbstractTower|None): The shadow tower or None if no tower
                                        should be drawn
        """
        self.delete("shadow", "range")

        if tower is None:
            return

        # draw a hover tower for placement
        if legal:
            tags = RangeView.draw(self, tower.range, tower.position,
                                  tower.cell_size)
            for tag in tags:
                self.itemconfig(tag, outline='green')

        top_left, bottom_right = tower.get_bounding_box()

        left, top = top_left
        right, bottom = bottom_right

        colour = tower.colour

        if legal:
            # TODO abstract
            self.create_oval(top_left, bottom_right, tag='shadow', fill=colour)
        else:
            self.create_line(top_left, bottom_right, tag='shadow', fill='black')
            self.create_line((right, top), (left, bottom), tag='shadow', fill='black')
