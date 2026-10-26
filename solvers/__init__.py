from .astar import astar
from .bfs import bfs
from .dfs import dfs
from .ids import ids
from .ucs import ucs

# Đăng ký solver theo tên để run_experiments.py gọi bằng chuỗi.
SOLVERS = {"bfs": bfs, "dfs": dfs, "ids": ids, "ucs": ucs, "astar": astar}

__all__ = ["bfs", "dfs", "ids", "ucs", "astar", "SOLVERS"]