import threading
from tkinter import filedialog
from tkinter.ttk import Button

from hdrify import ssaProcessor

_button_instance = None


def files_picker() -> None:
    """询问用户并返回字幕文件"""
    files = filedialog.askopenfilenames(filetypes=[('ASS files', '.ass .ssa'),
                                                   ('all files', '.*')])
    if not files:
        return

    if _button_instance:
        _button_instance.configure(state='disabled')

    def worker():
        try:
            for f in files:
                print(f"Converting file: {f}")
                ssaProcessor(f)
        finally:
            if _button_instance:
                _button_instance.configure(state='normal')

    threading.Thread(target=worker, daemon=True).start()


class FileSelectionButton(Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, text="Select file and convert", **kwargs)
        self.configure(command=files_picker)
        global _button_instance
        _button_instance = self

