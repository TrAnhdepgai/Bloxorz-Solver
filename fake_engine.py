"""ENGINE GIẢ để B test solver khi engine thật của A chưa xong.

Làm đúng theo ENGINE_CONTRACT.md (State, Engine, bảng chuyển tư thế) nhưng chỉ hỗ trợ:
sàn, void, goal, fragile. Chưa hỗ trợ bridge/switch/split (sẽ báo lỗi nếu file màn chơi có).
Khi engine thật có, chạy: python run_experiments.py --engine <module>:<Class>
"""
import json
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SplitState:
    cubes: tuple
    active: int


@dataclass(frozen=True)
class State:
    orient: str
    row: int
    col: int
    bridges: frozenset = frozenset()
    split: Optional[SplitState] = None


# (orient mới, d_row, d_col) theo bảng chuyển tư thế trong contract
TRANSITIONS = {
    "S": {"U": ("V", -2, 0), "D": ("V", 1, 0), "L": ("H", 0, -2), "R": ("H", 0, 1)},
    "H": {"U": ("H", -1, 0), "D": ("H", 1, 0), "L": ("S", 0, -1), "R": ("S", 0, 2)},
    "V": {"U": ("S", -1, 0), "D": ("S", 2, 0), "L": ("V", 0, -1), "R": ("V", 0, 1)},
}
DIRECTIONS = ("U", "D", "L", "R")
COST = {"U": 1.0, "D": 1.0, "L": 1.0, "R": 1.0}   # chỗ duy nhất cấu hình step_cost


def occupied(orient, r, c):
    if orient == "S":
        return [(r, c)]
    if orient == "H":
        return [(r, c), (r, c + 1)]
    return [(r, c), (r + 1, c)]


class Engine:
    def __init__(self, level_path):
        with open(level_path, encoding="utf-8") as f:
            level = json.load(f)
        if level.get("bridges") or level.get("switches"):
            raise NotImplementedError("fake_engine chưa hỗ trợ bridge/switch/split")
        self.grid = level["grid"]
        self.start = tuple(level["start"])
        self.goal = tuple(level["goal"])
        self.fragile = {tuple(p) for p in level.get("fragile", [])}

    def initial_state(self):
        return State("S", self.start[0], self.start[1])

    def is_goal(self, state):
        return state.split is None and state.orient == "S" and (state.row, state.col) == self.goal

    def _is_floor(self, r, c):
        return 0 <= r < len(self.grid) and 0 <= c < len(self.grid[r]) and self.grid[r][c] == "#"

    def _legal(self, orient, r, c):
        for cell in occupied(orient, r, c):
            if not self._is_floor(*cell):
                return False
            if orient == "S" and cell in self.fragile:   # đứng trên ô fragile -> vỡ
                return False
        return True

    def get_successors(self, state):
        result = []
        for action in DIRECTIONS:                         # thứ tự cố định U, D, L, R
            orient, dr, dc = TRANSITIONS[state.orient][action]
            r, c = state.row + dr, state.col + dc
            if self._legal(orient, r, c):
                result.append((action, State(orient, r, c, state.bridges), COST[action]))
        return result
