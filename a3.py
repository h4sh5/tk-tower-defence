import tkinter as tk

from model import TowerGame
from tower import SimpleTower, MissileTower, LaserTower
from enemy import SimpleEnemy, HardenedEnemy
from utilities import Stepper
from view import GameView
from level import AbstractLevel
from tower_view import TowerView
import math

BACKGROUND_COLOUR = "#4a2f48"

__author__ = "Haoxi Tan"



# Could be moved to a separate file, perhaps levels/simple.py, and imported
class MyLevel(AbstractLevel):
    """A simple game level containing examples of how to generate a wave"""
    waves = 20

    def get_wave(self, wave):
        """Returns enemies in the 'wave_n'th wave

        Parameters:
            wave_n (int): The nth wave

        Return:
            list[tuple[int, AbstractEnemy]]: A list of (step, enemy) pairs in the
                                             wave, sorted by step in ascending order 
        """
        enemies = []

        if wave == 1:
            # A hardcoded singleton list of (step, enemy) pairs

            enemies = [(10, SimpleEnemy())]

        elif wave == 2:
            # A hardcoded list of multiple (step, enemy) pairs

            enemies = [(5, HardenedEnemy()), (15, SimpleEnemy()), (30, SimpleEnemy())]


        elif 3 <= wave < 10:
            # List of (step, enemy) pairs spread across an interval of time (steps)

            steps = int(40 * (wave ** .5))  # The number of steps to spread the enemies across
            count = wave * 2  # The number of enemies to spread across the (time) steps

            for step in self.generate_intervals(steps, count):
                enemies.append((step, SimpleEnemy()))

        elif wave == 10:
            # Generate sub waves
            sub_waves = [
                # (steps, number of enemies, enemy constructor, args, kwargs)
                (50, 10, SimpleEnemy, (), {}),  # 10 enemies over 50 steps
                (100, None, None, None, None),  # then nothing for 100 steps
                (50, 10, SimpleEnemy, (), {})  # then another 10 enemies over 50 steps
            ]

            enemies = self.generate_sub_waves(sub_waves)

        else:  # 11 <= wave <= 20
            # Now it's going to get hectic

            sub_waves = [
                (
                    int(13 * wave),  # total steps
                    int(25 * wave ** (wave / 50)),  # number of enemies
                    SimpleEnemy,  # enemy constructor
                    (),  # positional arguments to provide to enemy constructor
                    {},  # keyword arguments to provide to enemy constructor
                ),
                # ...
            ]
            enemies = self.generate_sub_waves(sub_waves)

        return enemies


class StatusBar(tk.Frame):
    '''class for status bar'''

    def __init__(self, master):
        '''
        Constructs a status bar for the game

        Parameters:
            master (tk.Tk) the parent widget
        '''

        self._master = master

        self._status_bar = tk.Frame(self._master)
        self._status_bar.pack(expand=True, anchor=tk.N)

        self._wave_strvar = tk.StringVar()
        self._wave_label = tk.Label(self._status_bar, textvariable=self._wave_strvar)
        self._wave_label.pack(expand=True, side=tk.TOP)

        self._score_strvar = tk.StringVar()
        self._score_label = tk.Label(self._status_bar, textvariable=self._score_strvar)
        self._score_label.pack(expand=True, side=tk.TOP)

        self._coins_strvar = tk.StringVar()
        self._coins_image = tk.PhotoImage(file="images/coins.gif")
        self._coins_image_label = tk.Label(self._status_bar, image=self._coins_image)
        self._coins_label = tk.Label(self._status_bar, textvariable=self._coins_strvar)
        self._coins_image_label.pack(side=tk.LEFT,expand=True)
        self._coins_label.pack(side=tk.LEFT,expand=True)

        self._lives_strvar = tk.StringVar()
        self._lives_image = tk.PhotoImage(file="images/heart.gif")
        self._lives_image_label = tk.Label(self._status_bar, image=self._lives_image)
        self._lives_label = tk.Label(self._status_bar, textvariable=self._lives_strvar)
        self._lives_image_label.pack(side=tk.LEFT,expand=True)
        self._lives_label.pack(side=tk.LEFT,expand=True)

    def set_score(self, score):
        '''updates the score on the display
        Parameters:
            score (int)
        '''
        self._score_strvar.set("score: %d" % score)

    def set_coins(self, coins):
        '''updates the coins on the display
        Parameters:
            coins (int)
        '''
        self._coins_strvar.set(coins)

    def set_lives(self, lives):
        '''updates the lives on the display
        Parameters:
            lives (int)
        '''
        self._lives_strvar.set(lives)

    def set_wave(self, wave):
        '''updates the waves on the display
        Parameters:
            waves (int)
        '''
        self._wave_strvar.set("Wave: %d/20" % wave)


class ShopTowerView(tk.Frame):
    '''class for each shop tower item'''

    def __init__(self, master, tower, click_command, *args, **kwargs):#, *args, **kwargs):
        '''
        Constructs an individual shop tower view
    
        tower (AbstractTower)

        '''
        super().__init__(master, **kwargs)

        tower.position = (tower.cell_size//2, tower.cell_size//2)  # Position in centre
        tower.rotation = 3 * math.pi / 2  # Point up

        self._canvas = tk.Canvas(master, width=tower.cell_size, height=tower.cell_size,
            bg="#ff6600", bd=0, highlightthickness=0)
        self._canvas.pack(expand=True)

        TowerView.draw(self._canvas, tower, tower.cell_size)



    def set_available(self, enabled=True):
        '''set the status of the shop view

        Parameters:
            enabled (bool): if the player can afford the tower. If not the text
            will be red
        '''
        if enabled:
            self.configure(color='black')
        else:
            self.configure(color='red')



class TowerGameApp(Stepper):
    """Top-level GUI application for a simple tower defence game"""

    # All private attributes for ease of reading
    _current_tower = None
    _paused = False
    _won = None

    _level = None
    _wave = None
    _score = None
    _coins = None
    _lives = None

    _master = None
    _game = None
    _view = None

    def __init__(self, master: tk.Tk, delay: int = 20):
        """Construct a tower defence game in a root window

        Parameters:
            master (tk.Tk): Window to place the game into
        """

        self._master = master
        super().__init__(master, delay=delay)
        master.title("tkDefend")

        self._game = game = TowerGame()

        self.setup_menu()
        self._master.configure(menu=self._menu)

        # create a game view and draw grid borders
        self._view = view = GameView(master, size=game.grid.cells,
                                     cell_size=game.grid.cell_size,
                                     bg='#000033') # was antique white
        view.pack(side=tk.LEFT, expand=True)

        #have a menu frame on the right
        self._right_frame = tk.Frame(self._master)
        self._right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.Y)

        # Task 1.3 (Status Bar): instantiate status bar
        self._status_bar = StatusBar(self._right_frame)

        #shop goes between status bar and control frame
        shop = tk.Frame(self._right_frame, bg="#ff6600")
        shop.pack(side=tk.TOP, expand = True, anchor=tk.N, fill=tk.BOTH)


        towers = [
            SimpleTower,
            MissileTower,
            LaserTower
        ]

        # Create views for each tower & store to update if availability changes
        self._tower_views = []
        for tower_class in towers:
            tower = tower_class(self._game.grid.cell_size // 2)

            view = ShopTowerView(shop, tower,
                click_command=lambda class_=tower_class: self.select_tower(class_),
                bg="#ff6600", highlightbackground="#4b3b4a",bd=0,highlightthickness=0)

            view.pack(fill=tk.X)
            # Used to check if tower is affordable when refreshing view
            self._tower_views.append((tower, view))  

        # Task 1.5 (Play Controls): instantiate widgets here
        self._control_frame = tk.Frame(self._right_frame)
        self._control_frame.pack(expand=True)
        self._wave_button = tk.Button(self._control_frame,
            text="next wave", command=self.next_wave)
        self._wave_button.pack(side=tk.LEFT)

        self._play_button_text = tk.StringVar()
        self._play_button_text.set("play")
        self._play_button = tk.Button(self._control_frame, textvariable=self._play_button_text,
            command=self._toggle_paused)
        self._play_button.pack(side=tk.RIGHT)


        # bind game events
        game.on("enemy_death", self._handle_death)
        game.on("enemy_escape", self._handle_escape)
        game.on("cleared", self._handle_wave_clear)

        #Task 1.2 (Tower Placement): bind mouse events to canvas here
        #Binds left click, mouse motion and mouse leave
        self._view.bind("<Button-1>", self._left_click)
        self._view.bind("<Motion>", self._move)
        #self._view.bind("<ButtonRelease-1>", self._mouse_leave)
        self._view.bind("<Leave>",self._mouse_leave)
        self._view.bind("<Button-2>", self._right_click)

        #handling close window
        import sys
        if len(sys.argv) == 1:
            self._master.protocol("WM_DELETE_WINDOW", self._exit)
        #catching keyboard event Destroy
        #self._master.bind("<Destroy>", self._exit)

        # Level
        self._level = MyLevel()

        #self.select_tower(SimpleTower)
        self.select_tower(SimpleTower)

        self._view.draw_borders(game.grid.get_border_coordinates(), "#66ff66")

        # Get ready for the game
        self._setup_game()

        # Remove the relevant lines while attempting the corresponding section
        # Hint: Comment them out to keep for reference

        # # Task 1.2 (Tower Placement): remove these lines
        # towers = [
        #     ([(2, 2), (3, 0), (4, 1), (4, 2), (4, 3)], SimpleTower),
        #     ([(2, 5)], MissileTower)
        # ]

        # for positions, tower in towers:
        #     for position in positions:
        #         self._game.place(position, tower_type=tower)



    def setup_menu(self):
        '''
        Construct a file menu
        '''
        # Task 1.4: construct file menu here
        self._menu = tk.Menu(self._master)
        self._filemenu = tk.Menu(self._menu)

        self._filemenu.add_command(label="New Game", command=self._new_game)
        self._filemenu.add_command(label="Exit", command=self._exit)
        self._menu.add_cascade(label="File", menu=self._filemenu)

    

    def _toggle_paused(self, paused=None):
        """Toggles or sets the paused state

        Parameters:
            paused (bool): Toggles/pauses/unpauses if None/True/False, respectively
        """
        if paused is None:
            paused = not self._paused

        # Task 1.5 (Play Controls): Reconfigure the pause button here
        
        if paused:
            self.pause()
            self._play_button_text.set("play")
        else:
            self.start()
            self._play_button_text.set("pause")

        self._paused = paused

    def _setup_game(self):
        self._wave = 0
        self._score = 0
        self._coins = 1000 #was 50
        self._lives = 20

        self._won = False

        # Task 1.3 (Status Bar): Update status here
        self._status_bar.set_wave(self._wave)
        self._status_bar.set_score(self._score)
        self._status_bar.set_coins(self._coins)
        self._status_bar.set_lives(self._lives)

        # Task 1.5 (Play Controls): Re-enable the play controls here (if they were ever disabled)
        if self._wave_button.cget('state') != 'normal' or self._play_button.cget('state') != 'normal':
            self._wave_button.config(state=tk.NORMAL)
            self._play_button.config(state=tk.NORMAL)

        self._game.reset()

        # Auto-start the first wave
        self.next_wave()
        self._toggle_paused(paused=True)

    # Task 1.4 (File Menu): Complete menu item handlers here (including docstrings!)
    
    def _new_game(self):
        '''
        restarts the game
        '''

        
        #clears the enemies
        self._view.delete("enemy","tower")
        self._game.enemies = [] 
        self._setup_game()


    def _exit(self):
        '''
        exits the application
        '''
        confirm_window = tk.Toplevel(self._master)

        exit_label = tk.Label(confirm_window, text="Are you sure you want to exit?")
        exit_label.pack(pady=10)
        yes_button = tk.Button(confirm_window, text="Yes", command=self._master.destroy)
        yes_button.pack(side=tk.LEFT, padx=20)
        no_button = tk.Button(confirm_window, text="No", command=confirm_window.destroy)
        no_button.pack(side=tk.LEFT, padx=20)

        #quitting with keyboard
        def handle_return(event):
            self._master.destroy()

        confirm_window.bind("<Return>", handle_return)



    def refresh_view(self):
        """Refreshes the game view"""
        if self._step_number % 2 == 0:
            self._view.draw_enemies(self._game.enemies)
        self._view.draw_towers(self._game.towers)
        self._view.draw_obstacles(self._game.obstacles)


    def _step(self):
        """
        Perform a step every interval

        Triggers a game step and updates the view

        Returns:
            (bool) True if the game is still running
        """
        self._game.step()
        self.refresh_view()

        return not self._won

    # Task 1.2 (Tower Placement): Complete event handlers here (including docstrings!)
    # Event handlers: _move, _mouse_leave, _left_click
    def _move(self, event):
        """
        Handles the mouse moving over the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        if self._current_tower.get_value() > self._coins:
            return

        # move the shadow tower to mouse position
        position = event.x, event.y
        self._current_tower.position = position

        legal, grid_path = self._game.attempt_placement(position)

        # find the best path and covert positions to pixel positions
        path = [self._game.grid.cell_to_pixel_centre(position)
                for position in grid_path.get_shortest()]

        # Task 1.2 (Tower placement): Draw the tower preview here
        self._view.draw_preview(self._current_tower, legal)
        self._view.draw_path(path)


    def _mouse_leave(self, event):
        """
        Handles the mouse leaving the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """

        # Task 1.2 (Tower placement): Delete the preview
        # Hint: Relevant canvas items are tagged with: 'path', 'range', 'shadow'
        #       See tk.Canvas.delete (delete all with tag)
        self._view.delete("shadow", "range", "path")

    def _left_click(self, event):
        """
        Handles the mouse left clicking in the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        # retrieve position to place tower
        if self._current_tower is None:
            return

        position = event.x, event.y
        cell_position = self._game.grid.pixel_to_cell(position)

        if self._game.place(cell_position, tower_type=self._current_tower.__class__):
            # Task 1.2 (Tower placement): Attempt to place the tower being previewed
            legal, grid_path = self._game.attempt_placement(position)
            if legal:
                self._game.place(cell_position, self._current_tower)
                #refresh view upon placing a tower
                self._step()

    def _right_click(self, event):
        """
        Handles the mouse right clicking in the game view canvas.
        The tower in that cell position will be removed and 80% of its value 
        will be returned to the player.

        Parameter:
            event (tk.Event): Tkinter mouse event
        """

        position = event.x, event.y
        cell_position = self._game.grid.pixel_to_cell(position)

        removed_tower = self._game.remove(cell_position)
        self._coins += removed_tower.get_value()

        #updates coins string var to display coins
        self._status_bar.set_coins(self._coins)

            

    def next_wave(self):
        """Sends the next wave of enemies against the player"""
        if self._wave == self._level.get_max_wave():
            return

        self._wave += 1

        # Task 1.3 (Status Bar): Update the current wave display here
        self._status_bar.set_wave(self._wave)

        # Task 1.5 (Play Controls): Disable the add wave button here (if this is the last wave)
        if self._wave == 20:
            self._wave_button.config(state=tk.DISABLED)

        # Generate wave and enqueue
        wave = self._level.get_wave(self._wave)
        for step, enemy in wave:
            enemy.set_cell_size(self._game.grid.cell_size)

        self._game.queue_wave(wave)

    def select_tower(self, tower):
        """
        Set 'tower' as the current tower

        Parameters:
            tower (AbstractTower): The new tower type
        """
        print(tower)
        self._current_tower = tower(self._game.grid.cell_size)

    def _handle_death(self, enemies):
        """
        Handles enemies dying

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which died in a step
        """
        bonus = len(enemies) ** .5
        for enemy in enemies:
            self._coins += enemy.points
            self._score += int(enemy.points * bonus)

        # Task 1.3 (Status Bar): Update coins & score displays here
        self._status_bar.set_coins(self._coins)
        self._status_bar.set_score(self._score)

    def _handle_escape(self, enemies):
        """
        Handles enemies escaping (not being killed before moving through the grid

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which escaped in a step
        """
        self._lives -= len(enemies)
        if self._lives < 0:
            self._lives = 0

        # Task 1.3 (Status Bar): Update lives display here
        self._status_bar.set_lives(self._lives)

        # Handle game over
        if self._lives == 0:
            self._handle_game_over(won=False)

    def _handle_wave_clear(self):
        """Handles an entire wave being cleared (all enemies killed)"""
        if self._wave == self._level.get_max_wave():
            self._handle_game_over(won=True)


    def _handle_game_over(self, won=False):
        """Handles game over
        
        Parameter:
            won (bool): If True, signals the game was won (otherwise lost)
        """
        self._won = won
        self.stop()

        # Task 1.4 (Dialogs): show game over dialog here
        dialog_box = tk.Toplevel(self._master)
        dialog_box.title("Game Over")

        if won:
            message = "You won!"
        else:
            message = "You lost!"

        label = tk.Label(dialog_box, text=message)
        label.pack(padx=50,pady=20)

        ok_button = tk.Button(dialog_box, text="ok", command=dialog_box.destroy)
        ok_button.pack()

        #disable buttons if game over
        self._wave_button.config(state=tk.DISABLED)
        self._play_button.config(state=tk.DISABLED)



# Task 1.1 (App Class): Instantiate the GUI here

if __name__ == "__main__":
    '''main function, instantiates the GUI'''
    root = tk.Tk()
    app = TowerGameApp(root)
    root.mainloop()

