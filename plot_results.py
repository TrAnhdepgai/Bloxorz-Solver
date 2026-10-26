"""Vẽ biểu đồ và bảng markdown từ results.csv (do run_experiments.py ghi).

    python plot_results.py                       # đọc results.csv -> figures/*.png + figures/results_tables.md
    python plot_results.py --csv results.csv --out figures

Cần: pip install matplotlib. Solver mới (vd. astar) tự xuất hiện trong biểu đồ khi có trong CSV.
"""
import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# (cột CSV, nhãn trục, hệ số nhân, tên file)
METRICS = [
    ("expanded", "Số node mở rộng (log)", 1, "expanded_nodes"),
    ("time_s", "Thời gian tìm kiếm, ms (log)", 1000, "search_time"),
    ("peak_mem_kb", "Bộ nhớ đỉnh, KB (log)", 1, "peak_memory"),
    ("length", "Độ dài lời giải, số nước (log)", 1, "solution_length"),
    ("cost", "Chi phí lời giải (log)", 1, "solution_cost"),   # khác độ dài khi hàm cost không đều
]
COLORS = {"bfs": "#4C78A8", "dfs": "#E45756", "ids": "#F58518", "ucs": "#54A24B", "astar": "#B279A2"}
GROUP_NAMES = {"basic": "Cơ bản", "fragile": "Ô giòn", "switch": "Công tắc", "combined": "Kết hợp"}


def read_results(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("expanded", "time_s", "peak_mem_kb", "length", "cost", "optimal_moves"):
            try:
                r[k] = float(r[k])
            except (TypeError, ValueError):
                r[k] = math.nan
    return rows


def short(level):
    parts = level.split("_")
    return " ".join(parts[2:]) if len(parts) > 2 else level


def draw(ax, rows, levels, solvers, key, ylabel, scale, optimal=False):
    width = 0.8 / len(solvers)
    for i, s in enumerate(solvers):
        vals = [next((r[key] * scale for r in rows if r["level"] == lv and r["solver"] == s), math.nan) for lv in levels]
        xs = [j + (i - (len(solvers) - 1) / 2) * width for j in range(len(levels))]
        ax.bar(xs, vals, width, label=s.upper(), color=COLORS.get(s))
    if optimal:                                            # vạch đen = số nước tối ưu (BFS)
        opt = [next(r["optimal_moves"] for r in rows if r["level"] == lv) for lv in levels]
        ax.scatter(range(len(levels)), opt, marker="_", s=900, color="black", zorder=5, label="Tối ưu")
    ax.set_yscale("log")
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels([short(lv) for lv in levels], rotation=40, ha="right", fontsize=8)
    ax.grid(axis="y", which="major", alpha=0.3)
    ax.set_axisbelow(True)
    groups = [next(r["group"] for r in rows if r["level"] == lv) for lv in levels]
    for j in range(1, len(levels)):                        # vạch phân cách nhóm + nhãn nhóm
        if groups[j] != groups[j - 1]:
            ax.axvline(j - 0.5, color="gray", ls=":", lw=1)
    top = ax.get_ylim()[1]
    for g in dict.fromkeys(groups):
        idx = [j for j, x in enumerate(groups) if x == g]
        ax.text(sum(idx) / len(idx), top, GROUP_NAMES.get(g, g), ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xlim(-0.6, len(levels) - 0.4)


def tables_markdown(rows, levels, solvers):
    out = []
    for key, label, scale, _ in METRICS:
        if all(math.isnan(r[key]) for r in rows):
            continue
        out += [f"**{label.replace(' (log)', '')}**", "",
                "| Màn | Nhóm | " + " | ".join(s.upper() for s in solvers)
                + (" | Tối ưu |" if key == "length" else " | Nhỏ nhất |" if key == "cost" else " |"),
                "|---|---|" + "---:|" * (len(solvers) + (key in ("length", "cost")))]
        for lv in levels:
            cells = []
            for s in solvers:
                v = next((r[key] * scale for r in rows if r["level"] == lv and r["solver"] == s), math.nan)
                cells.append("-" if math.isnan(v) else (f"{v:,.0f}" if v >= 100 or key in ("expanded", "length")
                                                      else f"{v:,.2f}"))
            grp = next(r["group"] for r in rows if r["level"] == lv)
            opt = []
            if key == "length":
                opt = [str(int(next(r["optimal_moves"] for r in rows if r["level"] == lv)))]
            elif key == "cost":
                costs = [r["cost"] for r in rows if r["level"] == lv and not math.isnan(r["cost"])]
                opt = [f"{min(costs):,.2f}"]
            out.append(f"| {lv} | {grp} | " + " | ".join(cells + opt) + " |")
        out.append("")
    return "\n".join(out)


def summary_markdown(rows, levels, solvers, ref="bfs"):
    """Tỉ lệ của từng solver so với BFS trên mọi màn: min–max (trung vị) và số màn không tệ hơn BFS.
    Dùng để lấy số liệu viết nhận xét cho đúng với lần chạy hiện tại."""
    if ref not in solvers:
        return ""

    def get(lv, s, key):
        return next((r[key] for r in rows if r["level"] == lv and r["solver"] == s), math.nan)

    def cell(vals):
        vals = [v for v in vals if not math.isnan(v)]
        if not vals:
            return "-"
        vals_sorted = sorted(vals)
        med = vals_sorted[len(vals) // 2] if len(vals) % 2 else (vals_sorted[len(vals) // 2 - 1] + vals_sorted[len(vals) // 2]) / 2
        return f"{min(vals):.2f}–{max(vals):.2f} (tb {med:.2f}); ≤BFS: {sum(v <= 1 for v in vals)}/{len(vals)}"

    out = [f"Tỉ lệ so với {ref.upper()} (giá trị < 1 nghĩa là tốt hơn {ref.upper()}), trên {len(levels)} màn: "
           "min–max (trung vị tb); ≤BFS = số màn solver không tệ hơn BFS.", "",
           "| Solver | Node mở rộng | Thời gian | Bộ nhớ đỉnh | Độ dài / tối ưu |", "|---|---|---|---|---|"]
    for s in solvers:
        if s == ref:
            continue
        cols = [cell([get(lv, s, k) / get(lv, ref, k) for lv in levels]) for k in ("expanded", "time_s", "peak_mem_kb")]
        cols.append(cell([get(lv, s, "length") / get(lv, s, "optimal_moves") for lv in levels]))
        out.append(f"| {s.upper()} | " + " | ".join(cols) + " |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results.csv")
    ap.add_argument("--out", default="figures")
    args = ap.parse_args()

    rows = read_results(args.csv)
    levels = list(dict.fromkeys(r["level"] for r in rows))
    solvers = list(dict.fromkeys(r["solver"] for r in rows))
    out = Path(args.out)
    out.mkdir(exist_ok=True)

    usable = [m for m in METRICS if not all(math.isnan(r[m[0]]) for r in rows)]
    for key, label, scale, name in usable:                 # mỗi chỉ số một hình riêng (chèn vào báo cáo)
        fig, ax = plt.subplots(figsize=(11, 4.6))
        draw(ax, rows, levels, solvers, key, label, scale, optimal=(key == "length"))
        ax.legend(ncol=len(solvers) + 1, fontsize=8, loc="upper left", bbox_to_anchor=(0, -0.28))
        fig.tight_layout()
        fig.savefig(out / f"{name}.png", dpi=200)
        plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(15, 9))        # hình tổng quan 2x2
    for ax, (key, label, scale, _) in zip(axes.flat, usable[:4]):   # hình tổng quan: 4 chỉ số đầu
        draw(ax, rows, levels, solvers, key, label, scale, optimal=(key == "length"))
    axes.flat[0].legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "overview.png", dpi=200)
    plt.close(fig)

    (out / "results_tables.md").write_text(tables_markdown(rows, levels, solvers), encoding="utf-8")
    (out / "summary_vs_bfs.md").write_text(summary_markdown(rows, levels, solvers), encoding="utf-8")
    print(f"Đã ghi {len(usable) + 1} hình, results_tables.md và summary_vs_bfs.md vào {out}/")


if __name__ == "__main__":
    main()
