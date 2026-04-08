import platform
import tkinter
from tkinter import Tk, messagebox
from tkinter.ttk import Style

from ui.MessageFrame import MessageFrame
from ui.OptionFrame import OptionFrame


def setStyle():
    sys_name = platform.system()
    tk_style = Style()
    if sys_name == 'Windows':
        tk_style.theme_use('vista')
    return


class Root(Tk):
    def __init__(self):
        super().__init__()
        self.title("Convert subtitle from SDR to HDR colorspace")
        setStyle()
        self.wm_minsize(640, 480)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # Option frame
        self.options_frame = OptionFrame(master=self, text="Options")
        self.options_frame.grid(row=0, sticky="new", padx=5, pady=5)

        # Message frame
        self.textFrame = MessageFrame(master=self, text="Message", borderwidth=1)
        self.textFrame.grid(row=1, sticky=tkinter.NSEW, padx=5, pady=5)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        convert_btn = self.options_frame.select_file_button
        if convert_btn.is_converting:
            if messagebox.askyesno(
                "Conversion in progress",
                "A conversion is still running.\nWait for it to finish before closing?"
            ):
                self.after(200, self._on_close)
                return
        self.textFrame.stopPolling()
        self.destroy()
