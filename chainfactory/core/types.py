from typing import Literal
from enum import Enum

ChainlinkTypeTokens = Literal["sequential", "parallel", "--", "||"]


class ChainlinkTypesEnum(str, Enum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
