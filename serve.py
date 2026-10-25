"""Chạy GUI 3D: python main.py (hoặc python serve.py). Phục vụ web và API level/solver."""
import json
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from engine import Engine
from engine.catalog import load_catalog, to_gui_level
from solvers import SOLVERS

ROOT = Path(__file__).resolve().parent

# Renderer 3D hiện chỉ vẽ và mô phỏng ô sàn thường. Thêm nhóm vào đây ("fragile", "switch",
# "combined") khi GUI đã hỗ trợ cơ chế tương ứng, để người chơi không gặp màn không thể chơi tay.
GUI_GROUPS = {"basic"}


def gui_entries():
    return load_catalog(groups=GUI_GROUPS)       # đọc lại mỗi lần gọi: sửa file level không cần restart


def load_gui_levels():
    return [to_gui_level(e) for e in gui_entries()]


def solve_level(index, algorithm):
    entries = gui_entries()
    if not isinstance(index, int) or index < 0 or index >= len(entries):
        raise ValueError("level_index không hợp lệ")
    if algorithm not in SOLVERS:
        raise ValueError("algorithm phải là một trong: " + ", ".join(SOLVERS))
    entry = entries[index]
    outcome = SOLVERS[algorithm](Engine(entry["data"]))
    return {"ok": True, "level": entry["data"]["name"], "algorithm": algorithm,
            "path": outcome.path, "cost": outcome.cost,
            "expanded": outcome.expanded, "solvable": outcome.path is not None}


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
            self._json(404, {"ok": False, "error": "Endpoint không tồn tại"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 100_000:
                raise ValueError("Request body không hợp lệ")
            payload = json.loads(self.rfile.read(size).decode("utf-8"))
            self._json(200, solve_level(payload.get("level_index"), payload.get("algorithm", "bfs")))
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
        print("\nTạm biệt!")


if __name__ == "__main__":
    main()
