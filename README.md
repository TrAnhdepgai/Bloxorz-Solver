# Bloxorz-Solver

Dự án AI cơ bản: mô hình hóa trò chơi Bloxorz thành bài toán tìm kiếm, cài đặt các thuật toán
BFS, DFS, IDS, UCS, A\* để giải, và có giao diện web 3D để chơi tay hoặc xem solver giải.

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

| Đường dẫn             | Vai trò                                                                                  |
| --------------------- | ---------------------------------------------------------------------------------------- |
| `main.py`             | Điểm vào của dự án, gọi `serve.main()`                                                   |
| `serve.py`            | Server HTTP: phục vụ `web/` và các API                                                   |
| `engine/`             | Engine trò chơi: `state.py` (`State`, `SplitState`), `engine.py` (`Engine`, luật chơi), `level.py` (đọc và kiểm tra level), `catalog.py` (danh mục màn), `costs.py` (các hàm cost) |
| `solvers/`            | Các thuật toán tìm kiếm; `SOLVERS` là bảng đăng ký theo tên                              |
| `metrics.py`          | Đo thời gian, bộ nhớ đỉnh, số nút mở rộng, độ dài lời giải                               |
| `run_experiments.py`  | Chạy các solver trên bộ benchmark, in bảng và ghi CSV                                    |
| `levels/`             | Mọi màn chơi theo MỘT định dạng, dùng cho engine, solver, GUI và thực nghiệm             |
| `compute_optimal.py`  | Tính và ghi `optimal_moves` (BFS) cho từng màn                                           |
| `plot_results.py`     | Vẽ biểu đồ và bảng từ file CSV kết quả vào `figures/` và `tables/`                       |
| `web/`                | Giao diện Three.js                                                                       |
| `tests/`              | Test bằng pytest; `tests/fixtures/` là màn nhỏ riêng cho unit test                       |
| `ENGINE_CONTRACT.md`  | Hợp đồng interface của engine (State, `get_successors`, bảng chuyển tư thế, định dạng level) |
| `INTEGRATION_NOTES.md`| Ghi chú tích hợp engine, solver và GUI                                                   |

## Engine

Trạng thái của khối gồm tư thế (`S` đứng, `H` nằm ngang, `V` nằm dọc), vị trí góc trên trái,
tập cầu đang mở và trạng thái tách đôi (`split`). Các hành động: `U`, `D`, `L`, `R`, và `SWAP`
(đổi khối đang điều khiển khi tách đôi). Nước đi bất hợp lệ không được sinh ra, nên solver không tự kiểm tra luật.

Cơ chế đặc biệt: ô `fragile` (khối đứng sẽ vỡ), cầu (bridge) đóng/mở bằng công tắc, công tắc
`soft`, `heavy`, `split` (teleport và tách khối). Chi tiết luật nằm trong `ENGINE_CONTRACT.md` và `engine/engine.py`.

### Hook cost

Cost của mỗi nước đi tính qua hàm `(state, action, next_state) -> float`.
Mặc định mỗi nước tốn 1.0 (`default_cost`, cấu hình ở bảng `COST` trong `engine/engine.py`).
Muốn thử cost khác:

```python
from engine.engine import Engine

def my_cost(state, action, next_state):
    return 1.0 if state.orient == next_state.orient else 1.5

problem = Engine("levels/<ten-level>.json", cost_fn=my_cost)
```

Chỉ UCS và A\* dùng cost; BFS, DFS, IDS bỏ qua cost. Cost phải lớn hơn 0.

Hai hàm cost dựng sẵn nằm ở `engine/costs.py` (bảng `COST_FUNCTIONS`):

| Tên        | Quy ước                                                                                         | `cost_per_cell` |
| ---------- | ----------------------------------------------------------------------------------------------- | --------------- |
| `uniform`  | mọi nước tốn 1.0 (UCS khi đó cho cùng kết quả với BFS)                                          | 0.5             |
| `weighted` | khối nguyên đổi tư thế (đứng ↔ nằm) tốn 2.0, lăn giữ tư thế tốn 1.0; khi tách đôi mọi nước (kể cả `SWAP`) tốn 1.0 | 1.0 |

Chọn hàm cost bằng `python run_experiments.py --cost uniform|weighted` (**mặc định là `weighted`**) hoặc bằng ô chọn cost trên GUI.

Heuristic của A\* dựa trên khoảng cách Manhattan nhân với thuộc tính `cost_per_cell` của hàm cost: mỗi bước tốn ít nhất
`cost_per_cell` nhân số ô Manhattan mà bước đó rút ngắn được. Hàm cost không khai báo `cost_per_cell` thì A\* dùng h = 0 (trở thành UCS, vẫn đúng).

## Điều khiển giao diện

| Phím                          | Tác dụng                                                  |
| ----------------------------- | --------------------------------------------------------- |
| Mũi tên hoặc `W` `A` `S` `D`  | lăn khối (hướng tính theo góc nhìn hiện tại của camera)    |
| `Space` hoặc `F`              | đổi khối đang điều khiển khi khối tách đôi (`SWAP`)        |
| `R`                           | chơi lại màn hiện tại                                      |
| `N` hoặc `]` / `[`            | màn kế tiếp / màn trước                                    |
| `Q` / `E`                     | xoay camera trái / phải (kéo chuột cũng xoay được)         |
| `+` / `-`                     | phóng to / thu nhỏ                                         |
| `Esc`                         | mở hoặc đóng menu                                          |
| `Enter`                       | ở bảng kết quả: sang màn kế tiếp                           |

Trên màn hình có các nút Menu, Restart, Đổi khối (chỉ hiện khi tách đôi), hai nút xoay camera, ô chọn thuật toán
(BFS, DFS, IDS, UCS, A\*), ô chọn hàm cost (`uniform` hoặc `weighted`) và nút `Solve`. Sau khi chạy, dòng số liệu hiện
cost, số nút mở rộng, thời gian và bộ nhớ; lời giải được phát lại trên bảng, kể cả các nước `SWAP`. Phải chơi lại màn
(`Restart`) trước khi bấm `Solve` nếu khối đã thắng hoặc rơi.

## Định dạng màn chơi (MỘT định dạng cho engine, solver, GUI và thí nghiệm)

Mỗi màn là một file JSON trong `levels/`, tên file `NN_<chủ đề>_<tên>.json`, ví dụ `14_switch_soft_touch.json`:

- `NN` là số thứ tự hai chữ số, **trùng với `difficulty`** của màn.
- `<chủ đề>` là `group` của màn. Riêng các màn tách khối (19 đến 21) có chủ đề `split` nhưng vẫn thuộc `group` `switch`.

```json
{
  "name": "Stone Bridge",
  "group": "fragile",
  "difficulty": 9,
  "benchmark": true,
  "hint": "Ô cam giòn: đừng đứng lên, hãy nằm ngang qua.",
  "optimal_moves": 15,
  "grid": ["#####", "#...#"],
  "start": [1, 1],
  "goal": [1, 3],
  "fragile": [[1, 2]],
  "bridges": {
    "B1": [
      [0, 6],
      [0, 7]
    ]
  },
  "bridges_initial_open": [],
  "switches": [
    { "pos": [1, 3], "type": "soft", "targets": ["B1"], "mode": "toggle" }
  ]
}
```

| Trường          | Ý nghĩa                                                                                       |
| --------------- | --------------------------------------------------------------------------------------------- |
| `name`          | Tên hiển thị trên GUI, chuỗi không rỗng                                                       |
| `group`         | `basic`, `fragile`, `switch`, `combined`                                                      |
| `difficulty`    | Số nguyên, thứ tự trong chiến dịch GUI. Các màn đánh số liên tục `1..N`, trùng tiền tố `NN` của tên file |
| `benchmark`     | `true` = thuộc bộ test cố định dùng cho báo cáo (xem bên dưới)                                |
| `optimal_moves` | **không sửa tay**, do `compute_optimal.py` ghi (BFS, `SWAP` tính là một nước)                 |
| `grid`          | `#` = ô sàn, `.` = ô trống. Ô của cầu để là `.` và khai báo trong `bridges`                   |
| còn lại         | xem `engine/level.py` (kiểm tra hợp lệ ngay khi nạp); metadata (`name`, `group`, `difficulty`, `optimal_moves`) được kiểm tra thêm ở `engine/catalog.py: validate` |

Màn hình web đọc cùng file này qua `/api/levels` (`engine/catalog.py: to_gui_level` đổi `#` → `O`
và đánh dấu `S`/`G`). GUI nạp cả 4 nhóm (`GUI_GROUPS` trong `serve.py`), hiện là toàn bộ 27 màn, sắp theo
nhóm rồi theo `difficulty`, và dùng `/api/step` làm nguồn luật.

## Thêm hoặc sửa một màn

1. Tạo/sửa file trong `levels/` (xem sơ đồ bằng `python compute_optimal.py --show <id>`, với `<id>` là tên file bỏ đuôi `.json`).
2. `python compute_optimal.py <id>`: BFS tính và ghi `optimal_moves`; báo lỗi nếu màn benchmark không giải được.
3. `python -m pytest -q`: kiểm tra định dạng, tên file, số màn benchmark từng nhóm và `optimal_moves`.
4. `python compute_optimal.py --check`: dùng trước khi commit (thoát mã 1 nếu có file lệch).

Lưu ý khi thêm màn mới vì test ràng buộc khá chặt:

- `difficulty` của mọi màn phải là `1, 2, ..., N` liên tục, nên chèn màn vào giữa thì phải đánh số lại `difficulty` và đổi tên file các màn phía sau.
- `benchmark` phải là `true` khi và chỉ khi `difficulty >= 6`.
- Số màn benchmark mỗi nhóm và ô sàn tối thiểu của màn lớn nhất được khai báo ở đầu `tests/test_catalog.py` (`BENCHMARK_COUNTS`, `MIN_LARGEST_FLOOR`); thêm màn benchmark thì cập nhật hai bảng này.
- Test chỉ so sánh nội dung JSON đã parse, nên cách thụt lề và xuống dòng của file không bị ràng buộc.

## Bộ test cố định (benchmark)

Có 27 màn trong `levels/`. Màn 01 đến 05 là tutorial của nhóm `basic`, dùng cho chiến dịch GUI và không đưa vào báo cáo.
Từ `difficulty` 6 trở đi, mọi màn đều có `"benchmark": true`: **cùng một danh sách 22 màn cho mọi solver**, chia bốn nhóm theo `group`, khó dần:

| Nhóm       | Màn (`difficulty`) | Số màn | Nội dung                                                          |
| ---------- | ------------------ | ------ | ----------------------------------------------------------------- |
| `basic`    | 06 đến 08          | 3      | sàn / void / hố; không fragile, cầu, công tắc                     |
| `fragile`  | 09 đến 13          | 5      | có ô giòn                                                         |
| `switch`   | 14 đến 21          | 8      | cầu + công tắc (soft, heavy, split; toggle hoặc permanent); 19 đến 21 là màn tách khối |
| `combined` | 22 đến 27          | 6      | vừa ô giòn vừa cầu/công tắc                                       |

Mỗi nhóm có một màn lớn để thấy khác biệt giữa các thuật toán; ngưỡng ô sàn tối thiểu ở `MIN_LARGEST_FLOOR`
trong `tests/test_catalog.py`. Bộ benchmark gộp lại phải bao phủ đủ cơ chế: cả ba loại công tắc, cả hai chế độ
`toggle` và `permanent`, ô giòn, và ít nhất một màn `combined` có cả ô giòn lẫn công tắc.

`python compute_optimal.py --list` in thống kê. Bảng đưa vào báo cáo (cỡ hàng×cột, số ô bridge, số nước tối ưu BFS)
là `tables/testset.tex`, sinh tự động, không chép tay.

Màn trong `tests/fixtures/` là màn nhỏ dành riêng cho unit test (gồm một màn vô nghiệm), không thuộc benchmark.

## Thực nghiệm và báo cáo

Cách đo (khớp mục Thực nghiệm): thời gian = trung vị `--repeat` lần `time.perf_counter()` **chỉ quanh solver** (mặc định 3);
bộ nhớ đỉnh = `tracemalloc` ở **lượt chạy riêng**; node mở rộng = trạng thái được lấy ra và sinh hậu duệ
(IDS cộng dồn mọi tầng); độ dài = số nước, kèm `cost` khi cost không đều; mọi path được replay trên engine.

```powershell
python run_experiments.py --repeat 3 --out figures/results_used_in_report.csv
python plot_results.py --csv figures/results_used_in_report.csv --out figures --tables tables
```

Các tùy chọn khác của `run_experiments.py`:

| Tùy chọn                          | Ý nghĩa                                                         |
| --------------------------------- | --------------------------------------------------------------- |
| `--solvers bfs ucs astar`         | chỉ chạy các solver này (mặc định: mọi solver trong `SOLVERS`)   |
| `--group fragile switch`          | chỉ chạy các nhóm này                                            |
| `--all`                           | chạy cả màn không thuộc benchmark                                |
| `--cost uniform` / `weighted`     | hàm cost của engine (mặc định `weighted`)                        |
| `--repeat N`                      | số lần chạy để lấy thời gian trung vị (mặc định 3)               |
| `--no-memory`                     | bỏ lượt đo bộ nhớ (nhanh hơn)                                    |
| `--levels DIR`, `--out FILE`      | thư mục màn chơi (mặc định `levels/`) và file CSV đầu ra         |

Ví dụ chạy nhanh hai solver trên nhóm fragile, không đo bộ nhớ:

```powershell
python run_experiments.py --solvers bfs astar --group fragile --no-memory --out results.csv
```

Sinh ra `tables/testset.tex`, `tables/results_by_tier.tex`, `tables/results_detail.tex` (phụ lục) và
`figures/fig_{expanded,time,memory,length,scaling}.pdf`. Trung bình theo nhóm chỉ tính màn giải được (`valid`).
Vì số màn mỗi nhóm không bằng nhau (3, 5, 8, 6), so sánh giữa các nhóm nên dựa trên trung bình theo nhóm chứ không dựa trên tổng.
Solver mới chỉ cần đăng ký trong `solvers/__init__.py` rồi chạy lại hai lệnh. `results.csv` bị `.gitignore`;
bản dùng trong báo cáo là `figures/results_used_in_report.csv`.

## Khi đổi hàm cost

- `run_experiments.py` và `plot_results.py` tự lấy số liệu mới (CSV có cột `cost`; bảng nhóm có cột Cost, không vẽ riêng hình cost). Chạy lại cả hai.
- `COST` trong `engine/engine.py` chỉ theo hướng (U/D/L/R/SWAP). Muốn cost phụ thuộc ô (phạt ô giòn, ưu đãi công tắc),
  truyền hàm `cost_fn(state, action, next_state)` vào `Engine(level, cost_fn=...)` hoặc gán `engine.step_cost = ...`.
- `optimal_moves` là số nước tối thiểu (BFS), **không** phải chi phí tối thiểu: khi cost không đều, UCS/A\* có thể dùng nhiều
  nước hơn `optimal_moves` mà vẫn tối ưu. So sánh UCS và A\* bằng cột `cost`, không dùng `length`.
- Hàm cost mới muốn A\* có heuristic thì phải khai báo `cost_fn.cost_per_cell` (xem `engine/costs.py`) sao cho mỗi bước tốn ít nhất `cost_per_cell` nhân số ô Manhattan mà nó rút ngắn; không khai báo thì A\* dùng h = 0. Đổi giá trị này thì chạy lại `tests/test_heuristic.py` (kiểm tra h admissible và consistent).
- `tests/test_optimal_cost.py` kiểm tra A\* cho cùng chi phí với UCS (tự chạy khi `"astar"` có trong `SOLVERS`).

## Thêm solver mới

1. Viết hàm `ten_solver(problem)` trong `solvers/`, trả về `SearchOutcome(path, cost, expanded)`
   (xem `solvers/base.py` và `solvers/ucs.py`).
2. Đăng ký trong `solvers/__init__.py`: `SOLVERS["ten_solver"] = ten_solver`.

`run_experiments.py` và `/api/solve` tự nhận solver mới, không cần sửa thêm.

## API

Tất cả endpoint POST nhận và trả JSON. Lỗi đầu vào trả HTTP 400 `{"ok": false, "error": "..."}`;
endpoint không tồn tại trả 404; lỗi bên trong solver trả 500. `level_index` là chỉ số trong danh sách
của `/api/levels` (sắp theo nhóm rồi theo `difficulty`, hiện là `0` đến `26`).

**`GET /api/levels`**: danh sách level của giao diện.

**`POST /api/solve`**

```json
{ "level_index": 0, "algorithm": "bfs", "cost": "uniform" }
```

`algorithm` là một khóa của `SOLVERS` (`bfs`, `dfs`, `ids`, `ucs`, `astar`). `cost` (tuỳ chọn): `uniform` | `weighted` (chỉ UCS và A\* dùng).
Trả về: `ok`, `level`, `algorithm`, `cost_mode`, `solvable`, `path`, `cost`, `length`, `expanded`, `time_ms`, `memory_kb`.
Màn không giải được thì `path`, `cost`, `length` là `null`. Solver chạy hai lượt, một lượt đo thời gian và một lượt đo bộ nhớ.

**`POST /api/step`**

```json
{
  "level_index": 0,
  "state": { "orient": "S", "row": 0, "col": 0, "bridges": [], "split": null },
  "action": "R"
}
```

- `action` thuộc `U`, `D`, `L`, `R`, `SWAP`. Bỏ `state` thì dùng trạng thái ban đầu; bỏ `action` thì chỉ trả về trạng thái và thông tin tile.
- `split` là `null` hoặc `{"cubes": [[r, c], [r, c]], "active": 0}`. Khi đang tách đôi, `orient` là `"S"` và `row`/`col` chỉ là giá trị giữ chỗ (0).
- Trả về: `legal`, `status` (`playing`, `won`, `fell`), `state` mới, `cost`, `actions` (các nước hợp lệ),
  `attempt` (vị trí định tới khi rơi, chỉ có khi chưa tách đôi) và `tiles`
  (`fragile`, `bridges` kèm trạng thái mở/đóng, `switches`). Nước đi bất hợp lệ cho `status = "fell"` và giữ nguyên `state`.

## Test

```bash
python -m pytest -q
```

Các nhóm test chính:

- **Engine:** bảng chuyển tư thế khớp hợp đồng engine; nước đi bất hợp lệ; thắng khi đứng trên goal; công tắc, cầu, split.
- **Solver:** mọi solver tìm được lời giải hợp lệ trên level giải được; BFS/IDS/UCS cho cùng độ dài; level không giải được trả về không có lời giải; UCS theo cost; A\* cho cùng chi phí với UCS.
- **Heuristic** (`tests/test_heuristic.py`): h(goal) = 0, h admissible và consistent trên toàn bộ không gian trạng thái của từng màn (bỏ qua màn có hơn 20 000 trạng thái), với 3 cấu hình cost: mặc định của engine, `uniform`, `weighted`.
- **Catalog** (`tests/test_catalog.py`): tên file `NN_<chủ đề>_<tên>` khớp `difficulty` và `group`; `difficulty` liên tục `1..N`; số màn benchmark mỗi nhóm và `benchmark` khớp `difficulty >= 6`; mỗi nhóm có màn đủ lớn; bộ benchmark bao phủ mọi cơ chế; mọi màn benchmark giải được và `optimal_moves` đúng BFS; chuyển đổi sang GUI giữ nguyên hình học; metadata sai bị từ chối.

Xem thêm `INTEGRATION_NOTES.md` cho ghi chú tích hợp GUI và engine.