import tkinter as tk

from model import TowerGame
from tower import SimpleTower, MissileTower, LaserTower, InfernoTower, SlowTower, GunTower
from enemy import SimpleEnemy, HardenedEnemy, SuperRichardEnemy, SwarmEnemy
from utilities import Stepper
from view import GameView
from level import AbstractLevel
from advanced_view import TowerView
from high_score_manager import HighScoreManager 
import os.path

import math
import time


BACKGROUND_COLOUR = "#4a2f48"

__author__ = "Haoxi Tan"



#Could be moved to a separate file, perhaps levels/simple.py, and imported
class MyLevel(AbstractLevel):
    """A simple game level containing examples of how to generate a wave"""
    waves = 20

    def get_wave(self, wave, game):
        """Returns enemies in the 'wave_n'th wave

        Parameters:
            wave_n (int): The nth wave
            game (TowerGame): the instance of the game

        Return:
            list[tuple[int, AbstractEnemy]]: A list of (step, enemy) pairs in the
                                             wave, sorted by step in ascending order 
        """
        enemies = []

        if 1 <= wave <= 2:
            #A hardcoded singleton list of (step, enemy) pairs

            enemies = [ (10, SimpleEnemy()),(12, SimpleEnemy()),(14, SimpleEnemy())]


        elif 3 <= wave < 8:
            #List of (step, enemy) pairs spread across an interval of time (steps)

            steps = int(40 * (wave ** .5))  #The number of steps to spread the enemies across
            count = wave * 2  #The number of enemies to spread across the (time) steps

            for step in self.generate_intervals(steps, count):
                #make enemies have more health each wave!
                enemies.append((step, SimpleEnemy(health=wave/2*100)))
                #enemies.append((step+20, SwarmEnemy()))

        elif 7 <= wave < 10:
            #List of (step, enemy) pairs spread across an interval of time (steps)

            steps = int(40 * (wave ** .5))  #The number of steps to spread the enemies across
            count = wave  #The number of enemies to spread across the (time) steps

            for step in self.generate_intervals(steps, count):
                enemies.append((step, SimpleEnemy(health=wave/2*100)))
                enemies.append((step+20, HardenedEnemy(health=wave/2*100)))

        elif wave == 10:
            #Generate sub waves
            sub_waves = [
                #(steps, number of enemies, enemy constructor, args, kwargs)
                (50, 10, SimpleEnemy, (), {}),  #10 enemies over 50 steps
                (100, None, None, None, None),  #then nothing for 100 steps
                (50, 10, SimpleEnemy, (), {}),  #then another 10 enemies over 50 steps
                (30, 1, lambda game=game: SuperRichardEnemy(game,health=wave/2.5*1500), (), {}),
            ]

            enemies = self.generate_sub_waves(sub_waves)

        else:  #11 <= wave <= 20
            #Now it's going to get hectic

            sub_waves = [
                (
                    int(13 * wave),  #total steps
                    int(25 * wave ** (wave / 50)),  #number of enemies
                    SimpleEnemy,  #enemy constructor
                    (),  #positional arguments to provide to enemy constructor
                    {},  #keyword arguments to provide to enemy constructor
                ),
                (
                    int(13 * wave),  #total steps
                    int(25 * wave ** (wave / 50)),  #number of enemies
                    HardenedEnemy,  #enemy constructor
                    (),  #positional arguments to provide to enemy constructor
                    {},  #keyword arguments to provide to enemy constructor
                ),
                (
                    int(2 * wave),  #total steps
                    int(wave/8 + 1),  #number of enemies
                    lambda game=game: SuperRichardEnemy(game),  #enemy constructor
                    (),  #positional arguments to provide to enemy constructor
                    {},  #keyword arguments to provide to enemy constructor
                ),

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
        coins_file = os.path.join("images", "coins.gif")
        self._coins_image = tk.PhotoImage(file=coins_file)




        self._coins_image_label = tk.Label(self._status_bar, image=self._coins_image)
        self._coins_label = tk.Label(self._status_bar, textvariable=self._coins_strvar)
        self._coins_image_label.pack(side=tk.LEFT,expand=True)
        self._coins_label.pack(side=tk.LEFT,expand=True)



        self._lives_strvar = tk.StringVar()
        heart_file = os.path.join("images", "heart.gif")
        self._lives_image = tk.PhotoImage(file=heart_file)
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

    def __init__(self, master, tower, click_command, **kwargs):#, *args, **kwargs):
        '''
        Constructs an individual shop tower view including the tower on display
        and the command to execute upon clicked.
    
        tower (AbstractTower): the tower to display on the frame
        click_command: the command to run when the shop
            view is clicked on
        
        **kwargs: additional positional arguments
        '''
        super().__init__(master, **kwargs)
        self.configure(pady=10)

        self._tower = tower

        tower.position = (tower.cell_size//2, tower.cell_size//2)  #Position in centre
        tower.rotation = 3 * math.pi / 2  #Point up

        self._canvas = tk.Canvas(self, width=tower.cell_size, height=tower.cell_size,
            bg="#ff6600", bd=0, highlightthickness=0)
        self._canvas.pack(expand=True, side=tk.LEFT)

        TowerView.draw(self._canvas, tower)

        self._label = tk.Label(self, bg="#ff6600")
        self._label.configure(text="%s\nprice:%s" %(tower.name, tower.get_value()))
        self._label.pack(expand=True, side=tk.RIGHT)

        self.bind("<Button-1>", lambda event:click_command())
        self._canvas.bind("<Button-1>", lambda event:click_command())
        self._label.bind("<Button-1>", lambda event: click_command())


    def get_tower(self):
        '''return tower'''
        return self._tower.__class__


    def set_available(self, enabled=True):
        '''set the status of the shop view

        Parameters:
            enabled (bool): if the player can afford the tower. If not the text
            will be red
        '''
        self._enabled = enabled
        if enabled:
            self._label.configure(fg='black')
        else:
            self._label.configure(fg='red')

    def set_selected(self, selected):
        '''set a different colour once its selected 
        
        parameters:
            selected (bool): if it's selected or not.
        '''
        if selected:
            self.configure(bg='yellow')
            self._label.configure(bg='yellow')
            self._canvas.configure(bg='yellow')

        else:
            self.configure(bg='#ff6600')
            self._label.configure(bg='#ff6600')
            self._canvas.configure(bg='#ff6600')




class UpgradeControl(tk.Frame):
    '''controls the upgrade of the towers'''

    def __init__(self, master, tower, app):
        '''construct a upgrade control frame under the 
        play control frame
        
        There will be 3 levels in total and the tower is initially level 1.
        parameters:
            master (tk.Frame): the parent of the widget
            tower (AbstractTower)
            app (TowerGameApp): the instance of the TowerGameApp
        '''
        super().__init__(master)
        #know where the instance of the app is
        self._app = app

        #get price of the tower upgrade and its level
        self._tower = tower

        self._price = tower.level_cost

        self._level2_label = tk.Label(self, text="level 2: %d"%self._price)
        self._level2_label.pack(side=tk.LEFT, expand=True)

        self._level2_checkbox = tk.Checkbutton(self, 
            command=lambda:self.level_up(2))
        self._level2_checkbox.deselect()
        self._level2_checkbox.pack(side=tk.LEFT, expand=True)

        self._level3_label = tk.Label(self, text="level 3: %d"%self._price)
        self._level3_label.pack(side=tk.LEFT, expand=True)
       
        self._level3_checkbox = tk.Checkbutton(self, 
            command=lambda:self.level_up(3))
        self._level3_checkbox.deselect()
        self._level3_checkbox.pack(side=tk.LEFT, expand=True)

        #self.check_available()



    def level_up(self, level):
        '''level up the tower to a level,
        can only do one level at a time.
        parameters:
            level (int): level to level up to
        '''

        if not self._app._coins < self._price and (level == self._tower.level + 1) :
            self._app._coins -= self._price
            self._app._status_bar.set_coins(self._app._coins)
            self._tower.level = level 

            print('%s level %d!'%(self._tower.name,self._tower.level))

        else:
            if level == 2:
                self._level2_checkbox.deselect()
            elif level == 3:
                self._level3_checkbox.deselect()


    def check_status(self):
        '''
        checks the level of the current tower and selects/deselects the 
        checkbox accordingly.
        '''
        if self._tower.level == 2:
            self._level2_checkbox.select()
            self._level3_checkbox.deselect()

        elif self._tower.level == 3:
            self._level2_checkbox.select()
            self._level3_checkbox.select()

        else:
            self._level2_checkbox.deselect()
            self._level3_checkbox.deselect()
            


class TowerGameApp(Stepper):
    """Top-level GUI application for a simple tower defence game"""

    #All private attributes for ease of reading
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

        self._highscores = {}

        self.setup_menu()
        self._master.configure(menu=self._menu)

        #create a game view and draw grid borders
        self._view = view = GameView(master, size=game.grid.cells,
                                     cell_size=game.grid.cell_size,
                                     bg='#000033') #was antique white
        view.pack(side=tk.LEFT, expand=True)

        #have a menu frame on the right
        self._right_frame = tk.Frame(self._master)
        self._right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.Y)

        #Task 1.3 (Status Bar): instantiate status bar
        self._status_bar = StatusBar(self._right_frame)

        #shop goes between status bar and control frame
        shop = tk.Frame(self._right_frame, bg="#ff6600")
        shop.pack(side=tk.TOP, expand = True, anchor=tk.N, fill=tk.BOTH)


        self._towers = towers = [
            SimpleTower,
            SlowTower,
            InfernoTower,
            LaserTower,
            MissileTower,
            GunTower,
        ]

        self._towers.sort(key=lambda tower_class:tower_class.base_cost)

        #Create views for each tower & store to update if availability changes
        self._tower_views = []
        for tower_class in towers:
            tower = tower_class(self._game.grid.cell_size // 2)

            #lambda class_=tower_class: self.select_tower(class_)

            view = ShopTowerView(shop, tower, 
                lambda class_=tower_class: 
                    self.select_tower(class_),
                bg="#ff6600", highlightbackground="#4b3b4a",bd=0,highlightthickness=0)


            view.pack(fill=tk.X)
            #Used to check if tower is affordable when refreshing view
            self._tower_views.append((tower, view)) 



        #Task 1.5 (Play Controls): instantiate widgets here
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

        #6.3 initiate upgrade dictionary to store upgrade controls for each tower
        self._upgrade_controls = {}


        #bind game events
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

        #high scores
        self._high_score_manager = HighScoreManager()



        #handling close window
        import sys
        if len(sys.argv) == 1:
            self._master.protocol("WM_DELETE_WINDOW", self._exit)
        #catching keyboard event Destroy
        #self._master.bind("<Destroy>", self._exit)

        #Level
        self._level = MyLevel()

        #self.select_tower(SimpleTower)
        self.select_tower(SimpleTower)

        self._view.draw_borders(game.grid.get_border_coordinates(), "#66ff66")

        #Get ready for the game
        self._setup_game()

        #laser count
        self._laser_count = 0

    def setup_menu(self):
        '''
        Construct a file menu
        '''
        #Task 1.4: construct file menu here
        self._menu = tk.Menu(self._master)
        self._filemenu = tk.Menu(self._menu)

        self._filemenu.add_command(label="New Game", command=self._new_game)
        self._filemenu.add_command(label="High Scores", command=self._handle_highscores)
        self._filemenu.add_command(label="Exit", command=self._exit)

        self._menu.add_cascade(label="File", menu=self._filemenu)


    def _toggle_paused(self, paused=None):
        """Toggles or sets the paused state

        Parameters:
            paused (bool): Toggles/pauses/unpauses if None/True/False, respectively
        """
        #automatically start the first wave
        if self._wave == 0:
            self.next_wave()

        if paused is None:
            paused = not self._paused

        #Task 1.5 (Play Controls): Reconfigure the pause button here
        
        if paused:
            self.pause()
            self._play_button_text.set("play")
        else:
            self.start()
            self._play_button_text.set("pause")

        self._paused = paused

    def _setup_game(self):
        '''setup the game'''

        self._wave = 0
        self._score = 0
        self._coins = 100
        self._lives = 30

        self._won = False

        #Task 1.3 (Status Bar): Update status here
        self._status_bar.set_wave(self._wave)
        self._status_bar.set_score(self._score)
        self._status_bar.set_coins(self._coins)
        self._status_bar.set_lives(self._lives)

        #Task 1.5 (Play Controls): Re-enable the play controls here (if they were ever disabled)
        if self._wave_button.cget('state') != 'normal' or self._play_button.cget('state') != 'normal':
            self._wave_button.config(state=tk.NORMAL)
            self._play_button.config(state=tk.NORMAL)

        #set initial availability for tower views
        for tower, view in self._tower_views:
            if self._coins < tower.get_value():
                view.set_available(False)
            else: 
                view.set_available(True)

        self._game.reset()

        self._toggle_paused()

        #to store and retrive boss images
        self._view._boss_images = {}
        self._view.laser_counts = {}
        self._view.total_laser_count = 0

    #Task 1.4 (File Menu): Complete menu item handlers here (including docstrings!)
    
    def _new_game(self):
        '''
        restarts the game
        '''
        
        #clears the enemies
        self._view.delete("enemy","tower","obstacle","laser")
        self._game.queue_wave([], True) #clear all enemies
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
            '''handle quitting with keyboard'''
            self._master.destroy()

        confirm_window.bind("<Return>", handle_return)

    def _handle_highscores(self):
        '''displays highscores'''
        label_txt = "High scores:\n"
        high_score_entries = self._high_score_manager.get_entries()
        for entry in high_score_entries:
            label_txt += "%s: %s\n" %(entry['name'], entry['score'])

        highscore_window = tk.Toplevel(self._master)
        highscore_window.title("high scores")
        highscore_window.geometry('200x200')
        label = tk.Label(highscore_window, text=label_txt, padx=20)
        label.pack()


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

        self._view.delete('laser')


        self.refresh_view()

        return not self._won

    #Task 1.2 (Tower Placement): Complete event handlers here (including docstrings!)
    #Event handlers: _move, _mouse_leave, _left_click
    def _move(self, event):
        """
        Handles the mouse moving over the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        if self._current_tower.get_value() > self._coins:
            return

        #move the shadow tower to mouse position
        position = event.x, event.y
        self._current_tower.position = position

        legal, grid_path = self._game.attempt_placement(position)

        #find the best path and covert positions to pixel positions
        path = [self._game.grid.cell_to_pixel_centre(position)
                for position in grid_path.get_shortest()]

        #Task 1.2 (Tower placement): Draw the tower preview here
        self._view.draw_preview(self._current_tower, legal)
        self._view.draw_path(path)


    def _mouse_leave(self, event):
        """
        Handles the mouse leaving the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """

        #Task 1.2 (Tower placement): Delete the preview
        #Hint: Relevant canvas items are tagged with: 'path', 'range', 'shadow'
        #      See tk.Canvas.delete (delete all with tag)
        self._view.delete("shadow", "range", "path")

    def _left_click(self, event):
        """
        Handles the mouse left clicking in the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        #retrieve position to place tower
        if self._current_tower is None:
            return

        position = event.x, event.y
        cell_position = self._game.grid.pixel_to_cell(position)
        
        #if the event position already has a tower, show the upgrades for it
        if cell_position in self._game.towers:

            tower = self._game.towers[cell_position]


            #hide all upgrade_controls
            for t in self._upgrade_controls:
                self._upgrade_controls[t].pack_forget()

            
            #initiate the upgrade control if it doesn't already exist
            if tower not in self._upgrade_controls:
                upgrade_control = UpgradeControl(self._right_frame, tower, self)
                self._upgrade_controls[tower] = upgrade_control
                upgrade_control.pack(expand=True)

            else:
                #pack the one with the tower
                tower = self._game.towers[cell_position]
                upgrade_control = self._upgrade_controls[tower]
                upgrade_control.pack(expand=True)
                upgrade_control.check_status()


        #Task 1.2 (Tower placement): Attempt to place the tower being previewed
        legal, grid_path = self._game.attempt_placement(position)

        if legal and (self._current_tower.get_value() <= self._coins):
            self._coins -= self._current_tower.get_value()            
            self._status_bar.set_coins(self._coins)

            #refresh view upon placing a tower

            if self._game.place(cell_position, tower_type=self._current_tower.__class__):
                #delete preview after placing
                self._view.delete("shadow", "range", "path")
                for tower_type, shop_tower_view in self._tower_views:
                    if tower_type.base_cost > self._coins:
                        shop_tower_view.set_available(False)
                self.refresh_view()
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
        self._coins += removed_tower.get_value() * 0.8

        #updates coins string var to display coins
        self._status_bar.set_coins(self._coins)

        #update availability for tower views
        for tower, view in self._tower_views:
            if self._coins < tower.get_value():
                view.set_available(False)
            else: 
                view.set_available(True)

    def next_wave(self):
        """Sends the next wave of enemies against the player"""
        if self._wave == self._level.get_max_wave():
            return

        self._wave += 1

        #Task 1.3 (Status Bar): Update the current wave display here
        self._status_bar.set_wave(self._wave)

        #Task 1.5 (Play Controls): Disable the add wave button here (if this is the last wave)
        if self._wave == 20:
            self._wave_button.config(state=tk.DISABLED)

        #Generate wave and enqueue
        wave = self._level.get_wave(self._wave, self._game)
        for step, enemy in wave:
            enemy.set_cell_size(self._game.grid.cell_size)

        self._game.queue_wave(wave)

    def select_tower(self, tower):
        """
        Set 'tower' as the current tower

        Parameters:
            tower (AbstractTower): The new tower type
        """
        for tower_type, shop_tower_view in self._tower_views:
            shop_tower_view.set_selected(False)
            if tower_type.__class__ == tower:
                shop_tower_view.set_selected(True)

        self._current_tower = tower(self._game.grid.cell_size)

    def _handle_death(self, enemies):
        """
        Handles enemies dying

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which died in a step
        """
        # for enemy in enemies:
        #     if type(enemy) == SuperRichardEnemy:
        #         time.sleep(0.2)
        bonus = len(enemies) ** .5
        for enemy in enemies:
            self._coins += enemy.points
            self._score += int(enemy.points * bonus)

        #Task 1.3 (Status Bar): Update coins & score displays here
        self._status_bar.set_coins(self._coins)
        self._status_bar.set_score(self._score)

        for tower, view in self._tower_views:
            if self._coins < tower.get_value():
                view.set_available(False)
            else: 
                view.set_available(True)


    def _handle_escape(self, enemies):
        """
        Handles enemies escaping (not being killed before moving through the grid

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which escaped in a step
        """
        for enemy in enemies:
            self._lives -= enemy.live_damage
            if self._lives < 0:
                self._lives = 0

        #Task 1.3 (Status Bar): Update lives display here
        self._status_bar.set_lives(self._lives)

        #Handle game over
        if self._lives <= 0:
            self._handle_game_over(won=False)

    def _handle_wave_clear(self):
        """Handles an entire wave being cleared (all enemies killed)"""
        if self._wave == self._level.get_max_wave():
            self._handle_game_over(won=True)


    def record_high_score_from_game_over(self, entry_box):
        '''record the highscore of that player and add it to the highscore 
        list, then destroy the game over dialog box and show the highscore 
        box.

        parameter:
            player (string): name of the player
            highscore (string): the highscore to record
            entry_box (tk.Entry): the entry box to get the player's name and
            destroy its parent from.
        '''
        player = entry_box.get()
        self._high_score_manager.add_entry(player, self._score, '')
        self._high_score_manager.save()
        entry_box.master.destroy()

        #show the high scores
        self._handle_highscores()




    def _handle_game_over(self, won=False):
        """Handles game over
        
        Parameter:
            won (bool): If True, signals the game was won (otherwise lost)
        """
        self._won = won
        self.stop()

        #Task 1.4 (Dialogs): show game over dialog here
        dialog_box = tk.Toplevel(self._master)
        dialog_box.title("Game Over")

        if won:
            message = "You won! Enter your name:"
        else:
            message = "You lost! Enter your name:"

        label = tk.Label(dialog_box, text=message)
        label.pack(padx=50,pady=10)


        highscore_prompt = tk.Entry(dialog_box)
        highscore_prompt.pack(expand=True, pady=10)

        ok_button = tk.Button(dialog_box, text="ok",
         command=lambda entry_box=highscore_prompt: self.record_high_score_from_game_over(entry_box))
        ok_button.pack(pady=10)

        #disable buttons if game over
        self._wave_button.config(state=tk.DISABLED)
        self._play_button.config(state=tk.DISABLED)




#Task 1.1 (App Class): Instantiate the GUI here

if __name__ == "__main__":
    '''main function, instantiates the GUI'''
    root = tk.Tk()
    app = TowerGameApp(root)
    root.mainloop()

