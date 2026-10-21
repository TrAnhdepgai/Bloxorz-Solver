from collections import deque

from .base import SearchOutcome, build_path


def bfs(problem):
    """BFS: lời giải ít bước nhất. Kiểm tra đích khi lấy node ra (cùng quy ước với các solver khác)."""
    start = problem.initial_state()
    frontier = deque([(start, None, 0.0)])   # (state, node, cost)
    visited = {start}                         # đánh dấu lúc push để không đưa trùng vào hàng đợi
    expanded = 0
    while frontier:
        state, node, cost = frontier.popleft()
        if problem.is_goal(state):
            return SearchOutcome(build_path(node), cost, expanded)
        expanded += 1
        for action, nxt, step in problem.get_successors(state):
            if nxt not in visited:
                visited.add(nxt)
                frontier.append((nxt, (action, node), cost + step))
    return SearchOutcome(None, None, expanded)
