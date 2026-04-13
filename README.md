# Ramp Data Collection Tool

A desktop application for recording and visualising sensor data collected during ramp and stair traversal experiments — intended to be used for development of a robot for the RoboCupJunior Rescue Maze where encoder, IMU, and timing measurements need to be organised across multiple test sessions.
Made with Claude Caude as a test project.

## What it does

- **Session management** — create, edit, and delete named test sessions with date, location, and notes.
- **Data entry** — log individual traversal entries per session, capturing:
  - Surface type (`Ramp` / `Stair`) and direction (`Up` / `Down`)
  - Number of fields, actual distance (mm), encoder distance (mm)
  - Duration (ms), angle mean/median, gyro variance, and an optional note
- **Filtering** — quickly filter the entry table by type or direction.
- **Visualisation** — interactive 2×2 scatter plot grid (Ramp Up / Ramp Down / Stair Up / Stair Down), with a configurable X-axis (encoder distance, duration, gyro variance, angle mean/median) plotted against actual distance.
- **Local storage** — all data is persisted in a SQLite database (`ramp_data.db`) next to the executable.

## Stack

| Layer | Library |
|---|---|
| GUI | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Charts | [Matplotlib](https://matplotlib.org/) (optional — app works without it) |
| Database | SQLite via `sqlite3` (stdlib) |
| Packaging | [PyInstaller](https://pyinstaller.org/) |

## Getting started

```bash
# 1. Install dependencies
pip install customtkinter matplotlib pillow

# 2. Run
python main.py
```

A pre-built Windows executable is available under `dist/RampDataCollectionTool.exe` — no Python installation required.

## Project structure

```
main.py                 # Entry point
app/
  app_window.py         # Top-level window, screen transitions
  home_screen.py        # Session list / management
  session_screen.py     # Tabbed session view
  data_entry.py         # Entry table and toolbar
  visualization.py      # Matplotlib scatter plots
  modals.py             # Add / edit dialogs
  database.py           # All SQLite access
  widgets.py            # Shared UI components
  constants.py          # Theme colours, paths, optional-dep flags
```
