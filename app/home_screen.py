"""
Home screen: topbar, session card grid, team picture, footer.
"""

import os
import customtkinter as ctk

from .constants import (
    APP_BG, CARD_BG, CARD_BG_HOVER, TOPBAR_BG, ACCENT,
    TEXT_MUTED, TEXT_SECONDARY, TEXT_MAIN,
    BORDER_COLOR, BORDER_HOVER, TEAM_PATH, PIL_AVAILABLE,
)
from .database import db_get_sessions, db_get_session
from .modals   import NewSessionModal, EditSessionModal

if PIL_AVAILABLE:
    from PIL import Image


# ── Session card ───────────────────────────────────────────────────────────────

class SessionCard(ctk.CTkFrame):
    def __init__(self, parent, session, on_click, on_edit):
        super().__init__(parent, fg_color=CARD_BG, corner_radius=12,
                         border_width=1, border_color=BORDER_COLOR,
                         width=210, height=120, cursor="hand2")
        self.pack_propagate(False)

        ctk.CTkFrame(self, fg_color=ACCENT, height=3,
                     corner_radius=0).place(relx=0, rely=0, relwidth=1)

        edit_btn = ctk.CTkButton(
            self, text="···", width=30, height=22,
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color=CARD_BG_HOVER,
            text_color=TEXT_MUTED, corner_radius=6,
            command=lambda: on_edit(session),
        )
        edit_btn.place(relx=1.0, x=-6, y=6, anchor="ne")

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(x=14, y=14, relwidth=0.75)

        ctk.CTkLabel(inner, text=session["name"],
                     font=("Segoe UI", 13, "bold"), text_color=TEXT_MAIN,
                     wraplength=150, anchor="w", justify="left").pack(anchor="w")

        meta = f"  {session['date']}"
        if session["location"]:
            meta += f"       {session['location']}"
        ctk.CTkLabel(inner, text=meta,
                     font=("Segoe UI", 9), text_color=TEXT_MUTED,
                     anchor="w").pack(anchor="w", pady=(4, 0))

        def _bind(w):
            if w is edit_btn:
                return
            w.bind("<Button-1>", lambda _: on_click(session))
            w.bind("<Enter>",    lambda _: self._hover(True))
            w.bind("<Leave>",    lambda _: self._hover(False))
            for child in w.winfo_children():
                _bind(child)

        _bind(self)

    def _hover(self, on: bool):
        self.configure(
            fg_color=CARD_BG_HOVER if on else CARD_BG,
            border_color=BORDER_HOVER if on else BORDER_COLOR,
        )


class NewSessionCard(ctk.CTkFrame):
    def __init__(self, parent, on_click):
        super().__init__(parent, fg_color="transparent", corner_radius=12,
                         border_width=1, border_color=BORDER_COLOR,
                         width=210, height=120, cursor="hand2")
        self.pack_propagate(False)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(inner, text="+", font=("Segoe UI", 30, "bold"),
                     text_color=ACCENT).pack()
        ctk.CTkLabel(inner, text="New Session", font=("Segoe UI", 11),
                     text_color=TEXT_SECONDARY).pack(pady=(2, 0))

        def _bind(w):
            w.bind("<Button-1>", lambda _: on_click())
            w.bind("<Enter>",    lambda _: self._hover(True))
            w.bind("<Leave>",    lambda _: self._hover(False))
            for child in w.winfo_children():
                _bind(child)

        _bind(self)

    def _hover(self, on: bool):
        self.configure(
            fg_color=CARD_BG if on else "transparent",
            border_color=BORDER_HOVER if on else BORDER_COLOR,
        )


# ── Home screen ────────────────────────────────────────────────────────────────

class HomeScreen(ctk.CTkFrame):
    COLS = 4

    def __init__(self, parent, on_open_session):
        super().__init__(parent, fg_color="transparent")
        self.on_open_session = on_open_session
        self._build()
        self.refresh()

    def _build(self):
        self.configure(fg_color=APP_BG)

        # ── topbar ────────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self, fg_color=TOPBAR_BG, height=50, corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        ctk.CTkLabel(topbar, text="Ramp Data Collection Tool",
                     font=("Segoe UI", 16, "bold"),
                     text_color=TEXT_MAIN).pack(side="left", padx=20, pady=12)
        ctk.CTkFrame(self, fg_color=ACCENT, height=2, corner_radius=0).pack(fill="x")

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

        # ── team picture ──────────────────────────────────────────────────────
        self._team_frame = ctk.CTkFrame(content, fg_color="transparent")
        self._team_frame.pack(fill="both", expand=True, padx=16, pady=(8, 4))
        self._load_team_picture()

        # ── footer ────────────────────────────────────────────────────────────
        ctk.CTkLabel(self,
                     text="Made with \u2665 by Florian Wiesner (and Claude Code)",
                     font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(pady=(0, 6))

    # ── team picture ──────────────────────────────────────────────────────────

    def _load_team_picture(self):
        if not PIL_AVAILABLE or not os.path.exists(TEAM_PATH):
            return
        try:
            self._team_pil   = Image.open(TEAM_PATH)
            self._team_label = ctk.CTkLabel(self._team_frame, text="")
            self._team_label.pack(fill="both", expand=True)
            self._team_frame.bind("<Configure>", self._resize_team)
            self.after(50, self._resize_team)
        except Exception:
            pass

    def _resize_team(self, _event=None):
        if not hasattr(self, "_team_pil") or not hasattr(self, "_team_label"):
            return
        fw = self._team_frame.winfo_width()
        fh = self._team_frame.winfo_height()
        if fw < 10 or fh < 10:
            return
        ow, oh  = self._team_pil.size
        scale   = min(fw / ow, fh / oh)
        nw, nh  = int(ow * scale), int(oh * scale)
        resized = self._team_pil.resize((nw, nh), Image.LANCZOS)
        self._team_ctk = ctk.CTkImage(light_image=resized, dark_image=resized,
                                      size=(nw, nh))
        self._team_label.configure(image=self._team_ctk, text="")

    # ── session card grid ─────────────────────────────────────────────────────

    def refresh(self):
        for w in self._grid_scroll.winfo_children():
            w.destroy()

        all_items = [None] + list(db_get_sessions())
        row_frame = None
        for idx, item in enumerate(all_items):
            if idx % self.COLS == 0:
                row_frame = ctk.CTkFrame(self._grid_scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=6)
            if item is None:
                NewSessionCard(row_frame, on_click=self._new_session).pack(side="left", padx=8)
            else:
                SessionCard(
                    row_frame, item,
                    on_click=lambda s=item: self.on_open_session(s),
                    on_edit =lambda s=item: self._edit_session(s),
                ).pack(side="left", padx=8)

    def _new_session(self):
        NewSessionModal(self, on_save=self._on_session_created)

    def _edit_session(self, session):
        EditSessionModal(self, session,
                         on_save=self.refresh,
                         on_delete=self.refresh)

    def _on_session_created(self, session_id: int):
        self.refresh()
        s = db_get_session(session_id)
        if s:
            self.after(50, lambda: self.on_open_session(s))
