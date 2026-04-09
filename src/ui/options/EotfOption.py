import tkinter
from tkinter.ttk import Frame, Label, Combobox

import i18n
from conversion_setting import config

EOTF_OPTIONS = ["PQ", "HLG"]
_EOTF_DESC_KEYS = {"PQ": "eotf_pq_desc", "HLG": "eotf_hlg_desc"}


class EotfOption(Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)

        self._label = Label(master=self, text=i18n.get("eotf_label"))
        self._label.grid(row=0, column=0, sticky=tkinter.W)

        self._dropdown = Combobox(self, state='readonly', values=EOTF_OPTIONS)
        self._dropdown.current(0)
        self._dropdown.grid(row=0, column=1, sticky=tkinter.EW)
        self._dropdown.bind("<<ComboboxSelected>>", self._on_select)

        self._desc = Label(master=self, text=i18n.get("eotf_pq_desc"),
                           wraplength=300, foreground="gray")
        self._desc.grid(row=1, column=0, columnspan=2, sticky=tkinter.W, pady=(2, 0))

    def _on_select(self, _event=None):
        selected = self._dropdown.get()
        config.eotf = selected
        desc_key = _EOTF_DESC_KEYS.get(selected, "eotf_pq_desc")
        self._desc.configure(text=i18n.get(desc_key))

    def refresh_language(self):
        self._label.configure(text=i18n.get("eotf_label"))
        selected = self._dropdown.get()
        desc_key = _EOTF_DESC_KEYS.get(selected, "eotf_pq_desc")
        self._desc.configure(text=i18n.get(desc_key))
