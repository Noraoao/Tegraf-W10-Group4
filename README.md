# Informatics ITS Graph Theory class Group 4
|Name|NRP|
|---|---|
|Naura Rizky Ameira|5025251001|
|Farras Al-Ghifari|5025251006|
|Nisrina Zahralilla|5025251013|
|Safiya Nadira Az-zahra|5025251268|

## Week 10 Task 

## Coloring: DSATUR & Backtracking Algorithm
- ### BRIEF ALGORITHM EXPLANATION
  The algorithm uses Graph Coloring with the DSATUR (Degree of Saturation) heuristic and Backtracking to solve Sudoku puzzles. The idea is to represent the Sudoku board as a graph, where each of the 81 cells is a vertex. Two vertices are connected if their cells belong to the same row, column, or 3×3 box. The numbers 1–9 are treated as colors, and connected vertices cannot have the same color.

  The algorithm uses DSATUR to select which empty cell should be filled first. It prioritizes the vertex with the highest saturation degree, which means the vertex has the largest number of different colors among its neighboring vertices. If two vertices have the same saturation degree, it selects the one with more uncolored neighbors.

  After selecting a vertex, Backtracking tries to assign a valid color from 1 to 9. If a color does not create a conflict, the algorithm continues to the next vertex. If no valid color is available, it goes back to the previous vertex, removes its previous assignment, and tries another color. This process continues until every cell is successfully colored, resulting in a valid Sudoku solution.

- ### RUNNING THE CODE
  1. Open the file in your compiler
  2. Run it
 
- ### RESULT:

  <img width="446" height="521" alt="image" src="https://github.com/user-attachments/assets/469b336c-5f8a-45a6-ab3e-b9e34e2d9630" />

  <img width="451" height="532" alt="image" src="https://github.com/user-attachments/assets/4b4a1281-c9bc-4a9c-9b31-b32908824337" />


## Matching: Algorithm

- ### BRIEF ALGORITHM EXPLANATION
  The algorithm uses a Modified Least Cost Method with a Vogel's Approximation Method (VAM) approach to solve the Transportation Problem. The goal is to allocate goods from multiple sources to different destinations while minimizing the total transportation cost. The problem is represented using a cost matrix, where each cell represents the transportation cost from a source to a destination.

  The algorithm first calculates the penalty for each available row and column by finding the difference between the two lowest transportation costs. It then selects the row or column with the highest penalty, prioritizing the one where choosing a more expensive alternative could result in a greater additional cost.

  After selecting a row or column, the algorithm finds the cell with the lowest transportation cost and allocates the maximum possible amount based on the available supply and demand. The supply and demand values are updated after each allocation. This process continues until all possible allocations are completed, producing an initial feasible solution with its corresponding total transportation cost.

The program also supports dynamic matrix sizes, allowing users to enter different numbers of sources and destinations without changing the code.

- ### RUNNING THE CODE
  1. Open the file in your C++ compiler.
  2. Compile and run the program.
  3. Enter the number of sources (M) and destinations (N).
  4. Enter the transportation cost matrix.
  5. Enter the supply values for each source.
  6. Enter the demand values for each destination.
  7. The program displays the total transportation cost.

- ### SAMPLE INPUTS

    RESULT:


## AI USAGE DISCLOSURE

- Coloring [DSATUR and Backtracking Algorithm]: https://claude.ai/share/399496ce-90cc-4c2f-a805-8dd08e689d61
