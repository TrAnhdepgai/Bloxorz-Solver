"""Kiểu dữ liệu và hàm dùng chung cho mọi solver.

Solver chỉ dùng 3 hàm của engine (theo ENGINE_CONTRACT.md):
    problem.initial_state()
    problem.is_goal(state)
    problem.get_successors(state) -> [(action, next_state, step_cost), ...]
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchOutcome:
    path: Optional[list]      # danh sách action ['R','D',...]; None nếu không có lời giải
    cost: Optional[float]     # tổng step_cost của path
    expanded: int             # số trạng thái được lấy ra và sinh hậu duệ (không tính node đích).
                              # IDS cộng dồn qua mọi vòng lặp độ sâu.


def build_path(node):
    """Node là danh sách liên kết (action, node_cha); node gốc là None."""
    actions = []
    while node is not None:
        action, node = node
        actions.append(action)
    actions.reverse()
    return actions


def replay_path(problem, path):
    """Chạy lại path trên engine để kiểm tra: mọi bước hợp lệ và kết thúc ở đích."""
    state = problem.initial_state()
    for action in path:
        for a, nxt, _ in problem.get_successors(state):
            if a == action:
                state = nxt
                break
        else:
            return False
    return problem.is_goal(state)
