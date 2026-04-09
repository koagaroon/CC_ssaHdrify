from tkinter.ttk import LabelFrame

import i18n
from ui.options.BrightnessOption import BrightnessOption
from ui.options.EotfOption import EotfOption
from ui.options.FileSelectionButton import FileSelectionButton


class OptionFrame(LabelFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.brightness_frame = BrightnessOption(master=self)
        self.brightness_frame.grid(row=0, column=1, sticky="new", padx=5, pady=5)

        self.eotf_frame = EotfOption(master=self, on_eotf_change=self.brightness_frame.update_recommendation)
        self.eotf_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.select_file_button = FileSelectionButton(master=self)
        self.select_file_button.grid(row=1, column=0, columnspan=2, pady=5)

    def refresh_language(self):
        self.eotf_frame.refresh_language()
        self.brightness_frame.refresh_language()
        self.select_file_button.configure(text=i18n.get("select_convert"))
