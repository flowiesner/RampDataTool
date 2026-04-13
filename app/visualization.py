"""
Visualization tab: 2×2 scatter plot grid embedded via matplotlib.
"""

import customtkinter as ctk

from .constants import (TOPBAR_BG, TEXT_MUTED, TEXT_MAIN, BORDER_COLOR,
                        MPL_AVAILABLE)
from .database  import db_get_entries

if MPL_AVAILABLE:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class VisualizationTab(ctk.CTkFrame):
    X_OPTIONS = {
        "Encoder distance (mm)": "encoder_dist_mm",
        "Duration (ms)":         "duration_ms",
        "Gyro variance":         "gyro_variance",
        "Angle mean (°)":        "angle_mean",
        "Angle median (°)":      "angle_median",
    }

    _SUBPLOTS = [
        ("ramp",  "up",   "Ramp — Up",    "#4f8ef7"),
        ("ramp",  "down", "Ramp — Down",  "#e05555"),
        ("stair", "up",   "Stair — Up",   "#50c87a"),
        ("stair", "down", "Stair — Down", "#f7a94f"),
    ]

    def __init__(self, parent, session):
        super().__init__(parent, fg_color="transparent")
        self.session = session
        self._build()

    def _build(self):
        if not MPL_AVAILABLE:
            ctk.CTkLabel(self,
                         text="matplotlib not installed.\nRun:  pip install matplotlib",
                         font=("Segoe UI", 13),
                         text_color=TEXT_MUTED).pack(expand=True)
            return

        ctrl = ctk.CTkFrame(self, fg_color=TOPBAR_BG, corner_radius=8)
        ctrl.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(ctrl, text="X-axis:",
                     text_color=TEXT_MUTED).pack(side="left", padx=(12, 6), pady=6)
        self.x_var = ctk.StringVar(value=list(self.X_OPTIONS.keys())[0])
        ctk.CTkOptionMenu(ctrl, variable=self.x_var,
                          values=list(self.X_OPTIONS.keys()),
                          command=lambda _: self._redraw_plots()
                          ).pack(side="left", pady=6)

        self._fig_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._fig_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._redraw_plots()

    def _redraw_plots(self):
        for w in self._fig_frame.winfo_children():
            w.destroy()

        x_col   = self.X_OPTIONS[self.x_var.get()]
        x_label = self.x_var.get()
        y_col   = "actual_dist_mm"
        entries = db_get_entries(self.session["id"])

        fig    = Figure(figsize=(9, 6), facecolor="#1a1a2e")
        ax_bg  = "#1e1e2e"

        for i, (etype, edir, title, color) in enumerate(self._SUBPLOTS):
            ax = fig.add_subplot(2, 2, i + 1, facecolor=ax_bg)
            subset = [e for e in entries
                      if e["type"].lower() == etype
                      and e["direction"].lower() == edir]
            xs = [e[x_col] for e in subset
                  if e[x_col] is not None and e[y_col] is not None]
            ys = [e[y_col] for e in subset
                  if e[x_col] is not None and e[y_col] is not None]

            if xs:
                ax.scatter(xs, ys, color=color, alpha=0.8, s=48, edgecolors="none")
            else:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                        ha="center", va="center",
                        color=TEXT_MUTED, fontsize=10)

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
