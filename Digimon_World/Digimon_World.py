import pandas as pd
import time
from pathlib import Path
from pynput.keyboard import Key

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_automation import game_automation, keyboard

from memory_scan import get_address_values, print_watch_values
from dw1_addresses import ADDRESSES

DATA_FILENAME = "Digimon_World/Digimon World Data Sheet.xlsx"

Evolution_requirements = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Evolution")
Food                   = pd.read_excel(DATA_FILENAME, sheet_name="Food")
Digimon_raise          = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Raise")
Item_spawns            = pd.read_excel(DATA_FILENAME, sheet_name="Item Spawns (NTSC-U)")
Map_setup              = pd.read_excel(DATA_FILENAME, sheet_name="Map Setup")
Arena_rewards          = pd.read_excel(DATA_FILENAME, sheet_name="Arena Rewards") 

def main():
    print_watch_values()
    # digimon_world = Digimon_World()
    # digimon_world.run_script(keys_to_hold=[Key.down, Key.right])

# ==================================================================

def get_value(value_name):
    pass

class Digimon_World(game_automation):
    def __init__(self):
        super(Digimon_World, self).__init__()
        self.initialize_state()

    def main(self):
        self.Mojyamon_arbitrage()

# ==================================================================

    def initialize_state(self):
        # Run at the top of the opening menu
        self.boot_up_game()
        self.update_game_state()
        

    def update_game_state(self):
        for address, value in self.address_values.items():
            self.care_mistakes = get_value()

    def Mojyamon_arbitrage(self):
        # Eventually should begin and end at Jijimon"s house
        self.execute_inputs(["z"])

    def Restock(self):
        # Just press square on all the items we need
        # Also restock devil chips if time between 6pm and 12pm
        pass

if __name__=="__main__":
    main()
