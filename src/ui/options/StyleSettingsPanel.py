"""Collapsible advanced style settings panel for SRT/SUB → ASS conversion."""

from __future__ import annotations

from tkinter import StringVar, colorchooser
from tkinter.ttk import Button, Entry, Frame, Label, LabelFrame, Separator

import i18n
from conversion_setting import config


class StyleSettingsPanel(LabelFrame):
    """Collapsible panel for font/size/color/outline/FPS settings.

    Always present in the grid (never dynamically created/destroyed).
    When input is ASS/SSA, all children are disabled and shown in gray.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, text=i18n.get("advanced_style"), **kwargs)
        self._expanded = False
        self._enabled = True
        self._children_widgets: list = []

        # Toggle button (▶ / ▼)
        self._toggle_btn = Button(self, text="\u25b6 " + i18n.get("advanced_style"),
                                  command=self._toggle, style="Toolbutton.TButton")
        self._toggle_btn.grid(row=0, column=0, columnspan=4, sticky="w", padx=2, pady=2)

        # Content frame (hidden by default)
        self._content = Frame(self)

        # --- Row 0: Font name + Font size ---
        self._lbl_font = Label(self._content, text=i18n.get("font_label"))
        self._lbl_font.grid(row=0, column=0, sticky="w", padx=(4, 2), pady=2)
        self._font_var = StringVar(value=config.style.font_name)
        self._font_entry = Entry(self._content, textvariable=self._font_var, width=18)
        self._font_entry.grid(row=0, column=1, padx=2, pady=2)
        self._font_var.trace_add("write", lambda *_: self._sync("font_name", self._font_var.get()))

        self._lbl_size = Label(self._content, text=i18n.get("font_size_label"))
        self._lbl_size.grid(row=0, column=2, sticky="w", padx=(8, 2), pady=2)
        self._size_var = StringVar(value=str(config.style.font_size))
        self._size_entry = Entry(self._content, textvariable=self._size_var, width=5)
        self._size_entry.grid(row=0, column=3, padx=2, pady=2)
        self._size_var.trace_add("write", lambda *_: self._sync_int("font_size", self._size_var.get()))

        # --- Row 1: Primary color + Outline color ---
        self._lbl_color = Label(self._content, text=i18n.get("primary_color_label"))
        self._lbl_color.grid(row=1, column=0, sticky="w", padx=(4, 2), pady=2)
        self._color_btn = Button(self._content, text="\u25a0 White", width=10,
                                 command=lambda: self._pick_color("primary_color"))
        self._color_btn.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        self._lbl_outline = Label(self._content, text=i18n.get("outline_color_label"))
        self._lbl_outline.grid(row=1, column=2, sticky="w", padx=(8, 2), pady=2)
        self._outline_btn = Button(self._content, text="\u25a0 Black", width=10,
                                   command=lambda: self._pick_color("outline_color"))
        self._outline_btn.grid(row=1, column=3, padx=2, pady=2, sticky="w")

        # --- Row 2: Outline width + Shadow depth ---
        self._lbl_ow = Label(self._content, text=i18n.get("outline_width_label"))
        self._lbl_ow.grid(row=2, column=0, sticky="w", padx=(4, 2), pady=2)
        self._ow_var = StringVar(value=str(config.style.outline_width))
        self._ow_entry = Entry(self._content, textvariable=self._ow_var, width=5)
        self._ow_entry.grid(row=2, column=1, padx=2, pady=2, sticky="w")
        self._ow_var.trace_add("write", lambda *_: self._sync_float("outline_width", self._ow_var.get()))

        self._lbl_sh = Label(self._content, text=i18n.get("shadow_depth_label"))
        self._lbl_sh.grid(row=2, column=2, sticky="w", padx=(8, 2), pady=2)
        self._sh_var = StringVar(value=str(config.style.shadow_depth))
        self._sh_entry = Entry(self._content, textvariable=self._sh_var, width=5)
        self._sh_entry.grid(row=2, column=3, padx=2, pady=2, sticky="w")
        self._sh_var.trace_add("write", lambda *_: self._sync_float("shadow_depth", self._sh_var.get()))

        # --- Row 3: FPS (only for SUB format) ---
        self._lbl_fps = Label(self._content, text=i18n.get("fps_label"))
        self._lbl_fps.grid(row=3, column=0, sticky="w", padx=(4, 2), pady=2)
        self._fps_var = StringVar(value=str(config.style.fps))
        self._fps_entry = Entry(self._content, textvariable=self._fps_var, width=8)
        self._fps_entry.grid(row=3, column=1, padx=2, pady=2, sticky="w")
        self._fps_var.trace_add("write", lambda *_: self._sync_float("fps", self._fps_var.get()))
        self._fps_desc = Label(self._content, text=i18n.get("fps_desc"),
                               foreground="gray")
        self._fps_desc.grid(row=3, column=2, columnspan=2, sticky="w", padx=(8, 2))

        # Collect all interactive children for enable/disable
        self._children_widgets = [
            self._font_entry, self._size_entry,
            self._color_btn, self._outline_btn,
            self._ow_entry, self._sh_entry,
            self._fps_entry,
        ]

        # Hint label (shown when disabled)
        self._hint_label = Label(self, text=i18n.get("style_disabled_hint"),
                                 foreground="gray")

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        if self._expanded:
            arrow = "\u25bc"
            self._content.grid(row=1, column=0, columnspan=4, sticky="ew")
        else:
            arrow = "\u25b6"
            self._content.grid_forget()
        self._toggle_btn.configure(text=f"{arrow} {i18n.get('advanced_style')}")
        self._refresh_hint()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all settings widgets."""
        self._enabled = enabled
        state = "normal" if enabled else "disabled"
        for w in self._children_widgets:
            w.configure(state=state)
        self._refresh_hint()

    def _refresh_hint(self) -> None:
        """Show hint label when disabled, regardless of expanded state."""
        if not self._enabled:
            self._hint_label.grid(row=2, column=0, columnspan=4, sticky="w", padx=4)
        else:
            self._hint_label.grid_forget()

    def _sync(self, attr: str, value: str) -> None:
        setattr(config.style, attr, value)

    def _sync_int(self, attr: str, value: str) -> None:
        try:
            setattr(config.style, attr, int(value))
        except ValueError:
            pass

    def _sync_float(self, attr: str, value: str) -> None:
        try:
            setattr(config.style, attr, float(value))
        except ValueError:
            pass

    def _pick_color(self, attr: str) -> None:
        """Open a color picker dialog and update the style attribute."""
        title_key = "primary_color_label" if attr == "primary_color" else "outline_color_label"
        result = colorchooser.askcolor(title=i18n.get(title_key))
        if result[1] is None:
            return
        hex_rgb = result[1].lstrip("#")
        r, g, b = hex_rgb[0:2], hex_rgb[2:4], hex_rgb[4:6]
        ass_color = f"&H00{b}{g}{r}"
        setattr(config.style, attr, ass_color)

        # Update button label with color name
        btn = self._color_btn if attr == "primary_color" else self._outline_btn
        btn.configure(text=f"\u25a0 #{hex_rgb}")

    def refresh_language(self) -> None:
        arrow = "\u25bc" if self._expanded else "\u25b6"
        self.configure(text=i18n.get("advanced_style"))
        self._toggle_btn.configure(text=f"{arrow} {i18n.get('advanced_style')}")
        self._hint_label.configure(text=i18n.get("style_disabled_hint"))
        self._lbl_font.configure(text=i18n.get("font_label"))
        self._lbl_size.configure(text=i18n.get("font_size_label"))
        self._lbl_color.configure(text=i18n.get("primary_color_label"))
        self._lbl_outline.configure(text=i18n.get("outline_color_label"))
        self._lbl_ow.configure(text=i18n.get("outline_width_label"))
        self._lbl_sh.configure(text=i18n.get("shadow_depth_label"))
        self._lbl_fps.configure(text=i18n.get("fps_label"))
        self._fps_desc.configure(text=i18n.get("fps_desc"))
