"""
Contains view logic for towers

Ideally, there would be a view class for each tower, inheriting from a super class (i.e. AbstractTowerView) with a more
complicated file structure. However, for simplicity's sake, this has been avoided in favour of a single view class with
methods for each kind of tower.

If you wish to add additional types of visuals for towers, simply inherit from this class
"""

#
#                         /-------------\
#                        /               \
#                       /                 \
#                      /                   \
#                      |   XXXX     XXXX   |
#                      |   XXXX     XXXX   |
#                      |   XXX       XXX   |
#                      \         X         /
#                       --\     XXX     /--
#                        | |    XXX    | |
#                        | |           | |
#                        | I I I I I I I |
#                        |  I I I I I I  |
#                         \              /
#                           --         --
#                             \-------/
#                     XXX                    XXX
#                   XXXXX                  XXXXX
#                   XXXXXXXXX         XXXXXXXXXX
#                           XXXXX   XXXXX
#                             XXXXXXX
#                           XXXXX   XXXXX
#                   XXXXXXXXX         XXXXXXXXXX
#                   XXXXX                  XXXXX
#                     XXX                    XXX
#                           **************
#                           *  BEWARE!!  *
#                           **************
#                       All ye who enter here:
#                  Most of the code in this module
#                      is twisted beyond belief!
#                         Tread carefully
#                  If you think you understand it,
#                             You Don't,
#                           So Look Again
#

import math
import tkinter as tk


import tower

__author__ = "Benjamin Martin"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"


class TowerView:
    # Sorting ensures child classes are given higher precedence than their parent classes
    draw_methods = sorted([
        (tower.SimpleTower, '_draw_simple'),
        (tower.MissileTower, '_draw_simple'),
        (tower.PulseTower, '_draw_simple'),
        (tower.AbstractTower, '_draw_simple'),
    ], key=lambda i: len(i[0].mro()), reverse=True)

    @classmethod
    def draw(cls, canvas: tk.Canvas, tower: tower.AbstractTower, cell_size, *args, **kwargs):
        method = None

        for key, method_name in cls.draw_methods:
            if isinstance(tower, key) or tower == key:
                method = getattr(cls, method_name)
                break

        if method is None:
            raise KeyError(f"Unable to find draw method for {tower}")

        return method(canvas, tower, cell_size, *args, **kwargs)

    @classmethod
    def _draw_simple(cls, canvas: tk.Canvas, tower_: tower.SimpleTower, cell_size, *args, **kwargs):
        x, y = tower_.position
        angle = tower_.rotation

        x_diameter, y_diameter = tower_.grid_size
        top_left, bottom_right = tower_.get_bounding_box()

        colour = tower_.colour

        return [canvas.create_oval(top_left, bottom_right, tag='tower', fill=colour),
                canvas.create_line(x, y, x + (x_diameter / 2) * cell_size * math.cos(angle),
                                   y + (y_diameter / 2) * cell_size * math.sin(angle),
                                   tag='tower')]
