# Sokoban Solver Analysis: Beam Search vs. LRTA*

This document outlines the implementation and analysis of different search algorithms and heuristics applied to the Sokoban game.

## Beam Search

Beam Search was initially implemented with a beam width of 15 to build intuition about the Sokoban game dynamics and heuristic design for an offline search algorithm.

### Euclidean Distance Heuristic

* **Initial Design:** The simplest heuristic, Euclidean distance, was considered first. A key challenge compared to standard A* search (like the lab labyrinth) is that boxes have multiple potential target positions, not a single fixed goal. This creates a large final state domain (N^2, where N is the number of boxes).
* **Interpreting Final States:** Assigning a box to its nearest target via Euclidean distance could lead to non-admissible heuristics and deadlocks (e.g., two boxes needing the same single target position on a border, as observed in `super_hard_map1` and `hard_map1`). Pull moves are undesirable and considered irreversible in such deadlocks.
* **Deadlock Penalty:** To avoid deadlocks, moves leading to them were given an infinite cost, effectively removing them from the search space.
* **Assignment Problem:** The core issue remained managing the final state domain. The solution involved modeling it as a bipartite graph (boxes on one side, targets on the other) with edge weights as Euclidean distances. The goal is to find the minimum cost perfect matching, a classic assignment problem. The `scipy` library's O(N^3) algorithm was sufficient for the map sizes (max 5 boxes).
* **Heuristic Calculation:** The final heuristic value is the sum of weights in the minimum cost perfect matching. Pull moves were completely disabled (zero tolerance).
* **Results:**
    * **Easy/Medium Maps:** Performed as expected, with states explored and runtime proportional to map size. Medium maps showed a ~2.5x increase in explored states but similar runtime to easy maps.
    * **Hard/Super Hard Maps:** Surprisingly, runtime and explored states remained similar to easier maps (~0.4s range), not increasing significantly despite map complexity.
    * **Large Maps:** Showcased the heuristic's downfall. `large_map1` (2 boxes, similar size to medium) was solved similarly to medium maps. However, `large_map2` (larger space, 3 boxes, complex placement) could not be solved.
* **Conclusion:** The failure on `large_map2` was attributed to the heuristic's quality. Beam Search's greedy nature likely got stuck in a local minimum. The next step was to find a better distance calculation method while keeping the min-weight perfect matching approach.

### Manhattan Distance Heuristic

* **Improvement:** Calculated as the sum of absolute differences in coordinates (number of non-diagonal moves). This is better suited as it reflects the box movement constraints (no diagonal moves).
* **Results:**
    * Compared to Euclidean distance: Similar number of explored states (slightly lower), but runtime decreased significantly (~0.5x factor) across all maps.
    * `large_map2` was now solvable, indicating better avoidance of local minima.
* **Conclusion:** Manhattan distance is a better heuristic for Sokoban than Euclidean distance. The next optimization step involved calculating distances considering obstacles (walls, other boxes) using Breadth-First Search (BFS).

### BFS Distance Heuristic

* **Improvement:** Calculates distances considering only passable trajectories (ignoring walls/boxes) using BFS, aiming for more accurate heuristic values.
* **Expectations:** Lower explored states (more accurate heuristic), lower runtime (faster convergence), especially beneficial for large maps or maps with many walls.
* **Observed Behaviour:**
    * **Easy/Medium/Hard/Super Hard Maps:** Very slight decrease in explored states and runtime.
    * **Large Maps:** Significant decrease (0.5x factor) in total explored states. Runtime slightly increased due to BFS's higher computational cost compared to O(1) Manhattan/Euclidean calculations.
* **Conclusion:** The quality of the distance calculation method within the Min-Weight Perfect Matching framework is crucial. Performance is proportional to distance calculation quality: BFS > Manhattan > Euclidean, with a trade-off in computational time.

## LRTA* (Learning Real-Time A*)

* Implemented similarly to Beam Search, starting with Min-Weight Perfect Matching using Euclidean distance.
* **Key Differences:** Pull moves were allowed (necessary for optimal solutions on some maps) but penalized with a heuristic cost of 10 to minimize them. The cost of any move `c(s, s')` was set to 4 to reduce redundant back-and-forth "switches" between adjacent states, a common LRTA* pattern.

### Euclidean Distance Heuristic (LRTA*)

* **Comparison to Beam Search:**
    * Significantly higher steps taken for complex/larger maps (expected for online vs. offline search).
    * Interestingly, *lower* steps taken for easy maps.

### Manhattan Distance Heuristic (LRTA*)

* **Comparison to LRTA* Euclidean:** Lower steps and runtime for most maps, as expected, but the difference wasn't as pronounced as in Beam Search.
* **Outlier (`super_hard_map2`):** Showed significant improvement (0.5x steps, 0.7x runtime, 0.5x pull moves), possibly benefiting from the diagonal assumptions of Euclidean in some complex way.

### BFS Distance Heuristic (LRTA*)

* **Surprising Results:** Performance was generally *worse* (higher steps/runtime) than both Euclidean and Manhattan LRTA* heuristics, contrary to expectations.
* **Outlier (`large_map2`):** BFS performed better here, possibly due to the large map size benefiting more from obstacle-aware distance calculation.

## Comparing Beam Search and LRTA*

* **Runtime:** LRTA* runtimes were consistently higher than Beam Search for the same heuristic.
* **Reason:** Attributed to LRTA* being an online algorithm without lookahead, compared to Beam Search's offline nature.
* **LRTA* Redundancy:** Observed significant redundant moves (player moving back and forth), especially in large maps, likely due to getting stuck in local minima. Increasing move cost from 1 to 4 helped reduce this.

## Improving LRTA* with Player-Proximity Penalty

To reduce the tendency of the player roaming without purpose in LRTA*, a penalty was added for moves leading the player *away* from the closest box.

* **New Heuristics:**
    * `mw_mnht_with_player`: Min-Weight Manhattan + Player Proximity Penalty (distance to box via Manhattan).
    * `mw_bfs_with_player`: Min-Weight BFS + Player Proximity Penalty (distance to box via BFS).
* **Penalty Calculation:** Proportional to the min-weight matching cost, multiplied by a factor 'alpha'.

### LRTA* Results with Proximity Penalty

* **Manhattan + Penalty:** Surprisingly performed *worse* on most maps (more steps, runtime, pull moves), except for `large_map2` where steps decreased.
* **BFS + Penalty:** Performed closer to expectations:
    * Slight improvements on easier maps.
    * Significant improvements (0.2x-0.5x runtime decrease, fewer pull moves) on medium, hard, super-hard, and `large_map1`.
    * **Counter-intuitive Outlier (`large_map2`):** Performed *much worse* (5x runtime increase, added a pull move) than BFS without the penalty.

## Player-Proximity Penalty in Beam Search

Testing the proximity penalty heuristics with Beam Search yielded interesting results:

* **Easy/Medium/Hard/Super Hard Maps:** Similar performance to heuristics without the penalty (sometimes slightly worse).
* **Large Maps:** Significant performance increase:
    * Manhattan + Penalty: ~0.5x decrease in explored states.
    * BFS + Penalty: ~0.7x decrease in explored states.

### Beam Search with Reduced Beam Width

* **Beam Width = 10:**
    * Euclidean now also failed on `medium_map2`.
    * BFS (with and without penalty) now failed on `large_map2`.
* **Beam Width = 5:**
    * All heuristics failed on `medium_map2`, `large_map2`, and `super_hard_map1` EXCEPT **Min-Weight BFS with Player-to-Box Proximity Penalty**.
    * This prevailing heuristic performed even better with the smaller beam width (fewer explored states).

### Interesting conclusion

In conclusion, the best heuristic for the Beam Search algorithm remains the Min-Weight Matching where distances are calculated using the Manhattan Distance, taking into account a Player-to-Box Proximity Penalty proportional to the sum of the previuosly mentioned assignments. Quite shocking since I designed this heuristic for LRTA*, not for Beam Search, how interesting!