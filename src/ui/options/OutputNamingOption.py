"""Output naming UI: preset dropdown + custom template input."""

from __future__ import annotations

from tkinter import StringVar
from tkinter.ttk import Combobox, Frame, Label

import i18n
from conversion_setting import config
from output_naming import PRESETS, DEFAULT_TEMPLATE


class OutputNamingOption(Frame):
    """Combobox with presets + Entry for custom template, mutually linked."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._label = Label(self, text=i18n.get("output_label"))
        self._label.grid(row=0, column=0, sticky="w", padx=(0, 4))

        # Preset dropdown — includes named presets + "Custom..." option
        self._preset_values = PRESETS + [i18n.get("custom_template")]
        self._preset_var = StringVar(value=DEFAULT_TEMPLATE)
        self._preset_combo = Combobox(
            self,
            textvariable=self._preset_var,
            values=self._preset_values,
            state="readonly",
            width=22,
        )
        self._preset_combo.grid(row=0, column=1, padx=(0, 8))
        self._preset_combo.bind("<<ComboboxSelected>>", self._on_preset_select)

        # Template entry — for custom input
        self._tmpl_label = Label(self, text=i18n.get("template_label"))
        self._tmpl_label.grid(row=0, column=2, sticky="w", padx=(0, 4))

        self._tmpl_var = StringVar(value=DEFAULT_TEMPLATE)
        self._tmpl_entry = Combobox(
            self,
            textvariable=self._tmpl_var,
            values=PRESETS,
            width=24,
        )
        self._tmpl_entry.grid(row=0, column=3)
        self._tmpl_var.trace_add("write", self._on_template_change)

    def _on_preset_select(self, _event=None) -> None:
        """When a preset is selected, update the template entry."""
        selected = self._preset_var.get()
        if selected == i18n.get("custom_template"):
            # "Custom" selected — let user type freely, don't overwrite
            self._tmpl_entry.focus_set()
            return
        self._tmpl_var.set(selected)
        config.output_template = selected

    def _on_template_change(self, *_args) -> None:
        """When template text changes, sync to config."""
        config.output_template = self._tmpl_var.get()

    @property
    def template(self) -> str:
        """Current output template string."""
        return self._tmpl_var.get()

    def refresh_language(self) -> None:
        self._label.configure(text=i18n.get("output_label"))
        self._tmpl_label.configure(text=i18n.get("template_label"))
        # If currently showing old "Custom..." label, update to new language
        old_custom = self._preset_values[-1]
        self._preset_values = PRESETS + [i18n.get("custom_template")]
        self._preset_combo.configure(values=self._preset_values)
        if self._preset_var.get() == old_custom:
            self._preset_var.set(i18n.get("custom_template"))
