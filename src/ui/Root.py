import platform
import time
from tkinter import NSEW, Menu, Tk, messagebox
from tkinter.ttk import Style, Menubutton

import i18n
from ui.MessageFrame import MessageFrame
from ui.OptionFrame import OptionFrame


def setStyle():
    sys_name = platform.system()
    tk_style = Style()
    if sys_name == 'Windows':
        tk_style.theme_use('vista')


class Root(Tk):
    def __init__(self):
        super().__init__()
        self.title(i18n.get("window_title"))
        setStyle()

        # Window sizing: ~30% screen area (3/5 width × 1/2 height), centered
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = screen_w * 3 // 5
        win_h = screen_h // 2
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.wm_minsize(640, 400)

        self.rowconfigure(0, weight=0)  # language button row
        self.rowconfigure(1, weight=0)  # options (natural size)
        self.rowconfigure(2, weight=1)  # message (fills remaining, has scrollbar)
        self.columnconfigure(0, weight=1)

        # Language menu button (top-left)
        self._lang_btn = Menubutton(self, text=self._lang_btn_label(), width=8)
        self._lang_menu = Menu(self._lang_btn, tearoff=0)
        self._lang_menu.add_command(label="English", command=lambda: self._set_language("en"))
        self._lang_menu.add_command(label="\u4e2d\u6587", command=lambda: self._set_language("zh"))
        self._lang_btn["menu"] = self._lang_menu
        self._lang_btn.grid(row=0, column=0, sticky="nw", padx=5, pady=(5, 0))

        # Option frame
        self.options_frame = OptionFrame(master=self, text=i18n.get("options"))
        self.options_frame.grid(row=1, sticky="new", padx=5, pady=5)

        # Message frame
        self.textFrame = MessageFrame(master=self, text=i18n.get("message"), borderwidth=1)
        self.textFrame.grid(row=2, sticky=NSEW, padx=5, pady=5)

        self._closing = False  # re-entry guard for _on_close
        self._wait_deadline = 0.0
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _lang_btn_label() -> str:
        return "\u8bed\u8a00" if i18n.current() == "zh" else "Language"

    def _set_language(self, lang: str):
        if lang == i18n.current():
            return
        i18n.set_language(lang)
        self._refresh_language()

    def _refresh_language(self):
        self.title(i18n.get("window_title"))
        self._lang_btn.configure(text=self._lang_btn_label())
        self.options_frame.configure(text=i18n.get("options"))
        self.textFrame.configure(text=i18n.get("message"))
        self.options_frame.refresh_language()

    def _on_close(self):
        if self._closing:
            return  # suppress re-entrant calls (e.g. rapid double-click)
        convert_btn = self.options_frame.select_file_button
        if convert_btn.is_converting:
            if messagebox.askyesno(
                i18n.get("confirm_close_title"),
                i18n.get("confirm_close_msg"),
            ):
                # Yes = wait silently until conversion finishes, then close
                self._closing = True
                self._wait_deadline = time.monotonic() + 30
                self.after(200, self._wait_and_close)
                return
            # No = cancel and close. Set _closing first to block re-entry,
            # hide window immediately for responsive UX, then signal cancel
            # and poll until the worker exits (no main-thread blocking).
            self._closing = True
            self.withdraw()
            convert_btn.cancel_and_wait(timeout=0)  # signal only, don't block
            self._wait_deadline = time.monotonic() + 12
            self.after(200, self._wait_and_close)
            return
        self._closing = True
        self.textFrame.stopPolling()
        self.destroy()

    def _wait_and_close(self):
        """Poll until conversion finishes, then close — no repeated dialogs."""
        if not self.winfo_exists():
            return
        if self.options_frame.select_file_button.is_converting:
            if time.monotonic() < self._wait_deadline:
                self.after(200, self._wait_and_close)
                return
            self.options_frame.select_file_button.cancel_and_wait(timeout=2)
        self.textFrame.stopPolling()
        self.destroy()
