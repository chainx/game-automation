import time
from pathlib import Path
from pynput.keyboard import Key

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from game_automation import game_automation

def main():
    digimon_world = Digimon_World()
    digimon_world.run_script()

class Digimon_World(game_automation):
    def __init__(self):
        pass

    def main(self):
        self.Mojyamon_arbitrage()

    def Mojyamon_arbitrage(self):
        inputs = ['z', 'z', 'z']
        # for N in range(99):
        #     inputs = ['s', Key.up, 's']
        # inputs += ['s', 'd']
        self.execute_inputs(inputs)
        self.execute_script = False

if __name__=='__main__':
    main()