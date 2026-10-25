"""Tự tính `optimal_moves` cho mọi màn trong levels/ bằng BFS và ghi ngược vào file JSON.

    python compute_optimal.py                  # tính + ghi các file bị thiếu/lệch
    python compute_optimal.py --check          # chỉ kiểm tra, thoát mã 1 nếu có file lệch (dùng trước khi commit)
    python compute_optimal.py fragile combined # chỉ các màn có id chứa một trong các chuỗi này
    python compute_optimal.py --list           # bảng thống kê màn (kích thước, số ô giòn, cầu, công tắc)
    python compute_optimal.py --show fragile_03  # in sơ đồ ASCII của màn

`optimal_moves` = số nước ÍT NHẤT để thắng (SWAP của khối tách đôi cũng tính là một nước).
BFS tối ưu theo số nước nên giá trị này không phụ thuộc hàm chi phí của UCS/A*.
"""
import argparse
import sys
import time

from engine import Engine
from engine.catalog import LEVEL_DIR, ascii_preview, describe, load_catalog, write_level
from solvers import bfs
from solvers.base import replay_path


def selected(entries, patterns):
    return [e for e in entries if not patterns or any(p in e["id"] for p in patterns)]


def solve(data):
    """Trả về (độ dài lời giải ngắn nhất hoặc None, số node đã mở rộng, thời gian giây)."""
    engine = Engine(data)
    t0 = time.perf_counter()
    outcome = bfs(engine)
    elapsed = time.perf_counter() - t0
    if outcome.path is None:
        return None, outcome.expanded, elapsed
    if not replay_path(engine, outcome.path):          # tự kiểm: chạy lại đường đi trên engine
        raise RuntimeError("BFS trả về đường đi không hợp lệ — engine hoặc solver có lỗi")
    return len(outcome.path), outcome.expanded, elapsed


def cmd_list(entries):
    print(f"{'id':<28}{'group':<10}{'size':>8}{'floor':>7}{'fragile':>9}{'bridges':>9}  {'switches':<18}{'opt':>5}  bench")
    for e in entries:
        d, info = e["data"], describe(e["data"])
        opt = d.get("optimal_moves")
        print(f"{e['id']:<28}{d['group']:<10}{info['size']:>8}{info['floor']:>7}{info['fragile']:>9}"
              f"{info['bridges']:>9}  {info['switches']:<18}{'-' if opt is None else opt:>5}  "
              f"{'yes' if d.get('benchmark') else ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("patterns", nargs="*", help="chỉ xử lý các màn có id chứa chuỗi này")
    ap.add_argument("--dir", default=str(LEVEL_DIR), help="thư mục màn chơi (mặc định: levels/)")
    ap.add_argument("--check", action="store_true", help="không ghi file; mã thoát 1 nếu có file lệch")
    ap.add_argument("--list", action="store_true", help="in bảng thống kê rồi thoát")
    ap.add_argument("--show", action="store_true", help="in sơ đồ ASCII của các màn được chọn rồi thoát")
    args = ap.parse_args()

    entries = selected(load_catalog(args.dir), args.patterns)
    if not entries:
        sys.exit("Không có màn nào khớp.")
    if args.list:
        return cmd_list(entries)
    if args.show:
        for e in entries:
            print(f"== {e['id']} ({e['data']['name']})\n{ascii_preview(e['data'])}\n")
        return

    print(f"{'id':<28}{'stored':>7}{'bfs':>6}  {'status':<11}{'expanded':>9}{'ms':>8}")
    bad = 0
    for e in entries:
        d = e["data"]
        stored = d.get("optimal_moves")
        found, expanded, secs = solve(d)
        if found is None:
            status = "UNSOLVABLE"
            if d.get("benchmark"):
                bad += 1                      # màn trong bộ test cố định bắt buộc phải giải được
        elif stored == found:
            status = "ok"
        else:
            status = "MISMATCH" if stored is not None else "new"
        if found != stored and not (found is None and stored is None):
            if args.check:
                bad += status != "UNSOLVABLE"
            else:
                d["optimal_moves"] = found
                write_level(e["path"], d)
                status += " ->written"
        print(f"{e['id']:<28}{'-' if stored is None else stored:>7}{'-' if found is None else found:>6}  "
              f"{status:<11}{expanded:>9}{secs * 1000:>8.1f}")
    if bad:
        print(f"\n{bad} vấn đề: " + ("file lệch hoặc " if args.check else "") + "màn benchmark không giải được.")
        sys.exit(1)
    print("\nTất cả optimal_moves khớp BFS." if args.check else "\nXong.")


if __name__ == "__main__":
    main()
