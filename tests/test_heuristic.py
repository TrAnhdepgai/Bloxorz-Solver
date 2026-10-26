"""h(goal)=0, admissible, consistent trên TOÀN BỘ không gian trạng thái, với 3 loại cost."""
import heapq
from collections import deque

import pytest

from engine import Engine
from engine.catalog import load_catalog
from engine.costs import uniform_cost, weighted_cost
from solvers.astar import build_heuristic

MAX_STATES = 20000
CATALOG = load_catalog()
COSTS = {"default": None, "uniform": uniform_cost, "weighted": weighted_cost}


def explore(problem):
    start = problem.initial_state()
    seen, edges, queue = {start}, {}, deque([start])
    while queue:
        s = queue.popleft()
        edges[s] = [(n, c) for _, n, c in problem.get_successors(s)]
        for n, _ in edges[s]:
            if n not in seen:
                seen.add(n)
                queue.append(n)
        if len(seen) > MAX_STATES:
            return None
    return edges


def cost_to_go(edges, goals):
    rev = {}
    for s, outs in edges.items():
        for n, c in outs:
            rev.setdefault(n, []).append((s, c))
    dist = {g: 0.0 for g in goals}
    heap = [(0.0, i, g) for i, g in enumerate(goals)]
    heapq.heapify(heap)
    counter = len(heap)
    while heap:
        d, _, s = heapq.heappop(heap)
        if d > dist.get(s, float("inf")):
            continue
        for p, c in rev.get(s, ()):
            if d + c < dist.get(p, float("inf")):
                dist[p] = d + c
                counter += 1
                heapq.heappush(heap, (d + c, counter, p))
    return dist


@pytest.mark.parametrize("cost_name", COSTS)
@pytest.mark.parametrize("entry", CATALOG, ids=lambda e: e["id"])
def test_heuristic_admissible_and_consistent(entry, cost_name):
    cost_fn = COSTS[cost_name]
    problem = Engine(entry["path"]) if cost_fn is None else Engine(entry["path"], cost_fn=cost_fn)
    edges = explore(problem)
    if edges is None:
        pytest.skip("không gian trạng thái quá lớn")
    h = build_heuristic(problem)
    goals = [s for s in edges if problem.is_goal(s)]
    assert goals
    assert all(h(g) == 0 for g in goals)
    for s, outs in edges.items():
        for n, c in outs:
            assert h(s) <= c + h(n) + 1e-9, f"không consistent: {s} -> {n}"
    star = cost_to_go(edges, goals)
    for s in edges:
        if s in star:
            assert h(s) <= star[s] + 1e-9, f"không admissible tại {s}"