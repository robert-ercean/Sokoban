from .solver import Solver
from sokoban.map import Map
from . import heuristics

class BeamSearch(Solver):

    def __init__(self, map: Map, beam_width: int, heuristic: callable, allow_pulls=False):
        super().__init__(map)
        self.beam_width = beam_width
        self.heuristic = heuristic
        self.max_restarts = 10
        self.allow_pulls = allow_pulls
        self.explored_states = 0

    def solve(self):
        """
        Finds a solution using Beam Search. If goal is not reached,
        returns the path to the state with the best heuristic found.
        """
        initial_map_state = self.map

        # Check if initial state is solvable according to the heuristic for debugging purposes
        initial_heuristic = self.heuristic(initial_map_state)
        if initial_heuristic == float('inf'):
            print("Initial state is deadlocked or unsolvable according to heuristic - I'll cry if I reach this point.")
            return None
        if initial_map_state.is_solved():
             print("Initial state is already solved.")
             return [initial_map_state.copy()]

        initial_hashable_state = self.get_hashable_state(initial_map_state)

        visited = {initial_hashable_state}
        parents = {} # Stores (k, v) : (child_hash, parent_hash)
        state_map = {initial_hashable_state: initial_map_state} # Stores hash -> Map object

        best_heuristic_so_far = initial_heuristic
        best_state_hash_so_far = initial_hashable_state

        goal_hash = None
        last_visited = {}
        last_parents = {}
        restarts, i = 0, 0

        # Beam stores: (heuristic_value, current_map_object)
        beam = [(initial_heuristic, initial_map_state)]
        while beam:
            candidates = []
            processed_in_step = set()

            for _, current_map in beam:
                current_hash = self.get_hashable_state(current_map)

                neighbours = current_map.get_neighbours(allow_pulls=self.allow_pulls)

                for neigh in neighbours:
                    neigh_hash = self.get_hashable_state(neigh)
                    if neigh_hash not in visited and neigh_hash not in processed_in_step:
                        processed_in_step.add(neigh_hash)
                        
                        # Avoid a two-way loop during reconstruction after a restarted search
                        if neigh_hash not in parents:
                            parents[neigh_hash] = current_hash
                        state_map[neigh_hash] = neigh

                        if neigh.is_solved():
                            goal_hash = neigh_hash
                            print(f"Goal state found!\nExplored states: {len(visited)}")
                            self.explored_states = len(visited)
                            beam = []
                            break

                        neigh_heur = self.heuristic(neigh)

                        # Ignore deadlock positions
                        if neigh_heur != float('inf'):
                            candidates.append((neigh_heur, neigh))
                            # Keep track of the best heuristic so far in case we need to reconstruct a partial solution
                            if neigh_heur < best_heuristic_so_far:
                                last_visited = visited.copy()
                                last_parents = parents.copy()
                                best_heuristic_so_far = neigh_heur
                                best_state_hash_so_far = neigh_hash

                if goal_hash is not None: break

            if goal_hash is not None: break

            # Sort based on the heuristic and keep the top k states
            candidates.sort(key=lambda state_tuple: state_tuple[0])
            # print the heuristic values of the candidates
            beam = candidates[:self.beam_width]

            for _, map_obj in beam:
                visited.add(self.get_hashable_state(map_obj))

            i += 1
            if not beam and restarts < self.max_restarts:
                print("Beam Searched emptied. Restarting with the visited set corresponding to the best heuristic found.")
                restarts += 1
                # Restart the search with the best heuristic found so far
                beam = [(best_heuristic_so_far, state_map[best_state_hash_so_far])]
                visited = last_visited
                parents = last_parents

        # Check if we have a partial solution or a goal solution
        reconstruction_start_hash = None
        
        if goal_hash is not None:
            # Goal was found, start reconstruction from the goal hash
            reconstruction_start_hash = goal_hash
        else:
            # Goal not found, start reconstruction from the best heuristic found during the search
            print(f"Goal not reached. Reconstructing path to best state found (heuristic: {best_heuristic_so_far}).")
            reconstruction_start_hash = best_state_hash_so_far

        # Goal / partial solution reconstruction
        state_sequence_reversed = []
        current_trace_hash = reconstruction_start_hash

        # Trace back using the parents dictionary
        while current_trace_hash is not None:
            if current_trace_hash in state_map:
                map_obj = state_map[current_trace_hash]
                state_sequence_reversed.append(map_obj.copy())

            parent_hash = parents.get(current_trace_hash)
            # print(f"Tracing back: {current_trace_hash} -> {parent_hash}")
            current_trace_hash = parent_hash

        state_sequence = list(reversed(state_sequence_reversed))
        print(f"Reconstructed path size: {len(state_sequence)}")
        return state_sequence