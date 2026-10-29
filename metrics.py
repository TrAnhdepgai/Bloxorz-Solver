"""Module đo đạc dùng chung cho mọi solver (BFS/DFS/IDS/UCS/A*).

Đo đúng 4 đại lượng của mục Experiments:

- Thời gian tìm kiếm: ``time.perf_counter()`` chỉ bọc lời gọi solver (không tính nạp màn).
  Lặp ``repeats`` lần và lấy **trung vị** (mặc định 3 lần, xem ``run_experiments.py --repeat``).
- Bộ nhớ đỉnh: ``tracemalloc`` trên **một lượt chạy riêng**, sau lượt bấm giờ.
  ``tracemalloc`` làm chậm nên không được bật khi đo thời gian. Đơn vị lưu: KB.
- Số node mở rộng: số trạng thái được lấy ra khỏi frontier và sinh hậu duệ
  (node đích không tính). IDS **cộng dồn** qua mọi vòng lặp độ sâu.
- Độ dài lời giải: số nước đi. ``cost`` là tổng step_cost (khác độ dài khi cost không đều).
  Mọi path đều được phát lại trên engine (``replay_path``); chỉ ``valid=True`` mới tính là giải được.
"""
import csv
import gc
import math
import statistics
import time
import tracemalloc
from dataclasses import asdict, dataclass, fields
from typing import Optional

from solvers.base import replay_path


@dataclass
class SolveResult:
    solver: str
    level: str
    found: bool
    valid: Optional[bool]        # path chạy lại trên engine có hợp lệ và tới đích không
    length: Optional[int]        # số nước đi
    cost: Optional[float]
    expanded: int
    time_s: float
    peak_mem_kb: float           # nan nếu không đo
    path: Optional[list]
    group: str = ""                      # nhóm màn (basic/fragile/switch/combined), do run_experiments điền
    optimal_moves: Optional[int] = None  # số nước tối ưu lưu trong file level (BFS), để so sánh độ dài lời giải
    name: str = ""
    rows: Optional[int] = None           # số hàng của lưới (cột "Cỡ" trong testset)
    cols: Optional[int] = None
    bridge_cells: Optional[int] = None   # số Ô bridge, không phải số cây cầu
    fragile_cells: Optional[int] = None
    switch_types: str = ""               # "soft,heavy,split" hoặc rỗng


def run_solver(solver, problem, level="", measure_memory=True, repeats=1):
    """Chạy một solver trên một problem, trả về SolveResult.

    Thời gian = trung vị của `repeats` lần gọi solver (không gồm nạp màn, không bật tracemalloc).
    Bộ nhớ đỉnh đo ở lượt riêng ngay sau đó."""
    name = solver.__name__

    # Lượt 1: đo thời gian (không bật tracemalloc)
    times = []
    for _ in range(max(1, repeats)):
        gc.collect()
        t0 = time.perf_counter()
        outcome = solver(problem)
        times.append(time.perf_counter() - t0)
    elapsed = statistics.median(times)

    # Lượt 2: đo bộ nhớ đỉnh
    peak_kb = math.nan
    if measure_memory:
        gc.collect()
        tracemalloc.start()
        try:
            solver(problem)
            _, peak_bytes = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        peak_kb = peak_bytes / 1024

    found = outcome.path is not None
    return SolveResult(
        solver=name,
        level=level,
        found=found,
        valid=replay_path(problem, outcome.path) if found else None,
        length=len(outcome.path) if found else None,
        cost=outcome.cost,
        expanded=outcome.expanded,
        time_s=elapsed,
        peak_mem_kb=peak_kb,
        path=outcome.path,
    )


def results_to_csv(results, filename):
    """Ghi kết quả ra CSV (path được nối thành chuỗi) để vẽ bảng/biểu đồ cho báo cáo."""
    names = [f.name for f in fields(SolveResult)]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        for r in results:
            row = asdict(r)
            row["path"] = "".join(r.path) if r.path else ""
            writer.writerow(row)


def format_table(results):
    """Bảng chữ để in ra terminal."""
    header = f"{'level':<28}{'solver':<8}{'found':<7}{'valid':<7}{'len':>5}{'opt':>5}{'cost':>8}{'expanded':>10}{'time(ms)':>11}{'peak(KB)':>11}"
    lines = [header, "-" * len(header)]
    for r in results:
        lines.append(
            f"{r.level:<28}{r.solver:<8}{str(r.found):<7}{str(r.valid):<7}"
            f"{'-' if r.length is None else r.length:>5}"
            f"{'-' if r.optimal_moves is None else r.optimal_moves:>5}"
            f"{'-' if r.cost is None else format(r.cost, '.1f'):>8}"
            f"{r.expanded:>10}{r.time_s * 1000:>11.2f}{r.peak_mem_kb:>11.1f}"
        )
    return "\n".join(lines)
