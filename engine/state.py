from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SplitState:
    cubes: tuple[tuple[int, int], tuple[int, int]]
    active: int

@dataclass(frozen=True)
class State:
    orient: str
    row: int
    col: int
    bridges: frozenset[str]
    split: Optional[SplitState] = None