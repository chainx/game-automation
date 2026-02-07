import pandas as pd, time, copy, shutil, sys, os
from pathlib import Path
from pynput.keyboard import Key

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from game_automation import game_automation, keyboard

from memory_scan import WATCH_KEYS, get_address_value, print_watch_values, attach_process
from dw1_addresses import ITEMS, ADDRESSES, LOCATIONS

DATA_FILENAME = "Digimon_World/Digimon World Data Sheet.xlsx"
MEMORY_CARD_LOCATION = Path("D:/Gaming/Emulators/PS1/cards/epsxe000.mcr")

Evo_requirements = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Evolution")
Food             = pd.read_excel(DATA_FILENAME, sheet_name="Food")
Digimon_raise    = pd.read_excel(DATA_FILENAME, sheet_name="Digimon Raise")
Arena_rewards    = pd.read_excel(DATA_FILENAME, sheet_name="Arena Rewards")

def main():
    digimon_world = Digimon_World()
    digimon_world.run_script()

class Digimon_World(game_automation):

    def main(self):
        if not hasattr(self, "inventory"):
            # Initialise address values
            self.execute_task_list(self.boot_up_and_leave_house())
        else:
            if (self.hour<7 or self.hour>18) and self.ice_shrooms < 99:
                self.ice_shroom_farming()
            elif self.chain_melons < 99:
                self.chain_melon_farming()
            elif self.digipines < 99:
                self.digipine_farming()
            elif self.bits < 999999:
                self.money_farming()
            else:
                self.execute_script = False

        self.execute_inputs([self.reload_key])

        # self.execute_task_list(self.warp_home_and_save({"Care mistakes": "same"}, from_shop=True))
        # self.practice_task(self.misty_trees_rng_manip_part1, task_location=119)
        # self.practice_task(self.save_game, task_location=205)
        # self.practice_task(self.care_taking, end_executiion=False)
        # self.practice_task(self.sell_goodies, task_location=216, end_executiion=False)
        # self.practice_task(self.auto_pilot_home, end_executiion=False)
        # self.practice_task((self.to_Jijimons_house, {"from_shop":False}))
                
    def __init__(self):
        super(Digimon_World, self).__init__()
        self.reload_key = Key.f1
        self.address_values = {key: None for key in WATCH_KEYS}
        self.process, self.psx_base = attach_process()
        self._closed = False
        print("Ready to run!")

        self.verbose = False
        self.initial_address_values = {}
        self.destination_ID = None # Used to check if a desync occured during a task

# ==========================   TASK PIPELINES   ===============================

    def chain_melon_farming(self):
        requirements = {
            "Care mistakes": "same",
            "Item/Chain melon": "increased",
        }
        tasks = self.from_boot_up_to_warp("Gear Savanna")
        tasks += [
            self.gear_savanna_rng_manip_part1,
            self.gear_savanna_rng_manip_part2,
            self.gear_savanna_rng_manip_part3,
            self.gear_savanna_rng_manip_part4,
            self.gear_savanna_rng_manip_part5,
        ]
        tasks += self.warp_home_and_save(requirements)
        self.execute_task_list(tasks)
        
        print(f"Total chain melons after {self.count+1} runs: {self.chain_melons}")

    def digipine_farming(self):
        requirements = {
            "Care mistakes": "same",
            "Item/Digipine": "increased",
        }
        tasks = self.from_boot_up_to_warp("Misty Trees")
        tasks += [
            self.misty_trees_rng_manip_part1,
            self.misty_trees_rng_manip_part2,
            self.misty_trees_rng_manip_part3,
        ]
        tasks += self.warp_home_and_save(requirements)
        self.execute_task_list(tasks)

        print(f"Total digipines after {self.count+1} runs: {self.digipines}")

    def ice_shroom_farming(self):
        requirements = {
            "Care mistakes": "same",
            "Item/Ice mushrm": "increased",
        }
        tasks = self.from_boot_up_to_warp("Freezeland")
        tasks += [self.pick_up_ice_shroom]
        tasks += self.warp_home_and_save(requirements)
        self.execute_task_list(tasks)

        print(f"Total ice shrooms after {self.count+1} runs: {self.ice_shrooms}")

    def money_farming(self):
        requirements = {
            "Care mistakes": "same",
            "Bits": "increased"
        }
        tasks = self.from_boot_up_to_warp("Freezeland")
        tasks += [
            self.to_Mojyamon_part1,
            self.to_Mojyamon_part2,
            self.to_Mojyamon_part3,
            self.to_Mojyamon_part4,
            self.Mojyamon_arbitrage,
            self.auto_pilot_home,
            self.enter_shop_part1,
            self.enter_shop_part2,
            self.sell_goodies,
        ]
        tasks += self.warp_home_and_save(requirements, from_shop=True)
        self.execute_task_list(tasks)

        print(f"Total bits after {self.count+1} runs: {self.bits}")

    def boot_up_and_leave_house(self):
        return [self.boot_up_game, self.exit_Jijimons_house]

    def from_boot_up_to_warp(self, destination):
        tasks = self.boot_up_and_leave_house()
        tasks += [self.to_Birdamon, (self.warp_to, destination)]
        return tasks

    def warp_home_and_save(self, requirements=None, from_shop=False):
        tasks = [
            self.care_taking,
            self.auto_pilot_home,
            (self.to_Jijimons_house, {"from_shop": from_shop}),
            (self.save_game, [requirements]),
        ]
        return tasks

# ==========================   TASK EXECUTION   ===============================

    def execute_task_list(self, tasks):
        for task in tasks:
            self.execute_task(task)
            if self.has_desynced:
                print(f"Desynced on task: {self.task_name}")
                return
            self.waiting()

    def execute_task(self, task):
        if isinstance(task, tuple):
            task, args = task[0], task[1]
            if isinstance(args, dict):
                task(**args)
            else:
                args = (args,) if not isinstance(args, (list, tuple)) else args
                task(*args)
        else:
            task()

    def waiting(self):
        if self.destination_ID:
            self.update_game_state()
            if self.location_ID!=self.destination_ID:
                self.wait_for_screen_transition(self.destination_ID)
            else:
                print(f"{self.task_name} executed too late", self.location_ID)
                self.has_desynced = True
            if self.has_desynced: 
                return
            self.destination_ID = None

    def wait_for_screen_transition(self, destination_ID, wait_indefinitely=False):
        count = 0
        while self.location_ID != destination_ID:
            time.sleep(0.1) # Check for update every 0.1 seconds
            self.update_game_state()
            count+=1
            if count == 25 and not wait_indefinitely: # Wait at most 2.5 seconds
                print("Didn't reach screen transition")
                self.has_desynced = True
                return
        if self.verbose:
            print(f"Time waited: {count*0.1:.1f} seconds")
            print(f"Arrived at location ID = {self.location_ID} ({self.location_name})")

    def practice_task(self, task, task_location=None, end_executiion=True):
        self.verbose = True
        if task_location:
            self.location_ID = 0
            self.wait_for_screen_transition(task_location, wait_indefinitely=True)
        self.execute_task(task)
        self.waiting()
        if end_executiion:
            self.execute_script = False

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
        self.location_name = LOCATIONS[self.location_ID]
        self.rng = self.address_values["RNG"]
        self.bits = self.address_values["Bits"]
        self.year, self.day, self.hour, self.minute = [
            self.address_values[address] for address in ("Year", "Day", "Hour", "Minute")
        ]
        flags = tuple(map(int, format(self.address_values["Condition flag"], "08b")[::-1]))
        self.sleepy, self.tired, self.hungry, self.poopy, self.unhappy, self.injured, self.sick, _ = flags
        self.update_inventory()
        self.chain_melons = self.inventory.get("Chain melon",{}).get("Amount", 0)
        self.ice_shrooms  = self.inventory.get("Ice mushrm",{}).get("Amount", 0)
        self.digipines    = self.inventory.get("Digipine",{}).get("Amount", 0)

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
            if requirement_type == "increased":
                proceed = proceed and (self.address_values[address] > self.initial_address_values[address])
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

# ==========================   TASK INPUTS (TOWN)   ===============================

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
        
        self.update_game_state()
        if self.address_values["Needs scolding"]:
            self.execute_inputs([("a", 0.3), Key.right, Key.down, ("z",2)])
            self.use_item(item_name)

    def care_taking(self, food_preference="Sirloin"):
        self.task_name = "care_taking"
        self.update_game_state()
        if self.verbose: print("Starting care taking")

        if self.poopy:
            self.use_item("Port. potty")
        if self.hungry:
            self.feeding(food_preference)
        if self.injured or self.sick:
            self.use_item("Medicine")
        if self.sleepy and self.address_values["Bedtime"]-self.hour < 4:
            self.execute_inputs([("a", 0.3), Key.left, ("z",7.2), ("z",2.5)])
    
    def feeding(self, food_preference="Sirloin"):
        if self.address_values["Lifespan"] < 20:
            food_preference = "Chain melon"
        self.use_item(food_preference)
        self.update_game_state()
        if self.sick: # Cancel sickness textbox
             self.execute_inputs([("z",0.1)])

    def save_game(self, requirements={}):
        self.task_name = "save_game"
        if self.check_requirements(requirements):
            self.execute_inputs([(Key.left, 2), (Key.up,0.1), (Key.left, 0.5, 0.5)])
            self.execute_inputs([("z",0.25), ("z",0.1), "z", Key.down, "z", "z"])
            time.sleep(3)

            debug_dir = MEMORY_CARD_LOCATION.parent / "Debug"
            debug_dir.mkdir(exist_ok=True)
            filename = f"{self.year}_{self.day}_{self.hour}_{self.minute}.mcr"
            shutil.copyfile(MEMORY_CARD_LOCATION, debug_dir / filename)

    def boot_up_game(self):
        """ Begins at the top of the opening menu """
        self.task_name = "boot_up_game"
        self.destination_ID = 205
        self.execute_inputs([(Key.down,0.02,0), "z", ("z",0.1,1.8), "z", ("z",0.1,4)])

    def exit_Jijimons_house(self):
        self.task_name = "exit_Jijimons_house"
        self.destination_ID = 179
        self.execute_inputs([(Key.right, 3)])
        self.update_game_state()
        self.initial_address_values = copy.deepcopy(self.address_values)

    def to_Jijimons_house(self, from_shop=False):
        self.task_name = "to_Jijimons_house"
        self.destination_ID = 205
        if from_shop:
            self.execute_inputs([ (Key.up,5),  ((Key.up,Key.left),1) ])
        else:
            self.execute_inputs([ (Key.up,6),  ((Key.up,Key.left),1) ])

    def to_Birdamon(self, From="Jijimons house"):
        self.task_name = "to_Birdamon"
        self.destination_ID = 207
        if From=="Jijimons house":
            self.execute_inputs([ ((Key.down,Key.right), 4.2) ])

    def warp_to(self, location):
        self.task_name = "warp_to"
        location_info = {
            "Great Canyon Top":    [0, 38],
            "Gear Savanna":         [1, 70],
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

    def sell_goodies(self):
        self.task_name = "sell_goodies"
        self.execute_inputs([ (Key.up, 2.5), ((Key.up, Key.left),.3) ])
        self.execute_inputs([ ("z",.5), ("z",.5), ("z",.8), Key.down, ("z",.3), "x", ("z",.3), ("z",.5) ])
        n = self.inventory["S.Def.disk"]["Location"]
        self.execute_inputs( [Key.down, ("z",.8)] + [Key.down]*n + [("z",.3), "x", ("z",.3), ("z",.5)] )
        self.execute_inputs([ ("a",.5), ("z",.2) ])        

    def enter_shop_part1(self):
        self.task_name = "enter_shop_part1"
        self.destination_ID = 192
        self.execute_inputs([ (Key.down, 3) ])

    def enter_shop_part2(self):
        self.task_name = "enter_shop_part2"
        self.destination_ID = 216
        self.execute_inputs([ (Key.down, 4.75), (Key.left, 1.5), (Key.up, 0.5) ])

# ==========================   TASK INPUTS (OUT OF TOWN)   ===============================

    def gear_savanna_rng_manip_part1(self):
        self.task_name = "gear_savanna_rng_manip_part1"
        self.destination_ID = 69
        self.execute_inputs([ ((Key.down,Key.left),4,1.5) ])
        self.update_game_state()
        if self.rng == 3852399341:
            self.execute_inputs([ (Key.down,2) ])
        elif self.rng == 1618087172:
            self.execute_inputs([ (Key.down,1,1.3), (Key.down,1) ])
        else:
            print(f"RNG desync in gear savanna: {self.rng}")
            self.has_desynced = True

    def gear_savanna_rng_manip_part2(self):
        self.task_name = "gear_savanna_rng_manip_part2"
        self.destination_ID = 70
        self.execute_inputs([ (Key.up,3) ])

    def gear_savanna_rng_manip_part3(self):
        self.task_name = "gear_savanna_rng_manip_part3"
        self.destination_ID = 69
        self.execute_inputs([ (Key.down,3) ])

    def gear_savanna_rng_manip_part4(self):
        self.task_name = "gear_savanna_rng_manip_part4"
        self.destination_ID = 74
        self.execute_inputs([ (Key.down,7), ((Key.down,Key.right),3), (Key.right,2) ])

    def gear_savanna_rng_manip_part5(self):
        self.task_name = "gear_savanna_rng_manip_part5"
        self.execute_inputs([ ((Key.down,Key.right),3.5), (Key.right,.6), ((Key.down,Key.right),2), ("z",1) ])

    def misty_trees_rng_manip_part1(self):
        self.task_name = "misty_trees_rng_manip_part1"
        self.destination_ID = 121
        
        time.sleep(2.7)
        self.execute_inputs([(Key.right,0.4)])
        for n in range(10):
            # self.execute_inputs([(Key.right,0.35), (Key.left,0.2)]) # For fast digimon
            self.execute_inputs([(Key.right,0.6), (Key.left,0.45)])   # For slow digimon
            self.update_game_state()
            if self.rng == 228325532: break
            # elif self.rng == 979431494: self.has_desynced = True
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

    def pick_up_ice_shroom(self):
        self.task_name = "pick_up_ice_shroom"
        inputs = [ ((Key.down, Key.right),5.2), (Key.down,1.8), ((Key.down, Key.left),1), ("z",.5) ]
        self.execute_inputs(inputs)

    def to_Mojyamon_part1(self):
        self.task_name = "to_Mojyamon_part1"
        self.destination_ID = 96
        self.execute_inputs([ ((Key.down,Key.right), 6) ])

    def to_Mojyamon_part2(self):
        self.task_name = "to_Mojyamon_part2"
        self.destination_ID = 132
        self.execute_inputs([ (Key.down, 6), ((Key.down,Key.right), 1.5),  (Key.down, 2.5)])

    def to_Mojyamon_part3(self):
        self.task_name = "to_Mojyamon_part3"
        self.destination_ID = 133
        self.execute_inputs([ ((Key.down,Key.left), 3),  (Key.down, 6)])

    def to_Mojyamon_part4(self):
        self.task_name = "to_Mojyamon_part4"
        self.execute_inputs([ ((Key.down,Key.left), 2.5),  (Key.down, 1.7) ])
        self.execute_inputs([ ((Key.down,Key.right), 1.5),  (Key.right, 1), ((Key.up,Key.right), 1) ])

    def Mojyamon_arbitrage(self):
        self.task_name = "Mojyamon_arbitrage"
        while "med.recovery" in self.inventory:
            self.execute_inputs([ ("z", 0.5), "z", ("z", 0.8), Key.down, "z", ("z", 0.5), ("z", 0.5), "z" ])
            self.update_game_state()

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
