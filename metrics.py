"""Module đo đạc dùng chung cho mọi solver (BFS/DFS/IDS/UCS/A*).

Đo 4 thứ theo đề: Search Time, Peak Memory, Expanded Nodes, Solution Length.
Thời gian và bộ nhớ được đo ở HAI lượt chạy riêng, vì tracemalloc làm chương trình chậm đi
đáng kể và sẽ làm sai số đo thời gian.
"""
import csv
import gc
import math
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


def run_solver(solver, problem, level="", measure_memory=True):
    """Chạy một solver trên một problem, trả về SolveResult."""
    name = solver.__name__

    # Lượt 1: đo thời gian (không bật tracemalloc)
    gc.collect()
    t0 = time.perf_counter()
    outcome = solver(problem)
    elapsed = time.perf_counter() - t0

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
    header = f"{'level':<16}{'solver':<8}{'found':<7}{'valid':<7}{'len':>5}{'cost':>8}{'expanded':>10}{'time(ms)':>11}{'peak(KB)':>11}"
    lines = [header, "-" * len(header)]
    for r in results:
        lines.append(
            f"{r.level:<16}{r.solver:<8}{str(r.found):<7}{str(r.valid):<7}"
            f"{'-' if r.length is None else r.length:>5}"
            f"{'-' if r.cost is None else format(r.cost, '.1f'):>8}"
            f"{r.expanded:>10}{r.time_s * 1000:>11.2f}{r.peak_mem_kb:>11.1f}"
        )
    return "\n".join(lines)
