# Bloxorz Solver

````

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
````

| Trường          | Ý nghĩa                                                                     |
| --------------- | --------------------------------------------------------------------------- |
| `grid`          | `#` = ô sàn, `.` = ô trống. Ô của cầu để là `.` và khai báo trong `bridges` |
| `group`         | `basic`, `fragile`, `switch`, `combined`                                    |
| `difficulty`    | thứ tự trong chiến dịch GUI                                                 |
| `benchmark`     | `true` = thuộc bộ test cố định dùng cho báo cáo                             |
| `optimal_moves` | **không sửa tay** — do `compute_optimal.py` ghi (SWAP tính là một nước)     |
| còn lại         | xem `engine/level.py` (kiểm tra hợp lệ ngay khi nạp)                        |

Màn hình web đọc cùng file này qua `/api/levels` (`engine/catalog.py: to_gui_level` đổi `#` → `O`
và đánh dấu `S`/`G`). Hiện GUI chỉ nạp nhóm `basic` — thêm nhóm vào `GUI_GROUPS` trong `serve.py`
khi renderer đã vẽ và mô phỏng được ô giòn / cầu / công tắc.

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
- `COST` trong `engine/engine.py` chỉ theo hướng (U/D/L/R/SWAP). Muốn phạt ô giòn hoặc ưu đãi công tắc, tính thêm
  chi phí trong `Engine.get_successors` (nơi biết ô nào được đặt chân).
- `optimal_moves` là số nước tối thiểu (BFS), **không** phải chi phí tối thiểu: khi cost không đều, UCS/A* có thể dùng nhiều
  nước hơn `optimal_moves` mà vẫn tối ưu. So sánh UCS và A* bằng cột `cost`, không dùng `length`.
- Heuristic của A\* phải admissible với hàm cost mới: h không vượt chi phí nhỏ nhất của một nước nhân số nước còn lại tối thiểu.
- `tests/test_optimal_cost.py` kiểm tra A\* cho cùng chi phí với UCS trên 12 màn (tự chạy khi `"astar"` có trong `SOLVERS`).
