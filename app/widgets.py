"""
Small reusable UI widgets: NumericEntry, Tooltip, category Badge.
"""

import tkinter as tk
import customtkinter as ctk
from .constants import (
    ACCENT, TEXT_MAIN, TEXT_SECONDARY, TOPBAR_BG, BORDER_COLOR,
)

# ── Numeric entry (comma → dot, cursor preserved) ─────────────────────────────

class NumericEntry(ctk.CTkEntry):
    """CTkEntry that silently converts ',' to '.' while preserving cursor pos."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._var = tk.StringVar()
        self.configure(textvariable=self._var)
        self._var.trace_add("write", self._on_write)
        self._modifying = False

    def _on_write(self, *_):
        if self._modifying or "," not in self._var.get():
            return
        self._modifying = True
        try:
            idx = self.index(tk.INSERT)
            self._var.set(self._var.get().replace(",", "."))
            self.icursor(idx)
        finally:
            self._modifying = False


# ── Tooltip ────────────────────────────────────────────────────────────────────

class Tooltip:
    """Lightweight hover tooltip for any widget."""

    def __init__(self, widget, text_func):
        self._widget   = widget
        self._text_func = text_func
        self._tw       = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None):
        text = self._text_func()
        if not text:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tw = tk.Toplevel(self._widget)
        self._tw.wm_overrideredirect(True)
        self._tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._tw, text=text,
            background="#2a2a3e", foreground=TEXT_MAIN,
            relief="flat", padx=8, pady=4,
            font=("Segoe UI", 9), wraplength=300, justify="left",
        ).pack()

    def _hide(self, _event=None):
        if self._tw:
            self._tw.destroy()
            self._tw = None


# ── Category badge ─────────────────────────────────────────────────────────────

_BADGE_COLORS: dict[str, tuple[str, str]] = {
    "ramp":  ("#1a3a6b", "#5b8dee"),
    "stair": ("#2d1f5e", "#9b7fe8"),
    "up":    ("#0f3d25", "#34c472"),
    "down":  ("#3d1515", "#ef6b6b"),
    "flat":  ("#2a2a2a", "#9ca3af"),
}


def make_badge(parent, text: str, width: int = 58) -> ctk.CTkLabel:
    bg, fg = _BADGE_COLORS.get(text.lower(), ("#2a2a3a", TEXT_SECONDARY))
    return ctk.CTkLabel(
        parent, text=text.capitalize(),
        width=width, height=22,
        font=("Segoe UI", 10, "bold"),
        text_color=fg, fg_color=bg,
        corner_radius=11,
    )
