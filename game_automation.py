import time
from pynput.keyboard import Key, Controller, Listener
from ewmh import EWMH
import pyautogui
from PIL import Image

ewmh = EWMH()
keyboard = Controller()

class game_automation:
    def __init__(self):
        self.execute_script = False
        self.has_desynced = False
        self.count = 0 # Counts number of cycles executed

    def main(self): 
        pass # Overwritten by parent class

    def print_state_variables(self):
        pass # Overwritten by parent class

    def on_press(self, key):
        if key == Key.f10:
            self.execute_script = not self.execute_script

    def run_script(self):
        listener = Listener(on_press=self.on_press)
        listener.start()
        while True:
            if self.execute_script:
                self.main()
                if self.has_desynced:
                    print('Desync detected!')
                    self.has_desynced = True
                    self.key_press(Key.f3, wait=1.5)
                else:
                    self.count += 1
                    if self.count%5 == 0:
                        print(f'Number of cycles: {self.count}')
            elif self.count>0:
                self.print_state_variables()
                self.count = 0

    # ================   AUTOMATION OF INPUTS   ==================

    def key_press(self, key, hold=0.05, wait=0.08):
        keyboard.press(key)
        time.sleep(hold)
        keyboard.release(key)
        time.sleep(wait)

    def execute_inputs(self, inputs):
        for input in inputs:
            if not self.execute_script:
                print('Execution aborted!')
                return
            if isinstance(input, tuple):
                self.key_press(*input)
            else:
                self.key_press(input)
    
    # ================   ANTI-DESYNC FUNCTIONALITY   ==================

    def get_window_geometry(self, window):
        geom = window.get_geometry()
        root = window.query_tree().root
        coords = window.translate_coords(root, 0, 0)

        return (-coords.x, -coords.y, geom.width, geom.height)

    def take_screenshot(self, get_screen_region):
        window = [win for win in ewmh.getClientList() if self.win_name_filter in win.get_wm_name()]
        if window:
            window = window[0]
        else:
            print('No matching window found')
            return None, None

        geom = self.get_window_geometry(window)
        screen_region = get_screen_region(geom)

        return pyautogui.screenshot(region=screen_region).convert('RGB')

    def images_match(self, screenshot, ref_img, threshold=1000):
        width, height = ref_img.size
        screenshot = screenshot.resize((width, height), Image.Resampling.LANCZOS)

        total_diff = 0
        for x in range(width):
            for y in range(height):
                rgb_val1 = screenshot.getpixel((x, y))
                rgb_val2 = ref_img.getpixel((x, y))
                for colour in range(3):
                    total_diff += abs(rgb_val1[colour] - rgb_val2[colour])

        return total_diff < threshold
