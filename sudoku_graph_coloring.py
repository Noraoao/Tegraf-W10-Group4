"""
Sudoku Solver via Graph Coloring (DSATUR + Backtracking)
=========================================================

Modelling
---------
* Vertex : each of the 81 cells (index = row * 9 + col)
* Edge   : two cells are adjacent if they share a row, column or 3x3 box
           (every vertex ends up with exactly 20 neighbours)
* Colour : digits 1..9.  Given clues are pre-coloured vertices.
* Goal   : a proper 9-colouring of the graph that extends the pre-colouring
           (no two adjacent vertices share a colour).

Algorithm
---------
DSATUR (Brelaz, 1979) with backtracking:
  1. Saturation of a vertex = number of DISTINCT colours among its neighbours.
  2. Always colour the uncoloured vertex with the highest saturation
     (i.e. the fewest remaining legal colours). Ties are broken by the
     largest number of uncoloured neighbours.
  3. Try each legal colour; recurse; undo (backtrack) on failure.

Plain DSATUR is a heuristic, but adding backtracking makes it exact:
it will find a valid colouring whenever one exists.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

N = 9          # board size == number of colours
BOX = 3        # box size
V = N * N      # number of vertices


# --------------------------------------------------------------------------- #
# Graph construction
# --------------------------------------------------------------------------- #
def build_sudoku_graph() -> List[Set[int]]:
    """Return adjacency sets for the 81-vertex Sudoku graph."""
    adj: List[Set[int]] = [set() for _ in range(V)]
    for v in range(V):
        r, c = divmod(v, N)
        br, bc = (r // BOX) * BOX, (c // BOX) * BOX
        for k in range(N):
            adj[v].add(r * N + k)          # same row
            adj[v].add(k * N + c)          # same column
        for i in range(br, br + BOX):      # same box
            for j in range(bc, bc + BOX):
                adj[v].add(i * N + j)
        adj[v].discard(v)                  # no self-loops
    return adj


# --------------------------------------------------------------------------- #
# DSATUR graph colouring solver
# --------------------------------------------------------------------------- #
class SudokuGraphColoring:
    def __init__(self, puzzle: List[List[int]]):
        self.adj = build_sudoku_graph()
        self.color: List[int] = [0] * V               # 0 = uncoloured
        # nbr_count[v][c] = how many neighbours of v currently have colour c
        self.nbr_count: List[List[int]] = [[0] * (N + 1) for _ in range(V)]
        # saturation[v] = number of distinct colours among v's neighbours
        self.saturation: List[int] = [0] * V
        self.uncolored: Set[int] = set(range(V))
        self.backtracks = 0

        self._load_precoloring(puzzle)

    # ---- colour / uncolour with incremental saturation bookkeeping --------- #
    def _assign(self, v: int, c: int) -> None:
        self.color[v] = c
        self.uncolored.discard(v)
        for u in self.adj[v]:
            if self.nbr_count[u][c] == 0:
                self.saturation[u] += 1
            self.nbr_count[u][c] += 1

    def _unassign(self, v: int) -> None:
        c = self.color[v]
        self.color[v] = 0
        self.uncolored.add(v)
        for u in self.adj[v]:
            self.nbr_count[u][c] -= 1
            if self.nbr_count[u][c] == 0:
                self.saturation[u] -= 1

    def _available(self, v: int) -> List[int]:
        return [c for c in range(1, N + 1) if self.nbr_count[v][c] == 0]

    def _load_precoloring(self, puzzle: List[List[int]]) -> None:
        if len(puzzle) != N or any(len(row) != N for row in puzzle):
            raise ValueError("Puzzle must be a 9x9 grid.")
        for r in range(N):
            for c in range(N):
                val = puzzle[r][c]
                if not 0 <= val <= N:
                    raise ValueError(f"Invalid value {val} at ({r},{c}).")
                if val:
                    v = r * N + c
                    if self.nbr_count[v][val] != 0:   # an adjacent vertex already has it
                        raise ValueError(
                            f"Invalid puzzle: clue {val} at ({r},{c}) conflicts "
                            f"with another clue (adjacent vertices share a colour)."
                        )
                    self._assign(v, val)

    # ---- DSATUR vertex selection ------------------------------------------ #
    def _select_vertex(self) -> int:
        """Max saturation first; tie-break on most uncoloured neighbours."""
        best, best_key = -1, (-1, -1)
        for v in self.uncolored:
            deg_uncol = sum(1 for u in self.adj[v] if self.color[u] == 0)
            key = (self.saturation[v], deg_uncol)
            if key > best_key:
                best, best_key = v, key
        return best

    # ---- backtracking search ---------------------------------------------- #
    def _solve(self) -> bool:
        if not self.uncolored:
            return True
        v = self._select_vertex()
        options = self._available(v)
        if not options:                    # saturation == 9 -> dead end
            return False
        for c in options:
            self._assign(v, c)
            if self._solve():
                return True
            self._unassign(v)              # backtrack
            self.backtracks += 1
        return False

    def solve(self) -> Optional[List[List[int]]]:
        """Return the solved grid, or None if no valid colouring exists."""
        if not self._solve():
            return None
        return [self.color[r * N:(r + 1) * N] for r in range(N)]


# --------------------------------------------------------------------------- #
# Verification & helpers
# --------------------------------------------------------------------------- #
def is_proper_coloring(grid: List[List[int]]) -> bool:
    """Check that the grid is a valid proper colouring of the Sudoku graph."""
    if len(grid) != N or any(len(row) != N for row in grid):
        return False
    flat = [x for row in grid for x in row]
    if any(not isinstance(x, int) or not 1 <= x <= N for x in flat):
        return False
    adj = build_sudoku_graph()
    return all(flat[v] != flat[u] for v in range(V) for u in adj[v])


def parse(s: str) -> List[List[int]]:
    """Parse exactly 81 digits ('0' or '.' = empty) into a 9x9 grid."""
    s = s.replace(".", "0")
    if any(ch not in "0123456789" for ch in s):
        raise ValueError("Use only digits 0-9 or '.' for empty cells.")
    if len(s) != V:
        raise ValueError(f"Expected exactly 81 cells, but received {len(s)}.")
    digits = [int(ch) for ch in s]
    return [digits[r * N:(r + 1) * N] for r in range(N)]


# Each digit is displayed using a consistent terminal colour.
COLOR_CODES = {
    1: "\033[91m", 2: "\033[93m", 3: "\033[92m",
    4: "\033[96m", 5: "\033[94m", 6: "\033[95m",
    7: "\033[38;5;208m", 8: "\033[38;5;45m",
    9: "\033[38;5;141m"
}
RESET = "\033[0m"


def print_grid(grid: List[List[int]], show_colors: bool = False) -> None:
    """Print the Sudoku grid, optionally displaying each digit in a colour."""
    for r, row in enumerate(grid):
        if r and r % BOX == 0:
            print("------+-------+------")
        parts = []
        for c, x in enumerate(row):
            if c and c % BOX == 0:
                parts.append("|")
            value = str(x) if x else "."
            if show_colors and x in COLOR_CODES:
                value = f"{COLOR_CODES[x]}{value}{RESET}"
            parts.append(value)
        print(" ".join(parts))


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    puzzles: Dict[str, str] = {
        "Easy": (
            "530070000600195000098000060800060003400803001"
            "700020006060000280000419005000080079"
        ),
        # Hard puzzle designed to stress brute-force solvers
        "Hard": (
            "000000907000420180000705026100904000050000040"
            "000507009920108000034059000507000000"
        ),
    }

    for name, s in puzzles.items():
        print(f"\n=== {name} puzzle ===")
        try:
            grid = parse(s)
            print("Original puzzle:")
            print_grid(grid)

            solver = SudokuGraphColoring(grid)
            solution = solver.solve()

            if solution is None:
                print("\nNo solution exists for this puzzle.")
            else:
                print(f"\nSolved ({solver.backtracks} backtracks), "
                      f"valid proper colouring: {is_proper_coloring(solution)}")
                print("\nSolved Sudoku (numbers shown as graph colours):")
                print_grid(solution, show_colors=True)

        except ValueError as error:
            print(f"\nInvalid puzzle: {error}")
