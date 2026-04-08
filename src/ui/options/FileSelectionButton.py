import tkinter
import threading
from tkinter import filedialog, messagebox
from tkinter.ttk import Button

from conversion_setting import config
from hdrify import ssaProcessor


class FileSelectionButton(Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, text="Select file and convert", **kwargs)
        self.configure(command=self._on_click)
        self._worker_thread = None

    def _on_click(self) -> None:
        """Open file dialog and convert selected subtitle files."""
        files = filedialog.askopenfilenames(filetypes=[('ASS files', '.ass .ssa'),
                                                       ('all files', '.*')])
        if not files:
            return

        brightness_str = self.master.brightness_frame.target_brightness_var.get()
        if not brightness_str or not brightness_str.isdigit() or int(brightness_str) < 1:
            messagebox.showerror("Invalid brightness",
                                 "Please enter a target brightness value (1\u201310000 nits).")
            return

        self.configure(state='disabled')
        brightness = config.targetBrightness

        def worker():
            try:
                for f in files:
                    print(f"Converting file: {f}")
                    ssaProcessor(f, target_brightness=brightness)
            finally:
                # 双重防御：
                # 1. self.after() 本身在 Tcl 解释器关闭后会抛出 TclError
                # 2. 即使 after() 成功，回调执行时 widget 也可能已销毁
                try:
                    self.after(
                        0,
                        lambda: self.configure(state='normal')
                        if self.winfo_exists() else None
                    )
                except tkinter.TclError:
                    pass  # 窗口已销毁，状态恢复无意义，直接跳过

        self._worker_thread = threading.Thread(target=worker, daemon=False)
        self._worker_thread.start()

    @property
    def is_converting(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.is_alive()
