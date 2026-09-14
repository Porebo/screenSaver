"""Tkinter app that keeps the computer awake and displays a countdown timer."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import ctypes

# Windows API flags to prevent sleep and display off
_ES_CONTINUOUS       = 0x80000000
_ES_SYSTEM_REQUIRED  = 0x00000001
_ES_DISPLAY_REQUIRED = 0x00000002


SECONDS_PER_MINUTE = 60
DEFAULT_MINUTES = 9999
WINDOW_TITLE = "Awake Timer"


class AwakeTimerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry("600x400")
        self.root.minsize(400, 300)

        self.session_active = False
        self.countdown_job = None
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.elapsed_seconds = 0

        self._build_ui()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # Top control frame
        top_frame = ttk.Frame(self.root, padding=12)
        top_frame.grid(row=0, column=0, sticky="ew")
        top_frame.columnconfigure(3, weight=1)

        ttk.Label(top_frame, text="Minutes:").grid(row=0, column=0, sticky="w")
        self.minutes_var = tk.StringVar(value=str(DEFAULT_MINUTES))
        self.minutes_entry = ttk.Entry(top_frame, textvariable=self.minutes_var, width=10)
        self.minutes_entry.grid(row=0, column=1, padx=(8, 16), sticky="w")

        self.start_button = ttk.Button(top_frame, text="Start", command=self.start_session)
        self.start_button.grid(row=0, column=2, padx=(0, 8), sticky="w")

        self.quit_button = ttk.Button(top_frame, text="Quit", command=self.quit_app)
        self.quit_button.grid(row=0, column=3, sticky="w")

        # Main timer display frame
        timer_frame = ttk.Frame(self.root, padding=12)
        timer_frame.grid(row=1, column=0, sticky="nsew")
        timer_frame.columnconfigure(0, weight=1)
        timer_frame.rowconfigure(0, weight=1)

        self.timer_label = tk.Label(
            timer_frame,
            text="00:00:00",
            font=("Arial", 120, "bold"),
            fg="#000000",
            anchor="center"
        )
        self.timer_label.grid(row=0, column=0, sticky="nsew")

        # Status message frame
        self.message_var = tk.StringVar(value="Enter minutes and press Start.")
        ttk.Label(self.root, textvariable=self.message_var, padding=(12, 8, 12, 12)).grid(
            row=2, column=0, sticky="sw"
        )

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def start_session(self) -> None:
        if self.session_active:
            return

        try:
            minutes = int(self.minutes_var.get().strip())
        except ValueError:
            self.message_var.set("Please enter a whole number of minutes.")
            return

        if minutes <= 0:
            self.message_var.set("Minutes must be greater than zero.")
            return

        self.total_seconds = minutes * SECONDS_PER_MINUTE
        self.elapsed_seconds = 0
        self.session_active = True
        self.start_button.configure(state="disabled")
        self.minutes_entry.configure(state="disabled")
        self.message_var.set(f"Keeping computer awake for {minutes} minute(s)...")

        ctypes.windll.kernel32.SetThreadExecutionState(
            _ES_CONTINUOUS | _ES_SYSTEM_REQUIRED | _ES_DISPLAY_REQUIRED
        )

        self._tick_countdown()

    def _tick_countdown(self) -> None:
        if not self.session_active:
            return

        if self.elapsed_seconds >= self.total_seconds:
            self._finish_session()
            return

        hours_elapsed = self.elapsed_seconds // 3600
        minutes_elapsed = (self.elapsed_seconds % 3600) // SECONDS_PER_MINUTE
        seconds_elapsed = self.elapsed_seconds % SECONDS_PER_MINUTE

        time_str = f"{hours_elapsed:02d}:{minutes_elapsed:02d}:{seconds_elapsed:02d}"
        self.timer_label.configure(text=time_str)

        self.elapsed_seconds += 1
        self.countdown_job = self.root.after(1000, self._tick_countdown)

    def _finish_session(self) -> None:
        self.session_active = False
        self.start_button.configure(state="normal")
        self.minutes_entry.configure(state="normal")

        if self.countdown_job is not None:
            self.root.after_cancel(self.countdown_job)
            self.countdown_job = None

        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)

        self.timer_label.configure(text="00:00:00")
        self.message_var.set("Done. Wake lock released.")

    def quit_app(self) -> None:
        if self.session_active:
            self._finish_session()
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    AwakeTimerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
