import heapq
import itertools

from engine.engine import COST, default_cost

from .base import SearchOutcome, build_path


def _passable(problem):
    """Các ô khối có thể chiếm: sàn '#' hoặc ô cầu."""
    cells = {(r, c) for r, row in enumerate(problem.grid) for c, ch in enumerate(row) if ch == "#"}
    for bridge_cells in problem.bridges.values():
        cells.update(map(tuple, bridge_cells))
    return cells


def cost_per_cell(problem):
    """Chi phí tối thiểu cho mỗi ô Manhattan mà một bước rút ngắn được."""
    declared = getattr(problem.step_cost, "cost_per_cell", None)
    if declared is not None:
        return declared
    if problem.step_cost is default_cost:
        return min(COST.values()) / 2
    return 0.0                          # hàm cost lạ -> h = 0, luôn admissible


def build_heuristic(problem, per_cell=None):
    """h(state) admissible + consistent.

    Nới lỏng bài toán: bỏ qua cầu/fragile/công tắc, chỉ giữ khoảng cách Manhattan.
    D(ô) = k * Manhattan(ô, goal); công tắc split cho teleport với chi phí 0
    từ ô công tắc tới 2 ô teleport -> cập nhật D qua các cạnh này.
    h(state) = min D(ô) trên các ô khối đang chiếm.
    """
    k = cost_per_cell(problem) if per_cell is None else per_cell
    goal = tuple(problem.goal)
    cells = _passable(problem)
    cells.add(goal)
    teleports = []
    for sw in problem.switches:
        if sw["type"] == "split":
            for t in sw["teleport"]:
                teleports.append((tuple(sw["pos"]), tuple(t)))
                cells.update([tuple(sw["pos"]), tuple(t)])

    manhattan = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1])
    D = {p: k * manhattan(p, goal) for p in cells}
    changed = True
    while changed:
        changed = False
        for sw_pos, t in teleports:
            for p in cells:
                via = k * manhattan(p, sw_pos) + D[t]
                if via < D[p] - 1e-12:
                    D[p] = via
                    changed = True

    def footprint(state):
        if state.split is not None:
            return state.split.cubes
        r, c = state.row, state.col
        if state.orient == "S":
            return ((r, c),)
        return ((r, c), (r, c + 1)) if state.orient == "H" else ((r, c), (r + 1, c))

    def h(state):
        return min(D[p] for p in footprint(state))

    return h


def astar(problem, heuristic=None):
    """A*: tối ưu theo tổng step_cost, mở rộng ít node hơn UCS."""
    h = heuristic or build_heuristic(problem)
    start = problem.initial_state()
    tie = itertools.count()
    heap = [(h(start), 0.0, next(tie), start, None)]      # (f, g, tie, state, node)
    best_g = {start: 0.0}
    closed = set()
    expanded = 0
    while heap:
        _, g, _, state, node = heapq.heappop(heap)
        if state in closed:
            continue
        closed.add(state)
        if problem.is_goal(state):
            return SearchOutcome(build_path(node), g, expanded)
        expanded += 1
        for action, nxt, step in problem.get_successors(state):
            new_g = g + step
            if nxt not in closed and new_g < best_g.get(nxt, float("inf")):
                best_g[nxt] = new_g
                heapq.heappush(heap, (new_g + h(nxt), new_g, next(tie), nxt, (action, node)))
    return SearchOutcome(None, None, expanded)