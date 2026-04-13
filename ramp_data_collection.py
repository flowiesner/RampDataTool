"""
Ramp Data Collection Tool
Single-file CustomTkinter + SQLite app for RoboCup Rescue Maze ramp/stair traversal data.
"""

import customtkinter as ctk
import sqlite3
import os
import datetime
from tkinter import messagebox
import tkinter as tk

# ── optional deps ──────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk
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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(SCRIPT_DIR, "ramp_data.db")
BANNER_PATH = os.path.join(SCRIPT_DIR, "banner.png")
MAZE_PATH   = os.path.join(SCRIPT_DIR, "maze_picture.png")
TEAM_PATH   = os.path.join(SCRIPT_DIR, "team.png")

# ── theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
BANNER_H       = 280

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                date     TEXT NOT NULL,
                location TEXT,
                notes    TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                type            TEXT NOT NULL,
                direction       TEXT NOT NULL,
                fields          INTEGER,
                actual_dist_mm  REAL,
                encoder_dist_mm REAL,
                duration_ms     REAL,
                angle_mean      REAL,
                angle_median    REAL,
                gyro_variance   REAL,
                note            TEXT
            )
        """)
        conn.commit()

def db_get_sessions():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM sessions ORDER BY date DESC, id DESC").fetchall()

def db_create_session(name, date, location, notes):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO sessions (name, date, location, notes) VALUES (?,?,?,?)",
            (name, date, location, notes)
        )
        conn.commit()
        return cur.lastrowid

def db_update_session(session_id, name, date, location, notes):
    with get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET name=?, date=?, location=?, notes=? WHERE id=?",
            (name, date, location, notes, session_id)
        )
        conn.commit()

def db_delete_session(session_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM entries WHERE session_id=?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()

def db_get_entries(session_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM entries WHERE session_id=? ORDER BY id",
            (session_id,)
        ).fetchall()

def db_create_entry(session_id, data: dict):
    cols = ["session_id","type","direction","fields","actual_dist_mm",
            "encoder_dist_mm","duration_ms","angle_mean","angle_median","gyro_variance","note"]
    vals = [session_id] + [data.get(c) for c in cols[1:]]
    with get_conn() as conn:
        conn.execute(
            f"INSERT INTO entries ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
            vals
        )
        conn.commit()

def db_update_entry(entry_id, data: dict):
    sets = ",".join(f"{k}=?" for k in data)
    vals = list(data.values()) + [entry_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE entries SET {sets} WHERE id=?", vals)
        conn.commit()

def db_delete_entry(entry_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        conn.commit()

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def direction_from_angle(angle_mean):
    try:
        v = float(str(angle_mean).replace(",", "."))
        if v > 0:
            return "up"
        elif v < 0:
            return "down"
        else:
            return "flat"
    except (TypeError, ValueError):
        return "flat"


def to_float_or_none(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", ".")
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def to_int_or_none(s):
    v = to_float_or_none(s)
    return int(v) if v is not None else None


# ══════════════════════════════════════════════════════════════════════════════
# COMMA→DOT ENTRY WIDGET
# ══════════════════════════════════════════════════════════════════════════════

class NumericEntry(ctk.CTkEntry):
    """Entry that converts comma to dot while preserving cursor position."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._var = tk.StringVar()
        self.configure(textvariable=self._var)
        self._var.trace_add("write", self._on_write)
        self._modifying = False

    def _on_write(self, *_):
        if self._modifying:
            return
        val = self._var.get()
        if "," in val:
            self._modifying = True
            try:
                idx = self.index(tk.INSERT)
                new_val = val.replace(",", ".")
                self._var.set(new_val)
                self.icursor(idx)
            finally:
                self._modifying = False


# ══════════════════════════════════════════════════════════════════════════════
# TOOLTIP
# ══════════════════════════════════════════════════════════════════════════════

class Tooltip:
    def __init__(self, widget, text_func):
        self._widget = widget
        self._text_func = text_func
        self._tw = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        text = self._text_func()
        if not text:
            return
        x = self._widget.winfo_rootx() + 20
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 4
        self._tw = tk.Toplevel(self._widget)
        self._tw.wm_overrideredirect(True)
        self._tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self._tw, text=text, background="#2a2a3e", foreground=TEXT_MAIN,
            relief="flat", padx=8, pady=4, font=("Segoe UI", 9),
            wraplength=300, justify="left"
        )
        lbl.pack()

    def _hide(self, event=None):
        if self._tw:
            self._tw.destroy()
            self._tw = None


# ══════════════════════════════════════════════════════════════════════════════
# EDIT SESSION MODAL
# ══════════════════════════════════════════════════════════════════════════════

class EditSessionModal(ctk.CTkToplevel):
    def __init__(self, parent, session, on_save, on_delete):
        super().__init__(parent)
        self.title("Edit Session")
        self.geometry("420x530")
        self.minsize(380, 490)
        self.resizable(True, True)
        self.grab_set()
        self.session   = session
        self.on_save   = on_save
        self.on_delete = on_delete
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 6}

        ctk.CTkLabel(self, text="Edit Session",
                     font=("Segoe UI", 16, "bold")).pack(pady=(20, 12))

        ctk.CTkLabel(self, text="Name *", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, self.session["name"] or "")
        self.name_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Date *", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.date_entry = ctk.CTkEntry(self)
        self.date_entry.insert(0, self.session["date"] or "")
        self.date_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Location", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.loc_entry = ctk.CTkEntry(self)
        self.loc_entry.insert(0, self.session["location"] or "")
        self.loc_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Notes", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.notes_box = ctk.CTkTextbox(self, height=80)
        self.notes_box.pack(fill="x", padx=24, pady=6)
        if self.session["notes"]:
            self.notes_box.insert("1.0", self.session["notes"])

        # Save / Cancel row
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(10, 6))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_row, text="Save", command=self._save
                      ).pack(side="left", expand=True, fill="x")

        # Delete row — separated visually
        ctk.CTkFrame(self, fg_color=BORDER_COLOR, height=1
                     ).pack(fill="x", padx=24, pady=(8, 0))
        ctk.CTkButton(self, text="🗑  Delete Session",
                      fg_color="transparent", border_width=1,
                      border_color=DANGER, text_color=DANGER,
                      hover_color="#2a1010",
                      command=self._delete
                      ).pack(fill="x", padx=24, pady=(8, 16))

    def _save(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        if not name:
            messagebox.showerror("Missing field", "Session name is required.", parent=self)
            return
        if not date:
            messagebox.showerror("Missing field", "Date is required.", parent=self)
            return
        loc   = self.loc_entry.get().strip()
        notes = self.notes_box.get("1.0", "end").strip()
        db_update_session(self.session["id"], name, date, loc, notes)
        self.destroy()
        self.on_save()

    def _delete(self):
        if messagebox.askyesno(
            "Delete Session",
            f"Delete session \"{self.session['name']}\" and ALL its entries?\nThis cannot be undone.",
            parent=self
        ):
            db_delete_session(self.session["id"])
            self.destroy()
            self.on_delete()


# ══════════════════════════════════════════════════════════════════════════════
# NEW SESSION MODAL
# ══════════════════════════════════════════════════════════════════════════════

class NewSessionModal(ctk.CTkToplevel):
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("New Session")
        self.geometry("420x460")
        self.minsize(380, 420)
        self.resizable(True, True)
        self.grab_set()
        self.on_save = on_save
        self._build()

    def _build(self):
        pad = {"padx": 24, "pady": 6}
        ctk.CTkLabel(self, text="New Session", font=("Segoe UI", 16, "bold")).pack(pady=(20, 12))

        ctk.CTkLabel(self, text="Name *", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Test Run 1")
        self.name_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Date *", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.date_entry = ctk.CTkEntry(self)
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.date_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Location", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.loc_entry = ctk.CTkEntry(self, placeholder_text="e.g. Lab A")
        self.loc_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Notes", anchor="w").pack(fill="x", padx=24, pady=(4,0))
        self.notes_box = ctk.CTkTextbox(self, height=60)
        self.notes_box.pack(fill="x", padx=24, pady=6)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(10, 20))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_row, text="Save", command=self._save).pack(side="left", expand=True, fill="x")

    def _save(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        if not name:
            messagebox.showerror("Missing field", "Session name is required.", parent=self)
            return
        if not date:
            messagebox.showerror("Missing field", "Date is required.", parent=self)
            return
        loc   = self.loc_entry.get().strip()
        notes = self.notes_box.get("1.0", "end").strip()
        sid = db_create_session(name, date, loc, notes)
        self.destroy()
        self.on_save(sid)


# ══════════════════════════════════════════════════════════════════════════════
# ADD / EDIT ENTRY MODAL
# ══════════════════════════════════════════════════════════════════════════════

class EntryModal(ctk.CTkToplevel):
    def __init__(self, parent, session_id, on_save, entry=None):
        super().__init__(parent)
        self.title("Edit Entry" if entry else "Add Entry")
        self.geometry("460x540")
        self.resizable(False, False)
        self.grab_set()
        self.session_id = session_id
        self.on_save = on_save
        self.entry = entry
        self._build()
        if entry:
            self._populate(entry)

    # ── layout ────────────────────────────────────────────────────────────────
    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        def row(label, widget_factory):
            ctk.CTkLabel(scroll, text=label, anchor="w").pack(fill="x", padx=20, pady=(6,0))
            w = widget_factory()
            w.pack(fill="x", padx=20, pady=(2,0))
            return w

        # Type
        ctk.CTkLabel(scroll, text="Type *", anchor="w").pack(fill="x", padx=20, pady=(10,0))
        self.type_var = ctk.StringVar(value="Ramp")
        self.type_combo = ctk.CTkOptionMenu(scroll, variable=self.type_var, values=["Ramp", "Stair"])
        self.type_combo.pack(fill="x", padx=20, pady=(2,0))

        # Direction (read-only, derived)
        ctk.CTkLabel(scroll, text="Direction (auto)", anchor="w").pack(fill="x", padx=20, pady=(6,0))
        self.dir_label = ctk.CTkLabel(scroll, text="—", anchor="w", text_color=TEXT_MUTED)
        self.dir_label.pack(fill="x", padx=20, pady=(2,0))

        # Fields
        ctk.CTkLabel(scroll, text="Fields (ground truth) *", anchor="w").pack(fill="x", padx=20, pady=(6,0))
        self.fields_entry = NumericEntry(scroll, placeholder_text="1 or 2")
        self.fields_entry.pack(fill="x", padx=20, pady=(2,0))

        # Numeric fields
        self.actual_entry    = self._num_row(scroll, "Actual dist. (mm)")
        self.encoder_entry   = self._num_row(scroll, "Encoder dist. (mm)")
        self.duration_entry  = self._num_row(scroll, "Duration (ms)")
        self.gyro_entry      = self._num_row(scroll, "Gyro variance")
        self.angle_mean_entry= self._num_row(scroll, "Angle mean (°)")
        self.angle_med_entry = self._num_row(scroll, "Angle median (°)")

        # Hook angle_mean to update direction label
        self.angle_mean_entry._var.trace_add("write", self._update_dir_label)

        # Note
        ctk.CTkLabel(scroll, text="Note (optional)", anchor="w").pack(fill="x", padx=20, pady=(6,0))
        self.note_box = ctk.CTkTextbox(scroll, height=70)
        self.note_box.pack(fill="x", padx=20, pady=(2,6))

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(4, 12))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0,6))
        ctk.CTkButton(btn_row, text="Save", command=self._save).pack(side="left", expand=True, fill="x")

    def _num_row(self, parent, label):
        ctk.CTkLabel(parent, text=label, anchor="w").pack(fill="x", padx=20, pady=(6,0))
        e = NumericEntry(parent)
        e.pack(fill="x", padx=20, pady=(2,0))
        return e

    def _update_dir_label(self, *_):
        raw = self.angle_mean_entry.get().replace(",", ".")
        direction = direction_from_angle(raw)
        self.dir_label.configure(text=direction.capitalize())

    # ── populate for edit ─────────────────────────────────────────────────────
    def _populate(self, e):
        self.type_var.set(e["type"].capitalize())
        self._set_entry(self.fields_entry,     e["fields"])
        self._set_entry(self.actual_entry,     e["actual_dist_mm"])
        self._set_entry(self.encoder_entry,    e["encoder_dist_mm"])
        self._set_entry(self.duration_entry,   e["duration_ms"])
        self._set_entry(self.gyro_entry,       e["gyro_variance"])
        self._set_entry(self.angle_mean_entry, e["angle_mean"])
        self._set_entry(self.angle_med_entry,  e["angle_median"])
        if e["note"]:
            self.note_box.insert("1.0", e["note"])
        self._update_dir_label()

    def _set_entry(self, widget, val):
        if val is not None:
            widget.delete(0, "end")
            widget.insert(0, str(val))

    # ── save ──────────────────────────────────────────────────────────────────
    def _save(self):
        angle_mean = to_float_or_none(self.angle_mean_entry.get())
        data = {
            "type":            self.type_var.get().lower(),
            "direction":       direction_from_angle(angle_mean),
            "fields":          to_int_or_none(self.fields_entry.get()),
            "actual_dist_mm":  to_float_or_none(self.actual_entry.get()),
            "encoder_dist_mm": to_float_or_none(self.encoder_entry.get()),
            "duration_ms":     to_float_or_none(self.duration_entry.get()),
            "angle_mean":      angle_mean,
            "angle_median":    to_float_or_none(self.angle_med_entry.get()),
            "gyro_variance":   to_float_or_none(self.gyro_entry.get()),
            "note":            self.note_box.get("1.0", "end").strip() or None,
        }
        if self.entry:
            db_update_entry(self.entry["id"], data)
        else:
            db_create_entry(self.session_id, data)
        self.destroy()
        self.on_save()


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY BADGE
# ══════════════════════════════════════════════════════════════════════════════

_BADGE_COLORS = {
    "ramp":  ("#1a3a6b", "#5b8dee"),   # bg, fg
    "stair": ("#2d1f5e", "#9b7fe8"),
    "up":    ("#0f3d25", "#34c472"),
    "down":  ("#3d1515", "#ef6b6b"),
    "flat":  ("#2a2a2a", "#9ca3af"),
}

def make_badge(parent, text, width=58):
    key = text.lower()
    bg, fg = _BADGE_COLORS.get(key, ("#2a2a3a", TEXT_SECONDARY))
    lbl = ctk.CTkLabel(
        parent, text=text.capitalize(),
        width=width, height=22,
        font=("Segoe UI", 10, "bold"),
        text_color=fg, fg_color=bg,
        corner_radius=11,
    )
    return lbl


# ══════════════════════════════════════════════════════════════════════════════
# DATA ENTRY TABLE ROW
# ══════════════════════════════════════════════════════════════════════════════

class EntryRow(ctk.CTkFrame):
    COLS = [
        ("# ",        40),
        ("Type",      60),
        ("Dir.",      50),
        ("Fields",    52),
        ("Actual\n(mm)", 72),
        ("Encoder\n(mm)", 72),
        ("Duration\n(ms)", 76),
        ("Angle\nmean", 68),
        ("Angle\nmedian", 72),
        ("Gyro\nvar.", 68),
        ("Actions",   72),
    ]

    @classmethod
    def header(cls, parent):
        hdr = ctk.CTkFrame(parent, fg_color=TOPBAR_BG, corner_radius=6)
        hdr.pack(fill="x", padx=4, pady=(0,2))
        for title, w in cls.COLS:
            ctk.CTkLabel(
                hdr, text=title, width=w, font=("Segoe UI", 10, "bold"),
                text_color=TEXT_MUTED, anchor="w"
            ).pack(side="left", padx=4, pady=4)
        return hdr

    def __init__(self, parent, index, entry, on_edit, on_delete):
        super().__init__(parent, fg_color=CARD_BG, corner_radius=6,
                         height=34)
        self.pack(fill="x", padx=4, pady=2)
        self.pack_propagate(False)
        self.entry     = entry
        self.on_edit   = on_edit
        self.on_delete = on_delete

        plain_vals = [
            str(index),
            None,                               # Type  → badge
            None,                               # Dir.  → badge
            str(entry["fields"] or ""),
            self._fmt(entry["actual_dist_mm"]),
            self._fmt(entry["encoder_dist_mm"]),
            self._fmt(entry["duration_ms"]),
            self._fmt(entry["angle_mean"]),
            self._fmt(entry["angle_median"]),
            self._fmt(entry["gyro_variance"]),
        ]
        for i, (val, (_, w)) in enumerate(zip(plain_vals, self.COLS[:-1])):
            if i == 1:   # Type badge
                make_badge(self, entry["type"], width=w).pack(side="left", padx=4)
            elif i == 2: # Direction badge
                make_badge(self, entry["direction"], width=w).pack(side="left", padx=4)
            else:
                ctk.CTkLabel(self, text=val, width=w, anchor="w",
                             font=("Segoe UI", 11)).pack(side="left", padx=4)

        # Actions
        act = ctk.CTkFrame(self, fg_color="transparent", width=90)
        act.pack(side="left", padx=2)
        act.pack_propagate(False)

        ctk.CTkButton(
            act, text="Edit", width=36, height=24,
            font=("Segoe UI", 10), corner_radius=4,
            fg_color="#2a2a4a", hover_color="#3a3a6a",
            text_color=TEXT_MAIN,
            command=lambda: on_edit(entry)
        ).pack(side="left", padx=2)

        has_note = bool(entry["note"])
        note_btn = ctk.CTkButton(
            act, text="Note", width=36, height=24,
            font=("Segoe UI", 10), corner_radius=4,
            fg_color="#2a2a4a" if has_note else "transparent",
            hover_color="#2a2a4a",
            text_color=ACCENT if has_note else TEXT_MUTED,
            command=lambda: None
        )
        note_btn.pack(side="left", padx=2)
        if has_note:
            Tooltip(note_btn, lambda e=entry: e["note"])

        ctk.CTkButton(
            act, text="Del", width=30, height=24,
            font=("Segoe UI", 10), corner_radius=4,
            fg_color="transparent", hover_color="#2a1010",
            text_color=DANGER,
            command=lambda: on_delete(entry)
        ).pack(side="left", padx=2)

    def _fmt(self, val):
        if val is None:
            return "—"
        v = float(val)
        return f"{v:.1f}" if v != int(v) else str(int(v))


# ══════════════════════════════════════════════════════════════════════════════
# DATA ENTRY TAB
# ══════════════════════════════════════════════════════════════════════════════

class DataEntryTab(ctk.CTkFrame):
    def __init__(self, parent, session):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self._filters = {"ramp": True, "stair": True, "up": True, "down": True, "flat": True}
        self._build()
        self.refresh()

    def _build(self):
        # ── toolbar ───────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=TOPBAR_BG, corner_radius=8)
        toolbar.pack(fill="x", padx=8, pady=(8,4))

        ctk.CTkLabel(toolbar, text="Filter:", text_color=TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(side="left", padx=(10,4), pady=6)

        self._filter_btns = {}
        for key in ("Ramp", "Stair", "Up", "Down"):
            btn = ctk.CTkButton(
                toolbar, text=key, width=64, height=28,
                font=("Segoe UI", 11),
                command=lambda k=key.lower(): self._toggle_filter(k)
            )
            btn.pack(side="left", padx=3, pady=6)
            self._filter_btns[key.lower()] = btn

        ctk.CTkButton(
            toolbar, text="+ Add Entry", width=110, height=28,
            font=("Segoe UI", 11, "bold"),
            command=self._open_add
        ).pack(side="right", padx=10, pady=6)

        # ── header ────────────────────────────────────────────────────────────
        self._hdr_container = ctk.CTkFrame(self, fg_color="transparent")
        self._hdr_container.pack(fill="x", padx=8)

        # ── scrollable table ─────────────────────────────────────────────────
        self._table = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._table.pack(fill="both", expand=True, padx=8, pady=(0,8))

    def _toggle_filter(self, key):
        self._filters[key] = not self._filters[key]
        # flat follows up/down — just keep it always on for simplicity
        btn = self._filter_btns.get(key)
        if btn:
            active = self._filters[key]
            if active:
                btn.configure(text=key.capitalize(), text_color=TEXT_MAIN, fg_color=ACCENT)
            else:
                btn.configure(text=f"̶{key.capitalize()}", text_color=TEXT_MUTED, fg_color="#333")
        self.refresh()

    def refresh(self):
        # Clear header
        for w in self._hdr_container.winfo_children():
            w.destroy()
        # Clear table
        for w in self._table.winfo_children():
            w.destroy()

        # Update filter button appearances
        for key, btn in self._filter_btns.items():
            active = self._filters[key]
            btn.configure(
                text=key.capitalize(),
                text_color=TEXT_MAIN if active else TEXT_MUTED,
                fg_color=ACCENT if active else "#2a2a3a"
            )

        all_entries = db_get_entries(self.session["id"])

        def visible(e):
            type_ok = self._filters.get(e["type"].lower(), True)
            dir_ok  = self._filters.get(e["direction"].lower(), True)
            return type_ok and dir_ok

        entries = [e for e in all_entries if visible(e)]

        EntryRow.header(self._hdr_container)

        if not entries:
            ctk.CTkLabel(self._table, text="No entries yet. Use '+ Add Entry' to add data.",
                         text_color=TEXT_MUTED, font=("Segoe UI", 12)).pack(pady=30)
            return

        for i, entry in enumerate(entries, 1):
            EntryRow(self._table, i, entry,
                     on_edit=self._open_edit,
                     on_delete=self._delete_entry)

    def _open_add(self):
        EntryModal(self, self.session["id"], on_save=self.refresh)

    def _open_edit(self, entry):
        EntryModal(self, self.session["id"], on_save=self.refresh, entry=entry)

    def _delete_entry(self, entry):
        if messagebox.askyesno("Delete entry",
                               f"Delete entry #{entry['id']}?",
                               parent=self):
            db_delete_entry(entry["id"])
            self.refresh()


# ══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION TAB
# ══════════════════════════════════════════════════════════════════════════════

class VisualizationTab(ctk.CTkFrame):
    X_OPTIONS = {
        "Encoder distance (mm)": "encoder_dist_mm",
        "Duration (ms)":         "duration_ms",
        "Gyro variance":         "gyro_variance",
        "Angle mean (°)":        "angle_mean",
        "Angle median (°)":      "angle_median",
    }

    def __init__(self, parent, session):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self._build()

    def _build(self):
        if not MPL_AVAILABLE:
            ctk.CTkLabel(self, text="matplotlib not installed. Run:\n  pip install matplotlib",
                         font=("Segoe UI", 13), text_color=TEXT_MUTED).pack(expand=True)
            return

        ctrl = ctk.CTkFrame(self, fg_color=TOPBAR_BG, corner_radius=8)
        ctrl.pack(fill="x", padx=8, pady=(8,4))
        ctk.CTkLabel(ctrl, text="X-axis:", text_color=TEXT_MUTED).pack(side="left", padx=(12,6), pady=6)
        self.x_var = ctk.StringVar(value=list(self.X_OPTIONS.keys())[0])
        ctk.CTkOptionMenu(ctrl, variable=self.x_var,
                          values=list(self.X_OPTIONS.keys()),
                          command=lambda _: self._redraw_plots()).pack(side="left", pady=6)

        self._fig_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._fig_frame.pack(fill="both", expand=True, padx=8, pady=(0,8))
        self._redraw_plots()

    def _redraw_plots(self):
        if not MPL_AVAILABLE:
            return
        for w in self._fig_frame.winfo_children():
            w.destroy()

        x_col  = self.X_OPTIONS[self.x_var.get()]
        x_label = self.x_var.get()
        y_col  = "actual_dist_mm"
        entries = db_get_entries(self.session["id"])

        fig = Figure(figsize=(9, 6), facecolor="#1a1a2e")
        subplots = [
            ("ramp",  "up",   "Ramp — Up",   "#4f8ef7"),
            ("ramp",  "down", "Ramp — Down", "#e05555"),
            ("stair", "up",   "Stair — Up",  "#50c87a"),
            ("stair", "down", "Stair — Down","#f7a94f"),
        ]
        axes_bg = "#1e1e2e"

        for i, (etype, edir, title, color) in enumerate(subplots):
            ax = fig.add_subplot(2, 2, i+1, facecolor=axes_bg)
            subset = [e for e in entries
                      if e["type"].lower() == etype and e["direction"].lower() == edir]
            xs = [e[x_col] for e in subset if e[x_col] is not None and e[y_col] is not None]
            ys = [e[y_col] for e in subset if e[x_col] is not None and e[y_col] is not None]

            if xs:
                ax.scatter(xs, ys, color=color, alpha=0.8, s=48, edgecolors="none")
            else:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                        ha="center", va="center", color=TEXT_MUTED, fontsize=10)

            ax.set_title(title, color=TEXT_MAIN, fontsize=11, pad=6)
            ax.set_xlabel(x_label, color=TEXT_MUTED, fontsize=8)
            ax.set_ylabel("Actual dist. (mm)", color=TEXT_MUTED, fontsize=8)
            ax.tick_params(colors=TEXT_MUTED, labelsize=8)
            for spine in ax.spines.values():
                spine.set_edgecolor(BORDER_COLOR)

        fig.tight_layout(pad=2.5)
        canvas = FigureCanvasTkAgg(fig, master=self._fig_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class SessionScreen(ctk.CTkFrame):
    def __init__(self, parent, session, on_back):
        super().__init__(parent, fg_color="transparent")
        self.session  = session
        self.on_back  = on_back
        self._build()

    def _build(self):
        # ── topbar ────────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self, fg_color=TOPBAR_BG, height=58, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        ctk.CTkButton(
            topbar, text="← Back", width=90, height=32,
            font=("Segoe UI", 11),
            fg_color="transparent", border_width=1, border_color=BORDER_COLOR,
            hover_color=CARD_BG,
            command=self.on_back
        ).pack(side="left", padx=14, pady=12)

        # vertical divider
        ctk.CTkFrame(topbar, fg_color=BORDER_COLOR, width=1).pack(
            side="left", fill="y", pady=10)

        info = ctk.CTkFrame(topbar, fg_color="transparent")
        info.pack(side="left", padx=14)
        ctk.CTkLabel(
            info, text=self.session["name"],
            font=("Segoe UI", 15, "bold"), text_color=TEXT_MAIN
        ).pack(anchor="w")
        sub = f"📅  {self.session['date']}"
        if self.session["location"]:
            sub += f"     📍  {self.session['location']}"
        ctk.CTkLabel(info, text=sub, font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(anchor="w")

        # accent line at bottom of topbar
        ctk.CTkFrame(self, fg_color=ACCENT, height=2, corner_radius=0).pack(fill="x")

        # ── tab view ──────────────────────────────────────────────────────────
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)
        tabs.add("Data Entry")
        tabs.add("Visualization")

        DataEntryTab(tabs.tab("Data Entry"), self.session).pack(fill="both", expand=True)
        VisualizationTab(tabs.tab("Visualization"), self.session).pack(fill="both", expand=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION CARD
# ══════════════════════════════════════════════════════════════════════════════

class SessionCard(ctk.CTkFrame):
    def __init__(self, parent, session, on_click, on_edit):
        super().__init__(parent, fg_color=CARD_BG, corner_radius=12,
                         border_width=1, border_color=BORDER_COLOR,
                         width=210, height=120, cursor="hand2")
        self.pack_propagate(False)
        self.session  = session
        self._onclick = on_click

        # Coloured accent strip at top
        strip = ctk.CTkFrame(self, fg_color=ACCENT, height=3, corner_radius=0)
        strip.place(relx=0, rely=0, relwidth=1)

        # Edit button — top-right corner, does NOT propagate click to card
        edit_btn = ctk.CTkButton(
            self, text="···", width=30, height=22,
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color=CARD_BG_HOVER,
            text_color=TEXT_MUTED, corner_radius=6,
            command=lambda: on_edit(session)
        )
        edit_btn.place(relx=1.0, x=-6, y=6, anchor="ne")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(x=14, y=14, relwidth=0.75)

        ctk.CTkLabel(inner, text=session["name"],
                     font=("Segoe UI", 13, "bold"),
                     text_color=TEXT_MAIN,
                     wraplength=150, anchor="w", justify="left").pack(anchor="w")

        meta = f"📅  {session['date']}"
        if session["location"]:
            meta += f"     📍  {session['location']}"
        ctk.CTkLabel(inner, text=meta,
                     font=("Segoe UI", 9),
                     text_color=TEXT_MUTED, anchor="w").pack(anchor="w", pady=(4,0))

        # Bind click/hover to everything except the edit button
        def _bind_click(w):
            if w is edit_btn:
                return
            w.bind("<Button-1>", lambda _: on_click(session))
            w.bind("<Enter>",    lambda _: self._hover(True))
            w.bind("<Leave>",    lambda _: self._hover(False))
            for child in w.winfo_children():
                _bind_click(child)

        _bind_click(self)

    def _hover(self, on):
        self.configure(
            fg_color=CARD_BG_HOVER if on else CARD_BG,
            border_color=BORDER_HOVER if on else BORDER_COLOR
        )


class NewSessionCard(ctk.CTkFrame):
    def __init__(self, parent, on_click):
        super().__init__(parent, fg_color="transparent", corner_radius=12,
                         border_width=1, border_color=BORDER_COLOR,
                         width=210, height=120, cursor="hand2")
        self.pack_propagate(False)
        self._onclick = on_click

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="+",
                     font=("Segoe UI", 30, "bold"),
                     text_color=ACCENT).pack()
        ctk.CTkLabel(inner, text="New Session",
                     font=("Segoe UI", 11),
                     text_color=TEXT_SECONDARY).pack(pady=(2,0))

        def _bind(w):
            w.bind("<Button-1>", lambda _: on_click())
            w.bind("<Enter>",    lambda _: self._hover(True))
            w.bind("<Leave>",    lambda _: self._hover(False))
            for child in w.winfo_children():
                _bind(child)

        _bind(self)

    def _hover(self, on):
        self.configure(
            fg_color=CARD_BG if on else "transparent",
            border_color=BORDER_HOVER if on else BORDER_COLOR
        )


# ══════════════════════════════════════════════════════════════════════════════
# HOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class HomeScreen(ctk.CTkFrame):
    COLS = 4

    def __init__(self, parent, on_open_session):
        super().__init__(parent, fg_color="transparent")
        self.on_open_session = on_open_session
        self._build()
        self.refresh()

    def _build(self):
        self.configure(fg_color=APP_BG)

        # ── hero banner (image + title overlay) ───────────────────────────────
        self._banner_frame = ctk.CTkFrame(self, fg_color="#0b0d14",
                                          height=BANNER_H, corner_radius=0)
        self._banner_frame.pack(fill="x")
        self._banner_frame.pack_propagate(False)
        self._load_banner()

        # Title overlay drawn as tk widgets on top of the banner canvas
        overlay = ctk.CTkFrame(self._banner_frame, fg_color="transparent")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        title_block = ctk.CTkFrame(overlay, fg_color="transparent")
        title_block.place(relx=0.5, rely=0.82, anchor="center")

        ctk.CTkLabel(
            title_block,
            text="Ramp Data Collection Tool",
            font=("Segoe UI", 22, "bold"),
            text_color="#ffffff",
        ).pack()
        ctk.CTkLabel(
            title_block,
            text="RoboCup Rescue Maze  ·  Ramp & Stair Traversal",
            font=("Segoe UI", 11),
            text_color="#aab4c8",
        ).pack(pady=(2, 0))

        # thin gradient separator line
        sep = ctk.CTkFrame(self, fg_color=ACCENT, height=2, corner_radius=0)
        sep.pack(fill="x")

        # ── main content ──────────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(content, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(18, 6))
        ctk.CTkLabel(hdr, text="SESSIONS",
                     font=("Segoe UI", 11, "bold"),
                     text_color=TEXT_MUTED).pack(side="left")

        self._grid_scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self._grid_scroll.pack(fill="x", padx=16, pady=(0, 4))

        # ── maze picture ──────────────────────────────────────────────────────
        self._maze_frame = ctk.CTkFrame(content, fg_color="transparent")
        self._maze_frame.pack(fill="both", expand=True, padx=16, pady=(8, 4))
        self._load_maze_picture()

        # ── footer ────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Made with ♥ by Florian Wiesner (and Claude Code)",
                     font=("Segoe UI", 9), text_color=TEXT_MUTED).pack(pady=(0, 6))

    def _load_banner(self):
        # Clear existing
        for w in self._banner_frame.winfo_children():
            w.destroy()
        if PIL_AVAILABLE and os.path.exists(BANNER_PATH):
            try:
                img = Image.open(BANNER_PATH)
                # Will be resized dynamically on configure event
                self._pil_img = img
                lbl = ctk.CTkLabel(self._banner_frame, text="")
                lbl.pack(fill="both", expand=True)
                self._banner_label = lbl
                self._banner_frame.bind("<Configure>", self._resize_banner)
                self._resize_banner()
                return
            except Exception:
                pass
        # Fallback
        ctk.CTkLabel(self._banner_frame, text="",
                     fg_color="#3a3a5a").pack(fill="both", expand=True)

    def _resize_banner(self, event=None):
        if not hasattr(self, "_pil_img") or not hasattr(self, "_banner_label"):
            return
        frame_w = self._banner_frame.winfo_width()
        if frame_w < 10:
            return
        H = BANNER_H
        orig_w, orig_h = self._pil_img.size
        # Scale so the image covers the full width, crop height to 170
        scale = frame_w / orig_w
        new_w = frame_w
        new_h = int(orig_h * scale)
        if new_h < H:
            # Image is too short after width-fit → scale to height instead
            scale = H / orig_h
            new_w = int(orig_w * scale)
            new_h = H
        resized = self._pil_img.resize((new_w, new_h), Image.LANCZOS)
        # Centre-crop to frame_w × H
        left = (new_w - frame_w) // 2
        top  = (new_h - H) // 2
        cropped = resized.crop((left, top, left + frame_w, top + H))
        self._ctk_img = ctk.CTkImage(light_image=cropped, dark_image=cropped, size=(frame_w, H))
        self._banner_label.configure(image=self._ctk_img, text="")

    # ── maze picture ──────────────────────────────────────────────────────────
    def _load_maze_picture(self):
        team_path = TEAM_PATH
        if not PIL_AVAILABLE or not os.path.exists(team_path):
            return
        try:
            self._team_pil = Image.open(team_path)
            self._team_label = ctk.CTkLabel(self._maze_frame, text="")
            self._team_label.pack(fill="both", expand=True)
            self._maze_frame.bind("<Configure>", self._resize_maze)
            self.after(50, self._resize_maze)
        except Exception:
            pass

    def _resize_maze(self, event=None):
        if not hasattr(self, "_team_pil") or not hasattr(self, "_team_label"):
            return
        fw = self._maze_frame.winfo_width()
        fh = self._maze_frame.winfo_height()
        if fw < 10 or fh < 10:
            return
        orig_w, orig_h = self._team_pil.size
        # Fit inside frame keeping aspect ratio
        scale = min(fw / orig_w, fh / orig_h)
        nw, nh = int(orig_w * scale), int(orig_h * scale)
        resized = self._team_pil.resize((nw, nh), Image.LANCZOS)
        self._maze_ctk = ctk.CTkImage(light_image=resized, dark_image=resized,
                                      size=(nw, nh))
        self._team_label.configure(image=self._maze_ctk, text="")

    def refresh(self):
        for w in self._grid_scroll.winfo_children():
            w.destroy()

        sessions = db_get_sessions()
        all_items = [None] + list(sessions)  # None = "New Session" placeholder

        row_frame = None
        for idx, item in enumerate(all_items):
            col = idx % self.COLS
            if col == 0:
                row_frame = ctk.CTkFrame(self._grid_scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=6)

            if item is None:
                card = NewSessionCard(row_frame, on_click=self._new_session)
            else:
                card = SessionCard(row_frame, item,
                                   on_click=lambda s=item: self.on_open_session(s),
                                   on_edit=lambda s=item: self._edit_session(s))
            card.pack(side="left", padx=8)

    def _new_session(self):
        NewSessionModal(self, on_save=self._on_session_created)

    def _edit_session(self, session):
        EditSessionModal(self, session,
                         on_save=self.refresh,
                         on_delete=self.refresh)

    def _on_session_created(self, session_id):
        self.refresh()
        with get_conn() as conn:
            s = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if s:
            # Defer navigation so the current call stack unwinds first
            self.after(50, lambda: self.on_open_session(s))


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()
