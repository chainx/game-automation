import os
from pathlib import Path
from pynput.keyboard import Key
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game_automation import game_automation
from image_to_text import find_items_to_sell

save_path = Path('Makai_Kingdom/Reference images')

# I use different key bindings on Windows and Linux due to conflicts with my key binds on Linux
linux_or_windows = 'windows' if os.name=='nt' else 'linux'
frame_limit_key = Key.f4 if linux_or_windows=='windows' else Key.end
win_name_filter = 'NTSC | Limiter: Normal | GSdx OGL HW | 640x224' if linux_or_windows=='windows' else 'Makai Kingdom - Chronicles of the Sacred Tome'
ref_image = Image.open(save_path / f'BabylonsMessenger_{linux_or_windows}.png').convert('RGB')

chars_to_summon = [
    {'char_slot': 1, 'char_name': 'First Sacrifice'},
    {'char_slot': 1, 'char_name': 'Second Sacrifice'},
    {'char_slot': 0, 'char_name': 'Executioner'},
]
time_to_finish_level = 1.5
character_healing_frequency = 1
vehicle_healing_frequency = 0
attack_castle = True

def main():
    makai_kingdom = Makai_Kingdom(chars_to_summon)
    makai_kingdom.run_script()
    
    # screenshot = Image.open(save_path / 'test.png').convert('RGB')

class Makai_Kingdom(game_automation):
    def __init__(self, chars_to_summon):
        super(Makai_Kingdom, self).__init__()
        self.chars_to_summon = chars_to_summon
        self.win_name_filter = win_name_filter

        self.enter_castle = ['s', 's', (Key.right, 0.52), (Key.down, 0.1), 's', Key.down, ('s', 1.2)]
        self.reselect_tome = [(Key.left, 0.3), (Key.enter, 0.1)]
        self.finish_level = ['w', 's', (frame_limit_key, 0.05, time_to_finish_level), 's', ('s', 0.5), (frame_limit_key, 0.05, 0.8)]

    def main(self):
        if self.execute_script:
            get_screen_region = lambda geom: (geom[0] + 20, geom[1] + 90, geom[2] // 3 - 30, geom[3] // 2 - 10)
            screenshot = self.take_screenshot(get_screen_region)

            items_to_sell = find_items_to_sell(screenshot)
            for item in items_to_sell:
                print(item)
            print()
            self.execute_script = False

    def alt_main(self):
        if self.execute_script:
            heal_characters = self.count % character_healing_frequency == 0 if character_healing_frequency > 0 else False
            heal_vehicles = self.count % vehicle_healing_frequency == 0 if vehicle_healing_frequency > 0 else False
            inputs = self.get_BabylonsMessenger_inputs(heal_characters, heal_vehicles)
            self.execute_inputs(inputs)
        else:
            self.count = 0

        if self.execute_script:
            get_screen_region = lambda geom: (geom[0] + 20, geom[1] + 50, geom[2] // 2, geom[3] // 2)
            self.screen_region = self.anti_desync(ref_image, get_screen_region)

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

        inputs += self.heal(heal_characters, heal_vehicles)
        stage = 2 if heal_characters or heal_vehicles else 0
        inputs += self.start_level(stage,  3)
                
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
                return [(Key.left, 1), ('s', 1), ('s', 0.3), ('w', 2), 'd', (Key.right, 0.38)]
            return [(Key.left, 1), ('s', 1), ('s', 0.3), 'w', 'd', (Key.right, 0.38)]
        elif heal_vehicles:
            return [(Key.right, 1), ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), 'w', 'd', 'd', (Key.left, 0.4)]
        else:
            return []

    def start_level(self, stage, level):
        inputs = [('s', 0.05, 1), ('s', 0.05, 1), 's']
        inputs += self.menu_select(stage) +  self.menu_select(level, select=False)
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
            inputs = ['s', Key.down, 's', 's', (Key.down, 0.3), (Key.right, 0.7), ('s', 0.7)]
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
            inputs = ['s', 's', (Key.right, 0.12), 'w', 's', (Key.down, 0.25), (Key.right, 0.5), ('s', 0.4)]
        if char_name=='RX-66 Helldam':
            inputs = ['s', Key.down, 's', 's', (Key.down, 0.3), (Key.right, 0.6), ('s', 0.8)]
        return inputs

if __name__=='__main__':
    main()