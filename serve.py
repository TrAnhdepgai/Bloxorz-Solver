"""Chạy GUI 3D: python serve.py. Phục vụ web và API level/solver."""
import json
import tempfile
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine.engine import ACTIONS, TRANSITIONS, Engine
from engine.state import SplitState, State
from metrics import run_solver
from solvers import SOLVERS

ROOT = Path(__file__).resolve().parent


def load_gui_levels():
    files = sorted((ROOT / "gui_levels").glob("*.json"))
    return [json.loads(f.read_text(encoding="utf-8")) for f in files]


def to_engine_level(data):
    """Adapt legacy O/S/G tile maps to the engine's #/. schema."""
    grid = data.get("grid", [])
    start = goal = None
    converted = []
    for r, row in enumerate(grid):
        chars = []
        for c, ch in enumerate(row):
            if ch == "S": start = [r, c]
            elif ch == "G": goal = [r, c]
            chars.append("." if ch == "." else "#")
        converted.append("".join(chars))
    if start is None or goal is None:
        raise ValueError("Level cần có đúng một ô bắt đầu S và ô đích G")
    out = {"grid": converted, "start": start, "goal": goal}
    # Pass through engine-supported special mechanics if a level defines them.
    for key in ("fragile", "bridges", "bridges_initial_open", "switches"):
        if key in data: out[key] = data[key]
    return out


def make_problem(index):
    """Dựng Engine cho level thứ `index` trong gui_levels. Trả về (problem, tên level)."""
    levels = load_gui_levels()
    if not isinstance(index, int) or index < 0 or index >= len(levels):
        raise ValueError("level_index không hợp lệ")
    engine_data = to_engine_level(levels[index])
    # Engine's public constructor accepts a JSON path; use a temporary file so the
    # adapter does not mutate the user's original level JSON.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f:
        json.dump(engine_data, f)
        temp_path = f.name
    try:
        problem = Engine(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)
    return problem, levels[index].get("name", f"Level {index + 1}")


# ---------- serialize / deserialize State cho API ----------
def serialize_state(state):
    return {
        "orient": state.orient,
        "row": state.row,
        "col": state.col,
        "bridges": sorted(state.bridges),
        "split": None if state.split is None else {
            "cubes": [list(c) for c in state.split.cubes],
            "active": state.split.active,
        },
    }


def _int(v, what):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{what} phải là số nguyên")
    return v


def parse_state(problem, data):
    """JSON -> State. data=None nghĩa là trạng thái ban đầu của level."""
    if data is None:
        return problem.initial_state()
    if not isinstance(data, dict):
        raise ValueError("state phải là object")
    raw_bridges = data.get("bridges", [])
    if not isinstance(raw_bridges, list):
        raise ValueError("state.bridges phải là danh sách id cầu")
    bridges = frozenset(raw_bridges)
    unknown = bridges - set(problem.bridges)
    if unknown:
        raise ValueError(f"state.bridges chứa id không tồn tại: {sorted(map(str, unknown))}")
    split = data.get("split")
    if split is not None:
        if not isinstance(split, dict):
            raise ValueError("state.split phải là object")
        cubes = split.get("cubes")
        if not isinstance(cubes, list) or len(cubes) != 2 or any(
                not isinstance(c, list) or len(c) != 2 for c in cubes):
            raise ValueError("state.split.cubes phải gồm đúng 2 toạ độ [r, c]")
        cubes = tuple((_int(c[0], "cube.r"), _int(c[1], "cube.c")) for c in cubes)
        active = _int(split.get("active", 0), "state.split.active")
        if active not in (0, 1):
            raise ValueError("state.split.active phải là 0 hoặc 1")
        return State("S", 0, 0, bridges, SplitState(cubes, active))
    orient = data.get("orient")
    if orient not in ("S", "H", "V"):
        raise ValueError("state.orient phải là S, H hoặc V")
    return State(orient, _int(data.get("row"), "state.row"), _int(data.get("col"), "state.col"), bridges)


def tiles_info(problem, state):
    """Thông tin ô đặc biệt: fragile, bridge (kèm đang mở hay đóng), switch."""
    return {
        "fragile": sorted([list(p) for p in problem.fragile]),
        "bridges": [{"id": bid, "cells": [list(p) for p in cells_], "open": bid in state.bridges}
                    for bid, cells_ in sorted(problem.bridges.items())],
        "switches": [{"pos": list(sw["pos"]), "type": sw["type"], "targets": list(sw["targets"]),
                      "mode": sw["mode"], "set": sw["set"],
                      "teleport": None if sw["teleport"] is None else [list(p) for p in sw["teleport"]]}
                     for sw in problem.switches],
    }


def step_level(index, state_data, action):
    """Đi một nước từ state cho trước. Không có state -> dùng trạng thái ban đầu."""
    problem, name = make_problem(index)
    state = parse_state(problem, state_data)
    if action is not None and action not in ACTIONS and action != "SWAP":
        raise ValueError("action phải là U, D, L, R hoặc SWAP")
    if action == "SWAP" and state.split is None:
        raise ValueError("SWAP chỉ dùng được khi khối đang tách đôi")

    result = {"ok": True, "level": name, "action": action, "legal": True,
              "status": "playing", "cost": None, "attempt": None}
    new_state = state
    if action is not None:
        move = next(((nxt, cost) for a, nxt, cost in problem.get_successors(state) if a == action), None)
        if move is None:
            result["legal"] = False
            result["status"] = "fell"          # nước đi không hợp lệ = khối rơi khỏi sàn
            if state.split is None:
                o, dr, dc = TRANSITIONS[(state.orient, action)]
                result["attempt"] = {"orient": o, "row": state.row + dr, "col": state.col + dc}
        else:
            new_state, result["cost"] = move
    if problem.is_goal(new_state):
        result["status"] = "won"
    result["state"] = serialize_state(new_state)
    result["actions"] = [a for a, _, _ in problem.get_successors(new_state)]
    result["tiles"] = tiles_info(problem, new_state)
    return result


def solve_level(index, algorithm):
    problem, name = make_problem(index)
    if algorithm not in SOLVERS:
        raise ValueError("algorithm phải là " + ", ".join(SOLVERS))
    r = run_solver(SOLVERS[algorithm], problem, name)
    return {"ok": True, "level": name, "algorithm": algorithm,
            "solvable": r.found, "path": r.path, "cost": r.cost,
            "length": r.length, "expanded": r.expanded,
            "time_ms": round(r.time_s * 1000, 3),
            "memory_kb": round(r.peak_mem_kb, 1)}


# endpoint POST -> hàm xử lý nhận payload (dict) và trả về dict
ROUTES = {
    "/api/solve": lambda p: solve_level(p.get("level_index"), p.get("algorithm", "bfs")),
    "/api/step": lambda p: step_level(p.get("level_index"), p.get("state"), p.get("action")),
}


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".js": "application/javascript", ".mjs": "application/javascript"}

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT / "web"), **k)

    def _json(self, code, value):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/api/levels":
            self._json(200, load_gui_levels())
            return
        super().do_GET()

    def do_POST(self):
        handler = ROUTES.get(urlparse(self.path).path)
        if handler is None:
            self._json(404, {"ok": False, "error": "Endpoint không tồn tại"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 100_000:
                raise ValueError("Request body không hợp lệ")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Request body phải là object JSON")
            self._json(200, handler(payload))
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self._json(400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._json(500, {"ok": False, "error": f"Solver error: {exc}"})

    def log_message(self, *args):
        pass


def main():
    port = 8000
    while True:
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    url = f"http://127.0.0.1:{port}"
    print(f"Bloxorz 3D đang chạy tại {url}  (Ctrl+C để tắt)")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBye ♡")


if __name__ == "__main__":
    main()