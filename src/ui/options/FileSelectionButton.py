import tkinter
import threading
from tkinter import filedialog, messagebox
from tkinter.ttk import Button

import i18n
from conversion_setting import config
from hdrify import ssaProcessor


class FileSelectionButton(Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, text=i18n.get("select_convert"), **kwargs)
        self.configure(command=self._on_click)
        self._worker_thread = None
        self._cancel_event = threading.Event()

    def _on_click(self) -> None:
        """Open file dialog and convert selected subtitle files."""
        files = filedialog.askopenfilenames(filetypes=[(i18n.get("ass_filter"), '.ass .ssa'),
                                                       (i18n.get("all_filter"), '.*')])
        if not files:
            return

        brightness_str = self.master.brightness_frame.target_brightness_var.get()
        if not brightness_str or not brightness_str.isdecimal() or int(brightness_str) < 1:
            messagebox.showerror(i18n.get("invalid_brightness"),
                                 i18n.get("brightness_error_msg"))
            return

        self.configure(state='disabled')
        brightness = int(brightness_str)
        self._cancel_event.clear()

        def worker():
            try:
                for f in files:
                    if self._cancel_event.is_set():
                        print(i18n.get("cancelled"))
                        break
                    print(i18n.get("converting").format(f))
                    ssaProcessor(f, target_brightness=brightness, eotf=config.eotf)
            finally:
                # 双重防御：
                # 1. self.after() 本身在 Tcl 解释器关闭后会抛出 TclError
                # 2. 即使 after() 成功，回调执行时 widget 也可能已销毁
                try:
                    self.after(0, self._restoreButton)
                except tkinter.TclError:
                    pass  # 窗口已销毁，状态恢复无意义，直接跳过

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def _restoreButton(self):
        if self.winfo_exists():
            self.configure(state='normal')

    def cancel_and_wait(self, timeout: float = 0) -> None:
        """Signal the worker thread to stop. Thread is daemon, no need to block."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._cancel_event.set()

    @property
    def is_converting(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.is_alive()
