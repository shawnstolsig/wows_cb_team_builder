# Shawn Stolsig
# PDX Code Guild 
# Assignment: Python Section Presentation
# Date: 11/11/2019

# These imports required for Google Sheets API
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Other imports
import api_keys                         # this is a file hidden from Github, containing API keys
import math                             # for using INF in Lineup scoring system
import json                             # for calling game's API
import requests                         # useful for calling game's API
from tkinter import *                   # for GUI
from tkinter import ttk                 # for themed widgets
from tkinter import messagebox
from itertools import permutations      # for finding all possible permutations of input players
# =====================    CLASSES  ============================= #
class Clan:
    '''
    '   This class will hold all information related to a clan (mainly the roster and preferred ship lineup)
    '   Attributes: A roster of players (list of Player objects)
    '               A list of ships (the header of the input spreadsheet)
    '   Methods: get_player - Get a player object from the clan's roster given a username string
    '            generate_lineup - the main player lineup algorithm
    '            get_list_of_players_owning_ship - get a list of players in the clan who own a specific ship
    '
    '''

    def __init__(self, input_data):
        ''' the init function for a Roster type '''

        # get ships list from header of input file
        self.all_game_ships = input_data[1][2:]

        # roster is list of Player objects
        self.roster = []

        # the desired ship lineup, as a list of strings
        self.target_ship_lineup = ['Kremlin', 'Yamato', 'Smolensk', 'Moskva', 'Des Moines', 'Kleber', 'Kleber', 'Gearing']
        # self.target_ship_lineup = ['Z-52', 'Khabarovsk', 'Yueyang', 'Shimakaze', 'Gearing', 'Grozovoi', 'Harugumo', 'Daring']
        # try to retrieve all of the data from input file
        try:
            # iterate through rows after header, add Player objects to roster
            for i in range(2,len(input_data)):
                self.roster.append(Player(self.all_game_ships,input_data[i])) 
        # handle any index errors
        except:
            print("Issue with input data, see Clan __init__ method")

    def get_player(self, name):
        '''
        '   A function for retrieving player object of given input username
        '   Parameters: WG username (string)        
        '   Returns: Player object
        '''
        for i in range(len(self.roster)):
            if self.roster[i].username_wg == name:
                return self.roster[i]

    def generate_lineup(self, player_list, team_size):
        '''
        '   This is the main algorithm for generating the best lineup.  One important note is that this algorithm
        '   is reliant on having a player list that is exactly as long as the target ship lineup
        '   Parameters: a list of player objects
        '   Returns: a Lineup object
        '''

        #   Here's how the algorithm works:
        #   1. Generate all possible permutations of n players.  Each permutation is stored as a type Lineup
        #       a. In the Lineup ___init__ function, a score for the Lineup will be generated
        #       b. The score will be used sort the Lineups, helping the user decide which is best
        #       c. If a player is paired with a ship that is not in their port for a given Lineup, 
        #          then that lineup will be given a score of -INF
        #   2. Each lineup is stored in a list
        #   3. Iterate through lineups, and remove any with a -INF score
        #   4. Sort Lineups by highest to lowest 
        #   5. Return list of sorted, valid lineups

        # Create empty list for Lineup permutations
        player_perm_list = []
        # create a counter, this will serve as each Lineup's ID
        lineup_id = 0
        # iterate through all possible permutations of input player list and specified team size
        for perm in list(permutations(player_list,team_size)):
            # increment lineup_ID
            lineup_id += 1
            # create a new Lineup, appended to lineup list
            player_perm_list.append(Lineup(perm, self, lineup_id))
        # after all Lineup permutations are generated, the lineup_id will be the same as the total permutation count
        total_perm_count = lineup_id
        
        # create variable for tracking the number of invalid lineups
        bad_perm_count = 0

        # iterate through all generated lineups
        # iterating in reverse order so that lineups can be removed without IndexError
        for i in range(len(player_perm_list)-1,-1,-1):
            # if the current lineup is invalid (score is -inf)
            if player_perm_list[i].score == -math.inf:
                # update the bad lineup count
                bad_perm_count += 1
                # pop this element from the list
                player_perm_list.pop(i)

        # sort the remaining lineups by score
        player_perm_list.sort(key=lambda x: x.score, reverse=True)

        # some print messages about stats
        print(f"{len(player_perm_list)} permutations were checked: {bad_perm_count} were invalid and {total_perm_count-bad_perm_count} were evaluated and compared against each other")

        # check to see if there is no a valid lineup
        if len(player_perm_list) == 0:
            return False, bad_perm_count, total_perm_count
        
        # return sorted best to worst list of lineups, the total bad lineups that were thrown out, and the total permutations generated
        return player_perm_list, bad_perm_count, total_perm_count
    
    def get_list_players_owning_ship(self, ship_name, player_list):
        '''
        '   This function will return a list of players in a given list who own a ship
        '   Parameters: ship_name (string) and list of Player objects
        '   Return: list of Player objects who own the ship
        '''
        # setup return list of players
        return_list = []
        # interate through players in player list
        for player in player_list:
            if ship_name in player.ships.keys():
                return_list.append(player)
        
        # return return list
        return return_list

    def get_ordered_rare_ship_list(self, player_list):
        ''' 
        '   This method will provide a list of ships (with duplicates) in order of rarity
        '   Parameters: Player list, ship list (strings)
        '   Returns: list of ship strings in order of most to least rare
        '''
        # get dict using class helper method
        # this dict has keys of ships in the lineup and values of how many players in the player list have that ship
        ship_dict = self.get_dict_players_with_ships(player_list)

        # set up empty return list
        return_list = []

        # this block of code creates a list of strings equal to the target ship lineup, 
        # with each element being a ship that is needed in the lineup, in order of least to most rare
        for i in range(min(ship_dict.values()), max(ship_dict.values())+1):     # iterate through ship rarirty from the most rare ship to least rare ship
            for ship in ship_dict:                                              # iterate through all ships in dict
                if ship_dict[ship] == i:                                        # if current ship is the rare one we are looking for
                    for j in range(self.target_ship_lineup.count(ship)):    # append that ship name to the return list as many times as the ship appears in our target lineup
                        return_list.append(ship)

        # return the return lis
        return return_list

    def get_dict_players_with_ships(self, player_list):
        '''
        '   This function will help figure out how "rare" each ship is, based on the input Players
        '   Parameters: list of Player objects, list of ships (as strings)
        '   Return: a dictionary of ship: number of players with ship 
        '''
        # declare empty return dictionary
        return_dict = {}

        # iterate through ships in target lineup:
        for ship in self.target_ship_lineup:
            # if ship is already in dictionary, skip
            if ship in return_dict.keys():
                pass
            # else if ship is not in dictionary
            else: 
                # init counter to 0
                counter = 0
                # iterate through players
                for player in player_list:
                    # check to see if player has that ship
                    if ship in player.ships.keys():
                        # increment counter if ship is there
                        counter += 1
                # add that ship to dictionary as a key with the number of players as the value
                return_dict[ship] = counter
            
        # return return dict
        return return_dict

class Player:
    '''
    '   This class will represent each member of a clans roster.  
    '   Attributes: username_wg (string)
    '               username_discord (string)
    '               join_date (string), 
    '               ships (nested dict)
    '               is_active (boolean)
    '               is_alpha_team (boolean)
    '               overall_PR (int)
    '               overall_WR (float)
    '               overall_avg_damage (int)
    '               main_ship_class (string)
    '               
    '   Methods: __repr__
    '
    '''
    def __init__(self, id, all_ships, input_list):
        ''' 
        '   The init function for setting up a player
        '   Parameters: list of strings (their line on the Google sheet)       
        '   Returns: none (sets up their lists of ships and some other attributes)
        '''

        # ATTRIBUTES
        self.player_id = id                     # player ID from WG UI
        self.username_wg = input_list[0]        # Username within Wargaming database
        self.username_discord = ''              # Username within Discord
        self.join_date = input_list[1]          # clan join date
        self.is_active = True                   # is player an active player
        self.is_alpha_team = True               # is the player a "core" or Alpha team player, as decided by clan admirals?
        self.main_ship_class = 'Not Specified'  # what is their main class of ship (carrier-CV, battleship-BB, cruiser-CA, destroyer-DD, submarine-SS)
        self.overall_PR = 1500                  # Overall Personal Rating
        self.overall_WR = .6                    # Overall Win Rate
        self.overall_avg_damage = 90,000        # Overall Avg Damage
        self.ships = {}                         # ship roster, list of dictionaries as a dict
           
        # iterate through header_list after the username/join date columns (iterate through each ship)
        for i in range(len(all_ships)):
            # append dictionary to ship list if the ship is unlocked
            if 'Y' in input_list[i+2]:          # using i+2 for input_list to trim username and join date

                # set ship-specific attributes
                is_ship_available = True        # do they have the ship in port, ready to play? 
                leg_mod = False                 # do they have legendary module for that ship?
                player_pref = False             # does the player prefer to play this ship?
                admiral_strong_pref = False     # does an admiral strongly prefer the player plays this ship?
                admiral_weak_pref = False       # does an admiral weakly prefer the player plays this ship?
                ship_PR = 2000                  # Ship-specific Personal Rating
                ship_WR  = .5                   # Ship-specific Win rate
                ship_avg_damage = 100,000       # Ship-specific Avg damage


                ####    This block of code will probably be deleted once Settings can be input in UI    #####
                # check to see if they have legendary mod 
                if 'mod' in input_list[i+2]:
                    leg_mod = True
                # check to see if this ship is preferred for them
                if '*' in input_list[i+2]:
                    player_pref = True
                # check player's PR rating with ship
                # CODE HERE to get and update PR, WR, and avg damage....json from Wargaming?
                
                # create ship entry for the current ship
                self.ships[all_ships[i]] = {  'is_ship_available': is_ship_available,
                                                'legendary': leg_mod, 
                                                'player_preferred': player_pref, 
                                                'admiral_strong_preferred': admiral_strong_pref,
                                                'admiral_weak_preferred': admiral_weak_pref,
                                                'ship_PR': ship_PR,
                                                'ship_WR': ship_WR,
                                                'ship_avg_damage': ship_avg_damage
                                                }


    # dunder function so that the player's WG username is how that player is displayed
    def __repr__(self):
        return self.username_wg

class Lineup:
    '''
    '   This object will be use to hold a certain lineup of ships.  It will also have many of 
    '   the methods needed for generating lineups.
    '
    '''

    # constant variables for all Lineups
    # total point constant.  the more points a player gets for a ship, the less likely to be slotted
    const_points = 100
    # modifiers per factor considered when slotting players into ships.  eventually, these should be user adjustable
    # mod_has_ship = 0.3
    mod_admiral_strong_preferred = 0.5
    mod_admiral_weak_preferred = 0.1
    mod_player_preferred = 0.1
    mod_is_alpha = 0.1
    mod_is_main_class = 0.5
    # (modifiers not yet used):
    mod_stat_PR = 1
    mod_stat_WR = 1
    mod_stat_AVG_DMG = 1
    mod_needs_wins = 1

    def __init__(self, input_player_list, clan, lineup_id):
        ''' Parameters: list of Player objects and clan object (so that the target ship lineup can be retrieved) '''

        # store lineup id
        self.id = lineup_id

        # player/ship nexted list
        self.player_and_ship_list = []

        # combine player and ship list into one list of lists
        for i in range(len(clan.target_ship_lineup)):
            self.player_and_ship_list.append( [input_player_list[i], clan.target_ship_lineup[i]] )

        # initialize points for this player/ship combo
        points = 0

        # calculate the Lineup's score
        for combo in self.player_and_ship_list:

            # if the ship is not in that player's list of ships, set points to -inf and skip the rest
            if combo[1] not in combo[0].ships.keys():
                points = -math.inf
            else:
                # add points if they are admiral preferred ship
                if combo[0].ships[combo[1]]['admiral_strong_preferred']:
                    points += Lineup.const_points * Lineup.mod_admiral_strong_preferred
                # add points if they are admiral preferred ship
                if combo[0].ships[combo[1]]['admiral_weak_preferred']:
                    points += Lineup.const_points * Lineup.mod_admiral_weak_preferred
                # add points if alpha team player
                if combo[0].is_alpha_team:
                    points += Lineup.const_points * Lineup.mod_is_alpha
                # add points if player preferred ship
                if combo[0].ships[combo[1]]['player_preferred']:
                    points += Lineup.const_points * Lineup.mod_player_preferred           

                # add points if player doesn't main that class
                # add points if they don't need wins
                # add points if they have bad ship stats

        # set score equal to points
        self.score = points

    # a function for displaying what a Lineup looks like (it'll print off all 8 player/ship combos)
    def __repr__(self):
        ''' Parameters: none Returns: string with each player/ship seperated on newlines '''
        return_string = ''
        for i in range(len(self.player_and_ship_list)):
            return_string += f'({self.player_and_ship_list[i][0]}, {self.player_and_ship_list[i][1]}) '
        return_string += f"Linup score is {self.score}"
        return return_string

class Interface:
    '''
    '   This is an interface class to managing information in the Tkinter Gui
    '''
    def __init__(self, root, clan, image):
        '''constructor'''

        # set some basic properties of GUI window
        root.title("WoWs Clan Battle Team Builder")

        # tell Tkinter to resize root frame with the window
        # root.columnconfigure(0,weight=1)                        
        # root.rowconfigure(0,weight=1)
        root.resizable(False, False)

        # setting up all grid framework that will hold all contents of main window
        self.main_frame = ttk.Frame(root).grid(column=0, row=0, sticky=(N,W,E,S))

        # add some padding to each widget
        for child in root.winfo_children(): child.grid_configure(padx=5, pady=5)

        # add label widgets
        # list labels that won't be changed
        ttk.Label(self.main_frame, text="Clan Roster").grid(column=1, row=1)
        ttk.Label(self.main_frame, text="Selected Players").grid(column=3, row=1)
        ttk.Label(self.main_frame, text="Possible Lineups").grid(column=1, row=15)
        ttk.Label(self.main_frame, text="Selected Lineup").grid(column=3, row=15)
        ttk.Label(self.main_frame, image=image).grid(column=4, row=4)
        ttk.Label(self.main_frame, text="   Ship Composition:  ").grid(column=4, row=6)        

        # list labels that will be changed
        # bottom status bar
        self.label_status = ttk.Label(self.main_frame, text=" ")
        self.label_status.grid(column=1, row=28, columnspan=4)
        self.player_count = ttk.Label(self.main_frame, text=" ")     
        # target ship list at the right
        self.update_target_ship_list(clan)                                           

        # add treeviews and pack for listing players/lineups
        self.tree_clan_players = ttk.Treeview(self.main_frame, show='tree')
        self.tree_clan_players.grid(column=1, row=2, rowspan=12)
        self.tree_selected_players = ttk.Treeview(self.main_frame, show='tree')
        self.tree_selected_players.grid(column=3, row=2, rowspan=12)
        self.tree_possible_lineups = ttk.Treeview(self.main_frame, show='tree', selectmode="browse")
        self.tree_possible_lineups.grid(column=1, row=16, rowspan=12)
        self.tree_selected_lineup = ttk.Treeview(self.main_frame, show='tree', selectmode="none")
        self.tree_selected_lineup.grid(column=3, row=16, rowspan=12)

        # add buttons and pack to grid
        self.button_add = ttk.Button(self.main_frame, text="Add", command=self.select_players)
        self.button_add.grid(column=2, row=6)
        self.error_label = ttk.Label(self.main_frame, text="Already selected!")
        self.button_remove = ttk.Button(self.main_frame, text="Remove", command=self.remove_players)
        self.button_remove.grid(column=2, row=7)
        self.button_clear = ttk.Button(self.main_frame, text="Clear", command=self.clear_players)
        self.button_clear.grid(column=2, row=8)
        self.button_generate_lineups = ttk.Button(self.main_frame, text="Generate Lineups", command=self.start_algorithm, state=DISABLED)
        self.button_generate_lineups.grid(column=2, row=14)
        self.button_team_comp = ttk.Button(self.main_frame, text="Update Ship Composition", command=self.update_ship_comp, state=DISABLED)
        self.button_team_comp.grid(column=4, row=20, rowspan=3)

        # add info to lists
        for player in clan.roster:
            self.tree_clan_players.insert('', 'end', clan.roster[player].player_id, text=clan.roster[player].username_wg)

        # store clan to be used for start_algorithm method
        self.stored_clan = clan

    def select_players(self):
        '''
        '   When button_add is pressed, call this fuction to move players to selected list
        '
        '''
        # using try to catch if player has already been added...can't add same player treeview twice
        try:
            # get selection from left treeview
            selection = self.tree_clan_players.selection()
            # for each player in selection
            for player in selection:
                # add player to selected tree view
                self.tree_selected_players.insert('','end', player, text=self.stored_clan.get_player_name_from_id(int(player)))

            # clear 'already selected" error message bhy forgetting the pack
            self.error_label.grid_forget()

            # update player count
            self.player_count.configure(text=f"Player Count: {len(self.tree_selected_players.get_children())}")
            self.player_count.grid(column=3, row=14, sticky=N)

            # enable button only if enough players are selected
            if len(self.tree_selected_players.get_children()) == len(self.stored_clan.target_ship_lineup):
                self.button_generate_lineups.configure(state = 'normal')
            else:
                self.button_generate_lineups.configure(state = DISABLED)

        # show/pack error message if player already selected
        except TclError:
            # error is shown by packing error message into grid (already created label in init)
            self.error_label.grid(column=2, row=4)

    def remove_players(self):
        '''
        '   When button_remove is pressed, call this fuction to remove players to selected list
        '
        '''
        selection = self.tree_selected_players.selection()
        for player in selection:
            self.tree_selected_players.delete(player)
        
        # update player count
        self.player_count.configure(text=f"Player Count: {len(self.tree_selected_players.get_children())}")
        self.player_count.grid(column=3, row=14, sticky=N)             

        # enable button if enough players are selected
        if len(self.tree_selected_players.get_children()) == len(self.stored_clan.target_ship_lineup):
            self.button_generate_lineups.configure(state = 'normal')
        else:
            self.button_generate_lineups.configure(state = DISABLED)

    def clear_players(self):
        '''
        '   When button_clear is pressed, call this fuction to clear players from selected list
        '
        '''
        # clear all trees, hide the player count
        self.tree_possible_lineups.delete(*self.tree_possible_lineups.get_children())
        self.tree_selected_lineup.delete(*self.tree_selected_lineup.get_children())
        self.tree_selected_players.delete(*self.tree_selected_players.get_children())
        self.player_count.grid_forget()
        # disable generate button
        self.button_generate_lineups.configure(state=DISABLED)

    def update_target_ship_list(self,clan):
        '''
        '   A function for updating the target ship lineup
        '
        '''
        for i in range(len(clan.target_ship_lineup)):
            ttk.Label(self.main_frame, text=f"{i+1}. {clan.target_ship_lineup[i]}").grid(column=4, row=(6+1+i))          

    def start_algorithm(self):

        # reset/remove items from possible and selected lineup trees
        self.tree_possible_lineups.delete(*self.tree_possible_lineups.get_children())
        self.tree_selected_lineup.delete(*self.tree_selected_lineup.get_children())

        # get list of player objects                                                                                            ###### PICKUP HERE, GET WORKING WITH NEW ROSTER/PLAYER DICTIONARY STRUCTURE
        player_obj_list = []
        for player in self.tree_selected_players.get_children():
            player_obj_list.append(self.stored_clan.get_player(player))
        print(f"playe_obj list is {player_obj_list}")

        print(self.stored_clan.get_dict_players_with_ships(player_obj_list))

        # call generate lineups
        self.generated_lineups, bad_perm_count, total_perm_count = self.stored_clan.generate_lineup(player_obj_list,len(player_obj_list))

        try:
            # put lineups into tree_possible_lineups
            for lineup in self.generated_lineups:
                self.tree_possible_lineups.insert('', 'end', lineup.id, text=f"Lineup ID: {lineup.id}  Score: {lineup.score}")      
        except TypeError:
            # if no valid lineups, show error message
            if not self.generated_lineups:
                messagebox.showerror("Lineup Error", "Those players cannot form the desired ship composition!  Please select different players.")
      
        # update status bar
        self.label_status.configure(text=f"{total_perm_count} total permutations with {bad_perm_count} invalid lineups.\n Showing {total_perm_count-bad_perm_count} valid lineups in best to worst order.")

        # bind an event so that you can display a lineup when it's selected in tree_possible_lineups
        self.tree_possible_lineups.bind("<<TreeviewSelect>>",self.on_possible_lineup_click)

    def on_possible_lineup_click(self,virtual_event):

        # reset/remove items from tree_selected_lineup
        self.tree_selected_lineup.delete(*self.tree_selected_lineup.get_children())

        # get lineup ID
        this_lineup_id = int(self.tree_possible_lineups.selection()[0])
        # retrieve lineup object
        for lineup in self.generated_lineups:
            if int(lineup.id) == this_lineup_id:
                this_lineup_obj = lineup

        # print(f"Lineup retrieved: {this_lineup_obj}")

        # print lineup to tree selected lineup
        for combo in this_lineup_obj.player_and_ship_list:
            self.tree_selected_lineup.insert('', 'end', combo[0], text=f"{combo[1]}:     {combo[0]}")           

    def update_ship_comp(self):
        print('update ship comp')
        
class WOWsGame:
    ''''
    '   This class will be used to manage current information about the game.
    '   Attributes: game_ships = list of dictionaries of active ships at specific tier
    '               game_tier = list of ships at a given tier
    '               
    '''

    def __init__(self, api_key, realm):
        ''' constructor for WOWsGame Object
        '   Attributes: 
        '
        '''
        # ATTRIBUTES:
        
        # WG API key for the program.  Imported/hidden so it's not revealed on GitHub
        self.api_key = api_key
        # based on which region is selected, store the appropriate extension for the url
        if realm == 'NA':
            self.region = 'com'
        elif realm == 'RU':
            self.region = 'ru'
        elif realm == 'EU':
            self.region = 'eu'
        elif realm == 'ASIA':
            self.region = 'asia'               
        # ship tier that we will be building a team at
        self.game_tier = 10
        # invalid/old/work in progress ships that should be excluded             
        self.game_invalid_ship_names = ['Paolo Emilio', 'Hayate', 'Slava', 'Brennus', 'STALINGRAD #2', 'Puerto Rico', 'Marceau', 'Goliath']
        # # read all ships from saved .pkl file
        self.game_ships = load_obj("all_ships")
        # self.game_ships = self.update_ships()
        # # read in all clans from saved .pkl file
        self.clan_directory = load_obj("clan_directory")
        # self.clan_directory = self.update_all_clan_directory() 

    def update_ships(self):
        '''
        '   A function for querying WG API to update the current ships in the game. 
        '
        '''
        # get ship info (all ships, with tier, name, type, and available upgrades)
        response = requests.get(f"https://api.worldofwarships.{self.region}/wows/encyclopedia/ships/?application_id={self.api_key}&fields=name")
        page_query = json.loads(response.text)

        # verify query worked
        try:
            # attempt to get page count for querying wiki
            if page_query['status'] == "ok":
                page_count = page_query['meta']['page_total']
                print("Updating ships from WG servers...data pull successful.")
        except:
            print("Error getting ship data from WG API.  This error thrown from WOWsGame update_ships() method")

        # empy list for storing all data
        page_list = []
        game_ships_dict = {}
        # iterate through page count
        for i in range(page_count):
            # query WG for that page of warships.  get ship ID (as key), name, tier, and type
            response = requests.get(f"https://api.worldofwarships.{self.region}/wows/encyclopedia/ships/?application_id={self.api_key}&fields=name%2C+type%2C+tier&page_no={i+1}")
            page_query = json.loads(response.text)
            # iterate through page query
            for ship in page_query['data'].items():
                # append to list.  ship is a tuple, put into list so that it can be cast to a dict
                page_list.append(dict([ship]))

        # take the JSON return and format a dicionary of ships, each with a 'name' string and a 'type' string
        for i in range(len(page_list)):
            # get ship id
            ship_id = list(page_list[i].keys())[0]
            if page_list[i][ship_id]['tier'] == self.game_tier:

                # get current element name
                name = page_list[i][ship_id]['name']

                # filter out ships that aren't currently active/valid and aren't rental ships
                if name[0] != '[' and name not in self.game_invalid_ship_names:
                    # add ship to self dictionary
                    game_ships_dict[ship_id] = {'name': name,
                                                'type': page_list[i][ship_id]['type'],
                                                }

        # save the ship listing to a file
        save_obj(game_ships_dict, "all_ships")

        # return game ships
        return game_ships_dict

    def update_all_clan_directory(self):
        '''
        '   A method for updating the clan listing based on region.
        '   note that this takes a minute or two to pull ~15k clans, 100 at a time.   
        '''
        # the api does not return a page count for this query, so we will iterate through until we get an error
        query_count = 100         # API returns a count of 100 max, so we will initilize variable with same amount
        page_num = 0              # will use this to pull specific page
        # empy list for storing all data
        clan_directory_dict = {}

        # continue iterating until API returns count of 0
        while query_count != 0:
            print(f"query count is {query_count} and page num is {page_num}")
            # increment page count
            page_num += 1

            # query WG for that page of clans.  get all clan data (mainly, id, tag and name)
            response = requests.get(f"https://api.worldofwarships.{self.region}/wows/clans/list/?application_id={self.api_key}&page_no={page_num}")
            query = json.loads(response.text)

            # iterate through page query
            for i in range(len(query['data'])):
                # append clan to dict.  each key is the clan tag, value is a nested dict containing "id" and "name"
                clan_directory_dict[   query['data'][i]['tag']   ] = { 'id': query['data'][i]['clan_id'], 'name': query['data'][i]['name'] }
            
            # set count equal to what was returned by API
            query_count = query['meta']['count']


        # write page_list to a file
        save_obj(clan_directory_dict, "clan_directory")

        # return clan directory dict after saving
        return clan_directory_dict

class Clan2:
    '''
    '   This class will hold all information related to a clan (mainly the roster and preferred ship lineup)
    '   Attributes: A roster of players (list of Player objects)
    '               A list of ships (the header of the input spreadsheet)
    '   Methods: get_player - Get a player object from the clan's roster given a username string
    '            generate_lineup - the main player lineup algorithm
    '            get_list_of_players_owning_ship - get a list of players in the clan who own a specific ship
    '
    '''

    def __init__(self, tag, wows_game_obj):
        ''' the init function for a Roster type '''

        # store pointer to the wows_game objected
        self.game_info = wows_game_obj

        # retreive clan info from pickled directory
        self.clan_tag = tag
        self.clan_id = self.game_info.clan_directory[self.clan_tag ]['id']
        self.clan_name = self.game_info.clan_directory[self.clan_tag ]['name']

        # roster is list of Player objects
        # self.roster = self.update_roster()
        self.roster = load_obj('clan_roster')

        # the desired ship lineup, as a list of strings
        self.target_ship_lineup = ['Kremlin', 'Yamato', 'Smolensk', 'Moskva', 'Des Moines', 'Kleber', 'Kleber', 'Gearing']

    def get_player(self, name):
        '''
        '   A function for retrieving player object of given input username
        '   Parameters: WG username (string)        
        '   Returns: Player object
        '''
        for i in range(len(self.roster)):
            if self.roster[i].username_wg == name:
                return self.roster[i]

    def get_player_name_from_id(self, player_id):
        '''
        '   A function for retrieving a player name when passed the player's id
        '   Parameters: player_id (int)  return: player.username_wg (string)
        '''
        return self.roster[player_id].username_wg


    def generate_lineup(self, player_list, team_size):
        '''
        '   This is the main algorithm for generating the best lineup.  One important note is that this algorithm
        '   is reliant on having a player list that is exactly as long as the target ship lineup
        '   Parameters: a list of player objects
        '   Returns: a Lineup object
        '''

        #   Here's how the algorithm works:
        #   1. Generate all possible permutations of n players.  Each permutation is stored as a type Lineup
        #       a. In the Lineup ___init__ function, a score for the Lineup will be generated
        #       b. The score will be used sort the Lineups, helping the user decide which is best
        #       c. If a player is paired with a ship that is not in their port for a given Lineup, 
        #          then that lineup will be given a score of -INF
        #   2. Each lineup is stored in a list
        #   3. Iterate through lineups, and remove any with a -INF score
        #   4. Sort Lineups by highest to lowest 
        #   5. Return list of sorted, valid lineups

        # Create empty list for Lineup permutations
        player_perm_list = []
        # create a counter, this will serve as each Lineup's ID
        lineup_id = 0
        # iterate through all possible permutations of input player list and specified team size
        for perm in list(permutations(player_list,team_size)):
            # increment lineup_ID
            lineup_id += 1
            # create a new Lineup, appended to lineup list
            player_perm_list.append(Lineup(perm, self, lineup_id))
        # after all Lineup permutations are generated, the lineup_id will be the same as the total permutation count
        total_perm_count = lineup_id
        
        # create variable for tracking the number of invalid lineups
        bad_perm_count = 0

        # iterate through all generated lineups
        # iterating in reverse order so that lineups can be removed without IndexError
        for i in range(len(player_perm_list)-1,-1,-1):
            # if the current lineup is invalid (score is -inf)
            if player_perm_list[i].score == -math.inf:
                # update the bad lineup count
                bad_perm_count += 1
                # pop this element from the list
                player_perm_list.pop(i)

        # sort the remaining lineups by score
        player_perm_list.sort(key=lambda x: x.score, reverse=True)

        # some print messages about stats
        print(f"{len(player_perm_list)} permutations were checked: {bad_perm_count} were invalid and {total_perm_count-bad_perm_count} were evaluated and compared against each other")

        # check to see if there is no a valid lineup
        if len(player_perm_list) == 0:
            return False, bad_perm_count, total_perm_count
        
        # return sorted best to worst list of lineups, the total bad lineups that were thrown out, and the total permutations generated
        return player_perm_list, bad_perm_count, total_perm_count
    
    def get_list_players_owning_ship(self, ship_name, player_list):
        '''
        '   This function will return a list of players in a given list who own a ship
        '   Parameters: ship_name (string) and list of Player objects
        '   Return: list of Player objects who own the ship
        '''
        # setup return list of players
        return_list = []
        # interate through players in player list
        for player in player_list:
            if ship_name in player.ships.keys():
                return_list.append(player)
        
        # return return list
        return return_list

    def get_ordered_rare_ship_list(self, player_list):
        ''' 
        '   This method will provide a list of ships (with duplicates) in order of rarity
        '   Parameters: Player list, ship list (strings)
        '   Returns: list of ship strings in order of most to least rare
        '''
        # get dict using class helper method
        # this dict has keys of ships in the lineup and values of how many players in the player list have that ship
        ship_dict = self.get_dict_players_with_ships(player_list)

        # set up empty return list
        return_list = []

        # this block of code creates a list of strings equal to the target ship lineup, 
        # with each element being a ship that is needed in the lineup, in order of least to most rare
        for i in range(min(ship_dict.values()), max(ship_dict.values())+1):     # iterate through ship rarirty from the most rare ship to least rare ship
            for ship in ship_dict:                                              # iterate through all ships in dict
                if ship_dict[ship] == i:                                        # if current ship is the rare one we are looking for
                    for j in range(self.target_ship_lineup.count(ship)):    # append that ship name to the return list as many times as the ship appears in our target lineup
                        return_list.append(ship)

        # return the return lis
        return return_list

    def get_dict_players_with_ships(self, player_list):
        '''
        '   This function will help figure out how "rare" each ship is, based on the input Players
        '   Parameters: list of Player objects, list of ships (as strings)
        '   Return: a dictionary of ship: number of players with ship 
        '''
        # declare empty return dictionary
        return_dict = {}

        # iterate through ships in target lineup:
        for ship in self.target_ship_lineup:
            # if ship is already in dictionary, skip
            if ship in return_dict.keys():
                pass
            # else if ship is not in dictionary
            else: 
                # init counter to 0
                counter = 0
                # iterate through players
                for player in player_list:
                    # check to see if player has that ship
                    if ship in player.ships.keys():
                        # increment counter if ship is there
                        counter += 1
                # add that ship to dictionary as a key with the number of players as the value
                return_dict[ship] = counter
            
        # return return dict
        return return_dict

    def update_roster(self):
        '''
        '   A function that will update the roster of players when given a clan tag
        '
        '''
        # get ship info (all ships, with tier, name, type, and available upgrades)
        response = requests.get(f"https://api.worldofwarships.{self.game_info.region}/wows/clans/info/?application_id={self.game_info.api_key}&clan_id={self.clan_id}")
        query = json.loads(response.text)

        # verify query worked
        try:
            # attempt to get page count for querying wiki
            if query['status'] == "ok":
                print("Updating clan player roster from WG servers...data pull successful.")
        except:
            print("Error getting roster from WG API.  This error thrown from update_roster method")
            return

        # empty object to return
        players = {}

        # iterate through member ids, create new player for each
        for player_id in query['data'][str(self.clan_id)]['members_ids']:
            players[player_id] = Player2(player_id, self.game_info)

        # store players
        save_obj(players, "clan_roster")

        # return players
        return players

class Player2:
    '''
    '   This class will represent each member of a clans roster.  
    '   Attributes: username_wg (string)
    '               username_discord (string)
    '               join_date (string), 
    '               ships (nested dict)
    '               is_active (boolean)
    '               is_alpha_team (boolean)
    '               overall_PR (int)
    '               overall_WR (float)
    '               overall_avg_damage (int)
    '               main_ship_class (string)
    '               
    '   Methods: __repr__
    '
    '''
    def __init__(self, id, game_info):
        ''' 
        '   The init function for setting up a player
        '   Parameters: list of strings (their line on the Google sheet)       
        '   Returns: none (sets up their lists of ships and some other attributes)
        '''

        # ATTRIBUTES
        self.player_id = id                     # player ID from WG UI
        self.game_info = game_info              # store pointer to WOWsGame obj for access to ships and clans
        self.update_player_api_info()

        # unused..will be specified through UI, if at all
        self.username_discord = ''              # Username within Discord      
        self.is_active = True                   # is player an active player
        self.is_alpha_team = True               # is the player a "core" or Alpha team player, as decided by clan admirals?
        self.main_ship_class = 'Not Specified'  # what is their main class of ship (carrier-CV, battleship-BB, cruiser-CA, destroyer-DD, submarine-SS)
        self.join_date = ''                     # clan join date

        # set ship-specific attributes
        is_ship_available = True        # do they have the ship in port, ready to play? 
        leg_mod = False                 # do they have legendary module for that ship?
        player_pref = False             # does the player prefer to play this ship?
        admiral_strong_pref = False     # does an admiral strongly prefer the player plays this ship?
        admiral_weak_pref = False       # does an admiral weakly prefer the player plays this ship?
        ship_PR = 2000                  # Ship-specific Personal Rating
        ship_WR  = .5                   # Ship-specific Win rate
        ship_avg_damage = 100,000       # Ship-specific Avg damage


        ####    This block of code will probably be deleted once Settings can be input in UI    #####
        # check to see if they have legendary mod 
        # check to see if this ship is preferred for them
        # check player's PR rating with ship
        # CODE HERE to get and update PR, WR, and avg damage....json from Wargaming?
        
        # create ship entry for the current ship
        # self.ships[all_ships[i]] = {  'is_ship_available': is_ship_available,
        #                                 'legendary': leg_mod, 
        #                                 'player_preferred': player_pref, 
        #                                 'admiral_strong_preferred': admiral_strong_pref,
        #                                 'admiral_weak_preferred': admiral_weak_pref,
        #                                 'ship_PR': ship_PR,
        #                                 'ship_WR': ship_WR,
        #                                 'ship_avg_damage': ship_avg_damage
        #                                 }

    def update_player_api_info(self):
        '''
        '   A function that will get WG API info for a player: username, last logout, ships unlocked, etc
        '
        '''
        # get ship info (all ships, with tier, name, type, and available upgrades)
        response = requests.get(f"https://api.worldofwarships.{self.game_info.region}/wows/account/info/?application_id={self.game_info.api_key}&account_id={self.player_id}&fields=last_battle_time%2C+nickname%2C+statistics.pvp.battles%2C+statistics.pvp.wins")
        query = json.loads(response.text)

        # verify query worked
        try:
            if query['status'] == "ok":
                print("Updating player basic info from WG servers...data pull successful.")
        except:
            print("Error getting player data from WG API.  This error thrown from WOWsGame update_player_api_info method")
            return

        # update attributes
        self.username_wg = query['data'][str(self.player_id)]['nickname']                       # user nickname
        self.last_battle_time = query['data'][str(self.player_id)]['last_battle_time']          # time of last battle in timestamp ie 1528408800000 //  is 06/07/2018 @ 10:00pm (UTC)
        wins = query['data'][str(self.player_id)]['statistics']['pvp']['wins']                  # total number of pvp wins
        total_battles = query['data'][str(self.player_id)]['statistics']['pvp']['battles']      # total number of pvp battles
        self.overall_WR = round(wins/total_battles,3)                                           # winrate, rounded to 3 decimals

        # self.overall_PR = 1500                  # Overall Personal Rating
        # self.overall_WR = .6                    # Overall Win Rate
        # self.overall_avg_damage = 90,000        # Overall Avg Damage

        # create URL string for desired game ships
        ship_url = ''
        # iterating through and adding string version of the ship ID plus divider %2C+ string
        for ship in self.game_info.game_ships:
            ship_url += str(ship) + '%2C+'
        # strip final %2C+ off
        ship_url = ship_url[:len(ship_url)-4]

        # get that player's ship stats for all ships of concern.  if the player doesn't have that ship, then no pvp stats will be returned
        response = requests.get(f"https://api.worldofwarships.{self.game_info.region}/wows/ships/stats/?application_id={self.game_info.api_key}&ship_id={ship_url}&account_id={self.player_id}&fields=ship_id%2C+pvp.battles%2C+pvp.damage_dealt%2C+pvp.wins")
        query = json.loads(response.text)

        # verify query worked
        try:
            if query['status'] == "ok":
                print("Updating ship info from WG servers...data pull successful.")
        except:
            print("Error getting player ship stat data from WG API.  This error thrown from update_player_api_info method")
            return

        # Create empty dict for player ships
        self.ships = {}

        # try first to make sure the API is returning some number of playable ships
        try:
            print(f"API for player {self.username_wg} {self.player_id} shows they have {len(query['data'][str(self.player_id)])} ships from game_ships")

            # for each ship returned by UI
            for i in range(len(query['data'][str(self.player_id)])):
                # retrieve ship ID
                ship_id = query['data'][str(self.player_id)][i]['ship_id']
                # retrieve ship wins
                ship_wins = query['data'][str(self.player_id)][i]['pvp']['wins']
                # retrieve total ship battles
                ship_total_battles = query['data'][str(self.player_id)][i]['pvp']['battles']
                # retreive total ship damage dealt
                ship_total_damage_dealt = query['data'][str(self.player_id)][i]['pvp']['damage_dealt']
                # calculate ship WR, rounded to 3 decimal places

                # try to calculate averages, but except ZeroDivisionError in case player has never played ship
                try:
                    ship_WR = round(ship_wins/ship_total_battles, 3)
                    # calculate ship averge damage, as an int/whole number
                    ship_avg_damage = int(ship_total_damage_dealt/ship_total_battles)
                except ZeroDivisionError:
                    ship_WR = 0
                    ship_avg_damage = 0

                # create ship key/nested dict
                self.ships[ship_id] = {     #'is_ship_available': True,
                                            #'legendary': False, 
                                            #'player_preferred': player_pref, 
                                            #'admiral_strong_preferred': admiral_strong_pref,
                                            #'admiral_weak_preferred': admiral_weak_pref,
                                            #'ship_PR': ship_PR,
                                            'ship_WR': ship_WR,
                                            'ship_avg_damage': ship_avg_damage,
                                            'ship_battles': ship_total_battles
                                        }
        except TypeError:
            print(f"API for player {self.username_wg} {self.player_id} shows they have NoneType ships from game_ships")



    

    # dunder function so that the player's WG username is how that player is displayed
    def __repr__(self):
        return self.username_wg
 

# =====================    END OF CLASSES  ======================= # 


# =====================   Non-class FUNCTIONS  =========================== #
def get_sheets_data(spreadsheets_id, range_name):
    '''
    '   This function handles the authentication and retrieval of data from a Google Sheet
    '   Parameters: The spreadsheet id and the range of data to pull    Return: 2D nested list of rows/cols
    '''

    # this is all commented out while temporarily using CSV version

    # # If modifying these scopes, delete the file token.pickle.  (not sure what this is for)
    # SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

    # creds = None
    # # The file token.pickle stores the user's access and refresh tokens, and is
    # # created automatically when the authorization flow completes for the first
    # # time.
    # if os.path.exists('token.pickle'):
    #     with open('token.pickle', 'rb') as token:
    #         creds = pickle.load(token)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             'secrets.json', SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open('token.pickle', 'wb') as token:
    #         pickle.dump(creds, token)

    # service = build('sheets', 'v4', credentials=creds)

    # # Call the Sheets API
    # sheet = service.spreadsheets()
    # result = sheet.values().get(spreadsheetId=spreadsheets_id,
    #                             range=range_name).execute()
    # values = result.get('values', [])

    # delete next 5 rows when turning Google Sheets
    values = []
    with open('resources\Test Clan Info - KSD Tier 10.csv', 'r', encoding='utf-8') as f:
        rows = f.read().split('\n')
    for row in rows:
        values.append(row.split(','))

    # if unable to find the sheet
    if not values:
        return 'No data found.'
    # if able to find values, return them 
    else:
        return values

def save_obj(obj, name ):
    ''' 
    '   A function for saving an object to a file using pickle
    '   Parameters: object and filename     Returns: none
    '''
    with open('resources/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    ''' 
    '   A function for loading an object from a file using pickle
    '   Parameters: filename     Returns: object
    '''
    with open('resources/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)
# =====================    END OF FUNCTIONS  ============================= #


# ============================    MAIN  ================================== #


# The ID and range of the test  spreadsheet.
clan_info_spreadsheet_ID = '14oxx0qpWg7VWhRyYIVP6uv5YL40BQI15APGDOwsdZdQ'
range_name = 'KSD Tier 10'
team_size = 8

# for seeing if the Google Sheets API get works
# print(get_sheets_data(clan_info_spreadsheet_ID, range_name))          

# # uncomment below when basic UI ready
# # 2D list of strings from Google Sheets
try:
    sheets_output = get_sheets_data(clan_info_spreadsheet_ID, range_name)        
    print(sheets_output)     
except:
    print("Error reaching Google Sheets, exiting. ")
    exit()

# create Game object, passing in hidden API key
game = WOWsGame(api_keys.wg_api_key, 'NA')

# # create Clan object using output from sheets
# clan = Clan(sheets_output)         
clan = Clan2('KSD', game)

# set up GUI
root = Tk()

# open image for right side
image = PhotoImage(file='images\wows_icon.png')

# create instance of interface
gui = Interface(root, clan, image)

# main Tkinter loop
root.mainloop()
