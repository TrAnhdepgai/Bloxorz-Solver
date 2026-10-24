# Engine + solver integration (first pass)

- `main.py` and `serve.py` now launch the Three.js web GUI. The old Pygame source remains in `gui/` but is no longer the default entry point.
- `engine/` and `solvers/` are copied from the supplied solver project.
- `POST /api/solve` accepts `{ "level_index": 0, "algorithm": "bfs" }`; supported algorithms: `bfs`, `dfs`, `ids`, `ucs`.
- `serve.py` adapts existing O/S/G map characters into the engine's #/. map format without changing the original level files.
- The web Solve button plays the returned U/D/L/R path through the existing Three.js roll animation.

## Run

```powershell
python main.py
```

Optional tests:

```powershell
python -m pytest -q
```

## Current limitations

The existing six GUI levels use only basic floor tiles. The engine supports fragile tiles, bridges, switches, and split states, but the current Three.js renderer and manual movement rules do not yet render/simulate all those special mechanics. `SWAP` actions therefore cannot be animated by the current GUI yet. This pass connects all four solvers for the existing six levels; special mechanics need a subsequent UI/state synchronization pass before those levels are exposed in the web game.


## Màn hình kết quả 5 sao
- Khi hoàn thành level bằng thao tác thủ công hoặc Solve, game hiển thị bảng kết quả thay vì tự chuyển màn.
- Đánh giá sao dựa trên số nước đi so với `optimal_moves`: 5 sao nếu tối ưu; 4 sao <= 1.2x; 3 sao <= 1.5x; 2 sao <= 2x; còn lại 1 sao.
- Người chơi có thể chọn Màn tiếp theo, Chơi lại, hoặc Về menu.
- Cài đặt tự động qua màn cũ được giữ trong dữ liệu nhưng không còn tự chuyển màn sau chiến thắng.


## Fix: khôi phục thao tác sau màn kết quả
- Các nút kết quả dừng solver playback trước khi chuyển màn hoặc mở menu.
- Nút Tiếp tục trong menu sẽ khởi tạo lại level nếu trạng thái trước đó là won/fell, tránh đóng menu nhưng giữ trạng thái khóa điều khiển.

- Additional fix: `loadLevel()` now resets `resultShown` and `winT` and hides the result overlay before initializing the new level, preventing the previous level's win timer from reopening the result panel.

## Cập nhật: cost hook, /api/step, metrics, main.py

### main.py (điểm vào duy nhất)
- `main.py` is the single entry point (`python main.py` launches the Three.js web GUI; `solve` and `experiments` subcommands are also available). `serve.py` holds the HTTP server and API code that `main.py` calls. The old Pygame source remains in `gui/` but is no longer the default entry point.
- `python main.py` = `python main.py serve` (có `--port N`, `--no-browser`).
- `python main.py solve --level levels/<file>.json --algo bfs [--no-memory]`: giải 1 level, in time/memory/expanded/length.
- `python main.py experiments --engine engine.engine:Engine [--no-memory]`: chạy `run_experiments.py`, ghi `results.csv`.

### Cost hook
- `Engine(level_path, cost_fn=None)`; `cost_fn(state, action, next_state) -> float` (không âm). Mặc định tra bảng `COST` trong `engine/engine.py`.
- Solver không đổi: dùng `step_cost` do `get_successors` trả về. BFS/DFS/IDS tối ưu theo số bước; chỉ UCS tối ưu theo cost.

### API
- `GET /api/solvers`: tên các solver trong registry `solvers.SOLVERS` (thêm solver mới chỉ cần đăng ký ở `solvers/__init__.py`).
- `POST /api/solve` `{level_index, algorithm, measure_memory?}` trả thêm `length`, `cost`, `time_s`, `time_ms`, `peak_mem_kb` (null nếu không đo), `valid`. Các key cũ (`ok, solvable, path, expanded`) giữ nguyên.
- `POST /api/step` `{level_index, state?, action?}` (`action` thuộc U/D/L/R/SWAP; bỏ `state` thì dùng state đầu; bỏ `action` thì chỉ mô tả state). Trả `valid, won, cost, state, cells, actions, tiles`.
  - `valid:false` = nước đi không hợp lệ, `state` giữ nguyên.
  - State split: `orient` là `"S"`, `row/col` chỉ là giá trị giữ chỗ; vị trí thật ở `state.split.cubes` và `cells`.
  - `tiles[r][c]` có `type` (empty/floor/fragile/switch/bridge), `walkable`, `fragile`, `bridge {id, open}`, `switches`, `start`, `goal`, theo đúng state hiện tại.
- Chi tiết request/response mẫu: xem `README.md`.

### Lưu ý
- GUI hiện vẫn tự mô phỏng nước đi bằng JS và chưa gọi `/api/step`. Khi làm bước đồng bộ UI cho fragile/bridge/switch/split, dùng `/api/step` làm nguồn đúng (engine là nguồn luật chơi duy nhất).
- Mọi file lưu bằng UTF-8; serve.py trả `charset=utf-8`.
- Test: `python -m pytest -q` (test mới: `tests/test_serialize_step_solve.py`).