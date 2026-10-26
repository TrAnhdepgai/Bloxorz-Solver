# Bloxorz-Solver

Dự án AI cơ bản: mô hình hóa trò chơi Bloxorz thành bài toán tìm kiếm, cài đặt các thuật toán
BFS, DFS, IDS, UCS, A* để giải, và có giao diện web 3D để chơi tay hoặc xem solver giải.

## Yêu cầu

- Python 3.9 trở lên
- `pip install -r requirements.txt` (`pytest` để chạy test, `matplotlib` để vẽ biểu đồ; server và solver chỉ dùng thư viện chuẩn)
- Trình duyệt hỗ trợ WebGL cho giao diện 3D

## Chạy nhanh

```bash
python main.py
```

Lệnh này mở server tại `http://127.0.0.1:8000` (tự chọn cổng trống kế tiếp nếu 8000 bận)
và tự mở trình duyệt. Nhấn `Ctrl+C` để tắt.

## Cấu trúc thư mục

| Đường dẫn | Vai trò |
|---|---|
| `main.py` | Điểm vào của dự án, gọi `serve.main()` |
| `serve.py` | Server HTTP: phục vụ `web/` và các API |
| `engine/` | Engine trò chơi: `State`, `SplitState`, `Engine`, đọc level |
| `solvers/` | Các thuật toán tìm kiếm; `SOLVERS` là bảng đăng ký theo tên |
| `metrics.py` | Đo thời gian, bộ nhớ đỉnh, số nút mở rộng, độ dài lời giải |
| `run_experiments.py` | Chạy các solver trên `levels/`, in bảng và ghi CSV |
| `levels/` | Mọi màn chơi theo MỘT định dạng, dùng cho engine, solver, GUI và thực nghiệm |
| `engine/catalog.py` | Nạp danh sách màn từ `levels/`, lọc theo nhóm / benchmark |
| `compute_optimal.py` | Tính và ghi `optimal_moves` (BFS) cho từng màn |
| `plot_results.py` | Vẽ biểu đồ và bảng từ `results.csv` vào `figures/` |
| `web/` | Giao diện Three.js |
| `tests/` | Test bằng pytest |

## Engine

Trạng thái của khối gồm tư thế (`S` đứng, `H` nằm ngang, `V` nằm dọc), vị trí góc trên trái,
tập cầu đang mở và trạng thái tách đôi (`split`). Các hành động: `U`, `D`, `L`, `R`, và `SWAP`
(đổi khối đang điều khiển khi tách đôi).

Cơ chế đặc biệt: ô `fragile` (khối đứng sẽ vỡ), cầu (bridge) đóng/mở bằng công tắc, công tắc
`soft`, `heavy`, `split` (teleport và tách khối).

**Hook cost**: cost của mỗi nước đi tính qua hàm `(state, action, next_state) -> float`.
Mặc định mỗi nước tốn 1.0 (`default_cost`, cấu hình ở bảng `COST` trong `engine/engine.py`).
Muốn thử cost khác:

```python
from engine.engine import Engine

def my_cost(state, action, next_state):
    return 1.0 if state.orient == next_state.orient else 1.5

problem = Engine("levels/<ten-level>.json", cost_fn=my_cost)
```

Chỉ UCS và A* dùng cost; BFS, DFS, IDS bỏ qua cost. Cost phải lớn hơn 0.
Hàm cost đề xuất (engine/costs.py, bật bằng python run_experiments.py --cost weighted) và A* dùng heuristic Manhattan có xét teleport.

## Định dạng màn chơi (MỘT định dạng cho engine, solver, GUI và thí nghiệm)

Mỗi màn là một file JSON trong `levels/`, tên file `<nhóm>_<số>_<tên>.json`:

```json
{
  "name": "Stone Bridge",
  "group": "fragile",
  "difficulty": 8,
  "benchmark": true,
  "hint": "Ô cam giòn: đừng đứng lên, hãy nằm ngang qua.",
  "optimal_moves": 15,
  "grid": ["#####", "#...#"],
  "start": [1, 1],
  "goal": [1, 3],
  "fragile": [[1, 2]],
  "bridges": {"B1": [[0, 6], [0, 7]]},
  "bridges_initial_open": [],
  "switches": [{"pos": [1, 3], "type": "soft", "targets": ["B1"], "mode": "toggle"}]
}
```

| Trường          | Ý nghĩa                                                                     |
| --------------- | --------------------------------------------------------------------------- |
| `grid`          | `#` = ô sàn, `.` = ô trống. Ô của cầu để là `.` và khai báo trong `bridges` |
| `group`         | `basic`, `fragile`, `switch`, `combined`                                    |
| `difficulty`    | thứ tự trong chiến dịch GUI                                                 |
| `benchmark`     | `true` = thuộc bộ test cố định dùng cho báo cáo                             |
| `optimal_moves` | **không sửa tay** — do `compute_optimal.py` ghi (SWAP tính là một nước)     |
| còn lại         | xem `engine/level.py` (kiểm tra hợp lệ ngay khi nạp)                        |

Màn hình web đọc cùng file này qua `/api/levels` (`engine/catalog.py: to_gui_level` đổi `#` → `O`
và đánh dấu `S`/`G`). GUI nạp cả 4 nhóm (`GUI_GROUPS` trong `serve.py`) và dùng `/api/step` làm nguồn luật.

## Thêm hoặc sửa một màn

1. Tạo/sửa file trong `levels/` (xem sơ đồ bằng `python compute_optimal.py --show <id>`).
2. `python compute_optimal.py <id>` — BFS tính và ghi `optimal_moves`; báo lỗi nếu màn benchmark không giải được.
3. `python -m pytest -q` — kiểm tra định dạng, 4 nhóm x 3 màn, `optimal_moves` đúng.
4. `python compute_optimal.py --check` — dùng trước khi commit (thoát mã 1 nếu có file lệch).

## Bộ test cố định (benchmark): 4 nhóm x 3 màn

`python compute_optimal.py --list` in bảng đầy đủ.

| Nhóm     | Nhỏ                                   | Vừa                                   | Lớn                                      |
| -------- | ------------------------------------- | ------------------------------------- | ---------------------------------------- |
| basic    | `basic_02_little_corner` 4x7 (7 nước) | `basic_05_garden_maze` 7x12 (12)      | `basic_07_grand_maze` 22x40 (38)         |
| fragile  | `fragile_01_stone_bridge` 4x16 (15)   | `fragile_02_two_crossings` 14x20 (25) | `fragile_03_glass_valley` 24x34 (37)     |
| switch   | `switch_01_soft_bridge` 3x13 (11)     | `switch_02_two_gates` 14x22 (28)      | `switch_03_twin_cubes` 11x21 (33, split) |
| combined | `combined_01_glass_gate` 7x22 (22)    | `combined_02_round_trip` 14x20 (39)   | `combined_03_grand_machine` 20x34 (42)   |

Màn trong `tests/fixtures/` là màn nhỏ dành riêng cho unit test (gồm một màn vô nghiệm), không thuộc benchmark.

## Thực nghiệm và báo cáo

```powershell
pip install -r requirements.txt
python run_experiments.py --repeat 3 --out results.csv   # ~75 giây (có đo bộ nhớ); thời gian = trung vị 3 lần
python plot_results.py                                   # figures/*.png + figures/results_tables.md
```

`figures/experiment_analysis.md` là bản nháp nhận xét cho phần Experiments (số liệu từ một lần chạy mẫu —
chạy lại trên máy nhóm và cập nhật số). Solver mới (vd. A\*) chỉ cần đăng ký trong `solvers/__init__.py`; chạy lại hai
lệnh trên là biểu đồ và bảng có thêm cột mới. `results.csv` bị `.gitignore`, nên hãy lưu bản dùng trong báo cáo ở nơi khác.

## Khi đổi hàm cost hoặc thêm A\*

- `run_experiments.py` và `plot_results.py` tự lấy số liệu mới (CSV có cột `cost`, hình `solution_cost.png`). Chạy lại cả hai.
- `COST` trong `engine/engine.py` chỉ theo hướng (U/D/L/R/SWAP). Muốn cost phụ thuộc ô (phạt ô giòn, ưu đãi công tắc),
  truyền hàm `cost_fn(state, action, next_state)` vào `Engine(level, cost_fn=...)` hoặc gán `engine.step_cost = ...`.
- `optimal_moves` là số nước tối thiểu (BFS), **không** phải chi phí tối thiểu: khi cost không đều, UCS/A* có thể dùng nhiều
  nước hơn `optimal_moves` mà vẫn tối ưu. So sánh UCS và A* bằng cột `cost`, không dùng `length`.
- Heuristic của A\* phải admissible với hàm cost mới: h không vượt chi phí nhỏ nhất của một nước nhân số nước còn lại tối thiểu.
- `tests/test_optimal_cost.py` kiểm tra A\* cho cùng chi phí với UCS trên 12 màn (tự chạy khi `"astar"` có trong `SOLVERS`).

## Thêm solver mới

1. Viết hàm `ten_solver(problem)` trong `solvers/`, trả về `SearchOutcome(path, cost, expanded)`
   (xem `solvers/base.py` và `solvers/ucs.py`).
2. Đăng ký trong `solvers/__init__.py`: `SOLVERS["ten_solver"] = ten_solver`.

`run_experiments.py` và `/api/solve` tự nhận solver mới, không cần sửa thêm.

## API

Tất cả endpoint POST nhận và trả JSON. Lỗi trả về `{"ok": false, "error": "..."}`.

**`GET /api/levels`**: danh sách level của giao diện.

**`POST /api/solve`**

```json
{"level_index": 0, "algorithm": "bfs", "cost": "uniform"}
```

`cost` (tuỳ chọn): `uniform` | `weighted` (chỉ UCS và A* dùng). Trả về: `solvable`, `path`, `cost`, `length`, `expanded`, `time_ms`, `memory_kb`.

**`POST /api/step`**

```json
{"level_index": 0, "state": {"orient": "S", "row": 0, "col": 0, "bridges": [], "split": null}, "action": "R"}
```

- Bỏ `state` thì dùng trạng thái ban đầu; bỏ `action` thì chỉ trả về trạng thái và thông tin tile.
- Trả về: `legal`, `status` (`playing`, `won`, `fell`), `state` mới, `cost`, `actions` (các nước hợp lệ),
  `attempt` (vị trí định tới khi rơi, chỉ có khi chưa tách đôi) và `tiles`
  (`fragile`, `bridges` kèm trạng thái mở/đóng, `switches`).

## Test

```bash
python -m pytest -q
```

Test kiểm tra: mọi solver tìm được lời giải hợp lệ trên level giải được, BFS/IDS/UCS cho cùng độ dài,
level không giải được trả về không có lời giải, UCS theo cost, và bảng chuyển tư thế khớp hợp đồng engine.

Xem thêm `INTEGRATION_NOTES.md` cho ghi chú tích hợp GUI và engine.