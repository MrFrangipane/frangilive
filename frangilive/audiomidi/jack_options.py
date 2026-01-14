from dataclasses import dataclass
from typing import Literal


@dataclass
class JackOptions:
    buffer_period_count: int
    buffer_size: int
    driver: Literal["alsa"]
