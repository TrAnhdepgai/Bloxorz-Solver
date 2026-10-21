from .base import SearchOutcome, build_path


def dfs(problem):
    """DFS (dùng stack, có visited set để tránh vòng lặp). Lời giải KHÔNG đảm bảo ngắn nhất."""
    start = problem.initial_state()
    stack = [(start, None, 0.0)]   # (state, node, cost)
    visited = set()
    expanded = 0
    while stack:
        state, node, cost = stack.pop()
        if state in visited:
            continue
        visited.add(state)
        if problem.is_goal(state):
            return SearchOutcome(build_path(node), cost, expanded)
        expanded += 1
        # đảo ngược để hướng đầu tiên (U) được thử trước
        for action, nxt, step in reversed(problem.get_successors(state)):
            if nxt not in visited:
                stack.append((nxt, (action, node), cost + step))
    return SearchOutcome(None, None, expanded)
