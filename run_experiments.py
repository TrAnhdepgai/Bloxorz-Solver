"""Chạy các solver trên bộ màn chơi cố định, in bảng và ghi CSV.

Ví dụ:
    python run_experiments.py                                   # engine giả, mọi level trong levels/
    python run_experiments.py --engine my_engine:Engine         # engine thật của A
    python run_experiments.py --solvers bfs ucs --no-memory
"""
import argparse
import glob
import importlib
import os

from metrics import format_table, results_to_csv, run_solver
from solvers import SOLVERS


def load_engine_class(spec):
    module_name, class_name = spec.split(":")
    return getattr(importlib.import_module(module_name), class_name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="fake_engine:Engine", help="module:Class")
    ap.add_argument("--levels", default="levels", help="thư mục chứa file .json")
    ap.add_argument("--solvers", nargs="+", default=list(SOLVERS), choices=list(SOLVERS))
    ap.add_argument("--out", default="results.csv")
    ap.add_argument("--no-memory", action="store_true", help="bỏ qua lượt đo bộ nhớ (nhanh hơn)")
    args = ap.parse_args()

    Engine = load_engine_class(args.engine)
    results = []
    for path in sorted(glob.glob(os.path.join(args.levels, "*.json"))):
        level = os.path.splitext(os.path.basename(path))[0]
        problem = Engine(path)
        for name in args.solvers:
            results.append(run_solver(SOLVERS[name], problem, level, measure_memory=not args.no_memory))

    print(format_table(results))
    results_to_csv(results, args.out)
    print(f"\nĐã ghi {len(results)} dòng vào {args.out}")


if __name__ == "__main__":
    main()
