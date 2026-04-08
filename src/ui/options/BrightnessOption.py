import tkinter
from tkinter.ttk import Frame, Label, Entry

from conversion_setting import config


def validateBrightness(newBrightness):
    """验证亮度输入值。

    规则：
    - 只允许纯数字
    - 允许临时清空（输入中间状态）
    - 有效范围：1–10000（nits）
    - 超界时拒绝键入，保持显示值与实际生效值严格一致
    """
    if not newBrightness.isdigit() and newBrightness != '':
        return False           # 拒绝非数字字符
    if newBrightness == '':
        return True            # 允许临时清空
    value = int(newBrightness)
    if value < 1 or value > 10000:
        return False           # 超界直接阻止键入，不截断
    config.targetBrightness = value
    return True


class BrightnessOption(Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(1, weight=1)

        target_brightness_label = Label(master=self, text="Target subtitle brightness (nits):")
        target_brightness_label.grid(row=0, column=0, sticky=tkinter.W)

        self.target_brightness_var = tkinter.StringVar()
        self.target_brightness_var.set(config.targetBrightness)
        validate_brightness_wrapper = (master.register(validateBrightness), '%P')
        target_brightness_input = Entry(master=self, textvariable=self.target_brightness_var, validate="key",
                                        validatecommand=validate_brightness_wrapper)

        target_brightness_input.grid(row=0, column=1, sticky=tkinter.EW)
