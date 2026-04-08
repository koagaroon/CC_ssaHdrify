import queue
import tkinter
from tkinter.ttk import LabelFrame


class QueueStream:
    """线程安全的文本输出流，写入底层 queue.Queue。

    实现了 write() / flush() 接口，可直接用于
    contextlib.redirect_stdout / redirect_stderr。
    消费即释放，无内存积累。
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()

    def write(self, text: str) -> None:
        if text:
            self._queue.put(text)

    def flush(self) -> None:
        pass  # 满足 TextIO 接口，无需实际实现


class MessageFrame(LabelFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.messageStream = QueueStream()
        self._queue = self.messageStream._queue
        self.callbackId = ""
        self.text = tkinter.Text(master=self)
        self.text.pack(expand=True, fill='both')

        self.updateText()

    def updateText(self):
        self.text.config(state=tkinter.NORMAL)
        try:
            while True:
                chunk = self._queue.get_nowait()
                self.text.insert(tkinter.END, chunk)
        except queue.Empty:
            pass
        self.text.config(state=tkinter.DISABLED)
        self.text.see(tkinter.END)  # 自动滚动到最新消息
        self.callbackId = self.after(500, self.updateText)

    def stopPolling(self):
        """Cancel the pending after callback to prevent errors on window close."""
        if self.callbackId:
            self.after_cancel(self.callbackId)
            self.callbackId = ""
