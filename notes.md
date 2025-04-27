

## Beam Search
- I started by implementing the Beam Search algorithm because my first thought was that I should start
to build my intuiton about the dynamic of the Sokoban game and implicitly the way i should design my
heuristics around an offline search algorithm.

### Euclidean Distance Heuristic
- I started off by designing the simplest heuristic one could think of for a 2D game: the euclidean distance.
One main difference from this semester's labwork, especially the A* search lab (the labyrinth part) was that,
for a given box, its final position is not fixed, that is, we have multiple target states for a box. This means 
that we would have a final state domain of size equal to the cardinality of the cartesian product of the set of 
boxes and the set of target positions i.e. N^2, where N is the number of boxes.
- The first critical thinking point was to understand how I should interpret this final state domain.
One idea would be to assign a given box to its closest target position where the euclidean distance is the smallest,
but, by following this line of thought I would have ended up with a non-admisable heuristic, considering the
following scenario which I observed after glancing at the maps: *super_hard_map1* and *hard_map1*.:
    - For a given box, I would have assigned it to its closest target position, but, this may not always be the best,
    for example, in *hard_map1* this would have led to a deadlock where I would encounter 2 boxes on a border column
    in which there is only one target position. As pull moves are not desirable, this will be an irreversible move.

- This lead me to the conclusion I need to add some kind of penalty for moves that lead to deadlocks.
I thought it would be a good idea if this penalty would just give zero-tolerance to those moves, thus just
removing them from the search space i.e. an infinite cost.

- After momentarily taking care of those assignments that lead to deadlocks, the main problem still persisted:
How to manage the final state domain? After researching a bit, I found that I could consider the final state domain
as a bipartite graph where the boxes are the left nodes and the target positions are the right nodes.
The edges of this graph are the euclidean distances between the boxes and the target positions. The goal is to find the
minimum cost perfect matching of this bipartite graph. This is a well known problem in combinatorial optimization
known as the assignment problem. I used the sci-py library that uses an O(N^3) algorithm which is pretty insignificant
in computational terms for the sizes of the maps I was dealing with (a maximum of 5 boxes) therefore I didn't bother to
optimize this further.

- I was pretty optimistic about this method of min-weight perfect matching so I introduced 0 tolerance for
pull moves, disabling them completly from the search space.

- After running the algorithm with this heuristic, and analysing the runtimes and states explored for each
kind of map, the results were as expected:
    - For the easy maps, where the search space is small, the number of states explored and the runtime 
    was proportional to the map size
    - For the medium maps, with a slightly larger search space, the number of states explored still remained
    proportional to the map size as we can see an average *2.5x increase factor* but the runtime remained similar to the easy maps.
    - For the hard maps and the super hard map,  the runtime still remained simiar to the previous maps i.e. the 0.4s range,
    and surprinsly so did the number of states explored. This was a bit unexpected as I thought that the number of states explored would be larger since these maps require more complex tactics to solve them
    - The last maps which I was most curious about, the *large* maps showcased this heuristic's true downfall.
    While for the first large map which is similar in size to one of the medium maps and has a total of 2 boxes the algo reaches
    a solution with a number of explored states and runtime similar to the medium maps, the second large map which has a signifcantly larger
    search space and a higher number of boxes (3) which are also placed in a more complex manner (the closest target position is not always the best one), the algorithm fails to find a solution.

- The best explanation I could come up with for this failure was the heuristic's quality. Because Beam Search is a greedy algorithm, it will always try to expand the most promising nodes first. This means that if the heuristic is not good enough, it will get stuck in a local minimum and will not be able to find the optimal solution as was the case for *large_map2*.

- Next step was finding a better heuristic for calculating the distances between the boxes and the targets while maintaing the min_weight perfect matching.
- Next candidate would the Manhattan distance.

### Manhattan Distance Heuristic
- The Manhattan distance is calculated as the sum of the absolute differences between the x and y coordinates of two points i.e. the total
number of moves needed to reach a target position from a given box position.

After analysing the results, these were the main conclusions:
- As expected, the Manhattan distance heuristic is a better heuristic than the Euclidean distance heuristic as it takes into account the fact that the boxes can only move in 4 directions (up, down, left, right) and not diagonally.
- While the number of states explored remained similar to the Euclidean distance, just a bit lower, we can see a decrease in the runtime for all maps, averaging around a 0.5x factor decrease to the Euclidean distance heuristic.
- Furthermore, now, the algorithm was able to find a solution for the *large_map2* which was previously unsolvable, indicating that the Manhattan distance avoids local minima better. Again, one conclusion is that this heuristic is better suited for the Sokoban game as it doesn't take into account diagonal moves.


- The next step was following the same line of thought as before which is to try and optimize the method of calculating the distances between the boxes and the targets while maintaing the min_weight perfect matching. First, we removed diagonal moves from the Euclidean distance since they were impossible, leading to the Manhattan distance which indeed showed better results. The obvious thing to do next
is to calculate the distances while ignoring unpassable obstacles i.e. walls and boxes. The best solution is using Breadth-First-Search.

- Here's a few things I expected to happen since BFS only considers passable trajectories, the distances will be more accurate and thus the heuristic will perform better:
    - The number of states explored will be lower since the heuristic will be more accurate and thus the algorithm will not get stuck in local minima as often.
    - The runtime will be lower since it will converge faster to the optimal paths
    - We'll see these benefits especially for the larger maps and maps in which we have plentiful walls (hards, super_hard and medium2)

- Observed behaviour:
    - While for the easy and medium maps and *even the hard / super hard maps*, we can see a *very slight* decrease in the number of states explored and the runtime, as expected, the main benefits were observed for larger maps.
    - For the larger maps, we can see a 0.5x factor decrease in the totam number of states explored
    - Although, for the runtime, we can see a slight increase in the runtime for the larger maps, as expected since BFS has a much higher
    time complexity than the Manhattan and Euclidean distances which are O(1) calculations.

- One critical conclusion I came up with is that, while Min-Weight Perfect Matching is a good heuristic, it's very important
how these distances are calculated. As seen and described above, the performance of the algorithm is proportional to the quality of 
the method of calculating this distance. Therefore we can say that: BFS > Manhattan > Euclidean in terms of admissibility with a slight
increase in computational time.


## LRTA*

- When designing the LRTA* algorithm, I started off similar to Beam Search. I began by analysing its performance when using
Min-Weight Perfect Matching where the distance is calculated using the Euclidean Distance.

- It should be noted that I allowed pull moves for LRTA* as I couldn't find optimal solutions for the all maps without them.
- One way to manage minimizing the pull moves I used is to assign an heuristic cost of 10 for pull moves, trying to avoid them as much as possible. Furthermore, I also considered that the heuristic cost of every move is 4 (c(s, s')) - the cost of an edge in the graph search space. I did this to try to lower the number of "switches" between two adjacent states as this is a common pattern in a LRTA* search.

When using Min-Weight with Euclidean distance, the results were as follows in comparison to Beam Search with the same heuristic:
- The number of steps taken was signficantly higher than Beam Search's explored states for more complex/ larger maps, as expected since LRTA* is an online search algorithm and it doesn't have the luxury of looking ahead in the search space.
- One interesting observation was that the number of steps was signifcantly *lower* for the easy maps.

- Next, as we move higher in the heuristic quality hierarchy, we'll analyse the performance using the Manhattan distance heuristic:
- As expected, the number of steps and implictly the runtime for the majority of maps was lower than the Euclidean distance, though the difference was not as significant as I expected, in contrast to the Beam Search where the difference was more pronounced.
- The only outlier was *super_hard_map2* where the number of steps was much lower that the Euclidean counterpart i.e. a 0.5x decrease factor,
a 0.7 decrease factor for the runtime and 0.5x decrease factor for the total pull moves used. This is probably because the map is so complex that it benefits from the diagonal moves assumptions that the Euclidean distance heuristic has in some way.

- Another very intereseting thing worth noting is that the number of pull moves seems to be proportional to the size of the map and not the complexity of the map.

- Next, the heuristic I was looking forward to testing the most: Distance with BFS:
- 

