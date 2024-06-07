import time
import pyautogui
from pynput.keyboard import Key, Controller, Listener, KeyCode
from PIL import Image
import pygetwindow as gw

keyboard = Controller()

def get_inputs(chars_to_summon, heal_characters, heal_vehicles, attack_castle=True, has_desynced=False):
    inputs = [] # Starts inside the level

    invite_selected, chars_summoned = True, 1
    for i, char_dict in enumerate(chars_to_summon):
        not_penultimate_char = (i < len(chars_to_summon)-1)
        char_slot, char_name, participating, is_vehicle = unpack_char_dict(char_dict)
        inputs += summon_char(char_slot, participating, is_vehicle, invite_selected, chars_summoned)
        if participating:
            if attack_castle:
                inputs += attack_castle_inputs(char_name)
                chars_summoned+=1
                if char_name=='Slash':
                    invite_selected = False
            else:
                inputs += enter_castle
                invite_selected = False
        if not_penultimate_char:
            inputs += reselect_tome(char_name)
        else:
            inputs += finish_level(speed_up_time)

    inputs += heal(heal_characters, heal_vehicles, has_desynced)
    stage = 2 if heal_characters or heal_vehicles else 0
    inputs += start_level(stage,  3)
            
    return inputs

def unpack_char_dict(char_dict):
    char_slot = char_dict.get('char_slot', 0)
    char_name = char_dict.get('char_name')
    participating = char_dict.get('participating', True)
    is_vehicle = char_dict.get('is_vehicle', False)
    return char_slot, char_name, participating, is_vehicle

def summon_char(char_slot, participating=True, is_vehicle=False, invite_selected=True, chars_summoned=1):
    inputs = ['s', 's'] if invite_selected else ['s', Key.up, 's']
    if is_vehicle:
        inputs += [Key.right]
    inputs += menu_select(char_slot)
    if participating:
        inputs += [(Key.right, 0.47), ('s', 2.6)] + [Key.enter] * chars_summoned
    else:
        inputs += [(Key.left, 0.3), ('s', 2.6)]
    return inputs

def finish_level(time_to_finish_level): # time_to_finish_level = 1.3 if entering castle
    return ['w', 's', (Key.f4, 0.05, time_to_finish_level), 's', ('s', 0.5), (Key.f4, 0.05, 0.8)]

def heal(heal_characters, heal_vehicles, has_desynced):
    if heal_characters and heal_vehicles:
        return [(Key.left, 1), ('s', 1), ('s', 0.3), 'w', 'd', (Key.right, 1.5), 
         ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), 'w', 'd', 'd', (Key.left, 0.4)]
    elif heal_characters:
        if has_desynced:
            return [(Key.left, 1), ('s', 1), ('s', 0.3), ('w', 2), 'd', (Key.right, 0.38)]
        return [(Key.left, 1), ('s', 1), ('s', 0.3), 'w', 'd', (Key.right, 0.38)]
    elif heal_vehicles:
        return [(Key.right, 1), ('s', 1.3), ('s', 0.3), Key.down, ('s', 0.1), 'w', 'd', 'd', (Key.left, 0.4)]
    else:
        return []

def start_level(stage, level):
    inputs = [('s', 0.05, 1), ('s', 0.05, 1), 's']
    inputs += menu_select(stage) +  menu_select(level, select=False)
    return inputs

enter_castle = ['s', 's', (Key.right, 0.52), (Key.down, 0.1), 's', Key.down, ('s', 1.2)]
def reselect_tome(char_name):
    # if char_name=='Marcel':
    #     return [(Key.left, 0.3)] + [(Key.enter, 0.1)]*6
    return [(Key.left, 0.3), (Key.enter, 0.1)]

#===========================================================================================


def menu_select(N, select=True):
    up_or_down = Key.up if N < 0 else Key.down
    inputs = [up_or_down for n in range(abs(N))]
    if select: # select = False when checking for desyncs
        inputs += ['s']
    return inputs

def key_press(key, hold=0.05, wait=0.08):
    keyboard.press(key)
    time.sleep(hold)
    keyboard.release(key)
    time.sleep(wait)

def execute_inputs(inputs):
    for input in inputs:
        if isinstance(input, tuple):
            key_press(*input)
        else:
            key_press(input)

def on_press(key):
    global Execute_script
    if key == Key.f10:
        Execute_script = not Execute_script

def take_screenshot(region):
    window_title = [window for window in gw.getAllTitles() if 'NTSC | Limiter: Normal | GSdx OGL HW | 640x224' in window][0]
    try:
        window = gw.getWindowsWithTitle(window_title)[0]
        region = window.left+20, window.top+50, window.width//2, window.height//2
    except:
        print(f'Could not fetch {window_title}')
    screenshot = pyautogui.screenshot(region=region).convert('RGB')
    return screenshot, region

def images_match(img1, img2, threshold=1000):
    total_diff = 0
    x_range, y_range = img1.size
    for x in range(x_range):
        for y in range(y_range):
            rgb_val1 = img1.getpixel((x,y))
            rgb_val2 = img2.getpixel((x,y))
            for colour in range(3):
                total_diff += abs(rgb_val1[colour] - rgb_val2[colour])
    return total_diff < threshold

def anti_desync(count, screen_region):
    has_desynced = False
    screenshot, screen_region = take_screenshot(screen_region)
    if images_match(ref_image, screenshot):
        key_press('s', wait=2.5)
        key_press(Key.f1, wait=1)
        count+=1
        print(f'Number of cycles: {count}')
    else:
        print('Desync detected!')
        has_desynced = True
        key_press(Key.f3, wait=1.5)
    return count, screen_region, has_desynced


#===========================================================================================

def attack_castle_inputs(char_name):
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


chars_to_summon = [
    {'char_slot': 1, 'char_name': 'First Sacrifice'},
    {'char_slot': 1, 'char_name': 'Second Sacrifice'},
    {'char_slot': 0, 'char_name': 'Executioner'},
    # {'char_slot': -1}
    # {'char_slot': 5, 'char_name': 'MikeOCD'},
    # {'char_slot': -1, 'char_name': 'Slash'},
    # {'char_slot': 0, 'char_name': 'MoonSlash'},
    # {'char_slot': 3, 'char_name': 'Thief'},
    # {'char_slot': 0, 'char_name': 'Lorna'},
    # {'char_slot': 3, 'char_name': 'Huw'},
    # {'char_slot': 1, 'char_name': 'Marcel'},
    # {'char_slot': 0, 'char_na2e': 'RX-66 Helldam', 'is_vehicle': True},
]
speed_up_time = 1.2
character_healing_frequency = 1
vehicle_healing_frequency = 0
attack_castle = True

ref_image = Image.open('Reference images/Makai Kingdom.png').convert('RGB')
listener = Listener(on_press=on_press)
listener.start()
Execute_script, count, screen_region, has_desynced = False, 0, None, False
while True:
    if Execute_script:
        heal_characters = count % character_healing_frequency == 0 if character_healing_frequency > 0 else False
        heal_vehicles = count % vehicle_healing_frequency == 0 if vehicle_healing_frequency > 0 else False
        inputs = get_inputs(chars_to_summon, heal_characters, heal_vehicles, attack_castle, has_desynced)
        execute_inputs(inputs)
    else:
        count = 0

    if Execute_script:
        count, screen_region, has_desynced = anti_desync(count, screen_region)