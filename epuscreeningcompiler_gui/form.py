"""
Build a form from the epuscreeningcompiler ArgumentParser, and turn its values back into an argv list.

The introspection (`describe`) and argv building (`build_argv`, `validate`) are pure and need no display; `Form` is the
tkinter widget layer on top of them.
"""
import argparse
import os
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, ttk

# argparse cannot say that a plain string option is a folder path, so name those here.
DIR_OPTIONS = {"--atlas"}
# Hard-coded assumptions about the CLI (unlikely to change).
SESSIONS_DEST = "epu_sessions"
OUTPUT_FLAG = "--output"

# kinds
DIRLIST, DIR, FLAG, TEXT, CHOICE = "dirlist", "dir", "flag", "text", "choice"


@dataclass
class Field:
    dest: str
    kind: str
    label: str              # flag (e.g. "--output") or dest for positionals
    help: str
    required: bool
    flag: str = None        # None for positionals
    choices: tuple = ()


def describe(parser):
    """Return a list of `Field`s for the parser's arguments, in definition order (help excluded)."""
    fields = []
    for a in parser._actions:
        if isinstance(a, argparse._HelpAction):
            continue
        flag = a.option_strings[0] if a.option_strings else None
        label = flag or a.dest
        help_text = a.help or ""
        if a.dest == SESSIONS_DEST:
            kind = DIRLIST
        elif flag == OUTPUT_FLAG or flag in DIR_OPTIONS:
            kind = DIR
        elif isinstance(a, argparse._StoreTrueAction):
            kind = FLAG
        elif a.choices:
            kind = CHOICE
        else:
            kind = TEXT
        fields.append(Field(a.dest, kind, label, help_text, bool(a.required) or a.dest == SESSIONS_DEST or
                            flag == OUTPUT_FLAG, flag, tuple(a.choices or ())))
    return fields


def validate(fields, values):
    """Return a list of human-readable problems with `values` (empty if all is well)."""
    problems = []
    for f in fields:
        v = values[f.dest]
        if f.kind == DIRLIST:
            if not v:
                problems.append("Add at least one EPU session folder.")
            problems += [f"Not a folder: {p}" for p in v if not os.path.isdir(p)]
        elif f.kind == DIR:
            if not v:
                if f.required:
                    problems.append(f"{f.label} is required.")
            elif not os.path.isdir(v):
                problems.append(f"{f.label}: not a folder: {v}")
        elif f.kind in (TEXT, CHOICE) and f.required and not v:
            problems.append(f"{f.label} is required.")
    return problems


def build_argv(fields, values):
    """Options first (in definition order), then positionals."""
    opts, positionals = [], []
    for f in fields:
        v = values[f.dest]
        if f.kind == DIRLIST:
            positionals += list(v)
        elif f.kind == FLAG:
            if v:
                opts.append(f.flag)
        elif v:
            opts += [f.flag, v]
    return opts + positionals


class Form(ttk.Frame):
    def __init__(self, master, parser, wraplength=560):
        super().__init__(master)
        self.fields = describe(parser)
        self._vars = {}      # dest -> tk variable (or Listbox for DIRLIST)
        self._widgets = []   # everything to disable while running
        self.columnconfigure(0, weight=1)
        row = 0
        if parser.description:
            ttk.Label(self, text=parser.description, wraplength=wraplength).grid(row=row, sticky="w", pady=(0, 8))
            row += 1
        for f in self.fields:
            ttk.Separator(self).grid(row=row, sticky="ew", pady=4)
            row += 1
            box = ttk.Frame(self)
            box.grid(row=row, sticky="ew")
            box.columnconfigure(0, weight=1)
            self._build_field(box, f)
            ttk.Label(box, text=f.help, wraplength=wraplength, foreground="gray40").grid(
                row=99, column=0, columnspan=3, sticky="w")
            row += 1

    def _build_field(self, box, f):
        title = f.label + (" *" if f.required else "")
        if f.kind == FLAG:
            var = tk.BooleanVar()
            w = ttk.Checkbutton(box, text=title, variable=var)
            w.grid(row=0, column=0, sticky="w")
            self._vars[f.dest] = var
            self._widgets.append(w)
            return
        ttk.Label(box, text=title).grid(row=0, column=0, sticky="w")
        if f.kind == DIRLIST:
            lb = tk.Listbox(box, height=5, selectmode=tk.EXTENDED, exportselection=False)
            lb.grid(row=1, column=0, sticky="ew")
            btns = ttk.Frame(box)
            btns.grid(row=1, column=1, sticky="n", padx=(6, 0))
            add = ttk.Button(btns, text="Add folder…", command=lambda: self._add_dir(lb))
            rem = ttk.Button(btns, text="Remove", command=lambda: self._remove_selected(lb))
            add.pack(fill="x")
            rem.pack(fill="x", pady=(4, 0))
            self._vars[f.dest] = lb
            self._widgets += [lb, add, rem]
        elif f.kind == CHOICE:
            var = tk.StringVar()
            w = ttk.Combobox(box, textvariable=var, values=("",) + f.choices, state="readonly")
            w.grid(row=1, column=0, sticky="ew")
            self._vars[f.dest] = var
            self._widgets.append(w)
        else:
            var = tk.StringVar()
            entry = ttk.Entry(box, textvariable=var)
            entry.grid(row=1, column=0, sticky="ew")
            self._vars[f.dest] = var
            self._widgets.append(entry)
            if f.kind == DIR:
                b = ttk.Button(box, text="Browse…", command=lambda: self._pick_dir(var))
                b.grid(row=1, column=1, padx=(6, 0))
                self._widgets.append(b)

    @staticmethod
    def _pick_dir(var):
        d = filedialog.askdirectory(mustexist=True, initialdir=var.get() or None)
        if d:
            var.set(os.path.normpath(d))

    @staticmethod
    def _add_dir(listbox):
        d = filedialog.askdirectory(mustexist=True)
        d = os.path.normpath(d) if d else None
        if d and d not in listbox.get(0, tk.END):
            listbox.insert(tk.END, d)

    @staticmethod
    def _remove_selected(listbox):
        for i in reversed(listbox.curselection()):
            listbox.delete(i)

    def values(self):
        out = {}
        for f in self.fields:
            v = self._vars[f.dest]
            out[f.dest] = list(v.get(0, tk.END)) if f.kind == DIRLIST else (v.get().strip() if f.kind != FLAG
                                                                              else v.get())
        return out

    def set_enabled(self, enabled):
        for w in self._widgets:
            if isinstance(w, ttk.Combobox):
                w.configure(state="readonly" if enabled else "disabled")
            else:
                w.configure(state="normal" if enabled else "disabled")
