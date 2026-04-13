"""
Top-level application window — manages screen transitions.
"""

import customtkinter as ctk

from .home_screen    import HomeScreen
from .session_screen import SessionScreen


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Ramp Data Collection Tool")
        self.geometry("1100x700")
        self.minsize(800, 560)
        self._current_screen = None
        self._show_home()

    def _clear(self):
        if self._current_screen:
            self._current_screen.destroy()
            self._current_screen = None

    def _show_home(self):
        self._clear()
        screen = HomeScreen(self, on_open_session=self._show_session)
        screen.pack(fill="both", expand=True)
        self._current_screen = screen

    def _show_session(self, session):
        self._clear()
        screen = SessionScreen(self, session, on_back=self._show_home)
        screen.pack(fill="both", expand=True)
        self._current_screen = screen
