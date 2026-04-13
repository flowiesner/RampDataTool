"""
Global constants: file paths, theme colours, optional-dependency flags.
"""

import os
import customtkinter as ctk

# ── optional dependencies ──────────────────────────────────────────────────────
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False

# ── paths ──────────────────────────────────────────────────────────────────────
import sys

# When frozen as .exe (PyInstaller), bundled data lives in sys._MEIPASS;
# the database should always sit next to the executable / script.
if getattr(sys, "frozen", False):
    _EXE_DIR    = os.path.dirname(sys.executable)
    _BUNDLE_DIR = sys._MEIPASS
else:
    _EXE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _BUNDLE_DIR = _EXE_DIR

DB_PATH   = os.path.join(_EXE_DIR,    "ramp_data.db")
TEAM_PATH = os.path.join(_BUNDLE_DIR, "images/team.png")

# ── CTk theme ──────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── colour palette ─────────────────────────────────────────────────────────────
APP_BG         = "#0f1117"
CARD_BG        = "#181c27"
CARD_BG_HOVER  = "#1f2435"
TOPBAR_BG      = "#0b0d14"
ACCENT         = "#5b8dee"
ACCENT2        = "#7c5be8"
TEXT_MUTED     = "#6b7280"
TEXT_SECONDARY = "#9ca3af"
TEXT_MAIN      = "#e8eaf0"
BORDER_COLOR   = "#252a3a"
BORDER_HOVER   = "#5b8dee"
DANGER         = "#ef4444"

