import heapq
import itertools

from .base import SearchOutcome, build_path


def ucs(problem):
    """Uniform-Cost Search: tối ưu theo tổng step_cost mà engine trả về.

    Nếu mọi step_cost = 1 thì UCS cho cùng độ dài lời giải với BFS.
    """
    start = problem.initial_state()
    tie = itertools.count()                       # tránh so sánh State khi cost bằng nhau
    heap = [(0.0, next(tie), start, None)]        # (g, tie, state, node)
    best_g = {start: 0.0}
    closed = set()
    expanded = 0
    while heap:
        g, _, state, node = heapq.heappop(heap)
        if state in closed:
            continue                              # bản cũ (đã có đường rẻ hơn)
        closed.add(state)
        if problem.is_goal(state):
            return SearchOutcome(build_path(node), g, expanded)
        expanded += 1
        for action, nxt, step in problem.get_successors(state):
            new_g = g + step
            if nxt not in closed and new_g < best_g.get(nxt, float("inf")):
                best_g[nxt] = new_g
                heapq.heappush(heap, (new_g, next(tie), nxt, (action, node)))
    return SearchOutcome(None, None, expanded)
