import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from epuscreeningcompiler.main import build_argparse

from .form import Form, build_argv, validate
from .runner import Runner


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.master = master
        self.runner = None
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.form = Form(self, build_argparse())
        self.form.grid(row=0, sticky="ew")

        bar = ttk.Frame(self)
        bar.grid(row=1, sticky="w", pady=8)
        self.run_btn = ttk.Button(bar, text="Run", command=self.run)
        self.run_btn.pack(side="left")
        self.cancel_btn = ttk.Button(bar, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left", padx=6)
        self.status = ttk.Label(bar, text="")
        self.status.pack(side="left", padx=6)

        self.log = ScrolledText(self, height=12, state="disabled", wrap="word")
        self.log.grid(row=2, sticky="nsew")
        master.protocol("WM_DELETE_WINDOW", self.on_close)

    def _append(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def run(self):
        values = self.form.values()
        problems = validate(self.form.fields, values)
        if problems:
            messagebox.showerror("Cannot run", "\n".join(problems))
            return
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.runner = Runner()
        self.runner.start(build_argv(self.form.fields, values))
        self.form.set_enabled(False)
        self.run_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.status.configure(text="Running…")
        self.after(100, self._poll)

    def _poll(self):
        done = False
        while True:
            try:
                line = self.runner.lines.get_nowait()
            except Exception:
                break
            if line is None:
                done = True
                break
            self._append(line)
        if done:
            rc = self.runner.returncode
            self.status.configure(text="Finished" if rc == 0 else f"Stopped (exit code {rc})")
            self.form.set_enabled(True)
            self.run_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
        else:
            self.after(100, self._poll)

    def cancel(self):
        if self.runner:
            self.runner.cancel()

    def on_close(self):
        if self.runner and self.runner.running:
            if not messagebox.askyesno("Quit", "A run is in progress. Cancel it and quit?"):
                return
            self.runner.cancel()
        self.master.destroy()


def main():
    root = tk.Tk()
    root.title("EPU Screening Compiler")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
