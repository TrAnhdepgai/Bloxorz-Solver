import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    grid: tuple[str, ...]
    start: tuple[int, int]
    goal: tuple[int, int]
    fragile: frozenset[tuple[int, int]]
    bridges: dict[str, tuple[tuple[int, int], ...]]   # id cầu -> các ô của cầu
    bridges_initial_open: frozenset[str]
    # Mỗi switch đã được chuẩn hoá thành dict:
    # {"pos": (r, c), "type": "soft"|"heavy"|"split", "targets": (id, ...),
    #  "mode": "toggle"|"permanent", "set": "open"|"close"|None,
    #  "teleport": ((r, c), (r, c)) | None}
    switches: tuple[dict, ...]


class LevelError(ValueError):
    """File màn chơi sai định dạng hoặc sai nội dung."""


SWITCH_TYPES = ("soft", "heavy", "split")
SWITCH_MODES = ("toggle", "permanent")


def _pt(p) -> tuple[int, int]:
    try:
        r, c = p
        return (int(r), int(c))
    except (TypeError, ValueError):
        raise LevelError(f"toạ độ không hợp lệ: {p!r}")


def _parse_switch(sw, is_floor, bridges) -> dict:
    if not isinstance(sw, dict):
        raise LevelError(f"switch phải là object: {sw!r}")
    for key in ("pos", "type"):
        if key not in sw:
            raise LevelError(f"switch thiếu trường '{key}': {sw}")

    typ = sw["type"]
    if typ not in SWITCH_TYPES:
        raise LevelError(f"switch có type không hợp lệ: {sw}")

    pos = _pt(sw["pos"])
    if not is_floor(pos):
        raise LevelError(f"switch tại {pos} phải nằm trên ô sàn '#'")

    targets = tuple(sw.get("targets", []))
    for t in targets:
        if t not in bridges:
            raise LevelError(f"switch trỏ tới cầu không tồn tại: {t}")

    mode = sw.get("mode", "toggle")
    if mode not in SWITCH_MODES:
        raise LevelError(f"switch có mode không hợp lệ (toggle|permanent): {sw}")
    set_ = sw.get("set")
    if targets and mode == "permanent" and set_ not in ("open", "close"):
        raise LevelError(f"switch permanent cần \"set\" là 'open' hoặc 'close': {sw}")

    teleport = None
    if typ == "split":
        tp = sw.get("teleport")
        if not isinstance(tp, (list, tuple)) or len(tp) != 2:
            raise LevelError(f"switch split cần 'teleport' gồm đúng 2 toạ độ: {sw}")
        a, b = _pt(tp[0]), _pt(tp[1])
        for p in (a, b):
            if not is_floor(p):
                raise LevelError(f"điểm teleport {p} phải nằm trên ô sàn '#'")
        if abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1:
            raise LevelError(
                f"hai điểm teleport {a}, {b} phải khác nhau và không liền kề "
                "(liền kề thì khối gộp lại ngay)")
        teleport = (a, b)

    return {"pos": pos, "type": typ, "targets": targets,
            "mode": mode, "set": set_, "teleport": teleport}


def load_level(path: str) -> Level:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)

    for key in ("grid", "start", "goal"):
        if key not in d:
            raise LevelError(f"Thiếu trường bắt buộc '{key}'")

    grid = tuple(d["grid"])
    if not grid:
        raise LevelError("grid rỗng")
    if len({len(row) for row in grid}) != 1:
        raise LevelError("Các hàng của grid phải cùng độ dài")
    for row in grid:
        if set(row) - {"#", "."}:
            raise LevelError(f"grid chỉ được chứa '#' và '.', gặp: {row!r}")

    rows, cols = len(grid), len(grid[0])

    def is_floor(p):
        r, c = p
        return 0 <= r < rows and 0 <= c < cols and grid[r][c] == "#"

    start, goal = _pt(d["start"]), _pt(d["goal"])
    fragile = frozenset(_pt(p) for p in d.get("fragile", []))
    bridges = {k: tuple(_pt(p) for p in v) for k, v in d.get("bridges", {}).items()}
    initial_open = frozenset(d.get("bridges_initial_open", []))

    # kiểm tra nội dung
    if not is_floor(start):
        raise LevelError(f"start {start} phải nằm trên ô sàn '#'")
    if not is_floor(goal):
        raise LevelError(f"goal {goal} phải nằm trên ô sàn '#'")
    if start in fragile:
        raise LevelError(f"start {start} không được nằm trên ô fragile (khối đứng sẽ rơi)")
    if goal in fragile:
        raise LevelError(f"goal {goal} không được nằm trên ô fragile (không thể thắng)")
    for p in fragile:
        if not is_floor(p):
            raise LevelError(f"ô fragile {p} phải nằm trên ô sàn '#'")
    for bid, cells_ in bridges.items():
        for p in cells_:
            if not (0 <= p[0] < rows and 0 <= p[1] < cols):
                raise LevelError(f"cầu {bid} có ô {p} ngoài bảng")
    unknown = initial_open - set(bridges)
    if unknown:
        raise LevelError(f"bridges_initial_open chứa id không tồn tại: {sorted(unknown)}")

    switches = tuple(_parse_switch(sw, is_floor, bridges) for sw in d.get("switches", []))

    return Level(grid, start, goal, fragile, bridges, initial_open, switches)