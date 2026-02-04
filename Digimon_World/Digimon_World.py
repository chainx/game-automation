import pandas as pd
import time
import copy
from pathlib import Path
from pynput.keyboard import Key

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_automation import game_automation, keyboard

from memory_scan import WATCH_KEYS, get_address_value, print_watch_values, attach_process
from dw1_addresses import ITEMS, ADDRESSES

DATA_FILENAME = "Digimon_World/Digimon World Data Sheet.xlsx"

Evolution_requirements = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Evolution")
Food                   = pd.read_excel(DATA_FILENAME, sheet_name="Food")
Digimon_raise          = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Raise")
Arena_rewards          = pd.read_excel(DATA_FILENAME, sheet_name="Arena Rewards")

def main():
    digimon_world = Digimon_World()
    digimon_world.run_script()

class Digimon_World(game_automation):
    def __init__(self):
        super(Digimon_World, self).__init__()
        self.reload_key = Key.f1
        self.address_values = {key: None for key in WATCH_KEYS}
        self.process, self.psx_base = attach_process()
        self._closed = False
        print("Ready to run!")

        self.destination_ID = None

    def main(self):
        # self.practice_task(self.misty_trees_rng_manip_part1, task_location=119)
        # self.practice_task(self.save_game, task_location=205)
        # self.practice_task(self.care_taking)
        self.digipine_farming()

# ==========================   TASK PIPELINES   ===============================

    def digipine_farming(self):
        requirements = {
            "Care mistakes": "same",
            "Item/Digipine": "plus 1",
        }
        tasks = [
            self.boot_up_game,
            self.exit_Jijimons_house,
            self.to_Birdamon,
            (self.warp_to, "Misty Trees"),
            self.misty_trees_rng_manip_part1,
            self.misty_trees_rng_manip_part2,
            self.misty_trees_rng_manip_part3,
            self.care_taking,
            self.auto_pilot_home,
            self.to_Jijimons_house,
            (self.save_game, requirements),
        ]
        self.execute_task_list(tasks)
        self.execute_inputs([self.reload_key])

# ==========================   TASK EXECUTION   ===============================

    def execute_task_list(self, tasks, verbose=False):
        for task in tasks:
            self.execute_task(task)
            if self.has_desynced:
                print(f"Desynced on task: {self.task_name}")
                return
            self.waiting(verbose)

    def execute_task(self, task):
        if isinstance(task, tuple):
            task, args = task[0], task[1]
            if not isinstance(args, (list, tuple)):
                args = (args,)
            task(*args)
        else:
            task()

    def practice_task(self, task, task_location=None):
        if task_location:
            self.location_ID = 0
            self.wait_for_screen_transition(task_location, verbose=True)
        self.execute_task(task)
        self.waiting(verbose=True)
        self.execute_script = False

    def waiting(self, verbose=False):
        if self.destination_ID:
            self.update_game_state()
            if self.location_ID!=self.destination_ID:
                self.wait_for_screen_transition(self.destination_ID, verbose)
                if self.has_desynced: return
            else:
                print("Task executed too late", self.location_ID)
            self.destination_ID = None

    def wait_for_screen_transition(self, destination_ID, verbose=False):
        count = 0
        while self.location_ID != destination_ID:
            time.sleep(0.1)
            self.update_game_state()
            count+=1
            if count == 25: # Wait at most 2.5 seconds
                print("Didn't reach screen transition")
                self.has_desynced = True
                return
        if verbose:
            print(f"Time waited: {count*0.1:.1f} seconds")
            print(f"Arrived at location ID = {self.location_ID}")

# ==========================   GAME STATE READING   ===============================
        
    def update_game_state(self, verbose=False):
        for address_name in self.address_values:
            self.address_values[address_name] = get_address_value(
                address_name,
                process=self.process,
                psx_base=self.psx_base,
            )
        if verbose:
            self.print_game_state()

        self.location_ID = self.address_values["Current Screen ID"]
        self.rng = self.address_values["RNG"]
        self.update_inventory()

    def update_inventory(self):
        self.inventory = {}
        for n in range(30):
            item_name = ITEMS.get(self.address_values[f"Slot{n}/Name"], None)
            if item_name:
                self.inventory[item_name] = {
                    "Location": n,
                    "Amount": self.address_values[f"Slot{n}/Amount"],
                }
    
    def check_requirements(self, requirements):
        self.update_game_state()
        proceed = True
        for address, requirement_type in requirements.items():
            if "Item/" in address:
                item_name = address[5:]
                location = self.inventory[item_name]["Location"]
                address = f"Slot{location}/Amount"
            if requirement_type == "same":
                proceed = proceed and (self.address_values[address] == self.initial_address_values[address])
            if requirement_type == "plus 1":
                proceed = proceed and (self.address_values[address] == self.initial_address_values[address] + 1)
            if not proceed:
                print(f"Requirement not met: {address}, {requirement_type}")
                print(self.address_values[address], self.initial_address_values[address])
        return proceed

    def print_game_state(self):
        for address, address_value in self.address_values.items():
            if "Slot" not in address:
                print(address, address_value)
        for item_name, item_info in self.inventory.items():
            print(item_name, item_info)

# ==========================   TASK INPUTS   ===============================

    def use_item(self, item_name):
        """ Begins at the top left of the menu """
        self.update_game_state()
        if item_name not in self.inventory:
            print(f"Desync due to {item_name} not being in the inventory")
            self.has_desynced = True
            return
        item_location = self.inventory[item_name]["Location"]
        self.execute_inputs([("a", 0.3), ("z", 0.9)])
        if item_location % 2 == 1:
            self.execute_inputs([Key.right])
        for n in range(item_location//2):
            self.execute_inputs([Key.down])
        self.execute_inputs([("z", 0.25), "z"])
        time.sleep(4)
        # Include logic to handle scolding

    def care_taking(self, food_preference="Sirloin"):
        self.task_name = "care_taking"
        self.update_game_state()

        condition_flag = self.address_values["Condition flag"]
        sleepy, tired, hungry, poop, unhappy, injured, sick, _ = map(int, format(condition_flag, "08b")[::-1])
        if poop:
            self.use_item("Port. potty")
        if hungry:
            self.use_item(food_preference)
        if injured or sick:
            self.use_item("Medicine")
        if sleepy:
            # Add logic to defer until close to bedtime
            self.execute_inputs([("a", 0.3), Key.right, Key.right, Key.down, ("z",8)])
            
    def save_game(self, requirements={}):
        self.task_name = "save_game"
        if self.check_requirements(requirements):
            self.execute_inputs([(Key.left, 2), (Key.up,0.1), (Key.left, 0.5, 0.5)])
            self.execute_inputs([("z",0.25), ("z",0.1), "z", Key.down, "z", "z"])
            time.sleep(3)

    def boot_up_game(self):
        """ Begins at the top of the opening menu """
        self.task_name = "boot_up_game"
        self.destination_ID = 205
        self.execute_inputs([(Key.down,0.02,0), "z", ("z",0.1,1.8), "z", ("z",0.1,4)])
        self.update_game_state()
        self.initial_address_values = copy.deepcopy(self.address_values)

    def exit_Jijimons_house(self):
        self.task_name = "exit_Jijimons_house"
        self.destination_ID = 179
        self.execute_inputs([(Key.right, 3)])

    def to_Jijimons_house(self):
        self.task_name = "to_Jijimons_house"
        self.destination_ID = 205
        self.execute_inputs([ ((Key.up,Key.left), 2.7), (Key.up,3.5) ])

    def to_Birdamon(self, From="Jijimons house"):
        self.task_name = "to_Birdamon"
        self.destination_ID = 207
        if From=="Jijimons house":
            self.execute_inputs([ ((Key.down,Key.right), 4.2) ])

    def warp_to(self, location):
        self.task_name = "warp_to"
        location_info = {
            "Great Canyon Top":    [0, 38],
            "Gear Savana":         [1, 70],
            "Ancient Dino Region": [2, 79],
            "Freezeland":          [3, 93],
            "Misty Trees":         [4, 119],
            "Beetle Land":         [5, 105],
        }
        down_presses = location_info[location][0]
        self.destination_ID = location_info[location][1]

        self.execute_inputs([ ((Key.up,Key.right), 1.3), ("z",0.7), ("z",0.5) ])
        for n in range(down_presses):
            self.execute_inputs([(Key.down,0.1)])
        self.execute_inputs(["z", ("z",0.5), ("z",0.5), ("z",1.5)])

    def auto_pilot_home(self):
        self.task_name = "auto_pilot_home"
        self.destination_ID = 179
        self.use_item("Auto Pilot")
        time.sleep(1)



    def misty_trees_rng_manip_part1(self, testing=False):
        self.task_name = "misty_trees_rng_manip_part1"
        self.destination_ID = 121
        
        time.sleep(2.7)
        for n in range(10):
            self.execute_inputs([(Key.right,0.35), (Key.left,0.2)])
            self.update_game_state()
            if self.rng == 228325532: break
        if self.rng != 228325532:
            print("RNG value wrong")
            self.has_desynced = True

        self.execute_inputs([(Key.right,2.5)])
        
    def misty_trees_rng_manip_part2(self):
        self.task_name = "misty_trees_rng_manip_part2"
        self.destination_ID = 119
        self.execute_inputs([(Key.left,3.5)])

    def misty_trees_rng_manip_part3(self):
        self.task_name = "misty_trees_rng_manip_part3"
        self.execute_inputs([ ((Key.down, Key.left),6), (Key.left,2), ("z", 1.5)])



    def Mojyamon_arbitrage(self):
        self.task_name = "Mojyamon_arbitrage"
        self.keys_to_hold = [Key.down, Key.right]
        self.execute_inputs(["z"])

    def restock(self):
        # Just press square on all the items we need
        # Also restock devil chips if time between 6pm and 12pm
        self.task_name = "restock"

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
