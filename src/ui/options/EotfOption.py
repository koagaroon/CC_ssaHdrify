import tkinter
from tkinter.ttk import Frame, Label, Combobox

import i18n
from conversion_setting import config

EOTF_OPTIONS = ["PQ", "HLG"]
_EOTF_DESC_KEYS = {"PQ": "eotf_pq_desc", "HLG": "eotf_hlg_desc"}


class EotfOption(Frame):
    def __init__(self, master=None, on_eotf_change=None, **kwargs):
        super().__init__(master, **kwargs)
        self._on_eotf_change = on_eotf_change
        self.columnconfigure(1, weight=1)

        self._label = Label(master=self, text=i18n.get("eotf_label"))
        self._label.grid(row=0, column=0, sticky=tkinter.W)

        self._dropdown = Combobox(self, state='readonly', values=EOTF_OPTIONS)
        self._dropdown.current(0)
        self._dropdown.grid(row=0, column=1, sticky=tkinter.EW)
        self._dropdown.bind("<<ComboboxSelected>>", self._on_select)

        self._desc = Label(master=self, text=i18n.get("eotf_pq_desc"),
                           wraplength=1, foreground="gray")
        self._desc.grid(row=1, column=0, columnspan=2, sticky=tkinter.EW, pady=(8, 0))
        # Dynamically adjust wraplength to match frame width
        self.bind("<Configure>", self._update_wraplength)

    def _update_wraplength(self, _event=None):
        # Set wraplength to frame width minus small padding
        width = self.winfo_width() - 10
        if width > 50:
            self._desc.configure(wraplength=width)

    def _on_select(self, _event=None):
        selected = self._dropdown.get()
        config.eotf = selected
        desc_key = _EOTF_DESC_KEYS.get(selected, "eotf_pq_desc")
        self._desc.configure(text=i18n.get(desc_key))
        # Notify sibling brightness frame via callback
        if self._on_eotf_change:
            self._on_eotf_change(selected)

    def refresh_language(self):
        self._label.configure(text=i18n.get("eotf_label"))
        selected = self._dropdown.get()
        desc_key = _EOTF_DESC_KEYS.get(selected, "eotf_pq_desc")
        self._desc.configure(text=i18n.get(desc_key))
        # Force wraplength recalculation after language change
        self.after(50, self._update_wraplength)
