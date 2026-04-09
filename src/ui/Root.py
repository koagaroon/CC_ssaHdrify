import platform
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

        # Window sizing: 1/4 screen area, centered
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = screen_w // 2
        win_h = screen_h // 2
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.wm_minsize(640, 400)

        self.rowconfigure(0, weight=0)  # language button row
        self.rowconfigure(1, weight=0)  # options
        self.rowconfigure(2, weight=1)  # message (fills remaining space)
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

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    @staticmethod
    def _lang_btn_label() -> str:
        return "\u4e2d\u6587" if i18n.current() == "zh" else "English"

    def _set_language(self, lang: str):
        if lang == i18n.current():
            return
        i18n.toggle()
        self._refresh_language()

    def _refresh_language(self):
        self.title(i18n.get("window_title"))
        self._lang_btn.configure(text=self._lang_btn_label())
        self.options_frame.configure(text=i18n.get("options"))
        self.textFrame.configure(text=i18n.get("message"))
        self.options_frame.refresh_language()

    def _on_close(self):
        convert_btn = self.options_frame.select_file_button
        if convert_btn.is_converting:
            if messagebox.askyesno(
                i18n.get("confirm_close_title"),
                i18n.get("confirm_close_msg"),
            ):
                self.after(200, self._on_close)
                return
            convert_btn.cancel_and_wait(timeout=2.0)
        self.textFrame.stopPolling()
        self.destroy()
