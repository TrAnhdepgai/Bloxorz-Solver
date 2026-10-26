"""Danh mục màn chơi — MỘT định dạng JSON duy nhất cho engine, solver, GUI và thí nghiệm.

Mỗi file trong `levels/` là một màn, ví dụ:

    {
      "name": "Stone Bridge",            # tên hiển thị trên GUI
      "group": "fragile",                # basic | fragile | switch | combined
      "difficulty": 8,                   # thứ tự trong chiến dịch (nhỏ -> dễ)
      "benchmark": true,                 # true = thuộc bộ test cố định dùng cho báo cáo
      "hint": "...",
      "optimal_moves": 15,               # do compute_optimal.py ghi (BFS), KHÔNG sửa tay
      "grid": ["#####", "#...#"],        # '#' = sàn, '.' = ô trống (void)
      "start": [r, c], "goal": [r, c],
      "fragile": [[r, c], ...],          # (tuỳ chọn) ô giòn, nằm trên ô '#'
      "bridges": {"B1": [[r, c], ...]},  # (tuỳ chọn) ô của từng cầu
      "bridges_initial_open": ["B1"],    # (tuỳ chọn) cầu mở sẵn lúc đầu
      "switches": [ ... ]                # (tuỳ chọn) xem engine/level.py
    }

Engine chỉ đọc grid/start/goal/fragile/bridges/switches; phần còn lại là metadata.
"""
import json
from pathlib import Path

from .level import LevelError, parse_level

ROOT = Path(__file__).resolve().parent.parent
LEVEL_DIR = ROOT / "levels"

GROUPS = ("basic", "fragile", "switch", "combined")   # thứ tự nhóm cũng là thứ tự trong GUI/báo cáo

# Thứ tự khoá khi ghi file để diff git gọn và dễ đọc.
KEY_ORDER = ("name", "group", "difficulty", "benchmark", "hint", "optimal_moves",
             "grid", "start", "goal", "fragile", "bridges", "bridges_initial_open", "switches")


# ---------------------------------------------------------------- đọc / kiểm tra
def validate(data: dict, where: str = "level"):
    """Kiểm tra phần engine (qua parse_level) và phần metadata."""
    try:
        parse_level(data)
    except LevelError as exc:
        raise LevelError(f"{where}: {exc}") from None
    if data.get("group") not in GROUPS:
        raise LevelError(f"{where}: 'group' phải là một trong {GROUPS}, gặp {data.get('group')!r}")
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        raise LevelError(f"{where}: thiếu 'name'")
    if not isinstance(data.get("difficulty"), int):
        raise LevelError(f"{where}: 'difficulty' phải là số nguyên")
    opt = data.get("optimal_moves")
    if opt is not None and not (isinstance(opt, int) and opt >= 0):
        raise LevelError(f"{where}: 'optimal_moves' phải là số nguyên >= 0 hoặc null")


def load_catalog(directory=LEVEL_DIR, benchmark_only=False, groups=None):
    """Trả về danh sách [{'id', 'path', 'data'}] đã sắp theo (nhóm, difficulty, id)."""
    entries = []
    for path in sorted(Path(directory).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        validate(data, path.name)
        entries.append({"id": path.stem, "path": path, "data": data})
    if benchmark_only:
        entries = [e for e in entries if e["data"].get("benchmark")]
    if groups:
        entries = [e for e in entries if e["data"]["group"] in groups]
    entries.sort(key=lambda e: (GROUPS.index(e["data"]["group"]), e["data"]["difficulty"], e["id"]))
    return entries


# ---------------------------------------------------------------- ghi file
def dump_level(data: dict) -> str:
    """Chuỗi JSON gọn: mỗi hàng của grid một dòng, toạ độ nằm trên một dòng."""
    keys = [k for k in KEY_ORDER if k in data] + [k for k in data if k not in KEY_ORDER]
    j = lambda v: json.dumps(v, ensure_ascii=False)
    lines = []
    for k in keys:
        v = data[k]
        if k == "grid":
            body = ",\n".join(f"    {j(row)}" for row in v)
            lines.append(f'  "grid": [\n{body}\n  ]')
        elif k == "bridges":
            body = ",\n".join(f"    {j(b)}: {j(cells)}" for b, cells in v.items())
            lines.append(f'  "bridges": {{\n{body}\n  }}')
        elif k == "switches":
            body = ",\n".join(f"    {j(sw)}" for sw in v)
            lines.append(f'  "switches": [\n{body}\n  ]')
        else:
            lines.append(f"  {j(k)}: {j(v)}")
    return "{\n" + ",\n".join(lines) + "\n}\n"


def write_level(path, data: dict):
    Path(path).write_text(dump_level(data), encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- thống kê / hiển thị
def describe(data: dict) -> dict:
    grid = data["grid"]
    bridges = data.get("bridges", {})
    kinds = sorted({sw["type"] for sw in data.get("switches", [])})
    return {
        "size": f"{len(grid)}x{len(grid[0])}",
        "floor": sum(row.count("#") for row in grid),
        "fragile": len(data.get("fragile", [])),
        "bridges": len(bridges),
        "switches": ",".join(kinds) if kinds else "-",
    }


def ascii_preview(data: dict) -> str:
    """Sơ đồ ASCII: # sàn, . trống, f giòn, 1-9 ô cầu B1-B9, o/x/p công tắc nhẹ/nặng/split,
    t/u điểm teleport của khối thứ nhất/thứ hai, S xuất phát, G đích."""
    g = [list(row) for row in data["grid"]]
    for r, c in data.get("fragile", []):
        g[r][c] = "f"
    for name, cells in data.get("bridges", {}).items():
        for r, c in cells:
            g[r][c] = name[-1]
    for sw in data.get("switches", []):
        r, c = sw["pos"]
        g[r][c] = {"soft": "o", "heavy": "x", "split": "p"}[sw["type"]]
        for mark, (tr, tc) in zip("tu", sw.get("teleport") or ()):
            g[tr][tc] = mark
    g[data["start"][0]][data["start"][1]] = "S"
    g[data["goal"][0]][data["goal"][1]] = "G"
    return "\n".join("".join(row) for row in g)


# ---------------------------------------------------------------- cầu nối sang GUI
def to_gui_level(entry: dict) -> dict:
    """Chuyển một mục catalog sang dạng web GUI đang đọc: ô sàn 'O', xuất phát 'S', đích 'G', trống '.'.
    Các trường đặc biệt (fragile, bridges, switches...) được giữ nguyên cho renderer dùng sau này."""
    d = entry["data"]
    rows = [list(row.replace("#", "O")) for row in d["grid"]]
    rows[d["start"][0]][d["start"][1]] = "S"
    rows[d["goal"][0]][d["goal"][1]] = "G"
    out = {k: v for k, v in d.items() if k not in ("grid", "start", "goal")}
    out["id"] = entry["id"]
    out["grid"] = ["".join(r) for r in rows]
    return out
