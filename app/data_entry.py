"""
Data Entry tab: filter toolbar, scrollable entry table, row widget.
"""

import customtkinter as ctk
from tkinter import messagebox

from .constants import (CARD_BG, TOPBAR_BG, ACCENT, TEXT_MUTED, TEXT_MAIN, DANGER)
from .database  import db_get_entries, db_delete_entry
from .widgets   import Tooltip, make_badge
from .modals    import EntryModal


# ── Table row ──────────────────────────────────────────────────────────────────

class EntryRow(ctk.CTkFrame):
    COLS = [
        ("# ",           40),
        ("Type",         60),
        ("Dir.",         50),
        ("Fields",       52),
        ("Actual\n(mm)", 72),
        ("Encoder\n(mm)",72),
        ("Duration\n(ms)",76),
        ("Angle\nmean",  68),
        ("Angle\nmedian",72),
        ("Gyro\nvar.",   68),
        ("Actions",      90),
    ]

    @classmethod
    def header(cls, parent):
        hdr = ctk.CTkFrame(parent, fg_color=TOPBAR_BG, corner_radius=6)
        hdr.pack(fill="x", padx=4, pady=(0, 2))
        for title, w in cls.COLS:
            ctk.CTkLabel(hdr, text=title, width=w,
                         font=("Segoe UI", 10, "bold"),
                         text_color=TEXT_MUTED, anchor="w"
                         ).pack(side="left", padx=4, pady=4)

    def __init__(self, parent, index: int, entry, on_edit, on_delete):
        super().__init__(parent, fg_color=CARD_BG, corner_radius=6, height=34)
        self.pack(fill="x", padx=4, pady=2)
        self.pack_propagate(False)

        plain_vals = [
            str(index),
            None,                                    # Type  → badge
            None,                                    # Dir.  → badge
            str(entry["fields"] or ""),
            self._fmt(entry["actual_dist_mm"]),
            self._fmt(entry["encoder_dist_mm"]),
            self._fmt(entry["duration_ms"]),
            self._fmt(entry["angle_mean"]),
            self._fmt(entry["angle_median"]),
            self._fmt(entry["gyro_variance"]),
        ]
        for i, (val, (_, w)) in enumerate(zip(plain_vals, self.COLS[:-1])):
            if i == 1:
                make_badge(self, entry["type"], width=w).pack(side="left", padx=4)
            elif i == 2:
                make_badge(self, entry["direction"], width=w).pack(side="left", padx=4)
            else:
                ctk.CTkLabel(self, text=val, width=w, anchor="w",
                             font=("Segoe UI", 11)).pack(side="left", padx=4)

        # Actions
        act = ctk.CTkFrame(self, fg_color="transparent", width=90)
        act.pack(side="left", padx=2)
        act.pack_propagate(False)

        ctk.CTkButton(act, text="Edit", width=36, height=24,
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
            command=lambda: None,
        )
        note_btn.pack(side="left", padx=2)
        if has_note:
            Tooltip(note_btn, lambda e=entry: e["note"])

        ctk.CTkButton(act, text="Del", width=30, height=24,
                      font=("Segoe UI", 10), corner_radius=4,
                      fg_color="transparent", hover_color="#2a1010",
                      text_color=DANGER,
                      command=lambda: on_delete(entry)
                      ).pack(side="left", padx=2)

    @staticmethod
    def _fmt(val) -> str:
        if val is None:
            return "—"
        v = float(val)
        return f"{v:.1f}" if v != int(v) else str(int(v))


# ── Data Entry tab ─────────────────────────────────────────────────────────────

class DataEntryTab(ctk.CTkFrame):
    def __init__(self, parent, session):
        super().__init__(parent, fg_color="transparent")
        self.session  = session
        self._filters = {"ramp": True, "stair": True, "up": True,
                         "down": True, "flat": True}
        self._build()
        self.refresh()

    def _build(self):
        toolbar = ctk.CTkFrame(self, fg_color=TOPBAR_BG, corner_radius=8)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkLabel(toolbar, text="Filter:", text_color=TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(side="left", padx=(10, 4), pady=6)

        self._filter_btns: dict[str, ctk.CTkButton] = {}
        for key in ("Ramp", "Stair", "Up", "Down"):
            btn = ctk.CTkButton(toolbar, text=key, width=64, height=28,
                                font=("Segoe UI", 11),
                                command=lambda k=key.lower(): self._toggle_filter(k))
            btn.pack(side="left", padx=3, pady=6)
            self._filter_btns[key.lower()] = btn

        ctk.CTkButton(toolbar, text="+ Add Entry", width=110, height=28,
                      font=("Segoe UI", 11, "bold"),
                      command=self._open_add
                      ).pack(side="right", padx=10, pady=6)

        self._hdr_container = ctk.CTkFrame(self, fg_color="transparent")
        self._hdr_container.pack(fill="x", padx=8)

        self._table = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._table.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _toggle_filter(self, key: str):
        self._filters[key] = not self._filters[key]
        self.refresh()

    def refresh(self):
        for w in self._hdr_container.winfo_children():
            w.destroy()
        for w in self._table.winfo_children():
            w.destroy()

        for key, btn in self._filter_btns.items():
            active = self._filters[key]
            btn.configure(
                text=key.capitalize(),
                text_color=TEXT_MAIN if active else TEXT_MUTED,
                fg_color=ACCENT if active else "#2a2a3a",
            )

        all_entries = db_get_entries(self.session["id"])
        entries = [e for e in all_entries
                   if self._filters.get(e["type"].lower(), True)
                   and self._filters.get(e["direction"].lower(), True)]

        EntryRow.header(self._hdr_container)

        if not entries:
            ctk.CTkLabel(self._table,
                         text="No entries yet. Use '+ Add Entry' to add data.",
                         text_color=TEXT_MUTED,
                         font=("Segoe UI", 12)).pack(pady=30)
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
                               f"Delete entry #{entry['id']}?", parent=self):
            db_delete_entry(entry["id"])
            self.refresh()
