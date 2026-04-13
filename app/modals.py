"""
Modal dialogs: NewSessionModal, EditSessionModal, EntryModal.
"""

import datetime
import customtkinter as ctk
from tkinter import messagebox

from .constants import BORDER_COLOR, DANGER, TEXT_MUTED
from .database  import (db_create_session, db_update_session, db_delete_session,
                        db_create_entry, db_update_entry)
from .helpers   import direction_from_angle, to_float_or_none, to_int_or_none
from .widgets   import NumericEntry


# ── New Session ────────────────────────────────────────────────────────────────

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
        ctk.CTkLabel(self, text="New Session",
                     font=("Segoe UI", 16, "bold")).pack(pady=(20, 12))

        ctk.CTkLabel(self, text="Name *", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.name_entry = ctk.CTkEntry(self, placeholder_text="e.g. Test Run 1")
        self.name_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Date *", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.date_entry = ctk.CTkEntry(self)
        self.date_entry.insert(0, datetime.date.today().isoformat())
        self.date_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Location", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.loc_entry = ctk.CTkEntry(self, placeholder_text="e.g. Lab A")
        self.loc_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Notes", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.notes_box = ctk.CTkTextbox(self, height=60)
        self.notes_box.pack(fill="x", padx=24, pady=6)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(10, 20))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Save",
                      command=self._save).pack(side="left", expand=True, fill="x")

    def _save(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        if not name:
            messagebox.showerror("Missing field", "Session name is required.", parent=self)
            return
        if not date:
            messagebox.showerror("Missing field", "Date is required.", parent=self)
            return
        sid = db_create_session(name, date, self.loc_entry.get().strip(),
                                self.notes_box.get("1.0", "end").strip())
        self.destroy()
        self.on_save(sid)


# ── Edit / Delete Session ──────────────────────────────────────────────────────

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

        ctk.CTkLabel(self, text="Name *", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, self.session["name"] or "")
        self.name_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Date *", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.date_entry = ctk.CTkEntry(self)
        self.date_entry.insert(0, self.session["date"] or "")
        self.date_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Location", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.loc_entry = ctk.CTkEntry(self)
        self.loc_entry.insert(0, self.session["location"] or "")
        self.loc_entry.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Notes", anchor="w").pack(fill="x", padx=24, pady=(4, 0))
        self.notes_box = ctk.CTkTextbox(self, height=80)
        self.notes_box.pack(fill="x", padx=24, pady=6)
        if self.session["notes"]:
            self.notes_box.insert("1.0", self.session["notes"])

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(10, 6))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Save",
                      command=self._save).pack(side="left", expand=True, fill="x")

        ctk.CTkFrame(self, fg_color=BORDER_COLOR, height=1).pack(fill="x", padx=24, pady=(8, 0))
        ctk.CTkButton(self, text="Delete Session",
                      fg_color="transparent", border_width=1,
                      border_color=DANGER, text_color=DANGER,
                      hover_color="#2a1010",
                      command=self._delete).pack(fill="x", padx=24, pady=(8, 16))

    def _save(self):
        name = self.name_entry.get().strip()
        date = self.date_entry.get().strip()
        if not name:
            messagebox.showerror("Missing field", "Session name is required.", parent=self)
            return
        if not date:
            messagebox.showerror("Missing field", "Date is required.", parent=self)
            return
        db_update_session(self.session["id"], name, date,
                          self.loc_entry.get().strip(),
                          self.notes_box.get("1.0", "end").strip())
        self.destroy()
        self.on_save()

    def _delete(self):
        if messagebox.askyesno(
            "Delete Session",
            f"Delete \"{self.session['name']}\" and ALL its entries?\nThis cannot be undone.",
            parent=self,
        ):
            db_delete_session(self.session["id"])
            self.destroy()
            self.on_delete()


# ── Add / Edit Entry ───────────────────────────────────────────────────────────

class EntryModal(ctk.CTkToplevel):
    def __init__(self, parent, session_id: int, on_save, entry=None):
        super().__init__(parent)
        self.title("Edit Entry" if entry else "Add Entry")
        self.geometry("460x540")
        self.resizable(False, False)
        self.grab_set()
        self.session_id = session_id
        self.on_save    = on_save
        self.entry      = entry
        self._build()
        if entry:
            self._populate(entry)

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(scroll, text="Type *", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.type_var   = ctk.StringVar(value="Ramp")
        self.type_combo = ctk.CTkOptionMenu(scroll, variable=self.type_var,
                                            values=["Ramp", "Stair"])
        self.type_combo.pack(fill="x", padx=20, pady=(2, 0))

        ctk.CTkLabel(scroll, text="Direction (auto)", anchor="w").pack(fill="x", padx=20, pady=(6, 0))
        self.dir_label = ctk.CTkLabel(scroll, text="—", anchor="w", text_color=TEXT_MUTED)
        self.dir_label.pack(fill="x", padx=20, pady=(2, 0))

        ctk.CTkLabel(scroll, text="Fields (ground truth) *", anchor="w").pack(fill="x", padx=20, pady=(6, 0))
        self.fields_entry = NumericEntry(scroll, placeholder_text="1 or 2")
        self.fields_entry.pack(fill="x", padx=20, pady=(2, 0))

        self.actual_entry    = self._num_row(scroll, "Actual dist. (mm)")
        self.encoder_entry   = self._num_row(scroll, "Encoder dist. (mm)")
        self.duration_entry  = self._num_row(scroll, "Duration (ms)")
        self.gyro_entry      = self._num_row(scroll, "Gyro variance")
        self.angle_mean_entry = self._num_row(scroll, "Angle mean (°)")
        self.angle_med_entry  = self._num_row(scroll, "Angle median (°)")

        self.angle_mean_entry._var.trace_add("write", self._update_dir_label)

        ctk.CTkLabel(scroll, text="Note (optional)", anchor="w").pack(fill="x", padx=20, pady=(6, 0))
        self.note_box = ctk.CTkTextbox(scroll, height=70)
        self.note_box.pack(fill="x", padx=20, pady=(2, 6))

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(4, 12))
        ctk.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(btn_row, text="Save",
                      command=self._save).pack(side="left", expand=True, fill="x")

    def _num_row(self, parent, label: str) -> NumericEntry:
        ctk.CTkLabel(parent, text=label, anchor="w").pack(fill="x", padx=20, pady=(6, 0))
        e = NumericEntry(parent)
        e.pack(fill="x", padx=20, pady=(2, 0))
        return e

    def _update_dir_label(self, *_):
        direction = direction_from_angle(self.angle_mean_entry.get())
        self.dir_label.configure(text=direction.capitalize())

    def _populate(self, e):
        self.type_var.set(e["type"].capitalize())
        for widget, key in [
            (self.fields_entry,     "fields"),
            (self.actual_entry,     "actual_dist_mm"),
            (self.encoder_entry,    "encoder_dist_mm"),
            (self.duration_entry,   "duration_ms"),
            (self.gyro_entry,       "gyro_variance"),
            (self.angle_mean_entry, "angle_mean"),
            (self.angle_med_entry,  "angle_median"),
        ]:
            if e[key] is not None:
                widget.delete(0, "end")
                widget.insert(0, str(e[key]))
        if e["note"]:
            self.note_box.insert("1.0", e["note"])
        self._update_dir_label()

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
