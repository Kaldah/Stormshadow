from __future__ import annotations

from subprocess import Popen
from typing import Optional, Sequence, Dict
import os
import platform
import tkinter as tk
from tkinter import scrolledtext, ttk

# Terminal backend interface + helpers
from utils.core.tty_terminal import TerminalIO, PipeTerminal, create_terminal


class ConsoleWindow:
    """
    Tk console that mirrors a running process.

    Exactly one of:
      - process: an existing Popen created with stdin=PIPE, stdout=PIPE (stderr optional)
      - io: a TerminalIO backend (e.g., PTY-backed on Unix)

    Closing the window does NOT kill the process. The window auto-closes when the process exits.
    """

    def __init__(
        self,
        process: Optional[Popen[bytes]] = None,
        *,
        io: Optional[TerminalIO] = None,
        title: str = "Console Window",
        interactive: bool = False,
        auto_close: bool = True,
    ) -> None:
        # Enforce EXACTLY one of process / io
        if (process is None) == (io is None):
            raise ValueError("Provide exactly one of `process` or `io`.")

        # If a Popen is provided, wrap it with a pipe-backed backend
        if io is None:
            if process is None or process.stdin is None or process.stdout is None:
                raise ValueError("`process` must be started with stdin=PIPE and stdout=PIPE.")
            io = PipeTerminal.wrap_existing(process)

        self.io: TerminalIO = io
        self.process: Optional[Popen[bytes]] = process or io.proc
        self.title = title
        self.interactive = interactive
        self.auto_close = auto_close

        self.root: Optional[tk.Tk] = None
        self.text_area: Optional[scrolledtext.ScrolledText] = None
        self.entry: Optional[ttk.Entry] = None

    # Optional: a spawner helper that *externally* decides PTY vs pipes
    @classmethod
    def spawn(
        cls,
        argv: Sequence[str],
        *,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        prefer_tty: bool = True,
        title: str = "Console Window",
        interactive: bool = False,
        auto_close: bool = True,
        start_new_session: bool = True,
    ) -> "ConsoleWindow":
        io = create_terminal(
            argv,
            cwd=cwd,
            env=env,
            prefer_tty=prefer_tty,
            start_new_session=start_new_session,
        )
        return cls(io=io, title=title, interactive=interactive, auto_close=auto_close)

    # --- Public -------------------------------------------------------------

    def create_tk_console(self) -> None:
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("920x540")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD)
        self.text_area.configure(
            font=("Fira Mono", 11),
            background="#0c0c0c",
            foreground="#e5e5e5",
            insertbackground="#e5e5e5",
        )
        self.text_area.pack(expand=True, fill="both")

        bar = ttk.Frame(self.root)
        bar.pack(fill="x")
        # ttk.Button(bar, text="INT (Ctrl‑C)", command=self.send_interrupt).pack(side="left", padx=4, pady=4)
        # ttk.Button(bar, text="TERM", command=self.send_terminate).pack(side="left", padx=4, pady=4)
        # ttk.Button(bar, text="KILL", command=self.send_kill).pack(side="left", padx=4, pady=4)

        if self.interactive:
            row = ttk.Frame(self.root)
            row.pack(fill="x")
            ttk.Label(row, text="stdin:").pack(side="left", padx=(6, 2))
            self.entry = ttk.Entry(row)
            self.entry.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=6)
            self.entry.bind("<Return>", self._send_line)
            # Allow keyboard shortcuts to work on the entry widget too
            self.entry.bind("<Control-c>", lambda e: self.send_interrupt())
            self.entry.bind("<Control-z>", lambda e: self.send_stop())
            self.entry.bind("<Control-backslash>", lambda e: self.send_quit())

        # Add global keyboard shortcuts for the window
        self.root.bind("<Control-c>", lambda e: self.send_interrupt())
        self.root.bind("<Control-z>", lambda e: self.send_stop())
        self.root.bind("<Control-backslash>", lambda e: self.send_quit())
        self.root.bind("<Control-d>", lambda e: self._send_eof())
        
        # Allow text area to have focus for keyboard shortcuts
        self.text_area.bind("<Control-c>", lambda e: self.send_interrupt())
        self.text_area.bind("<Control-z>", lambda e: self.send_stop())
        self.text_area.bind("<Control-backslash>", lambda e: self.send_quit())

        self._pump_output()
        self._watch_process()
        self.root.mainloop()

    def send_interrupt(self) -> None:
        self._signal("INT")

    def send_terminate(self) -> None:
        self._signal("TERM")

    def send_kill(self) -> None:
        self._signal("KILL")

    def send_stop(self) -> None:
        self._signal("STOP")

    def send_quit(self) -> None:
        self._signal("QUIT")

    # --- Internals ----------------------------------------------------------

    def _append(self, s: str) -> None:
        if self.text_area:
            self.text_area.insert("end", s)
            self.text_area.see("end")

    def _pump_output(self) -> None:
        while True:
            chunk = self.io.read_nowait()
            if not chunk:
                break
            try:
                text = chunk.decode("utf-8", "replace")
            except Exception:
                text = chunk.decode("latin-1", "replace")
            self._append(text)
        if self.root:
            self.root.after(30, self._pump_output)

    def _watch_process(self) -> None:
        proc = self.process or self.io.proc
        exited = (proc is not None and proc.poll() is not None)
        if exited and self.auto_close:
            try:
                self.io.close()
            except Exception:
                pass
            if self.root:
                self.root.after(50, self.root.destroy)
            return
        if self.root:
            self.root.after(200, self._watch_process)

    def _on_close(self) -> None:
        try:
            self.io.close()
        except Exception:
            pass
        if self.root:
            self.root.destroy()

    def _send_line(self, _evt: Optional[tk.Event] = None) -> None:
        if not self.interactive or not self.entry:
            return
        data = (self.entry.get() + "\n").encode("utf-8", "replace")
        try:
            self.io.write(data)
        except Exception:
            pass
        self.entry.delete(0, "end")

    def _send_eof(self) -> None:
        """Send EOF (Ctrl+D) to the process stdin."""
        try:
            # EOF is represented by closing stdin or sending \x04 (EOT)
            self.io.write(b"\x04")
        except Exception:
            pass

    def _signal(self, kind: str) -> None:
        proc = self.process or self.io.proc
        if proc is None:
            return

        system = platform.system().lower()
        if system == "windows":
            try:
                if kind in ("INT", "TERM"):
                    proc.terminate()
                else:
                    proc.kill()
            except Exception:
                pass
            return

        # POSIX
        try:
            import signal as _sig
            sigmap = {
                "INT": _sig.SIGINT, 
                "TERM": _sig.SIGTERM, 
                "KILL": _sig.SIGKILL,
                "STOP": _sig.SIGTSTP,  # Ctrl+Z
                "QUIT": _sig.SIGQUIT,  # Ctrl+\
            }
            sig = sigmap.get(kind, _sig.SIGTERM)
            try:
                pgid = os.getpgid(proc.pid)
            except Exception:
                pgid = None
            if pgid and pgid > 0:
                os.killpg(pgid, sig)
            else:
                os.kill(proc.pid, sig)
        except Exception:
            pass
