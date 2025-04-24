from .solver import Solver
from sokoban.map import Map
from . import heuristics

class BeamSearch(Solver):

    def __init__(self, map: Map, beam_width: int, heuristic: callable):
        super().__init__(map)
        self.beam_width = beam_width
        self.heuristic = heuristic

    def solve(self):
        initial_map_state = self.map 
        
        initial_hashable_state = self.get_hashable_state(initial_map_state)
        
        visited = {initial_hashable_state}
        # (k, v) - (child_hash, parent_hash)
        parents = {} 
        # Store map objects corresponding to hashes encountered
        # Needed for final path reconstruction
        state_map = {initial_hashable_state: initial_map_state} 

        initial_heuristic = self.heuristic(initial_map_state)
        beam = [(initial_heuristic, initial_map_state)] 

        goal_hash = None

        # Beam: [(heuristic_value, current_map_object)]
        while beam:
            candidates = []
            
            # Process states in the current beam
            for _, current_map in beam:
                current_hash = self.get_hashable_state(current_map)

                neighbours = current_map.get_neighbours() 

                for neigh in neighbours:
                    neigh_hash = self.get_hashable_state(neigh)
                    # Don't tolerate pull moves
                    if neigh_hash not in visited and neigh.undo_moves == 0:
                        visited.add(neigh_hash)
                        
                        # Track parent children relationships
                        parents[neigh_hash] = current_hash 
                        state_map[neigh_hash] = neigh 

                        if neigh.is_solved():
                            goal_hash = neigh_hash
                            print(f"Goal state found!\nExplored states: {len(visited)}")
                            break

                        # Calculate heuristic and add to next beam candidates
                        neigh_heur = self.heuristic(neigh)
                        candidates.append((neigh_heur, neigh))
                
                # Solution reached
                if goal_hash is not None:
                    break 

            # Solution reached
            if goal_hash is not None:
                break
            
            # Sort based on the heuristic and keep the top k states
            candidates.sort(key=lambda state: state[0]) 
            beam = candidates[:self.beam_width]

        # --- Path Reconstruction (if goal was found) ---
        if goal_hash is not None:
            state_sequence_reversed = []
            current_trace_hash = goal_hash

            # Trace back the solution
            while current_trace_hash is not None:
                if current_trace_hash in state_map:
                    map_obj = state_map[current_trace_hash]
                    state_sequence_reversed.append(map_obj) 
                else:
                    # This should never happen
                    print(f"Error: State hash {current_trace_hash} not found in state_map during reconstruction.")
                    return None 

                # Move to the parent state hash
                parent_hash = parents.get(current_trace_hash)
                current_trace_hash = parent_hash
            
            state_sequence = list(reversed(state_sequence_reversed))
            print(f"Reconstructed solution size: {len(state_sequence)}")
            return state_sequence
        else:
            # If the loop finished and goal_hash is still None
            print(f"No solution found\nExplored states: {len(visited)}")
            return None
