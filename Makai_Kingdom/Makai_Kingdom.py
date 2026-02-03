import time
import datetime
import os
import numpy as np
import pytesseract
# import easyocr    No longer imported due to reliance on Numpy 1.X
from collections import Counter
from pathlib import Path
from pynput.keyboard import Key
from PIL import Image
from fuzzywuzzy import fuzz

import warnings
warnings.filterwarnings("ignore", category=FutureWarning) # Filters easyocr warnings

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game_automation import game_automation
from image_to_text import find_items_to_sell, clean_image, isolate_text, partition_screenshot

save_path = Path('Makai_Kingdom/Reference images')

easyOCRreader = None # easyocr.Reader(['en'])

# I use different key bindings on Windows and Linux due to conflicts with my key binds on Linux
linux_or_windows = 'windows' if os.name=='nt' else 'linux'
frame_limit_key = Key.f4 if linux_or_windows=='windows' else Key.end
win_name_filter = 'NTSC | Limiter: Normal | GSdx OGL HW | 640x224' if linux_or_windows=='windows' else 'Makai Kingdom - Chronicles of the Sacred Tome'
ref_image = Image.open(save_path / f'BabylonsMessenger_{linux_or_windows}.png').convert('RGB')

# On Linux run:
#    wmctrl -r "Makai Kingdom - Chronicles of the Sacred Tome" -e 0,1400,250,640,480
# To ensure the window is the correct size for screenshots to match reference images

chars_to_summon = [
    {'char_slot': -1, 'char_name': 'Gracie'},
]
selling_frequency = 100

initial_item_count = 211
first_star_item_index = 179
first_food_item_index = 207

char_type = 'atk' # (atk, tec, int, yosh)
create_food_dungeon = False # Used when levelling up 
food_dungeons_total = 2

character_healing_frequency = selling_frequency
vehicle_healing_frequency = 0
attack_castle = True

def main():
    print(datetime.datetime.now())
    makai_kingdom = Makai_Kingdom()
    makai_kingdom.run_script()

class Makai_Kingdom(game_automation):

    def main(self):
        # self.hell_farming()
        # self.convert_hell_to_materials(41141494303)
        # self.weapon_mastery()
        # self.BabylonsMessenger_main()
        # self.FoodDungeon_main(feeding=True)
        # self.reincarnate()
        # self.beat_food_dungeon()
        # self.sell_items(total_item_count=764)
        # self.organise_inventory()
        # self.execute_inputs(self.finish_level('Zodiac'))
        self.execute_inputs(['s'])
        # self.execute_script = False

    def __init__(self):
        super(Makai_Kingdom, self).__init__()
        self.chars_to_summon = chars_to_summon
        self.win_name_filter = win_name_filter
        self.initial_item_count = initial_item_count
        self.total_item_count = self.initial_item_count
        self.first_food_item_index = first_food_item_index
        self.first_star_item_index = first_star_item_index
        self.mana_farming = True
        self.free_dungeons = 0
        self.mana_farming_cycles, self.mana = 0, 0

    def finish_level(self, attack=None):
        if attack == 'Giga Wind':
            return ['w', 's', (frame_limit_key, 0.01, 2.1)] + [('s', 0.04)]*4 + [('s', 0.65), (frame_limit_key, 0.01, 0.25)]
        if attack == 'Yoshitsuna':
            return ['w', 's', (frame_limit_key, 0.01, 2.3)] + [('s', 0.04)]*3 + [('s', 0.65), (frame_limit_key, 0.01, 0.25)]
        if attack == 'Zodiac':
            return ['w', 's', (frame_limit_key, 0.01, 1.9)] + [('s', 0.04)]*3 + [('s', 0.65), (frame_limit_key, 0.01, 0.25)]
        if attack == 'Seven Sins':
            return ['w', 's', (frame_limit_key, 0.01, 4)] + [('s', 0.04)]*3 + [('s', 0.65), (frame_limit_key, 0.01, 0.25)]
        else:
            return ['w', 's', (frame_limit_key, 0.01, 2.5)] + [('s', 0.04)]*3 + [('s', 0.65), (frame_limit_key, 0.01, 0.25)]
        
    def weapon_mastery(self, N_chars=2):
        inputs = [(Key.enter,0.3)]*2
        inputs += ['s', Key.down, 's', 's', 's', (Key.enter, 0.3)]*N_chars
        inputs += ['w', Key.down, 's', (frame_limit_key, 0.01, 1.5), (frame_limit_key, 0.5)]
        self.execute_inputs(inputs)
    
    def hell_farming(self):
        if self.mana_farming:
            inputs = self.mana_farming_inputs()
            if self.has_desynced or not self.execute_script:
                return
            self.mana += 3035295
            self.mana_farming_cycles += 1
            inputs += self.create_free_dungeon()
            inputs += self.heal(heal_characters=True, heal_vehicles=(self.mana_farming_cycles-1)%50==0)
        else:
            inputs = self.free_dungeon_inputs()
            if self.has_desynced or not self.execute_script:
                return
            self.free_dungeons -= 1
            if self.free_dungeons == 0:
                self.mana_farming = True
        
        self.execute_inputs(inputs)
        if self.mana_farming:
            inputs = self.start_level(stage=2, level=3)
        else:
            inputs = self.start_level(free_dungeon=True)
        if self.has_desynced or not self.execute_script:
            return           
        inputs += ['s', (Key.home, 1.75), Key.f1]
        self.execute_inputs(inputs)

    def mana_farming_inputs(self):
        inputs = []
        hut_distances = [0.88, 0.74, 0.62]
        for hut_distance in hut_distances:
            inputs += ['s', 's', Key.left, Key.up, 's', (Key.right, hut_distance), 's', (Key.home, 0.5)] #1.3)]
            self.execute_inputs(inputs)
            get_screen_region = lambda geom: (geom[0] + 0, geom[1] + 150, geom[2], 160)
            screenshot = self.take_screenshot(get_screen_region)
            text = isolate_text(screenshot)
            if fuzz.ratio(text, 'INVITE') < 60:
                self.has_desynced = True
                return
            inputs = [(Key.home, 0.8)]

        inputs += ['s', 's', Key.down, 's', (Key.right, 0.5), 's', (Key.home, 1.3)]
        inputs += ['s', 's', 's', (Key.right, 0.2), 's', (Key.home, 1.3)]
        inputs += ['s', 's', 's', (Key.down, 0.1), 's', (Key.home, 1.3)]
        inputs += [(Key.down, 0.1), 's'] + [Key.down]*3 + ['s', (Key.up, 0.1), 's'] + [Key.up]*3 +['s', (Key.right, 0.4), 'a', (Key.right, 0.55), ('s',0.5)]
        inputs += [Key.enter, 's', Key.down, 's', 's', 's', 'w', Key.down, 's', (frame_limit_key, 0.01, 2), frame_limit_key]

        for n in range(9):
            inputs += [(Key.left,0.4), 's', Key.down, 's', 's', 's', 'w', Key.down, 's', (frame_limit_key, 0.01, 1.8), frame_limit_key]

        inputs += [(Key.left,0.7), 's', Key.down, 's', 's', Key.right, 's']
        inputs += [(Key.left, 0.4)] + [(Key.enter, 0.1)]*4 + ['s', 's', (Key.right, 0.6), 'a', 'a', (Key.left,0.7), ('s', 0.7)]
        inputs += self.finish_level('Seven Sins')
        return inputs
    
    def create_free_dungeon(self):
        N = self.mana // 1000000
        self.mana -= N * 1000000
        self.free_dungeons += N
        self.mana_farming = False
        requip = ['w', ('s', 0.4)] + ['s']*5 + ['d', 'd', ('d', 0.55), 'd']
        inputs = [(Key.up, 0.4), Key.right] + requip
        inputs += [('s', 0.8), Key.up, Key.up, Key.up, ('s',0.3), ('s',0.5), 's', 's', (Key.home, 1.5)]*N
        inputs += requip + [(Key.down,0.45)]
        return inputs
    
    def free_dungeon_inputs(self):
        inputs = ['s', 's', Key.left, 's', (Key.up, 0.2), (Key.left, 0.1), 's', (Key.home, 1.3), Key.enter, 's', 's', (Key.left, 0.35), ('s', 1)]
        inputs += ['s', 's', (Key.up, 0.4), 's', ',', 's', Key.down, 's', 's', 's']
        inputs += self.finish_level('Yoshitsuna')
        return inputs
    
    def convert_hell_to_materials(self, total_hell):
        inputs, cycles = [], 0
        print(total_hell)
        while total_hell > 2699999:
            amount_to_sell = min(1200-initial_item_count, int(total_hell/2699999))
            inputs += [('s', 1.3), ('s', 0.3), 's'] + [Key.up]*5 + ['s']*amount_to_sell
            inputs += ['d', 'd', (Key.down, 0.5)]
            inputs += [('s', 1.3), ('s', 0.3), Key.down, Key.down, 's', Key.up] + ['s']*amount_to_sell
            inputs += ['d', 'd', (Key.up, 0.5)]
            inputs += [Key.right] if cycles>0 and cycles%10==0 else []
            total_hell -= amount_to_sell * 2699999
            cycles+=1
        print(f'Total selling cycles: {cycles}')
        self.execute_inputs(inputs+[Key.f1])
        self.execute_script=False

    def BabylonsMessenger_main(self):
        inputs = self.BabylonsMessenger_inputs()
        self.execute_inputs(inputs)
        
        if not self.execute_script:
            return
        if selling_frequency == 0:
            pass
        elif self.count > 0 and self.count % selling_frequency == 0 and self.execute_script and not self.has_previously_desynced:
            total_item_count = self.count_total_items(debug_label='initial_item_count')
            print(f'Total item count: {total_item_count}, previous item count: {self.initial_item_count}')
            if total_item_count < self.initial_item_count: # This will only happen if there's an OCR error
                self.has_desynced = True
                return
            else:
                self.go_ahead_with_sales(total_item_count)

        heal_characters = self.count % character_healing_frequency == 0 if character_healing_frequency > 0 else False
        heal_vehicles = self.count % vehicle_healing_frequency == 0 if vehicle_healing_frequency > 0 else False
        inputs = self.heal(heal_characters, heal_vehicles)
        self.execute_inputs(inputs)

        stage = 2 if heal_characters or heal_vehicles else 0
        inputs = self.start_level(stage=stage, level=3)
        if self.has_desynced or not self.execute_script:
            return           
        inputs += ['s', (Key.home, 1.75), Key.f1]
        self.execute_inputs(inputs)
        # if self.execute_script:
        #     get_screen_region = lambda geom: (geom[0] + 20, geom[1] + 50, geom[2] // 2, geom[3] // 2)
        #     screenshot = self.take_screenshot(get_screen_region)
        #     self.has_desynced = not self.images_match(ref_image, screenshot)
        #     if not self.has_desynced:
        #         self.key_press('s', wait=2.5)
        #         self.key_press(Key.f1, wait=1)

    def go_ahead_with_sales(self, total_item_count):
        self.sell_items(total_item_count)
        prev_initial_item_count = self.initial_item_count
        self.initial_item_count = self.count_total_items(exit_menu=False, debug_label='final_item_count')
        print(f'Total items after sales: {self.initial_item_count}')
        if self.initial_item_count < self.first_food_item_index: # This will only happen if there's an OCR error
            self.count += 1 # Collect a lot more items before trying again
            self.initial_item_count = prev_initial_item_count
            self.has_desynced = True
            return
        mana_count = self.count_mana(char_slot=5)

    def FoodDungeon_main(self, feeding=True):
        # Start with cursor on Equip in menu
        # Facility must be highlighted in the equip menu if creating food dungeons
        # Academy with char to be trained at top, warehouse just below

        self.beat_food_dungeon(feeding)
        if not self.execute_script:
            return
        self.prep_for_next_food_dungeon(create_food_dungeon)
        inputs = self.heal(heal_characters=True, heal_vehicles=False)
        if self.count < food_dungeons_total - 1:
            inputs += [('s', 0.05, 1), ('s', 0.05, 1), Key.down, 's', ('s', 4)]
            self.execute_inputs(inputs)
        else:
            self.execute_inputs(inputs)
            self.execute_script = False

    
    def beat_food_dungeon(self, feeding=True):
        inputs = [
            'e', 's', 's', Key.left, 's', (Key.left, 0.35), ('s', 2.6),             # Summon Academy
            's', 's', Key.left, 's', (Key.right, 0.4), ('s', 2.6),                  # Summon Warehouse
            (Key.left, 0.25), 's', 's', (Key.right, 0.25), (Key.up, 0.2), ('s', 1), # Exit Academy
            (Key.down, 0.2), 's',                                                   # Reselect Tome
        ]
        if feeding:
            feed_directions = [[(Key.down, 0.2)]] * 2 if char_type != 'yosh' else [] # Can't feed Yoshitsuna
            for x_direction in [(Key.left, 0.15), (Key.right, 0.05), (Key.right, 0.2)]:
                for y_direction in [(Key.up, 0.22), (Key.up, 0.4), (Key.up, 0.5)]:
                    feed_directions.append([x_direction, y_direction])
            for direction in feed_directions:
                inputs += ['s', Key.up, 's', (Key.up, 0.4), ('s', 2.6), (Key.up, 0.4)]
                for n in range(5): # Feeding
                    inputs += ['s', Key.down, Key.down, 's'] + [Key.down]*n + ['s', 's'] + direction + ['s', (Key.home, 1.7, .1)]
                inputs += ['s', 's', (Key.right, 0.4), (Key.down, 0.2), 's', Key.down, ('s', 1.2)]
                inputs += [(Key.enter, 0.2), 's', Key.up] if char_type != 'yosh' else [(Key.enter, 0.2)]*2 + ['s', Key.up]

        inputs += ['d', (Key.up, 0.15), 's'] # Select main char 
        inputs += self.attack_food_dungeon_inputs()
        inputs += self.finish_level('Zodiac')
        self.execute_inputs(inputs)

        if self.execute_script:
            self.total_item_count -= 11*5  if char_type != 'yosh' else 9*5 # 11 or 9 Chefs each using 5 food items

    def prep_for_next_food_dungeon(self, create_food_dungeon):
        total_item_count = self.count_total_items(position_in_menu=0, keep_arranging=True, debug_label='item_count')
        if total_item_count == self.total_item_count + 1:
            print('Item acquired in food dungeon')
            self.move_item_above_food_and_stars(total_item_count)
            self.total_item_count += 1
            self.first_food_item_index += 1
            self.first_star_item_index += 1

        inputs = [
            'd', Key.up, Key.up, ('s', 0.5), 's', ('s', 0.2), 'w', ('d', 0.2), ('d', 0.2), Key.up, 's', # Leave academy and navigate to char equip
            Key.up, 's', 'w', 's', Key.up, Key.up, 's', ('d', 0.2), ('d', 0.2), ('d', 0.5), 'd', (Key.up, 0.45), Key.right, # Equip food and move to Zetta
            ('s', 0.8), Key.up, Key.up, Key.up, ('s', 0.3), ('s', 0.5), 's', ('s', 2.7), (Key.down, 0.45), # Wish for dungeon
        ]
        if create_food_dungeon:
            self.execute_inputs(inputs)
            inputs = ['w', ('s', 0.5), 's'] # Navigate to char equip
        else:
            inputs = ['d', Key.up, Key.up, ('s', 0.5), 's'] # Navigate to char equip

        inputs += ['s', 's', 's', 'd'] if create_food_dungeon else [] # Re-equip weapon if food dungeon created
        # down_presses = 2 if create_food_dungeon and char_type != 'yosh' else 1 # Requires academy almost full / full
        inputs += [Key.up] #, 'q'] + [Key.down]*down_presses # Navigate to first chef

        for chef in range(11):
            inputs += ['s']
            for food_item in range(5):
                if chef == 0 and food_item == 0:
                    inputs += ['s', Key.up, 's', Key.down]
                else:
                    inputs += ['s', 's', Key.down]
            inputs += ['d', Key.up] 

        if create_food_dungeon: # Re-enter academy
            inputs += ['d', Key.down, 's', ('s', 0.2), 's', 's', ('d', 0.2), ('d', 0.2), ('d', 0.5), 'd']
        else:
            inputs += ['d', ('d', 0.5), 'd']
        self.execute_inputs(inputs)

    def move_item_above_food_and_stars(self, total_item_count):
        inputs = ['s', Key.up, 's']
        for N in range(2):
            for n in range((total_item_count-self.first_food_item_index)//8):
                inputs += [('q', 0.02, 0.02)]
            for n in range((total_item_count-self.first_food_item_index)%8):
                inputs += [(Key.up, 0.02, 0.02)]
            inputs += ['s']
        for n in range((self.first_food_item_index-self.first_star_item_index)//8):
            inputs += [('q', 0.02, 0.02)]
        for n in range((self.first_food_item_index-self.first_star_item_index)%8):
            inputs += [(Key.up, 0.02, 0.02)]
        inputs += ['s', 'd']
        self.execute_inputs(inputs)

    def sell_items(self, total_item_count):
        inputs = [(Key.right, 1), ('s', 1.3), ('s', 0.3), Key.down, Key.down, ('s', 0.1), Key.up]
        self.execute_inputs(inputs)

        total_items_kept, offset, total_items_sold, sell_from_bottom_up = [], 0, 0, True
        while total_items_sold < total_item_count - self.initial_item_count - len(total_items_kept):

            # Define region to screenshot and take screenshot
            get_screen_region = lambda geom: (geom[0]+geom[2]//10, geom[1]+geom[3]//6, geom[2] // 4, geom[3] // 2)
            screenshot = self.take_screenshot(get_screen_region)

            # Use OCR image to text processing to determines which items are kept, and where their indices are
            items_kept, items_kept_indices = find_items_to_sell(screenshot, offset, sell_from_bottom_up)
            total_items_kept += items_kept

            # Get inputs from items to keep scraped from images
            inputs = self.get_inputs_from_items_to_keep(offset, sell_from_bottom_up, total_items_kept, items_kept, items_kept_indices)
            self.execute_inputs(inputs)
            time.sleep(0.2)

            # Update variables used to determine inputs from the items to keep
            total_items_sold += 8 - offset - len(items_kept)
            if offset == 8:
                sell_from_bottom_up = False
            offset = len(total_items_kept) if sell_from_bottom_up else 0

        inputs = ['d', 'd', (Key.left, 0.8)]
        self.execute_inputs(inputs)

    def get_inputs_from_items_to_keep(self, offset, sell_from_bottom_up, total_items_kept, items_kept, items_kept_indices):
        inputs = [] 
        skip_key = Key.up if sell_from_bottom_up else Key.down
        if offset == 7:
            skip_key = 'q'
        for n in range(8 - offset):
            inputs += [skip_key] if n in items_kept_indices else ['s']
        if not sell_from_bottom_up:
            inputs += [Key.up] * len(items_kept) + ['q']
        return inputs
    
    def organise_inventory(self):
        get_screen_region = lambda geom: (geom[0]+geom[2]//3+10, geom[1]+geom[3]//6-5, geom[2]//3, geom[3]//2+40)
        current_pos = 0
        while current_pos < self.total_item_count - self.first_food_item_index -1 and self.execute_script:
            screenshot = self.take_screenshot(get_screen_region)
            offset = 0 if current_pos==0 else 7
            item_images = partition_screenshot(screenshot, offset, box_height=35)[::-1]
            for index, item_image in enumerate(item_images):
                _, has_stars = clean_image(item_image)
                if has_stars:
                    inputs = ['s']
                    distance_to_first_food_item=self.total_item_count-self.first_food_item_index-current_pos-index
                    distance_to_first_food_item -= 1 if current_pos!=0 else 0
                    for n in range(distance_to_first_food_item // 8):
                        inputs += [('q', 0.02, 0.02)]
                    for n in range(distance_to_first_food_item % 8):
                        inputs += [(Key.up, 0.02, 0.02)]
                    inputs += ['s', Key.up]
                    self.execute_inputs(inputs)
                    self.first_food_item_index += 1
                else:
                    self.execute_inputs([Key.up])
            current_pos += 7 if current_pos==0 else 1

    def reincarnate(self):
        if self.first_star_item_index == self.first_food_item_index:
            self.key_press(Key.f1)
            self.execute_script = False
            print(datetime.datetime.now())
            return
        
        # Summon star item
        if self.count>0:
            inputs = [('s', 0.8), ('s', 0.3), Key.right]
            for n in range(self.first_star_item_index//7):
                inputs += [('e', 0.02, 0.02)]
            for n in range(self.first_star_item_index%7-1):
                inputs += [(Key.down, 0.02, 0.02)]
            inputs += ['s', (Key.right, 0.1), (Key.down, 0.47), ('s', 1.9), (Key.down, 1.1), ('s', 0.8), ('s', 0.3)]
            self.execute_inputs(inputs)

        # Check star bonus
        # get_screen_region = lambda geom: (geom[0]+geom[1]//3+5, geom[1]+geom[3]//3+35, geom[2]//10 - 30, geom[3]//12-10)
        # star_bonus = self.extract_count(get_screen_region, debug_label='reincarnation')
        # if not star_bonus:
        #     print('Failed to read star bonus')
        #     self.has_desynced = True
        #     return
        # if type(star_bonus)==tuple:
        #     input('Continue?')
        # if self.count == 0:
        #     self.star_bonus = star_bonus
        self.star_bonus = 0
        star_bonus = self.star_bonus + 3

        if star_bonus < self.star_bonus or star_bonus > self.star_bonus + 4:
            self.first_food_item_index += 1
            self.total_item_count += 1
            self.has_desynced = True
            self.execute_script = False if self.count==0 else True
            return
        else:
            print(f'Current star bonus is: {star_bonus}, first food item is at index: {self.first_food_item_index}')
            self.star_bonus = star_bonus
            # self.key_press(Key.f1)
        if star_bonus >= 500:
            self.key_press(Key.f1)
            self.execute_script = False
            print(datetime.datetime.now())
            return

        # Create and sacrifice character
        inputs = [
            ('s', 0.5), 's', Key.up, 's', Key.up, 's', ('s', 4.8),           # Create new character
            (Key.left, 0.17), (Key.up, 0.77), (Key.right, 0.05),             # Move back to Zetta 
            ('s', 0.8), Key.up, Key.up, Key.up, ('s', 0.3),                  # Make a wish
            (Key.right, 0.09), (Key.down, 0.5), ('s', 0.5), 's', ('s', 0.9), # Navigate to sacrifice choice
            's', (frame_limit_key, 0.1, 2), (frame_limit_key, 0.1, 0.7),     # Sacrifice character
            ('s', 0.8), Key.down, Key.down, Key.down, ('s', 0.3), Key.left, Key.up, 's', Key.down, ('s', 2), ('d', 0.3) # Delete new building
        ]
        self.execute_inputs(inputs)

    def extract_count(self, get_screen_region, debug_label='', debug=False):
        if debug:
            screenshot = Image.open(save_path/f'debug_{debug_label}.png')
        else:
            screenshot = self.take_screenshot(get_screen_region)
            screenshot, _ = clean_image(screenshot)
            screenshot.save(save_path/f'debug_{debug_label}.png')

        result_1 = pytesseract.image_to_string(screenshot, config=r'--psm 8 -c tessedit_char_whitelist=0123456789').strip()
        result_2 = easyOCRreader.readtext(np.array(screenshot), detail=0, allowlist='0123456789') # Uses easyOCR
        result_2 = result_2[0] if result_2 else None
        
        if result_1==None and result_2==None:
            self.has_desynced = True
            return
        elif result_1 != result_2:
            print(f'The following results were obtained {result_1}, {result_2}')
            # Check if the two results only differ by a single digit
            c1, c2 = Counter(result_1), Counter(result_2)
            diff = {k: abs(c1.get(k, 0) - c2.get(k, 0)) for k in set(c1) | set(c2)}
            if sum(diff.values())==1:
                if len(c1) < len(c2):
                    return int(result_1)
                else:
                    return int(result_2)
            return result_1, result_2
        return int(result_1)

    def count_mana(self, char_slot=0):
        self.execute_inputs([Key.up, 's'] + [Key.down]*char_slot + [('s', 0.2)])
        get_screen_region = lambda geom: (geom[0]+300, geom[1]+geom[3]//8 + 10, geom[2]//8 - 10, geom[3]//20 - 7)
        mana_count = self.extract_count(get_screen_region, debug_label='mana')
        self.execute_inputs([('d', 0.1), 'd', Key.down, 'd'])
        print(f'Total mana is: {mana_count}')
        return mana_count
    
    def count_total_items(self, position_in_menu=2, exit_menu=True, keep_arranging=False, debug_label=''):
        menu_inputs = [Key.down if position_in_menu < 2 else Key.up]*abs(position_in_menu-2)
        self.execute_inputs(['w'] + menu_inputs + ['s', (Key.right, 0.2)])
        get_screen_region = lambda geom: (geom[0]+geom[2]//3 + 32, geom[1]+geom[3]//10 + 10, geom[2] // 15, geom[3] // 28)
        total_item_count = self.extract_count(get_screen_region, debug_label)
        if not keep_arranging:
            inputs = ['d', 'd'] if exit_menu else ['d']
            self.execute_inputs(inputs)
        return total_item_count

    def BabylonsMessenger_inputs(self):
        inputs = [] # Starts inside the level

        invite_selected, chars_summoned = True, 1
        for i, char_dict in enumerate(self.chars_to_summon):
            not_penultimate_char = (i < len(self.chars_to_summon)-1)
            char_slot, char_name, participating, is_vehicle = self.unpack_char_dict(char_dict)
            inputs += self.summon_char(char_slot, participating, is_vehicle, invite_selected, chars_summoned)
            if participating:
                if attack_castle:
                    inputs += self.attack_castle_inputs(char_name)
                    chars_summoned+=1
                    if char_name=='Slash':
                        invite_selected = False
                else:
                    inputs += ['s', 's', (Key.right, 0.52), (Key.down, 0.1), 's', Key.down, ('s', 1.2)] # Enter castle
                    invite_selected = False
            if not_penultimate_char:
                inputs += [(Key.left, 0.3), (Key.enter, 0.1)] # Reselect tome
            else:
                inputs += self.finish_level()
                
        return inputs

    def unpack_char_dict(self, char_dict):
        char_slot = char_dict.get('char_slot', 0)
        char_name = char_dict.get('char_name')
        participating = char_dict.get('participating', True)
        is_vehicle = char_dict.get('is_vehicle', False)
        return char_slot, char_name, participating, is_vehicle

    def summon_char(self, char_slot, participating=True, is_vehicle=False, invite_selected=True, chars_summoned=1):
        inputs = ['s', 's'] if invite_selected else ['s', Key.up, 's']
        if is_vehicle:
            inputs += [Key.right]
        inputs += self.menu_select(char_slot)
        if participating:
            inputs += [(Key.right, 0.47), 's', (Key.home, 1.3)] + [Key.enter] * chars_summoned
        else:
            inputs += [(Key.left, 0.3), 's', (Key.home, 1.3)]
        return inputs

    def heal(self, heal_characters=True, heal_vehicles=False):
        healing_time = 0.3 if not self.has_previously_desynced else 2
        if heal_characters and heal_vehicles:
            return [(Key.right, 1), ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), ('w', healing_time), 'd', 'd',
                    (Key.left, 1.5), ('s', 1), ('s', 0.3), ('w', healing_time), 'd', (Key.right, 0.38)]
        elif heal_characters:
            return [(Key.left, 0.5), ('s', 1), ('s', 0.3), ('w', healing_time), 'd', (Key.right, 0.38)]
        elif heal_vehicles:
            return [(Key.right, 1), ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), ('w', healing_time), 'd', 'd', (Key.left, 0.4)]
        else:
            return []

    def start_level(self, stage=0, level=0, free_dungeon=False):
        inputs = [('s', 0.05, 0.8), ('s', 0.05, 1)]
        self.execute_inputs(inputs)

        get_screen_region = lambda geom: (geom[0] + 217, geom[1] + 125, 205, 62)
        screenshot = self.take_screenshot(get_screen_region)
        tess_text = pytesseract.image_to_string(screenshot, config="--psm 6")
        if len(tess_text.split('\n'))>1 and self.execute_inputs:
            first_test = fuzz.ratio(tess_text.split('\n')[0], 'To overlord dungeon') > 70
            second_test = fuzz.ratio(tess_text.split('\n')[1], 'To free dungeon') > 70
            if not first_test or not second_test:
                self.has_desynced = True
                return []
        else:
            print(tess_text)
            self.has_desynced = True
            return []
        
        if free_dungeon:
            inputs = [Key.down, 's', 's']
        else:
            inputs = ['s'] + self.menu_select(stage) +  self.menu_select(level, select=False) +['s']
        return inputs

    def menu_select(self, N, select=True):
        up_or_down = Key.up if N < 0 else Key.down
        inputs = [up_or_down]*abs(N)
        if select:
            inputs += ['s']
        return inputs
        
    def attack_food_dungeon_inputs(self):
        if char_type=='atk':
            inputs = ['s', (Key.down, 0.15), 'w', 's', (Key.up, 0.1), 's']
        if char_type=='tec':
            inputs = ['s', (Key.up, 0.2), 'w', 's', (Key.up, 0.1), 's']
        if char_type=='int':
            inputs = [Key.down, 's', 's', (Key.up, 0.55), 's']
        if char_type=='yosh':
            inputs = ['s', (Key.up, 0.45), 'w', 's', 's']
        return inputs

    def attack_castle_inputs(self, char_name):
        if char_name=='Yoshitsuna':
            inputs = ['s', 's', (Key.right, 0.5), 'w', 's', 's']
        if char_name=='First Sacrifice':
            inputs = ['s', 's', (Key.right, 0.5), 's']
        if char_name=='Second Sacrifice':
            inputs = ['s', 's', (Key.down, 0.2), (Key.right, 0.35), 's']
        if char_name=='Executioner':
            inputs = ['s', 's', (Key.down, 0.2), (Key.left, 0.2), 'w', 's', (Key.right, 0.2), 's']
        if char_name=='MoonSlash':
            inputs = ['s', 's', (Key.down, 0.3), (Key.right, 0.2), 'w', 's', 's']
        if char_name=='Slash':
            inputs = ['s', Key.down, 's', 's', (Key.down, 0.3), (Key.right, 0.7), ('s', 0.7, 0.5)]
        if char_name=='7sins':
            inputs = ['s', Key.down, 's', 's', 's']
        if char_name=='Thief':
            inputs = ['s', 's', (Key.right, 0.3), 'w', 's', (Key.down, 0.3), (Key.right, 0.3), 's']
        if char_name=='Lorna':
            inputs = ['s', 's', (Key.down, 0.32), 'w', 's', (Key.right, 0.2), 's']
        if char_name=='Huw':
            inputs = ['s', 's', (Key.down, 0.25), (Key.right, 0.2), 'w', 's', 's']
        if char_name=='MikeOCD':
            #inputs = ['s', 's', (Key.down, 0.1), (Key.right, 0.1), 'w', 's', (Key.right, 0.2), 's']
            inputs = ['s', 's', (Key.down, 0.3), (Key.right, 0.2), 'w', 's', (Key.right, 0.4), 's']
        if char_name=='Marcel':
            # inputs = ['s', 's', (Key.right, 0.12), 'w', 's', (Key.down, 0.25), (Key.right, 0.5), ('s', 0.1)]
            inputs = ['s', Key.down, 's', 's', (Key.right, 0.5), (Key.down, 0.2), 's']
        if char_name=='RX-66 Helldam':
            inputs = ['s', Key.down, 's', 's', (Key.down, 0.3), (Key.right, 0.6), ('s', 0.8)]
        if char_name=='Gracie':
            inputs = ['s', 's', (Key.down, 0.25), (Key.right, 0.2), 'w', 's', 's'] 
            #['s', 's', (Key.right, 0.4), (Key.down, 0.35), Key.right, 'w', 's', 's']
        return inputs
    
    def print_state_variables(self):
        print(f'Total item count: {self.total_item_count}')
        print(f'First food item index: {self.first_food_item_index}')
        print(f'First star item index: {self.first_star_item_index}')

if __name__=='__main__':
    main()