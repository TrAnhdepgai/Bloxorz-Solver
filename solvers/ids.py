from .base import SearchOutcome, build_path


def ids(problem, max_depth=500):
    """Iterative Deepening Search: lời giải ít bước nhất, tốn ít bộ nhớ hơn BFS ở lý thuyết.

    Với mỗi giới hạn độ sâu, ghi lại độ sâu nhỏ nhất đã tới mỗi state (best_depth) để
    không mở rộng lại state ở độ sâu bằng hoặc sâu hơn -> xử lý trạng thái lặp.
    `expanded` được cộng dồn qua mọi vòng lặp.
    """
    start = problem.initial_state()
    expanded = 0
    for limit in range(max_depth + 1):
        best_depth = {}
        cutoff = False                       # có node bị chặn do chạm giới hạn không
        stack = [(start, None, 0.0, 0)]      # (state, node, cost, depth)
        while stack:
            state, node, cost, depth = stack.pop()
            if best_depth.get(state, float("inf")) <= depth:
                continue
            best_depth[state] = depth
            if problem.is_goal(state):
                return SearchOutcome(build_path(node), cost, expanded)
            if depth == limit:
                cutoff = True
                continue
            expanded += 1
            for action, nxt, step in reversed(problem.get_successors(state)):
                stack.append((nxt, (action, node), cost + step, depth + 1))
        if not cutoff:                       # đã duyệt hết không gian trạng thái mà không thấy đích
            break
    return SearchOutcome(None, None, expanded)
