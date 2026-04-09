import tkinter
from tkinter.ttk import Frame, Label, Entry

import i18n
from conversion_setting import config

_BRIGHTNESS_REC_KEYS = {"PQ": "brightness_rec_pq", "HLG": "brightness_rec_hlg"}


def validateBrightness(newBrightness):
    if not newBrightness.isdigit() and newBrightness != '':
        return False
    if newBrightness == '':
        return True
    value = int(newBrightness)
    if value < 1 or value > 10000:
        return False
    config.targetBrightness = value
    return True


class BrightnessOption(Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)

        self._label = Label(master=self, text=i18n.get("brightness_label"))
        self._label.grid(row=0, column=0, sticky=tkinter.W)

        self.target_brightness_var = tkinter.StringVar()
        self.target_brightness_var.set(config.targetBrightness)
        validate_brightness_wrapper = (master.register(validateBrightness), '%P')
        target_brightness_input = Entry(master=self, textvariable=self.target_brightness_var, validate="key",
                                        validatecommand=validate_brightness_wrapper)
        target_brightness_input.grid(row=0, column=1, sticky=tkinter.EW)

        # Recommendation label (dynamic, follows EOTF selection)
        rec_key = _BRIGHTNESS_REC_KEYS.get(config.eotf, "brightness_rec_pq")
        self._rec_label = Label(master=self, text=i18n.get(rec_key))
        self._rec_label.grid(row=1, column=0, columnspan=2, sticky=tkinter.W, pady=(2, 0))

    def update_recommendation(self, eotf: str = "PQ"):
        """Update the recommendation text based on EOTF selection."""
        rec_key = _BRIGHTNESS_REC_KEYS.get(eotf, "brightness_rec_pq")
        self._rec_label.configure(text=i18n.get(rec_key))

    def refresh_language(self):
        self._label.configure(text=i18n.get("brightness_label"))
        rec_key = _BRIGHTNESS_REC_KEYS.get(config.eotf, "brightness_rec_pq")
        self._rec_label.configure(text=i18n.get(rec_key))
