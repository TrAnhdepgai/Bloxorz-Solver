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
