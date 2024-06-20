import time
import datetime
import os
from pathlib import Path
from pynput.keyboard import Key
from PIL import Image
import pytesseract

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game_automation import game_automation
from image_to_text import find_items_to_sell, clean_image, is_not_black_image, extract_count, partition_screenshot

save_path = Path('Makai_Kingdom/Reference images')

# I use different key bindings on Windows and Linux due to conflicts with my key binds on Linux
linux_or_windows = 'windows' if os.name=='nt' else 'linux'
frame_limit_key = Key.f4 if linux_or_windows=='windows' else Key.end
win_name_filter = 'NTSC | Limiter: Normal | GSdx OGL HW | 640x224' if linux_or_windows=='windows' else 'Makai Kingdom - Chronicles of the Sacred Tome'
ref_image = Image.open(save_path / f'BabylonsMessenger_{linux_or_windows}.png').convert('RGB')

# On Linux run:
#    wmctrl -r "Makai Kingdom - Chronicles of the Sacred Tome" -e 0,0,0,640,480
# To ensure the window is the correct size for screenshots to match reference images

chars_to_summon = [
    # {'char_slot': 5, 'char_name': 'Marcel'},
    # {'char_slot': -1, 'char_name': 'Slash'},
    {'char_slot': 1, 'char_name': 'First Sacrifice'},
    {'char_slot': 1, 'char_name': 'Second Sacrifice'},
    {'char_slot': 0, 'char_name': 'Executioner'},
]
time_to_finish_level = 0.7
character_healing_frequency = 1
selling_frequency = 50
initial_item_count = 308
first_food_item_index = 163
first_star_item_index = 163
star_bonus = 419
vehicle_healing_frequency = 0
create_dungeon=False
attack_castle = True

def main():
    print(datetime.datetime.now())
    makai_kingdom = Makai_Kingdom()
    makai_kingdom.run_script()

    # makai_kingdom.count_mana()
    # count = makai_kingdom.count_total_items()
    # screenshot = Image.open(save_path/'debug_reincarnation.png')
    # count = extract_count(screenshot, debug=True)
    # print(count)

class Makai_Kingdom(game_automation):
    def __init__(self):
        super(Makai_Kingdom, self).__init__()
        self.chars_to_summon = chars_to_summon
        self.win_name_filter = win_name_filter
        self.initial_item_count = initial_item_count
        self.total_item_count = self.initial_item_count
        self.first_food_item_index = first_food_item_index
        self.first_star_item_index = first_star_item_index
        self.star_bonus = star_bonus

        self.enter_castle = ['s', 's', (Key.right, 0.52), (Key.down, 0.1), 's', Key.down, ('s', 1.2)]
        self.reselect_tome = [(Key.left, 0.3), (Key.enter, 0.1)]
        self.finish_level = ['w', 's', (frame_limit_key, 0.01, time_to_finish_level)] + [('s', 0.05)]*5 + [('s', 0.25), (frame_limit_key, 0.05, 0.8)]

    def main(self):
        self.BabylonsMessenger_main()
        # self.FoodDungeon_main()
        # self.reincarnate()
        # self.organise_inventory()

    def BabylonsMessenger_main(self):
        heal_characters = self.count % character_healing_frequency == 0 if character_healing_frequency > 0 else False
        heal_vehicles = self.count % vehicle_healing_frequency == 0 if vehicle_healing_frequency > 0 else False
        inputs = self.get_BabylonsMessenger_inputs(heal_characters, heal_vehicles)
        self.execute_inputs(inputs)

        if self.count % selling_frequency == 0 and self.execute_script:
            total_item_count = self.count_total_items(debug_label='initial_item_count')
            print(f'Total item count: {total_item_count}, previous item count: {self.initial_item_count}')
            if not total_item_count or total_item_count < self.initial_item_count: # This will only happen if there's an OCR error
                self.has_desynced = True
                return
            self.sell_items(total_item_count)
            self.initial_item_count = self.count_total_items(exit_menu=False, debug_label='final_item_count')
            print(f'Total items after sales: {self.initial_item_count}')
            mana_count = self.count_mana()
            if mana_count == 9999999:
                self.execute_inputs([(Key.f1, 0.5), Key.f2, 'w', 's', (Key.right, 0.2), 's', Key.up])
                self.organise_inventory()
                self.execute_inputs(['d', 'd', 'd', Key.f1])
                print(datetime.datetime.now())
                self.total_item_count = self.initial_item_count
                self.execute_script = False
                return
        
        inputs = self.heal(heal_characters, heal_vehicles)
        stage = 2 if heal_characters or heal_vehicles else 0
        inputs += self.start_level(stage,  3)
        self.execute_inputs(inputs)

        if self.execute_script:
            get_screen_region = lambda geom: (geom[0] + 20, geom[1] + 50, geom[2] // 2, geom[3] // 2)
            screenshot = self.take_screenshot(get_screen_region)
            self.has_desynced = not self.images_match(ref_image, screenshot)
            if not self.has_desynced:
                self.key_press('s', wait=2.5)
                self.key_press(Key.f1, wait=1)

    def FoodDungeon_main(self):
        self.beat_food_dungeon()
        self.prep_for_next_food_dungeon(create_dungeon)
        inputs = self.heal(heal_characters=True, heal_vehicles=False)
        inputs += [('s', 0.05, 1), ('s', 0.05, 1), Key.down, 's', ('s', 4)]
        self.execute_inputs(inputs)
    
    def beat_food_dungeon(self):
        inputs = [
            'r', 's', 's', Key.left, 's', (Key.left, 0.25), ('s', 2.6), # Summon academy
            's', 's', Key.left, 's', (Key.right, 0.4), ('s', 2.6), # Summon food stall
            (Key.left, 0.25), 's', 's', (Key.right, 0.3), (Key.up, 0.1), ('s', 1), # Exit academy
            (Key.right, 0.4), 's', 's', (Key.left, 0.35), 's', (Key.home, 1.7, .1), Key.enter, # Feed from food stall
            's', 's', Key.up, 's', (Key.down, 0.15), ('s', 2.6), (Key.down, 0.15), # Summon first chef
        ]
        for n in range(5): # Feed main char
            inputs += ['s', Key.down, Key.down, 's'] + [Key.down]*n + ['s', 's', (Key.up, 0.27), 's', (Key.home, 1.7, .1)]
        inputs += ['s', 's', (Key.up, 0.5), 's', (Key.down, 0.35), 's', 's', Key.up, 's', (Key.down, 0.15), ('s', 2.6), (Key.down, 0.15)]
        for n in range(3): # Feed main char
            inputs += ['s', Key.down, Key.down, 's'] + [Key.down]*n + ['s', 's', (Key.up, 0.27), 's', (Key.home, 1.7, .1)]
        inputs += [(Key.up, 0.25), 's', 's', (Key.down, 0.15), 'w', 's', (Key.up, 0.1), 's']
        inputs += self.finish_level
        self.execute_inputs(inputs)

        self.total_item_count -= 8

    def prep_for_next_food_dungeon(self, create_dungeon):
        total_item_count = self.count_total_items(position_in_menu=0, keep_arranging=True, debug_label='item_count')
        if total_item_count == self.total_item_count + 1:
            print('Item acquired in food dungeon')
            self.move_item_above_food_and_stars(total_item_count, keep_arranging=True)
            self.total_item_count += 1
            self.first_food_item_index += 1
            self.first_star_item_index += 1
        inputs = [
            Key.up, Key.up, ('s', 0.5), 's', ('s', 0.2), 'w', ('d', 0.2), ('d', 0.2), Key.up, 's', # Leave academy and navigate to char equip
            Key.up, 's', 'w', 's', Key.up, Key.up, 's', ('d', 0.2), ('d', 0.2), ('d', 0.5), 'd', (Key.up, 0.45), # Equip food and move to Zetta
            ('s', 0.8), Key.up, Key.up, Key.up, ('s', 0.3), ('s', 0.5), 's', ('s', 2.7), (Key.down, 0.45), # Wish for dungeon
        ]
        if create_dungeon:
            self.execute_inputs(inputs)
            inputs = ['w', ('s', 0.5), 's'] # Navigate to char equip
        else:
            inputs = ['d', Key.up, Key.up, ('s', 0.5), 's'] # Navigate to char equip

        inputs += ['s', 's', 's', 'd'] if create_dungeon else [] # Re-equip weapon if food dungeon created
        down_presses = 2 if create_dungeon else 1 # Requires academy almost full / full
        inputs += [Key.up, 'q'] + [Key.down]*down_presses + ['s', 's', Key.up, 's'] # Navigate to chef equipment
        inputs += [Key.down, 's', 's'] * 4 + ['d', Key.up, 's'] + ['s', 's', Key.down] * 3 # Equip food to chefs
        if create_dungeon: # Re-enter academy
            inputs += ['d', 'd', Key.down, 's', ('s', 0.2), 's', 's', ('d', 0.2), ('d', 0.2), ('d', 0.5), 'd']
        else:
            inputs += ['d', 'd', ('d', 0.5), 'd']
        self.execute_inputs(inputs)

    def move_item_above_food_and_stars(self, total_item_count, keep_arranging=False):
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
        inputs += ['s', 'd', 'd', 'd'] if not keep_arranging else ['s', 'd']
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
        if not self.has_desynced:
            inputs = [('s', 0.8), ('s', 0.3), Key.right]
            for n in range(self.first_star_item_index//7):
                inputs += [('r', 0.02, 0.02)]
            for n in range(self.first_star_item_index%7-1):
                inputs += [(Key.down, 0.02, 0.02)]
            inputs += ['s', (Key.right, 0.11), (Key.down, 0.48), ('s', 1.9), (Key.down, 1.1), ('s', 0.8), ('s', 0.3)]
            self.execute_inputs(inputs)

        # Check star bonus
        get_screen_region = lambda geom: (geom[0]+geom[1]//2-5, geom[1]+geom[3]//3+35, geom[2]//10 - 30, geom[3]//12-10)
        star_bonus = self.extract_count(get_screen_region, debug_label='reincarnation')
        if star_bonus < self.star_bonus or star_bonus > self.star_bonus + 4:
            self.has_desynced = True
            return
        else:
            self.first_food_item_index -= 1
            print(f'Current star bonus is: {star_bonus}, first food item is at index: {self.first_food_item_index}')
            self.star_bonus = star_bonus
            # self.key_press(Key.f1, 0.01, 0.2)
        if star_bonus >= 500:
            self.key_press(Key.f1)
            self.execute_script = False
            print(datetime.datetime.now())
            return

        # Create and sacrifice character
        inputs = [
            ('s', 0.5), 's', Key.up, 's', Key.up, 's', ('s', 4.8), # Create now character
            (Key.left, 0.17), (Key.up, 0.77), ('s', 0.8), Key.up, Key.up, Key.up, ('s', 0.3), # Move back to Zetta and make a wish
            (Key.right, 0.1), (Key.down, 0.5), ('s', 0.5), 's', ('s', 0.9), # Navigate to sacrifice choice
            's', (frame_limit_key, 0.1, 1), (frame_limit_key, 0.1, 0.7), # Sacrifice character
            ('s', 0.8), Key.down, Key.down, Key.down, ('s', 0.3), Key.left, Key.up, 's', Key.down, ('s', 2), ('d', 0.3) # Delete new building
        ]
        self.execute_inputs(inputs)
        self.has_desynced = False

    def extract_count(self, get_screen_region, char_width=10, debug_label='', debug=False):
        screenshot = self.take_screenshot(get_screen_region)
        screenshot, _ = clean_image(screenshot)
        screenshot.save(save_path/f'debug_{debug_label}.png')
        try:
            count = extract_count(screenshot, char_width, debug)
            return count
        except:
            self.has_desynced = True
            return None

    def count_mana(self):
        self.execute_inputs([Key.up, 's', ('s', 0.2)])
        get_screen_region = lambda geom: (geom[0]+300, geom[1]+geom[3]//8 + 10, geom[2]//8 - 10, geom[3]//20 - 7)
        mana_count = self.extract_count(get_screen_region, debug_label='mana')
        self.execute_inputs([('d', 0.1), 'd', Key.down, 'd'])
        print(f'Total mana is: {mana_count}')
        return mana_count
    
    def count_total_items(self, position_in_menu=2, exit_menu=True, keep_arranging=False, char_width=10, debug_label=''):
        menu_inputs = [Key.down if position_in_menu < 2 else Key.up]*abs(position_in_menu-2)
        self.execute_inputs(['w'] + menu_inputs + ['s', (Key.right, 0.2)])
        get_screen_region = lambda geom: (geom[0]+geom[2]//3 + 32, geom[1]+geom[3]//10 + 10, geom[2] // 15, geom[3] // 28)
        total_item_count = self.extract_count(get_screen_region, char_width, debug_label)
        if not keep_arranging:
            inputs = ['d', 'd'] if exit_menu else ['d']
            self.execute_inputs(inputs)
        return total_item_count

    def get_BabylonsMessenger_inputs(self, heal_characters, heal_vehicles):
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
                    inputs += self.enter_castle
                    invite_selected = False
            if not_penultimate_char:
                inputs += self.reselect_tome
            else:
                inputs += self.finish_level
                
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
            inputs += [(Key.right, 0.47), ('s', 2.6)] + [Key.enter] * chars_summoned
        else:
            inputs += [(Key.left, 0.3), ('s', 2.6)]
        return inputs

    def heal(self, heal_characters, heal_vehicles):
        if heal_characters and heal_vehicles:
            return [(Key.left, 1), ('s', 1), ('s', 0.3), 'w', 'd', (Key.right, 1.5), 
            ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), 'w', 'd', 'd', (Key.left, 0.4)]
        elif heal_characters:
            if self.has_desynced:
                return [(Key.left, 0.5), ('s', 1), ('s', 0.3), ('w', 2), 'd', (Key.right, 0.38)]
            return [(Key.left, 0.5), ('s', 1), ('s', 0.3), 'w', 'd', (Key.right, 0.38)]
        elif heal_vehicles:
            return [(Key.right, 1), ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), 'w', 'd', 'd', (Key.left, 0.4)]
        else:
            return []

    def start_level(self, stage, level):
        inputs = [('s', 0.05, 0.8), ('s', 0.05, 0.8), 's']
        inputs += self.menu_select(stage) +  self.menu_select(level, select=False)
        return inputs

    def menu_select(self, N, select=True):
        up_or_down = Key.up if N < 0 else Key.down
        inputs = [up_or_down]*abs(N)
        if select:
            inputs += ['s']
        return inputs

    def attack_castle_inputs(self, char_name):
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
            inputs = ['s', 's', (Key.down, 0.35), 'w', 's', (Key.right, 0.6), 's']
        if char_name=='Marcel':
            inputs = ['s', 's', (Key.right, 0.12), 'w', 's', (Key.down, 0.25), (Key.right, 0.5), ('s', 0.1)]
        if char_name=='RX-66 Helldam':
            inputs = ['s', Key.down, 's', 's', (Key.down, 0.3), (Key.right, 0.6), ('s', 0.8)]
        return inputs
    
    def print_state_variables(self):
        print(f'{self.total_item_count}')
        print(f'{self.first_food_item_index}')
        print(f'{self.first_star_item_index}')

if __name__=='__main__':
    main()