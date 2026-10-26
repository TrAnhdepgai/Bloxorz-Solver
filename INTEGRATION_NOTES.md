# Engine + solver integration (first pass)

- `main.py` and `serve.py` now launch the Three.js web GUI. The old Pygame source remains in `gui/` but is no longer the default entry point.
- `engine/` and `solvers/` are copied from the supplied solver project.
- `POST /api/solve` accepts `{ "level_index": 0, "algorithm": "bfs" }` (index into the levels the GUI shows); supported algorithms: every key of `solvers.SOLVERS` (`bfs`, `dfs`, `ids`, `ucs`).
- Level files now share ONE format in `levels/` (see README). `serve.py` serves them to the GUI through `engine/catalog.py: to_gui_level`; the old `gui_levels/` folder and the O/S/G adapter are gone.
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

The GUI currently exposes only the `basic` group (`GUI_GROUPS` in `serve.py`), which uses only basic floor tiles. The engine supports fragile tiles, bridges, switches, and split states, but the current Three.js renderer and manual movement rules do not yet render/simulate all those special mechanics. `SWAP` actions therefore cannot be animated by the current GUI yet. This pass connects all four solvers for the existing six levels; special mechanics need a subsequent UI/state synchronization pass before those levels are exposed in the web game.

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
- `python main.py` gọi `serve.main()`: chạy server HTTP, tự chọn cổng trống từ 8000 trở lên và mở trình duyệt. `serve.py` giữ server và toàn bộ code API.
- Chạy thực nghiệm bằng `run_experiments.py`: `python run_experiments.py [--engine module:Class] [--solvers bfs ucs] [--levels levels] [--out results.csv] [--no-memory]`. Mặc định dùng `engine.engine:Engine`, đọc mọi level trong `levels/` và ghi `results.csv`.

### Cost hook
- `Engine(level_path, cost_fn=default_cost)`; `cost_fn(state, action, next_state) -> float` (không âm). Mặc định `default_cost` tra bảng `COST` trong `engine/engine.py`, mọi nước tốn 1.0.
- Solver không đổi: dùng `step_cost` do `get_successors` trả về. BFS/DFS/IDS tối ưu theo số bước; chỉ UCS tối ưu theo cost.

### API
- `POST /api/solve` `{level_index, algorithm}`: `algorithm` lấy từ registry `solvers.SOLVERS` (thêm solver mới chỉ cần đăng ký ở `solvers/__init__.py`). Trả `ok, level, algorithm, solvable, path, cost, length, expanded, time_ms, memory_kb`. Các key cũ (`ok, solvable, path, cost, expanded`) giữ nguyên. Level không giải được thì `path`, `cost`, `length` là `null`. Bộ nhớ luôn được đo (solver chạy hai lượt: một lượt đo thời gian, một lượt đo bộ nhớ).
- `POST /api/step` `{level_index, state?, action?}` (`action` thuộc `U/D/L/R/SWAP`; bỏ `state` thì dùng state đầu; bỏ `action` thì chỉ mô tả state). Trả:
  - `legal`: nước đi có hợp lệ không. `status`: `playing`, `won` hoặc `fell` (`fell` = nước đi không hợp lệ, `state` giữ nguyên).
  - `state`: `{orient, row, col, bridges, split}`; `bridges` là danh sách id cầu đang mở; `split` là `null` hoặc `{cubes, active}`. Frontend gửi lại nguyên object này ở lượt sau.
  - `cost`: cost của nước vừa đi (`null` nếu không hợp lệ). `actions`: các nước hợp lệ từ state mới.
  - `attempt`: vị trí khối định tới khi `fell` (`{orient, row, col}`), chỉ có khi chưa tách đôi.
  - `tiles`: `fragile` (danh sách ô), `bridges` (`{id, cells, open}` theo state hiện tại), `switches` (`{pos, type, targets, mode, set, teleport}`).
  - State split: `orient` là `"S"`, `row/col` chỉ là giá trị giữ chỗ (0); vị trí thật ở `state.split.cubes`.
- Lỗi đầu vào trả HTTP 400 `{ok: false, error}`; endpoint không tồn tại trả 404.
- Chi tiết request/response mẫu: xem `README.md`.

### Lưu ý
- GUI hiện vẫn tự mô phỏng nước đi bằng JS và chưa gọi `/api/step`. Khi làm bước đồng bộ UI cho fragile/bridge/switch/split, dùng `/api/step` làm nguồn đúng (engine là nguồn luật chơi duy nhất). GUI cũng chưa hiển thị `length`, `time_ms`, `memory_kb`.
- Mọi file lưu bằng UTF-8; `serve.py` trả `charset=utf-8`.
- Test: `python -m pytest -q` (`tests/test_solvers.py` dùng engine thật, không còn `fake_engine`).