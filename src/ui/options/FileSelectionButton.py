import copy
import os
import tkinter
import threading
from tkinter import filedialog, messagebox
from ttkbootstrap import Button

import i18n
from conversion_setting import config
from hdrify import ssaProcessor, srtSubProcessor
from output_naming import resolve_output_path

# Extensions recognized as "needs conversion via pysubs2"
_SRT_SUB_EXTS = {".srt", ".sub"}
_ASS_SSA_EXTS = {".ass", ".ssa"}


class FileSelectionButton(Button):
    def __init__(self, master, **kwargs):
        super().__init__(master, text=i18n.get("select_convert"), **kwargs)
        self.configure(command=self._on_click)
        self._worker_thread = None
        self._cancel_event = threading.Event()

    def _on_click(self) -> None:
        """Open file dialog and convert selected subtitle files."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return
        files = filedialog.askopenfilenames(filetypes=[
            (i18n.get("subtitle_filter"), '.ass .ssa .srt .sub'),
            (i18n.get("ass_filter"), '.ass .ssa'),
            (i18n.get("srt_filter"), '.srt'),
            (i18n.get("sub_filter"), '.sub'),
            (i18n.get("all_filter"), '.*'),
        ])
        if not files:
            return

        brightness_str = self.master.brightness_frame.target_brightness_var.get()
        if (not brightness_str or not brightness_str.isdecimal()
                or int(brightness_str) < 1 or int(brightness_str) > 10000):
            messagebox.showerror(i18n.get("invalid_brightness"),
                                 i18n.get("brightness_error_msg"))
            return

        # Activate/disable style panel only after validation passes
        has_srt_sub = any(os.path.splitext(f)[1].lower() in _SRT_SUB_EXTS for f in files)
        self.master.style_panel.set_enabled(has_srt_sub)

        self.configure(state='disabled')
        brightness = int(brightness_str)
        self._cancel_event.clear()
        template = self.master.output_naming.template
        eotf = config.eotf
        style_snapshot = copy.copy(config.style)  # snapshot to avoid race with UI thread

        def worker():
            try:
                seen_outputs: set[str] = set()
                for f in files:
                    if self._cancel_event.is_set():
                        print(i18n.get("cancelled"))
                        break
                    print(i18n.get("converting").format(f))

                    ext = os.path.splitext(f)[1].lower()
                    try:
                        output_path = resolve_output_path(f, template, eotf)
                    except (KeyError, ValueError, IndexError) as e:
                        print(i18n.get("msg_template_error").format(template, e))
                        continue

                    # Guard: reject templates that resolve to the input file itself
                    if os.path.normcase(os.path.normpath(output_path)) == os.path.normcase(os.path.normpath(f)):
                        print(i18n.get("msg_overwrite_self").format(f))
                        continue

                    # Guard: skip duplicate output paths in batch mode
                    # normcase needed on Windows where filesystem is case-insensitive
                    norm_output = os.path.normcase(os.path.normpath(output_path))
                    if norm_output in seen_outputs:
                        print(i18n.get("msg_batch_collision").format(output_path))
                        continue
                    seen_outputs.add(norm_output)

                    if ext in _SRT_SUB_EXTS:
                        srtSubProcessor(f, target_brightness=brightness,
                                        eotf=eotf, output_path=output_path,
                                        style_config=style_snapshot,
                                        cancel_event=self._cancel_event)
                    else:
                        ssaProcessor(f, target_brightness=brightness,
                                     eotf=eotf, output_path=output_path,
                                     cancel_event=self._cancel_event)
            except Exception as exc:
                print(i18n.get("msg_unexpected_error").format(exc))
            finally:
                try:
                    self.after(0, self._restoreButton)
                except tkinter.TclError:
                    pass

        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()

    def _restoreButton(self):
        try:
            if self.winfo_exists():
                self.configure(state='normal')
        except tkinter.TclError:
            pass  # interpreter already destroyed

    def cancel_and_wait(self, timeout: float = 0) -> None:
        """Signal the worker thread to stop, optionally wait up to *timeout* seconds."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._cancel_event.set()
            if timeout > 0:
                self._worker_thread.join(timeout=timeout)

    @property
    def is_converting(self) -> bool:
        return self._worker_thread is not None and self._worker_thread.is_alive()
