"""
Sudoku Solver via Graph Coloring (DSATUR + Backtracking)
=========================================================
Single-file project: solver + web interface (Flask) + terminal interface.

Usage
-----
    pip install flask                         # only needed for the web interface
    python sudoku_graph_coloring.py           # web interface at http://127.0.0.1:5000

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

import argparse
import json
import sys
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
# Input handling
# --------------------------------------------------------------------------- #
DEMO_PUZZLES: Dict[str, str] = {
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

IGNORED = set(" \t|-+,_")   # separators allowed when pasting a board


def read_puzzle_interactive() -> Optional[List[List[int]]]:
    """Ask the user for a puzzle until a valid one is entered.

    Accepts either 9 lines of 9 cells, or all 81 cells on one line.
    Use 0 or . for an empty cell.  Type 'demo' for a sample puzzle,
    or 'q' to quit.  Returns None if the user quits / input ends.
    """
    print("Enter the Sudoku puzzle (0 or . = empty cell).")
    print("  - type it row by row (9 lines of 9 digits), or paste all 81 digits in one line")
    print("  - spaces, | and - are ignored, so you can paste a printed board")
    print("  - type 'demo' for a sample puzzle, 'q' to quit")
    buffer = ""
    while True:
        try:
            line = input(f"Row {min(len(buffer) // N + 1, N)}> ")
        except EOFError:
            return None
        text = line.strip().lower()
        if text in ("q", "quit", "exit"):
            return None
        if text == "demo":
            return parse(DEMO_PUZZLES["Easy"])
        buffer += "".join(ch for ch in line if ch not in IGNORED)
        if len(buffer) < V:
            continue
        try:
            return parse(buffer)
        except ValueError as error:
            print(f"Invalid input: {error} Let's start over.")
            buffer = ""


def read_puzzle_file(path: str) -> List[List[int]]:
    """Read a puzzle from a text file (same flexible format as typed input)."""
    with open(path, encoding="utf-8") as f:
        return parse("".join(ch for ch in f.read() if ch not in IGNORED and not ch.isspace()))


def solve_and_print(grid: List[List[int]]) -> None:
    print("\nOriginal puzzle:")
    print_grid(grid)
    try:
        solver = SudokuGraphColoring(grid)
    except ValueError as error:
        print(f"\n{error}")
        return
    solution = solver.solve()
    if solution is None:
        print("\nNo solution exists for this puzzle.")
        return
    print(f"\nSolved ({solver.backtracks} backtracks), "
          f"valid proper colouring: {is_proper_coloring(solution)}")
    print("\nSolved Sudoku (numbers shown as graph colours):")
    print_grid(solution, show_colors=True)


# --------------------------------------------------------------------------- #
# Web interface (Flask)
# --------------------------------------------------------------------------- #
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sudoku Solver: Graph Coloring</title>
<style>
  :root {
    --bg: #f5f5f4; --fg: #1c1917; --muted: #57534e; --card: #ffffff;
    --line: #a8a29e; --thick: #1c1917; --accent: #2563eb;
    --ok: #166534; --ok-bg: #dcfce7; --err: #991b1b; --err-bg: #fee2e2;
    --c1: #f87171; --c2: #fde047; --c3: #86efac; --c4: #67e8f9; --c5: #93c5fd;
    --c6: #f0abfc; --c7: #fdba74; --c8: #7dd3fc; --c9: #c4b5fd;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #1c1917; --fg: #fafaf9; --muted: #a8a29e; --card: #292524;
      --line: #57534e; --thick: #e7e5e4; --accent: #60a5fa;
      --ok: #bbf7d0; --ok-bg: #14532d; --err: #fecaca; --err-bg: #7f1d1d;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 24px 16px 48px; background: var(--bg); color: var(--fg);
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    display: flex; flex-direction: column; align-items: center;
  }
  h1 { font-size: 1.5rem; margin: 0 0 4px; text-align: center; }
  .sub { color: var(--muted); margin: 0 0 20px; text-align: center; max-width: 36rem; }
  .board {
    display: grid; grid-template-columns: repeat(9, 1fr);
    width: min(92vw, 468px); aspect-ratio: 1; background: var(--card);
    border: 3px solid var(--thick);
  }
  .board input {
    width: 100%; height: 100%; min-width: 0; padding: 0; text-align: center;
    font: 600 clamp(18px, 5vw, 26px) system-ui, sans-serif; color: #1c1917;
    background: var(--card); border: 1px solid var(--line); border-radius: 0; caret-color: var(--accent);
  }
  .board input:focus { outline: 3px solid var(--accent); outline-offset: -3px; position: relative; z-index: 1; }
  .board input:nth-child(9n+3), .board input:nth-child(9n+6) { border-right: 3px solid var(--thick); }
  .board input:nth-child(n+19):nth-child(-n+27),
  .board input:nth-child(n+46):nth-child(-n+54) { border-bottom: 3px solid var(--thick); }
  .board input.d1 { background: var(--c1); } .board input.d2 { background: var(--c2); }
  .board input.d3 { background: var(--c3); } .board input.d4 { background: var(--c4); }
  .board input.d5 { background: var(--c5); } .board input.d6 { background: var(--c6); }
  .board input.d7 { background: var(--c7); } .board input.d8 { background: var(--c8); }
  .board input.d9 { background: var(--c9); }
  .board input.solved { font-weight: 400; }
  .board input.clue { font-weight: 800; text-decoration: underline; text-underline-offset: 4px; }
  .controls { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 18px 0 12px; }
  button {
    font: 600 0.95rem system-ui, sans-serif; padding: 9px 18px; border-radius: 8px; cursor: pointer;
    border: 1px solid var(--line); background: var(--card); color: var(--fg);
  }
  button:hover { border-color: var(--accent); }
  button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  button:disabled { opacity: 0.6; cursor: wait; }
  #status {
    min-height: 2.6em; width: min(92vw, 468px); padding: 10px 14px; border-radius: 8px;
    text-align: center; font-size: 0.95rem; color: var(--muted);
  }
  #status.ok { background: var(--ok-bg); color: var(--ok); }
  #status.err { background: var(--err-bg); color: var(--err); }
  .hint { color: var(--muted); font-size: 0.85rem; text-align: center; max-width: 36rem; margin-top: 14px; }
</style>
</head>
<body>
  <h1>Sudoku Solver via Graph Coloring</h1>
  <p class="sub">Each cell is a vertex, each digit is a color. The solver finds a proper 9-coloring with DSATUR and backtracking.</p>

  <div class="board" id="board" role="grid" aria-label="Sudoku board"></div>

  <div class="controls">
    <button class="primary" id="solve">Solve</button>
    <button id="clear">Clear</button>
    <button id="easy">Easy sample</button>
    <button id="hard">Hard sample</button>
  </div>
  <div id="status" role="status">Type the given digits, then press Solve.</div>
  <p class="hint">Click a cell and type 1-9. Use the arrow keys to move, Backspace to clear. You can also paste a whole puzzle (81 digits, 0 or . for empty) into any cell.</p>

<script>
const SAMPLES = __SAMPLES__;
const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const solveBtn = document.getElementById("solve");
const cells = [];

for (let i = 0; i < 81; i++) {
  const el = document.createElement("input");
  el.type = "text"; el.maxLength = 1; el.inputMode = "numeric"; el.autocomplete = "off";
  el.setAttribute("aria-label", `Row ${Math.floor(i / 9) + 1}, column ${(i % 9) + 1}`);
  el.addEventListener("keydown", (e) => onKey(e, i));
  el.addEventListener("input", () => { clean(i); markUnsolved(); });
  el.addEventListener("paste", (e) => onPaste(e));
  el.addEventListener("focus", () => el.select());
  boardEl.appendChild(el);
  cells.push(el);
}

function paint(i) {
  const el = cells[i];
  el.className = "";
  if (/^[1-9]$/.test(el.value)) el.classList.add("d" + el.value);
}
function clean(i) {
  const el = cells[i];
  el.value = /^[1-9]$/.test(el.value) ? el.value : "";
  paint(i);
}
function markUnsolved() {
  cells.forEach((c) => c.classList.remove("solved", "clue"));
  setStatus("", "");
}
function focusCell(i) { if (i >= 0 && i < 81) cells[i].focus(); }

function onKey(e, i) {
  const move = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -9, ArrowDown: 9 }[e.key];
  if (move) { e.preventDefault(); focusCell(i + move); return; }
  if (e.key === "Backspace" || e.key === "Delete") {
    e.preventDefault(); cells[i].value = ""; paint(i); markUnsolved();
    if (e.key === "Backspace") focusCell(i - 1);
    return;
  }
  if (/^[1-9]$/.test(e.key)) {
    e.preventDefault(); cells[i].value = e.key; paint(i); markUnsolved(); focusCell(i + 1);
    return;
  }
  if (e.key === "0" || e.key === " " || e.key === ".") { e.preventDefault(); cells[i].value = ""; paint(i); markUnsolved(); focusCell(i + 1); return; }
  if (e.key === "Enter") { e.preventDefault(); solve(); return; }
  if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) e.preventDefault();
}
function onPaste(e) {
  const text = (e.clipboardData || window.clipboardData).getData("text");
  const digits = text.replace(/[\s|+\-_,]/g, "").replace(/\./g, "0");
  if (/^[0-9]{81}$/.test(digits)) {
    e.preventDefault();
    setBoard([...digits].map(Number));
  }
}

function getGrid() {
  const grid = [];
  for (let r = 0; r < 9; r++) {
    grid.push(cells.slice(r * 9, r * 9 + 9).map((c) => (c.value ? Number(c.value) : 0)));
  }
  return grid;
}
function setBoard(flat) {
  flat.forEach((v, i) => { cells[i].value = v ? String(v) : ""; paint(i); cells[i].classList.remove("solved", "clue"); });
  setStatus("", "");
}
function setStatus(text, kind) {
  statusEl.textContent = text || "Type the given digits, then press Solve.";
  statusEl.className = kind || "";
}

async function solve() {
  const grid = getGrid();
  solveBtn.disabled = true;
  setStatus("Solving...", "");
  try {
    const res = await fetch("/solve", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grid }),
    });
    const data = await res.json();
    if (data.status === "solved") {
      data.solution.flat().forEach((v, i) => {
        const wasClue = cells[i].value !== "";
        cells[i].value = String(v); paint(i);
        cells[i].classList.add(wasClue ? "clue" : "solved");
      });
      setStatus(`Solved (${data.backtracks} backtracks), valid proper coloring: ${data.valid ? "True" : "False"}`, "ok");
    } else {
      setStatus(data.message || "Something went wrong.", "err");
    }
  } catch (err) {
    setStatus("Could not reach the server. Is app.py still running?", "err");
  } finally {
    solveBtn.disabled = false;
  }
}

solveBtn.addEventListener("click", solve);
document.getElementById("clear").addEventListener("click", () => { setBoard(new Array(81).fill(0)); focusCell(0); });
document.getElementById("easy").addEventListener("click", () => setBoard(SAMPLES["Easy"].flat()));
document.getElementById("hard").addEventListener("click", () => setBoard(SAMPLES["Hard"].flat()));
</script>
</body>
</html>
"""


def create_app():
    """Build the Flask app. Flask is imported here so that the solver and the
    terminal interface work even when Flask is not installed."""
    from flask import Flask, Response, jsonify, request

    app = Flask(__name__)

    @app.get("/")
    def index():
        samples = {name: parse(s) for name, s in DEMO_PUZZLES.items()}
        return Response(HTML_PAGE.replace("__SAMPLES__", json.dumps(samples)),
                        mimetype="text/html")

    @app.post("/solve")
    def solve():
        data = request.get_json(silent=True) or {}
        grid = data.get("grid")

        # Basic shape / type check (the solver validates clue conflicts itself)
        if (
            not isinstance(grid, list)
            or len(grid) != N
            or any(not isinstance(row, list) or len(row) != N for row in grid)
            or any(not isinstance(x, int) or isinstance(x, bool)
                   for row in grid for x in row)
        ):
            return jsonify(status="error",
                           message="Puzzle must be a 9x9 grid of numbers."), 400
        try:
            solver = SudokuGraphColoring(grid)
        except ValueError as error:
            return jsonify(status="error", message=str(error)), 400

        solution = solver.solve()
        if solution is None:
            return jsonify(status="unsolvable",
                           message="No solution exists for this puzzle.")
        return jsonify(status="solved", solution=solution,
                       backtracks=solver.backtracks,
                       valid=is_proper_coloring(solution))

    return app


def run_web(port: int) -> None:
    try:
        app = create_app()
    except ImportError:
        print("The web interface needs Flask. Install it with:  pip install flask")
        print("(or use the terminal version:  python sudoku_graph_coloring.py --cli)")
        return

    import threading
    import webbrowser

    url = f"http://127.0.0.1:{port}"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"Sudoku solver running at {url}  (press Ctrl+C to stop)")
    try:
        app.run(host="127.0.0.1", port=port, debug=False)
    except OSError as error:
        print(f"Could not start the server on port {port}: {error}")
        print("Try another port, e.g.:  python sudoku_graph_coloring.py --port 8000")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def run_cli() -> None:
    while True:
        grid = read_puzzle_interactive()
        if grid is None:
            print("Bye!")
            return
        solve_and_print(grid)
        try:
            again = input("\nSolve another puzzle? (y/n): ").strip().lower()
        except EOFError:
            return
        if again not in ("y", "yes"):
            return
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sudoku solver using graph coloring (DSATUR + backtracking).")
    parser.add_argument("file", nargs="?", help="solve the puzzle stored in this text file")
    parser.add_argument("--cli", action="store_true", help="type the puzzle in the terminal")
    parser.add_argument("--demo", action="store_true", help="solve the built-in demo puzzles")
    parser.add_argument("--port", type=int, default=5000, help="web interface port (default 5000)")
    args = parser.parse_args()

    if args.demo:
        for name, s in DEMO_PUZZLES.items():
            print(f"\n=== {name} puzzle ===")
            solve_and_print(parse(s))
    elif args.file:
        try:
            solve_and_print(read_puzzle_file(args.file))
        except (OSError, ValueError) as error:
            print(f"Could not read puzzle: {error}")
    elif args.cli:
        run_cli()
    else:
        run_web(args.port)


if __name__ == "__main__":
    main()
