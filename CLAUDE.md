# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A desktop GUI application for recording and visualising sensor data from ramp/stair traversal experiments (RoboCupJunior Rescue Maze robot development). Built with CustomTkinter, SQLite, and Matplotlib.

## Running the app

```bash
pip install customtkinter matplotlib pillow
python main.py
```

Matplotlib and Pillow are optional — the app runs without them (visualisation tab is hidden if Matplotlib is missing).

## Building the executable

```bash
pyinstaller --onefile --windowed --add-data "images;images" main.py
```

Output lands in `dist/RampDataCollectionTool.exe`.

## Architecture

**Screen navigation** is handled by `app_window.py` (`App` class). It owns transitions between the two top-level screens by destroying the current screen widget and instantiating the next one. Screens receive callbacks (`on_open_session`, `on_back`) rather than holding a reference to `App`.

**Screens and their responsibilities:**
- `home_screen.py` — session list, create/edit/delete sessions
- `session_screen.py` — tabbed view: wraps `data_entry.py` (entries tab) and `visualization.py` (charts tab)
- `data_entry.py` — scrollable entry table with filter toolbar; add/edit/delete entries
- `visualization.py` — 2×2 Matplotlib scatter plot grid (Ramp Up / Ramp Down / Stair Up / Stair Down)
- `modals.py` — modal dialogs for add/edit of sessions and entries

**Database** (`database.py`) is a thin SQLite access layer. All SQL lives here — no SQL in UI files. Two tables: `sessions` and `entries` (entries foreign-key to sessions with `ON DELETE CASCADE`). The DB file (`ramp_data.db`) is always placed next to the executable/script, resolved via `constants.py`.

**Constants** (`constants.py`) centralises: DB and image paths (with PyInstaller `sys._MEIPASS` handling), optional-dependency flags (`PIL_AVAILABLE`, `MPL_AVAILABLE`), CustomTkinter theme setup, and the colour palette.

**Shared widgets** (`widgets.py`) and small utilities (`helpers.py`) are used across screens.
