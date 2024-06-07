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

    def on_press(self, key):
        if key == Key.f10:
            self.execute_script = not self.execute_script

    def run_script(self):
        listener = Listener(on_press=self.on_press)
        listener.start()
        while True:
            self.main()

    # ================      ==================

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

    # ================   GENERIC INPUTS   ==================

    def menu_select(self, N, select=True):
        up_or_down = Key.up if N < 0 else Key.down
        inputs = [up_or_down for n in range(abs(N))]
        if select:
            inputs += ['s']
        return inputs
    
    # ================   ANTI-DESYNC FUNCTIONALITY   ==================

    def get_window_geometry(self, window):
        geom = window.get_geometry()
        root = window.query_tree().root
        coords = window.translate_coords(root, 0, 0)

        geom_values = {
            "x": -coords.x,
            "y": -coords.y,
            "width": geom.width,
            "height": geom.height,
        }
        
        return geom_values

    def take_screenshot(self, win_name_filter, region=None):
        window = [win for win in ewmh.getClientList() if win.get_wm_name() and win_name_filter in win.get_wm_name()]
        if window:
            window = window[0]
        else:
            print('No matching window found')
            return None, None

        geom = self.get_window_geometry(window)
        region = (geom['x'] + 20, geom['y'] + 50, geom['width'] // 2, geom['height'] // 2)

        screenshot = pyautogui.screenshot(region=region).convert('RGB')
        return screenshot, region

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

    def anti_desync(self, win_name_filter, screen_region, ref_image):
        has_desynced = False
        screenshot, screen_region = self.take_screenshot(win_name_filter, screen_region)
        if self.images_match(ref_image, screenshot):
            self.key_press('s', wait=2.5)
            self.key_press(Key.f1, wait=1)
            self.count+=1
            print(f'Number of cycles: {self.count}')
        else:
            print('Desync detected!')
            self.has_desynced = True
            self.key_press(Key.f3, wait=1.5)
        return screen_region