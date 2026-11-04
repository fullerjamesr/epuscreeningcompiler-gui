"""Run the epuscreeningcompiler CLI as a subprocess and stream its output through a queue."""
import os
import queue
import subprocess
import sys
import threading


class Runner:
    """Start with `start(argv)`; poll `lines` (a queue of str, then a final `None`) and `returncode`."""

    def __init__(self):
        self.lines = queue.Queue()
        self.returncode = None
        self._proc = None

    def start(self, argv):
        cmd = [sys.executable, "-u", "-m", "epuscreeningcompiler", *argv]
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                      text=True, encoding="utf-8", errors="replace", bufsize=1, env=env, **kwargs)
        threading.Thread(target=self._pump, daemon=True).start()
        return cmd

    def _pump(self):
        for line in self._proc.stdout:
            self.lines.put(line)
        self.returncode = self._proc.wait()
        self.lines.put(None)

    @property
    def running(self):
        return self._proc is not None and self._proc.poll() is None

    def cancel(self):
        if self.running:
            self._proc.terminate()
            try:
                self._proc.wait(3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
