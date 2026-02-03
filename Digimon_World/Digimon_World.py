import pandas as pd
import time
from pathlib import Path
from pynput.keyboard import Key

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_automation import game_automation, keyboard

from memory_scan import WATCH_KEYS, get_address_value, print_watch_values, attach_process
from dw1_addresses import ADDRESSES

DATA_FILENAME = "Digimon_World/Digimon World Data Sheet.xlsx"

Evolution_requirements = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Evolution")
Food                   = pd.read_excel(DATA_FILENAME, sheet_name="Food")
Digimon_raise          = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Raise")
Item_spawns            = pd.read_excel(DATA_FILENAME, sheet_name="Item Spawns (NTSC-U)")
Map_setup              = pd.read_excel(DATA_FILENAME, sheet_name="Map Setup")
Arena_rewards          = pd.read_excel(DATA_FILENAME, sheet_name="Arena Rewards") 

def main():
    digimon_world = Digimon_World()
    digimon_world.initialize_game_state()
    digimon_world.print_game_state()
    # digimon_world.run_script(keys_to_hold=[Key.down, Key.right])



# ==========================   MAIN CLASS   ===============================

class Digimon_World(game_automation):
    def __init__(self):
        super(Digimon_World, self).__init__()
        self.address_values = {key: None for key in WATCH_KEYS}
        self.process, self.psx_base = attach_process()
        self.initialize_game_state()
        self._closed = False

    def main(self):
        self.initialize_state()
        self.Mojyamon_arbitrage()

# ==========================  GAME STATE READING   ===============================

    def initialize_game_state(self):
        # Run at the top of the opening menu
        # self.boot_up_game()
        self.update_game_state()
        
    def update_game_state(self):
        for address_name in self.address_values:
            self.address_values[address_name] = get_address_value(
                address_name,
                process=self.process,
                psx_base=self.psx_base,
            )

    def print_game_state(self):
        for address, address_value in self.address_values.items():
            print(address, address_value)

# ==========================   LIFECYCLE   ===================================

    def close(self):
        if self._closed:
            return
        if getattr(self, "process", None):
            try:
                from memory_scan import K
                K.CloseHandle(self.process)
            finally:
                self.process = None
        self._closed = True

    def __del__(self):
        # Best-effort cleanup if user forgets to call close()
        try:
            self.close()
        except Exception:
            pass

# ==========================   INPUTS TO GAME   ===============================

    def boot_up_game():
        # Run at the top of the opening menu
        pass

    def Mojyamon_arbitrage(self):
        # Eventually should begin and end at Jijimon"s house
        self.execute_inputs(["z"])

    def Restock(self):
        # Just press square on all the items we need
        # Also restock devil chips if time between 6pm and 12pm
        pass

if __name__=="__main__":
    main()
