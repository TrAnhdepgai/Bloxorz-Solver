# Bloxorz-Solver

Dự án AI cơ bản: mô hình hóa trò chơi Bloxorz thành bài toán tìm kiếm, cài đặt các thuật toán
BFS, DFS, IDS, UCS để giải, và có giao diện web 3D để chơi tay hoặc xem solver giải.

## Yêu cầu

- Python 3.9 trở lên
- `pip install -r requirements.txt` (chỉ cần `pytest` để chạy test; phần còn lại dùng thư viện chuẩn)
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
| `levels/` | Level theo schema của engine, dùng cho thực nghiệm và test |
| `gui_levels/` | Level cho giao diện web (có tên, gợi ý, độ khó...) |
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

Chỉ UCS (và A* sau này) dùng cost; BFS, DFS, IDS bỏ qua cost. Cost phải lớn hơn 0.

## Định dạng level (`levels/`)

```json
{
  "grid": ["####", "####"],
  "start": [0, 0],
  "goal": [1, 3],
  "fragile": [[0, 2]],
  "bridges": {"B1": [[0, 3]]},
  "bridges_initial_open": [],
  "switches": [{"pos": [0, 1], "type": "soft", "targets": ["B1"], "mode": "toggle"}]
}
```

- `grid`: `#` là sàn, `.` là trống. Các hàng phải cùng độ dài.
- `start`, `goal`: `[hàng, cột]`, phải nằm trên ô `#` và không nằm trên ô fragile.
- Các khóa `fragile`, `bridges`, `bridges_initial_open`, `switches` là tùy chọn.
- Switch có `type` là `soft`, `heavy` hoặc `split`; `mode` là `toggle` (mặc định) hoặc `permanent`
  (khi đó cần `"set": "open"` hoặc `"close"`); switch `split` cần `teleport` gồm 2 toạ độ không liền kề.

Level trong `gui_levels/` dùng ký tự `S` (xuất phát), `G` (đích), `O` (sàn), `.` (trống),
và `serve.py` tự chuyển sang schema của engine khi cần.

## Chạy thực nghiệm

```bash
python run_experiments.py
python run_experiments.py --solvers bfs ucs --no-memory
python run_experiments.py --levels levels --out results.csv
```

Mặc định dùng engine `engine.engine:Engine`, chạy mọi solver trên mọi level trong `levels/`,
in bảng kết quả và ghi `results.csv`. Mỗi dòng gồm: solver, level, tìm được hay không, lời giải
có hợp lệ không, độ dài, cost, số nút mở rộng, thời gian, bộ nhớ đỉnh. Thời gian và bộ nhớ đo ở
hai lượt chạy riêng vì `tracemalloc` làm chậm chương trình.

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
{"level_index": 0, "algorithm": "bfs"}
```

Trả về: `solvable`, `path`, `cost`, `length`, `expanded`, `time_ms`, `memory_kb`.

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