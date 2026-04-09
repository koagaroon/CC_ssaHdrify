import platform

# DPI awareness must be set BEFORE any tkinter import
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (ImportError, AttributeError, OSError):
        pass

from contextlib import redirect_stderr, redirect_stdout
from os import path

from PIL import Image, ImageTk

import i18n
from ui.Root import Root

if __name__ == '__main__':
    i18n.init()
    root = Root()
    icon = Image.open(path.abspath(path.join(path.dirname(__file__), 'asset/hdr.png')))
    root.wm_iconphoto(False, ImageTk.PhotoImage(icon))

    with redirect_stderr(root.textFrame.messageStream), \
         redirect_stdout(root.textFrame.messageStream):
        print(i18n.get("ready"))
        root.mainloop()
