import pandas as pd
import time
from pathlib import Path
from pynput.keyboard import Key

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_automation import game_automation, keyboard

from memory_scan import WATCH_KEYS, get_address_value, print_watch_values, attach_process
from dw1_addresses import LOCATIONS, ADDRESSES

DATA_FILENAME = "Digimon_World/Digimon World Data Sheet.xlsx"

Evolution_requirements = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Evolution")
Food                   = pd.read_excel(DATA_FILENAME, sheet_name="Food")
Digimon_raise          = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Raise")
Item_spawns            = pd.read_excel(DATA_FILENAME, sheet_name="Item Spawns (NTSC-U)")
Arena_rewards          = pd.read_excel(DATA_FILENAME, sheet_name="Arena Rewards")



def main():
    digimon_world = Digimon_World()
    digimon_world.run_script()



# ==========================   MAIN CLASS   ===============================

class Digimon_World(game_automation):
    def __init__(self):
        super(Digimon_World, self).__init__()
        self.address_values = {key: None for key in WATCH_KEYS}
        self.process, self.psx_base = attach_process()
        self._closed = False

    def main(self, location_ID=0):
        tasks = {
            self.boot_up_game: 205,
            self.exit_Jijimons_house: 179,
            self.to_Birdamon: 207,
            (self.warp_to, ("Misty Trees",)): 119,
            self.misty_trees_rng_manip_part1: 121,
            self.misty_trees_rng_manip_part2: 119,
            self.misty_trees_rng_manip_part3: 179,
            # self.to_Jijimons_house: 205,
        }
        self.execute_task_list(tasks)
        # self.misty_trees_rng_manip_part1(testing=True)
        self.execute_script = False

    def execute_task_list(self, tasks):
        for task, destination_ID in tasks.items():
            self.execute_task(task)
            self.update_game_state()
            if self.location_ID!=destination_ID:
                self.wait_for_screen_transition(destination_ID, verbose=True)
            else:
                print("Task executed too late", self.location_ID)

    def execute_task(self, task):
        if isinstance(task, tuple):
            task, args = task[0], task[1]
            if not isinstance(args, (list, tuple)):
                args = (args,)
            task(*args)
        else:
            task()

# ==========================  GAME STATE READING   ===============================

    def wait_for_screen_transition(self, destination_ID, verbose=False):
        # expected_location = LOCATIONS[destination_ID]
        count = 0
        while self.location_ID != destination_ID:
            time.sleep(0.1)
            self.update_game_state()
            count+=1
            if count == 100:
                self.has_desynced = True
                return
        if verbose:
            print(f"Time waited: {count*0.1:.1f} seconds")
            print(f"Arrived at location ID = {self.location_ID}")
        
    def update_game_state(self, print_game_state=False):
        for address_name in self.address_values:
            self.address_values[address_name] = get_address_value(
                address_name,
                process=self.process,
                psx_base=self.psx_base,
            )
        if print_game_state:
            self.print_game_state()

        self.location_ID = self.address_values["Current Screen ID"]
        self.rng = self.address_values["RNG"]

    def print_game_state(self):
        for address, address_value in self.address_values.items():
            print(address, address_value)

# ==========================   INPUTS TO GAME   ===============================

    def boot_up_game(self):
        """ Run at the top of the opening menu """
        self.execute_inputs([(Key.down,0.03,0), "z", ("z",0.1,1.8), "z", ("z",0.1,4)])

    def exit_Jijimons_house(self):
        self.execute_inputs([(Key.right, 3)])

    def to_Jijimons_house(self):
        self.execute_inputs([ ((Key.up,Key.right), 0.3), (Key.up,1.5) ])

    def to_Birdamon(self, From="Jijimons house"):
        if From=="Jijimons house":
            self.execute_inputs([ ((Key.down,Key.right), 4) ])

    def warp_to(self, location):
        self.execute_inputs([ ((Key.up,Key.right), 1.3), ("z",0.7), ("z",0.5) ])
        down_presses = {
            "Great Canyon Top": 0,
            "Gear Savana": 1,
            "Ancient Dino Region": 2,
            "Freezeland": 3,
            "Misty Trees": 4,
            "Beetle Land": 5,
        }
        for n in range(down_presses[location]):
            self.execute_inputs([(Key.down,0.1)])
        self.execute_inputs(["z", ("z",0.5), ("z",0.5), "z"])

    def auto_pilot_home(self):
        self.execute_inputs([("z", 0.35)])

    def misty_trees_rng_manip_part1(self, testing=False):
        if not testing:
            time.sleep(2.7)
        
        for n in range(10):
            self.execute_inputs([(Key.right,0.35), (Key.left,0.2)])
            self.update_game_state()
            print(self.rng)
            if self.rng == 228325532: break
        if self.rng != 228325532:
            self.has_desynced = True

        self.execute_inputs([(Key.right,2)])
        
    def misty_trees_rng_manip_part2(self):
        self.execute_inputs([(Key.left,3)])

    def misty_trees_rng_manip_part3(self):
        self.execute_inputs([ ((Key.down, Key.left),6), (Key.left,2), ("z", 0.3), "a"])

    def Mojyamon_arbitrage(self):
        # Eventually should begin and end at Jijimon"s house
        self.keys_to_hold = [Key.down, Key.right]
        self.execute_inputs(["z"])

    def Restock(self):
        # Just press square on all the items we need
        # Also restock devil chips if time between 6pm and 12pm
        pass

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

if __name__=="__main__":
    main()
