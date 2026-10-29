"""Chạy các solver trên bộ màn chơi CỐ ĐỊNH (benchmark), in bảng và ghi CSV.

Bộ benchmark = mọi file trong levels/ có "benchmark": true, dùng chung cho mọi solver.
Bốn nhóm (khó dần): basic (không tile nâng cao), fragile, switch (cầu/công tắc/split),
combined (fragile + cầu/công tắc).

Thời gian = trung vị của --repeat lần (mặc định 3), chỉ tính solver().
Bộ nhớ = lượt tracemalloc riêng. Chi tiết ở metrics.py.

Ví dụ:
    python run_experiments.py --repeat 3 --out figures/results_used_in_report.csv
    python plot_results.py --csv figures/results_used_in_report.csv --out figures --tables tables
    python run_experiments.py --group fragile switch
    python run_experiments.py --all
    python run_experiments.py --solvers bfs ucs --no-memory
"""
import argparse
import importlib

from engine.catalog import GROUPS, LEVEL_DIR, describe, load_catalog
from engine.costs import COST_FUNCTIONS
from metrics import format_table, results_to_csv, run_solver
from solvers import SOLVERS


def load_engine_class(spec):
    module_name, class_name = spec.split(":")
    return getattr(importlib.import_module(module_name), class_name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="engine.engine:Engine", help="module:Class")
    ap.add_argument("--levels", default=str(LEVEL_DIR), help="thư mục chứa file .json")
    ap.add_argument("--group", nargs="+", choices=GROUPS, help="chỉ chạy các nhóm này")
    ap.add_argument("--all", action="store_true", help="chạy cả màn không thuộc bộ benchmark")
    ap.add_argument("--solvers", nargs="+", default=list(SOLVERS), choices=list(SOLVERS))
    ap.add_argument("--cost", default="weighted", choices=list(COST_FUNCTIONS),
                help="hàm cost của engine: uniform (mọi nước 1.0) hoặc weighted (đổi tư thế tốn 2.0)")
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--repeat", type=int, default=3, help="số lần chạy để lấy thời gian trung vị (mặc định 3)")
    ap.add_argument("--no-memory", action="store_true", help="bỏ qua lượt đo bộ nhớ (nhanh hơn)")
    args = ap.parse_args()

    Engine = load_engine_class(args.engine)
    entries = load_catalog(args.levels, benchmark_only=not args.all, groups=args.group)
    if not entries:
        raise SystemExit("Không có màn nào được chọn (kiểm tra cờ \"benchmark\" trong file level).")

    results = []
    for entry in entries:
        data = entry["data"]
        problem = Engine(str(entry["path"]), cost_fn=COST_FUNCTIONS[args.cost])        
        print(f"[{data['group']}] {entry['id']} ...", flush=True)
        for name in args.solvers:
            r = run_solver(SOLVERS[name], problem, entry["id"], measure_memory=not args.no_memory,
                           repeats=args.repeat)
            info = describe(data)
            r.group, r.optimal_moves = data["group"], data.get("optimal_moves")
            r.name = data.get("name") or ""
            r.rows, r.cols = info["rows"], info["cols"]
            r.bridge_cells = info["bridge_cells"]
            r.fragile_cells = info["fragile"]
            r.switch_types = "" if info["switches"] == "-" else info["switches"]
            results.append(r)

    print("\n" + format_table(results))
    results_to_csv(results, args.out)
    print(f"\nĐã ghi {len(results)} dòng vào {args.out}")
    stale = {r.level for r in results if r.solver == "bfs" and r.found
             and r.optimal_moves is not None and r.length != r.optimal_moves}
    if stale:
        print("CẢNH BÁO: optimal_moves lệch BFS ở", sorted(stale), "-> chạy: python compute_optimal.py")


if __name__ == "__main__":
    main()
