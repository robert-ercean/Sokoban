from .solver import Solver
from sokoban.map import Map
from . import heuristics

class BeamSearch(Solver):

    def __init__(self, map: Map, beam_width: int, heuristic: callable):
        super().__init__(map)
        self.beam_width = beam_width
        self.heuristic = heuristic

    def solve(self): # Removed return type hint
        """
        Finds a solution using Beam Search. If goal is not reached,
        returns the path to the state with the best heuristic found.
        """
        # Use self.initial_map from the Solver base class if it exists and is preferred
        # Otherwise, use self.map if Solver doesn't store initial_map
        initial_map_state = getattr(self, 'initial_map', self.map) # Safer access

        # Check if initial state is solvable
        initial_heuristic = self.heuristic(initial_map_state)
        if initial_heuristic == float('inf'):
            print("Initial state is deadlocked or unsolvable according to heuristic.")
            return None
        if initial_map_state.is_solved():
             print("Initial state is already solved.")
             return [initial_map_state.copy()] # Ensure copy() method exists

        initial_hashable_state = self.get_hashable_state(initial_map_state)

        visited = {initial_hashable_state}
        parents = {} # Stores child_hash -> parent_hash
        state_map = {initial_hashable_state: initial_map_state} # Stores hash -> Map object

        # --- Track best state found ---
        best_heuristic_so_far = initial_heuristic
        best_state_hash_so_far = initial_hashable_state
        # --- End track best state ---

        # Beam stores: (heuristic_value, current_map_object)
        beam = [(initial_heuristic, initial_map_state)]

        goal_hash = None

        while beam:
            candidates = []
            processed_in_step = set()

            for _, current_map in beam:
                current_hash = self.get_hashable_state(current_map)

                neighbours = current_map.get_neighbours()

                for neigh in neighbours:
                    neigh_hash = self.get_hashable_state(neigh)

                    if neigh.undo_moves != 0:
                         continue

                    if neigh_hash not in visited and neigh_hash not in processed_in_step:
                        processed_in_step.add(neigh_hash) # Mark for this step

                        parents[neigh_hash] = current_hash
                        state_map[neigh_hash] = neigh

                        if neigh.is_solved():
                            goal_hash = neigh_hash
                            print(f"Goal state found!\nExplored states: {len(visited)}")
                            beam = []
                            break

                        neigh_heur = self.heuristic(neigh)

                        # Ignore deadlock positions
                        if neigh_heur != float('inf'):
                            candidates.append((neigh_heur, neigh))
                            # Keep track of the best heuristic so far in case we need to reconstruct a partial solution
                            if neigh_heur < best_heuristic_so_far:
                                best_heuristic_so_far = neigh_heur
                                best_state_hash_so_far = neigh_hash

                if goal_hash is not None: break

            if goal_hash is not None: break

            # Sort based on the heuristic and keep the top k states
            candidates.sort(key=lambda state_tuple: state_tuple[0])
            beam = candidates[:self.beam_width]

            for _, map_obj in beam:
                visited.add(self.get_hashable_state(map_obj))

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
        if reconstruction_start_hash is not None:
            state_sequence_reversed = []
            current_trace_hash = reconstruction_start_hash

            # Trace back using the parents dictionary
            while current_trace_hash is not None:
                if current_trace_hash in state_map:
                    map_obj = state_map[current_trace_hash]
                    state_sequence_reversed.append(map_obj.copy())

                parent_hash = parents.get(current_trace_hash)
                current_trace_hash = parent_hash

            state_sequence = list(reversed(state_sequence_reversed))
            print(f"Reconstructed path size: {len(state_sequence)}")
            return state_sequence
        else:
             # Should have been caught above, but as a fallback
             print(f"Beam search ended. No goal found and no best state identified. Explored: {len(visited)} states.")
             return None