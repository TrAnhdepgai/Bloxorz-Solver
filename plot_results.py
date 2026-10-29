"""Sinh bảng LaTeX và biểu đồ PDF đúng chỗ \\input / \\figorwarn của báo cáo.

    python plot_results.py
    python plot_results.py --csv figures/results_used_in_report.csv --out figures --tables tables

Đầu ra (đúng mẫu mục Thực nghiệm):
    tables/testset.tex           các màn: Cỡ, Fragile, Bridge (số ô), Switch, Tối ưu (BFS)
    tables/results_by_tier.tex   trung bình theo nhóm, chỉ trên màn giải được (replay hợp lệ)
    tables/results_detail.tex    chi tiết từng màn (phụ lục)
    figures/fig_expanded.pdf     node mở rộng trung bình theo nhóm (thang log)
    figures/fig_time.pdf         thời gian trung bình theo nhóm, ms (thang log)
    figures/fig_memory.pdf       bộ nhớ đỉnh trung bình theo nhóm, KB (thang log)
    figures/fig_length.pdf       độ dài lời giải trung bình theo nhóm (số nước, thang tuyến tính)
    figures/fig_scaling.pdf      node mở rộng theo độ dài tối ưu (mỗi chấm là một màn)

Trung bình = trung bình cộng. "Giải" = số màn giải được / tổng số màn trong nhóm.
Một màn tính là giải được khi found và valid không phải False (path đã replay trên engine).
"""
import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

COLORS = {"bfs": "#4C78A8", "dfs": "#E45756", "ids": "#F58518", "ucs": "#54A24B", "astar": "#B279A2"}
GROUP_ORDER = ("basic", "fragile", "switch", "combined")
GROUP_NAMES = {"basic": "Cơ bản", "fragile": "Ô giòn", "switch": "Công tắc", "combined": "Kết hợp"}
NUMERIC = ("expanded", "time_s", "peak_mem_kb", "length", "cost", "optimal_moves",
           "rows", "cols", "bridge_cells", "fragile_cells")
STALE = (
    "expanded_nodes.png", "overview.png", "peak_memory.png", "search_time.png",
    "solution_cost.png", "solution_length.png", "results_tables.md", "summary_vs_bfs.md",
)


def tex_escape(value):
    s = str(value)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def solver_label(name):
    return {"astar": "A*", "bfs": "BFS", "dfs": "DFS", "ids": "IDS", "ucs": "UCS"}.get(name, name.upper())


def solver_tex(name):
    return r"A$^*$" if name == "astar" else tex_escape(solver_label(name))


def group_label(name):
    return GROUP_NAMES.get(name, name)


def parse_bool(raw):
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in ("", "none", "nan"):
        return None
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None


def read_results(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["found"] = parse_bool(r.get("found")) is True
        r["valid"] = parse_bool(r.get("valid"))
        r["group"] = (r.get("group") or "").strip()
        r["name"] = r.get("name") or ""
        r["switch_types"] = (r.get("switch_types") or "").strip()
        for k in NUMERIC:
            raw = r.get(k, "")
            if raw is None or str(raw).strip() == "":
                r[k] = math.nan
                continue
            try:
                r[k] = float(raw)
            except (TypeError, ValueError):
                r[k] = math.nan
    return rows


def finite(v):
    return isinstance(v, (int, float)) and not math.isnan(v)


def is_solved(row):
    """Giải được: có path và replay không báo invalid. valid=None (CSV cũ) vẫn tính nếu found."""
    return row is not None and row["found"] and row["valid"] is not False


def levels_in(rows):
    return list(dict.fromkeys(r["level"] for r in rows))


def groups_in(rows):
    present = [g for g in GROUP_ORDER if any(r["group"] == g for r in rows)]
    for r in rows:
        if r["group"] and r["group"] not in present:
            present.append(r["group"])
    return present


def levels_of(rows, group):
    return [lv for lv in levels_in(rows) if any(r["level"] == lv and r["group"] == group for r in rows)]


def row_of(rows, level, solver):
    for r in rows:
        if r["level"] == level and r["solver"] == solver:
            return r
    return None


def solvers_in(rows):
    return list(dict.fromkeys(r["solver"] for r in rows))


def mean_on_solved(rows, group, solver, key, scale=1.0):
    """Trung bình cộng của `key` trên các màn trong nhóm mà solver giải được.

    Trả về (mean, n_solved, n_levels). mean = nan nếu không giải được màn nào
    hoặc mọi giá trị đều thiếu.
    """
    levels = levels_of(rows, group)
    vals = []
    solved = 0
    for lv in levels:
        r = row_of(rows, lv, solver)
        if not is_solved(r):
            continue
        solved += 1
        if finite(r[key]):
            vals.append(r[key] * scale)
    mean = sum(vals) / len(vals) if vals else math.nan
    return mean, solved, len(levels)


def fmt_num(v, nd):
    if not finite(v):
        return "---"
    if nd <= 0:
        return str(int(round(v)))
    return f"{v:.{nd}f}"


def fmt_int_opt(v):
    if not finite(v):
        return "---"
    return str(int(round(v)))


def write_testset(rows, path):
    lines = [
        "% Sinh bởi plot_results.py — không sửa tay.",
        r"\begin{tabular}{llrrrlr}",
        r"\hline",
        r"Màn & Nhóm & Cỡ & Fragile & Bridge & Switch & Tối ưu \\",
        r"\hline",
    ]
    seen = set()
    for r in rows:
        if r["level"] in seen:
            continue
        seen.add(r["level"])
        if finite(r["rows"]) and finite(r["cols"]):
            size = f"${int(r['rows'])} \\times {int(r['cols'])}$"
        else:
            size = "---"
        switches = r["switch_types"].replace(",", ", ") if r["switch_types"] else "---"
        lines.append(
            f"{tex_escape(r['level'])} & {tex_escape(group_label(r['group']))} & {size} & "
            f"{fmt_int_opt(r['fragile_cells'])} & {fmt_int_opt(r['bridge_cells'])} & "
            f"{tex_escape(switches)} & {fmt_int_opt(r['optimal_moves'])} \\\\"
        )
    lines += [r"\hline", r"\end{tabular}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_tier(rows, solvers, groups, path):
    lines = [
        "% Sinh bởi plot_results.py — không sửa tay.",
        "% Trung bình cộng trên các màn GIẢI ĐƯỢC (found và replay hợp lệ) trong nhóm.",
        "% Thời gian mỗi màn là trung vị các lần lặp (time_s); cột dưới đây đổi ra ms. Bộ nhớ: KB.",
        r"\begin{tabular}{llrlllll}",
        r"\hline",
        r"Nhóm & Solver & Giải & Node & Thời gian (ms) & Bộ nhớ (KB) & Độ dài & Cost \\",
        r"\hline",
    ]
    specs = (
        ("expanded", 1, 1),
        ("time_s", 1000, 2),
        ("peak_mem_kb", 1, 1),
        ("length", 1, 2),
        ("cost", 1, 2),
    )
    for gi, g in enumerate(groups):
        if gi:
            lines.append(r"\hline")
        for s in solvers:
            cells = []
            solved = total = None
            for key, scale, nd in specs:
                mean, n_sol, n_all = mean_on_solved(rows, g, s, key, scale)
                solved, total = n_sol, n_all
                cells.append(fmt_num(mean, nd))
            lines.append(
                f"{tex_escape(group_label(g))} & {solver_tex(s)} & {solved}/{total} & "
                + " & ".join(cells) + r" \\"
            )
    lines += [r"\hline", r"\end{tabular}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_detail(rows, solvers, levels, path):
    """Bảng từng màn cho phụ lục. Node/thời gian/bộ nhớ luôn ghi (kể cả không giải được);
    độ dài và cost chỉ ghi khi lời giải hợp lệ."""
    blocks = [
        ("Số node mở rộng", "expanded", 1, 0, False),
        ("Thời gian tìm kiếm (ms)", "time_s", 1000, 2, False),
        ("Bộ nhớ đỉnh (KB)", "peak_mem_kb", 1, 1, False),
        ("Độ dài lời giải (số nước)", "length", 1, 0, True),
        ("Cost", "cost", 1, 2, True),
    ]
    header = " & ".join(["Màn", "Nhóm"] + [solver_tex(s) for s in solvers]) + r" \\"
    colspec = "ll" + "r" * len(solvers)
    chunks = [
        "% Sinh bởi plot_results.py — không sửa tay. Phụ lục chi tiết từng màn.",
        r"% \input{tables/results_detail.tex}",
    ]
    for title, key, scale, nd, solved_only in blocks:
        chunks += [
            r"{\textbf{" + tex_escape(title) + r"}}\\[0.4em]",
            r"\begin{tabular}{" + colspec + "}",
            r"\hline",
            header,
            r"\hline",
        ]
        for lv in levels:
            sample = next(r for r in rows if r["level"] == lv)
            cells = []
            for s in solvers:
                r = row_of(rows, lv, s)
                if r is None or (solved_only and not is_solved(r)) or not finite(r[key]):
                    cells.append("---")
                else:
                    cells.append(fmt_num(r[key] * scale, nd))
            chunks.append(
                f"{tex_escape(lv)} & {tex_escape(group_label(sample['group']))} & "
                + " & ".join(cells) + r" \\"
            )
        chunks += [r"\hline", r"\end{tabular}", "", r"\vspace{1.1em}", ""]
    path.write_text("\n".join(chunks), encoding="utf-8")


def _style_ax(ax, ylabel, log):
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", which="both", alpha=0.3)
    ax.set_axisbelow(True)
    if log:
        ax.set_yscale("log")


def draw_group_bars(path, rows, solvers, groups, key, scale, ylabel, log):
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    width = 0.8 / max(len(solvers), 1)
    for i, s in enumerate(solvers):
        vals = []
        for g in groups:
            mean, _, _ = mean_on_solved(rows, g, s, key, scale)
            vals.append(mean if finite(mean) and (mean > 0 or not log) else math.nan)
        xs = [j + (i - (len(solvers) - 1) / 2) * width for j in range(len(groups))]
        ax.bar(xs, vals, width, label=solver_label(s), color=COLORS.get(s))
    _style_ax(ax, ylabel, log)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([group_label(g) for g in groups])
    ax.set_xlabel("Nhóm màn")
    ax.legend(ncol=min(len(solvers), 5), fontsize=8, loc="upper center",
              bbox_to_anchor=(0.5, -0.18), frameon=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def draw_scaling(path, rows, solvers, levels):
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    any_positive = False
    for s in solvers:
        xs, ys = [], []
        for lv in levels:
            r = row_of(rows, lv, s)
            if r is None or not finite(r["optimal_moves"]) or not finite(r["expanded"]):
                continue
            xs.append(r["optimal_moves"])
            ys.append(r["expanded"])
            if r["expanded"] > 0:
                any_positive = True
        ax.scatter(xs, ys, s=32, label=solver_label(s), color=COLORS.get(s), alpha=0.9, zorder=3)
    ax.set_xlabel("Độ dài lời giải tối ưu (nước)")
    ax.set_ylabel("Số node mở rộng")
    if any_positive:
        ax.set_yscale("log")
    ax.grid(True, which="both", alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(ncol=min(len(solvers), 5), fontsize=8, loc="upper center",
              bbox_to_anchor=(0.5, -0.18), frameon=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def any_finite_column(rows, key):
    return any(finite(r[key]) for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results.csv")
    ap.add_argument("--out", default="figures")
    ap.add_argument("--tables", default="tables")
    args = ap.parse_args()

    rows = read_results(args.csv)
    if not rows:
        raise SystemExit(f"CSV rỗng: {args.csv}")
    levels = levels_in(rows)
    solvers = solvers_in(rows)
    groups = groups_in(rows)
    out = Path(args.out)
    tables = Path(args.tables)
    out.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    for name in STALE:
        stale = out / name
        if stale.exists():
            stale.unlink()

    write_testset(rows, tables / "testset.tex")
    write_tier(rows, solvers, groups, tables / "results_by_tier.tex")
    write_detail(rows, solvers, levels, tables / "results_detail.tex")

    figures = [
        ("expanded", 1, "Số node mở rộng", True, "fig_expanded.pdf"),
        ("time_s", 1000, "Thời gian tìm kiếm (ms)", True, "fig_time.pdf"),
        ("peak_mem_kb", 1, "Bộ nhớ đỉnh (KB)", True, "fig_memory.pdf"),
        ("length", 1, "Độ dài lời giải (số nước)", False, "fig_length.pdf"),
    ]
    written = []
    for key, scale, ylabel, log, name in figures:
        if not any_finite_column(rows, key):
            continue
        draw_group_bars(out / name, rows, solvers, groups, key, scale, ylabel, log)
        written.append(name)
    draw_scaling(out / "fig_scaling.pdf", rows, solvers, levels)
    written.append("fig_scaling.pdf")
    print(f"Đã ghi {', '.join(written)} vào {out}/")
    print(f"Đã ghi testset.tex, results_by_tier.tex, results_detail.tex vào {tables}/")


if __name__ == "__main__":
    main()
