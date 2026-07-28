# Game Automation

A collection of Python scripts for automating repetitive tasks in emulated games.
The project combines timed keyboard input with game-state checks from screenshots,
OCR, and (for Digimon World) emulator memory.

This is a personal automation toolkit, not a general-purpose bot framework. The
current routines assume the author's emulator settings, controls, saves, window
geometry, and game state. Review and adapt a routine before running it.

## Supported games

### Digimon World (PS1)

`Digimon_World/Digimon_World.py` contains routines for:

- automated fishing;
- item and money farming;
- movement between known map locations;
- care-taking and save/reload loops;
- RNG-sensitive routes with desync detection.

It reads the running emulator's memory to track inventory, location, partner
stats, fishing state, and other values. The current memory scanner is
Windows-specific and targets a process named `psxfin.exe`.

`Digimon_World/evolution.py` also contains experimental evolution-path and
requirement helpers backed by the included Excel data sheet.

### Makai Kingdom

`Makai_Kingdom/Makai_Kingdom.py` contains routines for:

- level and mana farming;
- weapon mastery and reincarnation;
- food dungeons;
- inventory organisation and selling;
- healing and character summoning.

Some routines use screenshots and Tesseract OCR to check menus, count values,
and decide which inventory items to keep.

## How it works

[`game_automation.py`](game_automation.py) provides the shared runner:

- `F10` toggles automation on and off;
- input sequences may contain individual keys or `(key, hold, wait)` tuples;
- a routine can flag a desync and restore its previous Python state;
- game-specific code may validate progress using memory reads, screenshots, or
  OCR before continuing.

The game scripts subclass `game_automation` and select the active routine in
their class-level `main()` method.

## Running

Run commands from the repository root because several data and image paths are
relative to it.

For Digimon World, start the configured emulator and game first, then run:

```bash
python Digimon_World/Digimon_World.py
```

For Makai Kingdom:

```bash
python Makai_Kingdom/Makai_Kingdom.py
```

The runner initially waits without sending input. Focus the emulator, place the
game at the routine's expected starting point, and press `F10` to begin. Press
`F10` again to stop.


## Adding a routine

Add a method to the relevant game class, compose its inputs with
`execute_inputs()`, and call it from that class's `main()` method. Use
`self.execute_script` to allow clean cancellation and set
`self.has_desynced = True` when a state check fails.

For example:

```python
def my_routine(self):
    inputs = [
        "s",
        Key.down,
        ("s", 0.05, 0.5),
    ]
    self.execute_inputs(inputs)
```

Start with conservative timing. Emulator speed, frame limiting, focus, display
scaling, and input mappings can all affect a sequence.

## Project status

The repository is under active personal development. Automated tests, stable
configuration, and a supported public API are not currently provided. Expect
to customize the scripts for your own environment.

