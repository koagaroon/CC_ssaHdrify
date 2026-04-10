from output_naming import DEFAULT_TEMPLATE
from style_config import StyleConfig


class ConversionSetting:
    def __init__(self):
        self.targetBrightness = 203
        self.eotf = "PQ"
        self.output_template: str = DEFAULT_TEMPLATE
        self.style: StyleConfig = StyleConfig()


config = ConversionSetting()
