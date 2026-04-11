import platform
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import NSEW, Menu, StringVar, messagebox

import ttkbootstrap as ttk
from ttkbootstrap import Menubutton

import i18n
from ui.MessageFrame import MessageFrame
from ui.OptionFrame import OptionFrame

_LIGHT_THEME = "cosmo"
_DARK_THEME = "darkly"
_FONT_FAMILIES = ("Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", "Segoe UI")
_FONT_SIZE = 10


_VALID_THEME_MODES = {"auto", "light", "dark"}


def _detect_system_dark_mode() -> bool:
    """Return True if the OS is in dark mode. Windows only; defaults to False."""
    if platform.system() != "Windows":
        return False
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0  # 0 = dark, 1 = light
    except OSError:
        return False


def _pick_font_family() -> str:
    """Return the first available font from the preferred list, or empty string."""
    available = set(tkfont.families())
    for name in _FONT_FAMILIES:
        if name in available:
            return name
    return ""


class _ThemePopup:
    """Custom theme dropdown using ttkbootstrap widgets (avoids native Menu CJK font issues)."""

    def __init__(self, root):
        self._root = root
        self._top = None

    def toggle(self, x: int, y: int):
        """Toggle popup: dismiss if open, show if closed."""
        if self._top and self._top.winfo_exists():
            self.dismiss()
            return
        self._show(x, y)

    def _show(self, x: int, y: int):
        self.dismiss()
        self._top = tk.Toplevel(self._root)
        self._top.overrideredirect(True)
        self._top.attributes("-topmost", True)
        self._top.geometry(f"+{x}+{y}")

        colors = self._root.style.colors
        bg = str(colors.bg)
        fg = str(colors.fg)
        hover_bg = str(colors.selectbg)

        frame = tk.Frame(self._top, bg=bg, padx=4, pady=4)
        frame.pack(fill="both", expand=True)

        mode = self._root._theme_mode
        items = [
            (i18n.get("theme_follow_system"), "auto"),
            (None, None),  # separator
            (i18n.get("theme_light"), "light"),
            (i18n.get("theme_dark"), "dark"),
        ]

        for label, value in items:
            if label is None:
                ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=2)
                continue
            indicator = " \u2022" if mode == value else ""
            btn = tk.Label(
                frame,
                text=label + indicator,
                cursor="hand2",
                bg=bg, fg=fg,
                anchor="w",
                padx=8, pady=4,
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, w=btn: w.configure(bg=hover_bg))
            btn.bind("<Leave>", lambda e, w=btn: w.configure(bg=bg))
            btn.bind("<Button-1>", lambda e, v=value: self._on_click(v))

        # Use grab_set to capture all clicks; clicking outside dismisses the popup
        self._top.grab_set()

    def _on_click(self, mode: str):
        """Handle click: dismiss first, then apply theme via after() to avoid event ordering issues."""
        self.dismiss()
        self._root.after(1, lambda: self._root._set_theme(mode))

    def dismiss(self):
        if self._top and self._top.winfo_exists():
            self._top.grab_release()
            self._top.destroy()
        self._top = None


class Root(ttk.Window):
    def __init__(self):
        # Load saved theme preference from config (whitelist validated)
        cfg = i18n._load_config()
        saved_theme = cfg.get("theme")
        self._theme_mode = saved_theme if saved_theme in _VALID_THEME_MODES else "auto"
        initial_theme = self._resolve_theme()

        super().__init__(themename=initial_theme)
        self.title(i18n.get("window_title"))

        # Global font: pick best available CJK-capable font at 10pt
        family = _pick_font_family()
        font_cfg = {"size": _FONT_SIZE}
        if family:
            font_cfg["family"] = family
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(**font_cfg)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(**font_cfg)

        # Window sizing: ~30% screen area (3/5 width × 1/2 height), centered
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = screen_w * 3 // 5
        win_h = screen_h // 2
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.wm_minsize(640, 400)

        self.rowconfigure(0, weight=0)  # toolbar row
        self.rowconfigure(1, weight=0)  # options (natural size)
        self.rowconfigure(2, weight=1)  # message (fills remaining, has scrollbar)
        self.columnconfigure(0, weight=1)

        # Toolbar frame (language + theme buttons)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="nw", padx=5, pady=(5, 0))

        # Language menu button (native Menu OK — "English"/"中文" don't trigger CJK fallback)
        self._lang_btn = Menubutton(toolbar, text=self._lang_btn_label(), width=8)
        self._lang_menu = Menu(self._lang_btn, tearoff=0)
        self._lang_menu.add_command(label="English", command=lambda: self._set_language("en"))
        self._lang_menu.add_command(label="\u4e2d\u6587", command=lambda: self._set_language("zh"))
        self._lang_btn["menu"] = self._lang_menu
        self._lang_btn.pack(side="left", padx=(0, 4))

        # Theme button (custom popup — avoids native Menu CJK font issues)
        self._theme_popup = _ThemePopup(self)
        self._theme_btn = ttk.Button(toolbar, text=i18n.get("theme"), width=8,
                                     command=self._show_theme_popup)
        self._theme_btn.pack(side="left")

        # Option frame
        self.options_frame = OptionFrame(master=self, text=i18n.get("options"))
        self.options_frame.grid(row=1, sticky="new", padx=5, pady=5)

        # Message frame
        self.textFrame = MessageFrame(master=self, text=i18n.get("message"), borderwidth=1)
        self.textFrame.grid(row=2, sticky=NSEW, padx=5, pady=5)

        self._closing = False  # re-entry guard for _on_close
        self._wait_deadline = 0.0
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # --- Theme methods ---

    def _resolve_theme(self) -> str:
        """Return the ttkbootstrap theme name based on current mode."""
        if self._theme_mode == "light":
            return _LIGHT_THEME
        if self._theme_mode == "dark":
            return _DARK_THEME
        # auto: follow system
        return _DARK_THEME if _detect_system_dark_mode() else _LIGHT_THEME

    def _show_theme_popup(self):
        btn = self._theme_btn
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height()
        self._theme_popup.toggle(x, y)

    def _set_theme(self, mode: str):
        """Switch theme mode, apply, and persist."""
        self._theme_mode = mode
        new_theme = self._resolve_theme()
        self.style.theme_use(new_theme)
        # Persist to config
        cfg = i18n._load_config()
        cfg["theme"] = mode
        i18n._save_config(cfg)

    # --- Language methods ---

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
        self._theme_btn.configure(text=i18n.get("theme"))
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
