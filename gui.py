"""Tkinter selector used by game_automation.run_automations()."""

import ast
import copy
import inspect
import queue
import re
import threading
import tkinter as tk
from tkinter import font as tkfont, ttk
from typing import Literal, get_args, get_origin


def parse_arguments(function, values):
    """Convert form text to keyword arguments without evaluating Python code."""
    return parse_values(inspect.signature(function), values)


def parse_values(signature, values):
    """Shared validation for automation arguments and editable state."""
    kwargs = {}
    for name, parameter in signature.parameters.items():
        if parameter.kind in (parameter.POSITIONAL_ONLY, parameter.VAR_POSITIONAL):
            raise ValueError(f"{name}: positional-only arguments and *args are unsupported")
        raw = values.get(name, "")
        if parameter.kind == parameter.VAR_KEYWORD:
            extra = ast.literal_eval(raw or "{}")
            if not isinstance(extra, dict) or not all(isinstance(k, str) for k in extra):
                raise ValueError(f"{name}: enter a dictionary with string keys")
            if set(extra) & (set(signature.parameters) - {name}):
                raise ValueError(f"{name}: enter named arguments in their own fields")
            kwargs.update(extra)
            continue
        if not raw.strip():
            if parameter.default is not inspect.Parameter.empty:
                continue
            raise ValueError(f"{name} is required (use '' for an empty string)")
        expected = parameter.annotation
        if expected is inspect.Parameter.empty and parameter.default is not inspect.Parameter.empty:
            expected = type(parameter.default)
        expected = {"str": str, "int": int, "float": float, "bool": bool}.get(expected, expected)
        try:
            value = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            value = raw
        if get_origin(expected) is Literal:
            choices = get_args(expected)
            matches = [choice for choice in choices if str(choice) == raw]
            if not matches:
                raise ValueError(f"{name}: choose one of {', '.join(map(str, choices))}")
            value = matches[0]
        elif expected is str:
            value = value if isinstance(value, str) else raw
        elif expected in (int, float, bool, list, tuple, dict):
            if expected is float and type(value) is int:
                value = float(value)
            if type(value) is not expected:
                raise ValueError(f"{name}: expected {expected.__name__}")
        kwargs[name] = value
    signature.bind(**kwargs)
    return kwargs


def format_field_value(value):
    """Show strings as plain text and retain literal syntax for other values."""
    return value if isinstance(value, str) else repr(value)


def make_field(parent, parameter, value=None):
    """Create a typed input independently of any game or automation."""
    choices = get_args(parameter.annotation) if get_origin(parameter.annotation) is Literal else ()
    if not choices and (parameter.annotation is bool or type(parameter.default) is bool):
        choices = (True, False)
    default = "{}" if parameter.kind == parameter.VAR_KEYWORD else ""
    if parameter.default is not inspect.Parameter.empty:
        default = str(parameter.default) if choices else format_field_value(parameter.default)
    elif choices:
        default = str(choices[0])
    text = default if value is None else value
    if choices:
        field = ttk.Combobox(parent, state="readonly", values=list(map(str, choices)))
        field.set(text)
    else:
        field = ttk.Entry(parent)
        field.insert(0, text)
    field.pack(fill="x", pady=(2, 8))
    return field


class AutomationGUI:
    def __init__(self, runner, functions):
        self.functions = list(functions)
        if not self.functions or not all(callable(f) for f in self.functions):
            raise ValueError("Provide a non-empty list of automation functions")
        self.runner = runner
        self.worker = None
        self.stop_event = threading.Event()
        self.events = queue.Queue()
        self.closing = False
        self.hotkey_down = False
        self.saved_values = {}
        self.selected = None
        self.root = tk.Tk()
        self.root.title("Game automation")
        self.root.minsize(460, 240)
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Automation").pack(anchor="w")
        self.selector = ttk.Combobox(
            frame, state="readonly",
            values=[f.__name__.replace("_", " ").title() for f in self.functions],
        )
        self.selector.pack(fill="x", pady=(4, 12))
        self.selector.current(0)
        self.selector.bind("<<ComboboxSelected>>", self.show_arguments)
        self.description = tk.StringVar()
        description_frame = ttk.Frame(frame)
        description_frame.pack(fill="x", pady=(0, 12))
        self.description_view = tk.Text(description_frame, height=7, width=52, wrap="word",
                                        borderwidth=0, highlightthickness=0,
                                        font="TkDefaultFont", state="disabled",
                                        takefocus=False)
        self.description_view.pack(side="left", fill="x", expand=True)
        description_scroll = ttk.Scrollbar(description_frame, command=self.description_view.yview)
        description_scroll.pack(side="right", fill="y")
        self.description_view.configure(yscrollcommand=description_scroll.set)
        self.description_bold_font = tkfont.nametofont("TkDefaultFont").copy()
        self.description_bold_font.configure(weight="bold")
        self.description_view.tag_configure("bold", font=self.description_bold_font)
        tabs = ttk.Notebook(frame)
        tabs.pack(fill="both", expand=True)
        self.form = ttk.Frame(tabs, padding=8)
        tabs.add(self.form, text="Automation arguments")
        self.state_fields = {}
        self.state_signature = inspect.Signature([
            inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=value,
                              annotation=Literal[tuple(runner.state_choices[name])]
                              if name in getattr(runner, "state_choices", {}) else inspect.Parameter.empty)
            for name, value in getattr(runner, "state_defaults", {}).items()
        ])
        if self.state_signature.parameters:
            settings = ttk.Frame(tabs, padding=8)
            tabs.add(settings, text="Global settings")
            ttk.Label(settings, text="Applied to every automation when you start a run.",
                      wraplength=420).pack(anchor="w", pady=(0, 8))
            for name, parameter in self.state_signature.parameters.items():
                ttk.Label(settings, text=name.replace("_", " ").capitalize()).pack(anchor="w")
                self.state_fields[name] = make_field(settings, parameter, format_field_value(getattr(runner, name)))
            self.reset_state_button = ttk.Button(settings, text="Restore defaults", command=self.reset_state_fields)
            self.reset_state_button.pack(anchor="e")
        ttk.Label(frame, text="Use Python values for numbers, True/False, lists and dictionaries.\n"
                  "Text can be entered without quotes. Blank fields use defaults.",
                  wraplength=440).pack(anchor="w", pady=12)
        self.status = tk.StringVar(value="Stopped — focus the game and press F10 to start.")
        ttk.Label(frame, textvariable=self.status, wraplength=440).pack(anchor="w")
        self.error_message = tk.StringVar()
        error_frame = ttk.LabelFrame(frame, text="Error / stop reason", padding=8)
        error_frame.pack(fill="x", pady=(12, 0))
        ttk.Label(error_frame, textvariable=self.error_message, foreground="#b91c1c",
                  wraplength=420, justify="left").pack(fill="x")
        self.button = ttk.Button(frame, text="Start (F10)", command=self.toggle)
        self.button.pack(anchor="e", pady=(12, 0))
        self.show_arguments()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.listener = None

    def show_arguments(self, event=None):
        if self.selected is not None:
            self.saved_values[self.selected] = {k: v.get() for k, v in self.fields.items()}
        self.selected = self.selector.current()
        self.description.set(inspect.getdoc(self.functions[self.selected]) or "No description available.")
        self.description_view.configure(state="normal")
        self.description_view.delete("1.0", tk.END)
        for index, part in enumerate(re.split(r"\*\*(.*?)\*\*", self.description.get(), flags=re.DOTALL)):
            self.description_view.insert(tk.END, part, ("bold",) if index % 2 else ())
        self.description_view.configure(state="disabled")
        for widget in self.form.winfo_children():
            widget.destroy()
        self.fields = {}
        for name, parameter in inspect.signature(self.functions[self.selected]).parameters.items():
            label = name
            if parameter.default is inspect.Parameter.empty and parameter.kind != parameter.VAR_KEYWORD:
                label += " (required)"
            ttk.Label(self.form, text=label).pack(anchor="w")
            self.fields[name] = make_field(self.form, parameter, self.saved_values.get(self.selected, {}).get(name))
        if not self.fields:
            ttk.Label(self.form, text="This automation has no arguments.").pack(anchor="w")

    def reset_state_fields(self):
        if self.worker is not None:
            return
        for name, field in self.state_fields.items():
            value = format_field_value(self.state_signature.parameters[name].default)
            if isinstance(field, ttk.Combobox):
                field.set(value)
            else:
                field.delete(0, tk.END)
                field.insert(0, value)

    def set_fields_running(self, running):
        for field in list(self.fields.values()) + list(self.state_fields.values()):
            field.configure(state="disabled" if running else
                            "readonly" if isinstance(field, ttk.Combobox) else "normal")
        if self.state_fields:
            self.reset_state_button.configure(state="disabled" if running else "normal")

    def toggle(self):
        if self.closing:
            return
        if self.worker is not None:
            self.stop_event.set()
            self.runner.execute_script = False
            self.status.set("Stopping — waiting for the current routine to return…")
            return
        function = self.functions[self.selected]
        try:
            kwargs = parse_arguments(function, {k: v.get() for k, v in self.fields.items()})
            state = parse_values(self.state_signature, {k: v.get() for k, v in self.state_fields.items()})
            # Include defaults for blank fields; validate everything before changing state.
            bound_state = self.state_signature.bind(**state)
            bound_state.apply_defaults()
        except (ValueError, TypeError, SyntaxError) as error:
            self.error_message.set(f"Invalid input: {error}")
            return
        for name, value in bound_state.arguments.items():
            setattr(self.runner, name, copy.deepcopy(value))
        self.error_message.set("")
        self.stop_event.clear()
        self.runner.stop_reason = ""
        self.runner.count = 0
        self.runner.has_desynced = False
        self.runner.has_previously_desynced = False
        self.runner.execute_script = True
        self.selector.configure(state="disabled")
        self.set_fields_running(True)
        self.status.set(f"Running {function.__name__} — F10 to stop.")
        self.button.configure(text="Stop (F10)")
        self.worker = threading.Thread(target=self.execute, args=(function, kwargs), daemon=True)
        self.worker.start()

    def execute(self, function, kwargs):
        # End this worker when a routine switches itself off as well as on F10.
        def cycle(**arguments):
            function(**arguments)
            if not self.runner.execute_script:
                self.stop_event.set()
        try:
            self.runner.run_script(automation=cycle, kwargs=kwargs,
                                   stop_event=self.stop_event, listen=False)
        except Exception as error:
            self.events.put(("error", f"{type(error).__name__}: {error}"))

    def on_press(self, key):
        if key == self.runner.execution_key and not self.hotkey_down:
            self.hotkey_down = True
            # Stop immediately, even when Tk is busy; starting needs form validation.
            if self.runner.execute_script:
                self.stop_event.set()
                self.runner.execute_script = False
            self.events.put(("toggle", None))

    def on_release(self, key):
        if key == self.runner.execution_key:
            self.hotkey_down = False

    def poll(self):
        while not self.events.empty():
            event, value = self.events.get_nowait()
            if event == "toggle":
                self.toggle()
            elif not self.closing:
                self.error_message.set(f"Automation failed: {value}")
        if self.worker is not None and not self.worker.is_alive():
            self.worker.join()
            self.worker = None
            self.selector.configure(state="readonly")
            self.set_fields_running(False)
            self.button.configure(text="Start (F10)")
            self.status.set("Stopped — choose an automation, then focus the game and press F10.")
            if self.runner.stop_reason:
                self.error_message.set(self.runner.stop_reason)
        if self.closing and self.worker is None:
            self.root.destroy()
            return
        self.root.after(50, self.poll)

    def close(self):
        self.closing = True
        self.stop_event.set()
        self.runner.execute_script = False
        if self.listener:
            self.listener.stop()
        self.status.set("Closing — waiting for the current routine to return…")
        self.button.configure(state="disabled")

    def run(self):
        from pynput.keyboard import Listener
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        self.root.after(50, self.poll)
        try:
            self.root.mainloop()
        finally:
            self.listener.stop()
            self.stop_event.set()
            self.runner.execute_script = False
