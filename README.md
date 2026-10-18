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

The game scripts subclass `game_automation`. Digimon World opens a GUI to select
fishing, farming, tournament grinding, or curling and enter the selected routine's
arguments. Stop a routine before selecting another. Makai Kingdom continues to
use its class-level `main()` method.

## Running

Run commands from the repository root because several data and image paths are
relative to it.

Install dependencies into your Python installation with:

```powershell
python -m pip install -r requirements.txt
```

Use `python -m pip` with the same interpreter that runs the scripts; a standalone
`pip` command may belong to another Python installation.

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
`execute_inputs()`, and register bound methods with the GUI runner:

```python
game.run_automations([game.fishing, game.farming, game.tournament_grind, game.curling])
```

`gui.py` builds fields from each function's signature and calls it with `**kwargs`.
It displays the selected function's docstring as its description, or a fallback
message if none is provided. Add a docstring to any registered automation to
describe its purpose and starting requirements without modifying the GUI.
Wrap description text in `**double asterisks**` to display it in bold.

To expose game-wide instance settings, pass a dictionary of defaults to the base
class constructor. It initializes the corresponding `self` attributes and the
shared GUI builds a **Global settings** tab automatically:

```python
class MyGame(game_automation):
    def __init__(self):
        super().__init__(state_defaults={
            "food_preference": "Sirloin",
            "backup_food_preference": "Chain melon",
            "verbose": False,
        })
```

Do not reassign those defaults later in the constructor. Use the attributes as
normal inside routines, such as `self.food_preference`. Register only settings
that users should edit, not live memory values, process handles, or runner control
flags. Names must be public Python identifiers and must not collide with existing
base attributes or methods. Calling `super().__init__()` without a dictionary
continues to work and adds no settings tab.

Settings use the default's type for validation; booleans get a dropdown, while
strings, numbers and containers use text fields. All inputs are validated before
any settings are applied. Settings apply at the start of each run, stay selected
when switching automations, and cannot be edited during a run. **Restore defaults**
resets the form; blank fields also use their declared defaults. Changes last for
the GUI session only and are not saved to disk. Routine arguments remain separate
from global settings, even if they share a name.

For reusable dropdowns, pass an optional `state_choices` dictionary alongside
`state_defaults`:

```python
super().__init__(
    state_defaults={"food_preference": "Sirloin"},
    state_choices={"food_preference": ["Meat", "Giant Meat", "Sirloin", "Chain melon"]},
)
```

Each choices list must be non-empty and include its setting's default. The shared
GUI displays a dropdown and validates the selected value. Digimon World's two
food preferences use food names from its item spreadsheet; the GUI contains no
game-specific food lists.

Required arguments must be entered; blank optional fields use their defaults.
Enter text directly (for example, `Black trout`), numbers as `10` or `0.5`,
booleans as `True`/`False`, and containers as Python literals. A function accepting
`**kwargs` gets an additional dictionary field. Positional-only parameters and
`*args` are unsupported. Tkinter must be installed with Python.

The GUI runs routines in a background thread. F10 stops execution cooperatively;
switching routines or closing waits for the current routine to return. Use
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

Tasks can buffer failure-only diagnostics using the shared base class:

```python
self.start_task_diagnostics("My task", logging_fields={
    "bits": ("bits",),
    "bait": ("inventory", "Meat"),
}, cycle=self.count + 1)
self.record_task_state("before inputs")
```

Paths traverse instance attributes and dictionary keys. Snapshots copy cached
values. `logging_fields` is optional and extends or overrides the class's
`default_logging_fields`. The base class includes execution and desync flags;
Digimon World adds location, destination, bits, and scolding state by default.
Each game can extend the defaults without changing the shared logger.
Snapshots capture cached
values without reading emulator memory; missing values appear as `None`. The task
executor calls `_finish_task(reason)` after the task and transition check, printing
snapshots only on failure and discarding them on success. Other executors can use
the same lifecycle. `on_task_finished(callback)` remains available for task-specific
completion behavior alongside diagnostics.

Digimon World tasks can call `expect_transition(destination_id,
allow_already_arrived=True)` when reaching the destination during their input or
settling delay is acceptable. Auto Pilot uses this with its one-second partner
settling delay. The setting resets on task completion; other tasks retain strict
transition timing. If arrival has not happened yet, the existing transition wait
still applies.

## Project status

The repository is under active personal development. Automated tests, stable
configuration, and a supported public API are not currently provided. Expect
to customize the scripts for your own environment.

