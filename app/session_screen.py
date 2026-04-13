"""
Session screen: topbar with back button + tabbed Data Entry / Visualization.
"""

import customtkinter as ctk

from .constants      import TOPBAR_BG, ACCENT, BORDER_COLOR, CARD_BG, TEXT_MAIN, TEXT_MUTED
from .data_entry     import DataEntryTab
from .visualization  import VisualizationTab


class SessionScreen(ctk.CTkFrame):
    def __init__(self, parent, session, on_back):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self.on_back = on_back
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
            command=self.on_back,
        ).pack(side="left", padx=14, pady=12)

        ctk.CTkFrame(topbar, fg_color=BORDER_COLOR, width=1).pack(
            side="left", fill="y", pady=10)

        info = ctk.CTkFrame(topbar, fg_color="transparent")
        info.pack(side="left", padx=14)

        ctk.CTkLabel(info, text=self.session["name"],
                     font=("Segoe UI", 15, "bold"),
                     text_color=TEXT_MAIN).pack(anchor="w")

        sub = f"  {self.session['date']}"
        if self.session["location"]:
            sub += f"       {self.session['location']}"
        ctk.CTkLabel(info, text=sub,
                     font=("Segoe UI", 9),
                     text_color=TEXT_MUTED).pack(anchor="w")

        ctk.CTkFrame(self, fg_color=ACCENT, height=2, corner_radius=0).pack(fill="x")

        # ── tabs ──────────────────────────────────────────────────────────────
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)
        tabs.add("Data Entry")
        tabs.add("Visualization")

        DataEntryTab(tabs.tab("Data Entry"),
                     self.session).pack(fill="both", expand=True)
        VisualizationTab(tabs.tab("Visualization"),
                         self.session).pack(fill="both", expand=True)
