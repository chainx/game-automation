import time
from pathlib import Path
from pynput.keyboard import Key

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game_automation import game_automation, keyboard

def main():
    digimon_world = Digimon_World()
    digimon_world.run_script(keys_to_hold=[Key.down, Key.right])

class Digimon_World(game_automation):
    def __init__(self):
        super(Digimon_World, self).__init__()

    def main(self):
        self.Mojyamon_arbitrage()

    def Mojyamon_arbitrage(self):
        # inputs = []
        # for N in range(99):
        #     inputs += [('z',0.4), ('z',0.3), ('z',0.6), Key.down] + ['z']*8 +[('z',0.1)]
        # self.execute_inputs(inputs)
        # self.execute_script = False
        self.execute_inputs(['z'])     

if __name__=='__main__':
    main()