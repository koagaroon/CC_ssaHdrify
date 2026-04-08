import tkinter
from tkinter.ttk import Frame, Label, Combobox

EOTF_OPTIONS = ["PQ"]


class EotfOption(Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)

        eotf_label = Label(master=self, text="Content EOTF curve:")
        eotf_label.grid(row=0, column=0, sticky=tkinter.W)
        eotf_dropdown = Combobox(self, state='readonly', values=EOTF_OPTIONS)
        eotf_dropdown.config(state='disabled')
        eotf_dropdown.current(0)
        eotf_dropdown.grid(row=0, column=1, sticky=tkinter.EW)
