"""Cháº¡y GUI 3D: python serve.py. Phá»¥c vá»¥ web vÃ  API level/solver."""
import json
import tempfile
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine.engine import Engine
from solvers import bfs, dfs, ids, ucs

ROOT = Path(__file__).resolve().parent
SOLVERS = {"bfs": bfs, "dfs": dfs, "ids": ids, "ucs": ucs}


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
        raise ValueError("Level cáº§n cÃ³ Ä‘Ãºng má»™t Ã´ báº¯t Ä‘áº§u S vÃ  Ã´ Ä‘Ã­ch G")
    out = {"grid": converted, "start": start, "goal": goal}
    # Pass through engine-supported special mechanics if a level defines them.
    for key in ("fragile", "bridges", "bridges_initial_open", "switches"):
        if key in data: out[key] = data[key]
    return out


def solve_level(index, algorithm):
    levels = load_gui_levels()
    if not isinstance(index, int) or index < 0 or index >= len(levels):
        raise ValueError("level_index khÃ´ng há»£p lá»‡")
    if algorithm not in SOLVERS:
        raise ValueError("algorithm pháº£i lÃ  bfs, dfs, ids hoáº·c ucs")
    engine_data = to_engine_level(levels[index])
    # Engine's public constructor accepts a JSON path; use a temporary file so the
    # adapter does not mutate the user's original level JSON.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f:
        json.dump(engine_data, f)
        temp_path = f.name
    try:
        problem = Engine(temp_path)
        outcome = SOLVERS[algorithm](problem)
        return {"ok": True, "level": levels[index].get("name", f"Level {index + 1}"),
                "algorithm": algorithm, "path": outcome.path, "cost": outcome.cost,
                "expanded": outcome.expanded, "solvable": outcome.path is not None}
    finally:
        Path(temp_path).unlink(missing_ok=True)


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
        if urlparse(self.path).path != "/api/solve":
            self._json(404, {"ok": False, "error": "Endpoint khÃ´ng tá»“n táº¡i"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 100_000:
                raise ValueError("Request body khÃ´ng há»£p lá»‡")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            result = solve_level(payload.get("level_index"), payload.get("algorithm", "bfs"))
            self._json(200, result)
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
    print(f"Bloxorz 3D Ä‘ang cháº¡y táº¡i {url}  (Ctrl+C Ä‘á»ƒ táº¯t)")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBye â™¡")


if __name__ == "__main__":
    main()
