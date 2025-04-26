from .solver import Solver
from sokoban.map import Map
from . import heuristics

# We'll assume a standard cost for each possible move
# since pull moves are automatically filtered out in map.py
MOVE_COST = 1

class LrtaStar(Solver):

    def __init__(self,map: Map, heuristic: callable, max_steps = 10000000, allow_pulls=False):
        super().__init__(map)
        self.heuristic = heuristic
        self.H_table = {}
        self.explored_states = 0
        self.max_steps = max_steps
        self.allow_pulls = allow_pulls

    def get_from_heurs_table(self, state: Map):
        state_hash = self.get_hashable_state(state)

        if state_hash not in self.H_table:
            self.H_table[state_hash] = self.heuristic(state)

        return self.H_table[state_hash]

    def solve(self):
        curr = self.map
        self.solution_path = [curr]
        curr_heur = self.heuristic(curr)

        if curr_heur == float('inf'):
            print("Initial state is deadlocked according to heuristic - I'll cry if I reach this point.")
            return None
        
        if curr.is_solved():
            print("Initial state is already solved.")
            return [curr]

        steps = 0
        while steps < self.max_steps:
            if (curr.is_solved()):
                print("LRTA* found a goal solution")
                return self.solution_path

            curr_hash = self.get_hashable_state(curr)
            neighs = curr.get_neighbours(allow_pulls=self.allow_pulls)
            self.H_table[curr_hash] = self.heuristic(curr)

            min_lookahead_cost = float('inf')
            best_neigh = None

            for neigh in neighs:
                h_neigh = self.get_from_heurs_table(neigh)
                # Add a penalty if we get a pull move
                if neigh.undo_moves > curr.undo_moves:
                    h_neigh += 10

                lookahead_cost = None
                if h_neigh == float('inf'):
                    lookahead_cost = float('inf')
                else:
                    lookahead_cost = MOVE_COST + h_neigh

                if lookahead_cost < min_lookahead_cost:
                    min_lookahead_cost = lookahead_cost
                    best_neigh = neigh
            
            # Some debugging in case every possible move leads to a deadlock
            if best_neigh is None or min_lookahead_cost == float('inf'):
                print(f"LRTA* Stuck at an unavoidable deadlock.")
                return None

            self.H_table[curr_hash] = min_lookahead_cost
            curr = best_neigh

            self.solution_path.append(curr)
            steps += 1

        print("LRTA* ran out of max_steps and failed to reach a goal solution.")
        return self.solution_path
