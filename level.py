"""Contains abstract level for generating waves and relevant utilities functions"""

__author__ = "Benjamin Martin and Brae Webb"
__copyright__ = "Copyright 2018, The University of Queensland"
__license__ = "MIT"
__version__ = "1.0.0"


class AbstractLevel:
    """A level in the game, with multiple waves of enemies"""
    EASY = 0
    NORMAL = 1
    HARD = 2

    waves = None

    def __init__(self, difficulty=NORMAL):
        self.difficulty = difficulty

    def get_wave(self, wave_n):
        """Returns enemies in the 'wave_n'th wave

        Parameters:
            wave_n (int): The nth wave

        Return:
            list[tuple[int, AbstractEnemy]]: A list of (step, enemy) pairs in the
                                             wave, sorted by step in ascending order 
        """
        raise NotImplementedError("get_wave must be implemented by a subclass")

    def get_max_wave(self):
        """(int) Returns the total number of waves"""
        return self.waves

    @staticmethod
    def generate_intervals(total, intervals):
        """Divides a total into even intervals
    
        Loosely equivalent to range(0, total, total/intervals), where each yield is an integer
    
        Parameters:
            total (float|int): The total to be divided into intervals
            intervals (int): The number of intervals
    
        Yield:
            int: Each interval
        """
        interval_step = total / intervals

        for i in range(intervals):
            yield int(interval_step * i)

    @classmethod
    # TODO: convert to class structure which can be added together
    def generate_sub_wave(cls, steps, count, enemy_class_, args=None, kwargs=None, offset=0):
        # TODO: docstring
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}

        for step in cls.generate_intervals(steps, count):
            yield step + offset, enemy_class_(*args, **kwargs)

    @classmethod
    def generate_sub_waves(cls, sub_waves):
        enemies = []
        offset = 0
        for steps, count, enemy_type, args, kwargs in sub_waves:
            if count is not None:
                enemies.extend(cls.generate_sub_wave(steps, count, enemy_type, args=args, kwargs=kwargs, offset=offset))

            offset += steps

        return enemies
