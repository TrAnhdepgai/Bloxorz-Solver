from .bfs import bfs
from .dfs import dfs
from .ids import ids
from .ucs import ucs

# Đăng ký solver theo tên để run_experiments.py gọi bằng chuỗi.
# Tuần sau thêm: from .astar import astar ; SOLVERS["astar"] = astar
SOLVERS = {"bfs": bfs, "dfs": dfs, "ids": ids, "ucs": ucs}

__all__ = ["bfs", "dfs", "ids", "ucs", "SOLVERS"]
