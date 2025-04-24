from sokoban.map import Map


class Solver:

    def __init__(self, map: Map):
        self.map = map

    def solve(self):
        raise NotImplementedError("solve() is only implemented in children")

    def get_hashable_state(self, map_obj: Map):
        """
        Generates a hashable representation of the current map state.
        Essential for use in 'visited' sets. Includes player and sorted box positions.
        """
        player_pos = (map_obj.player.x, map_obj.player.y)
        # make it hashable then sort box positions to ensure the tuple maintains a consistent ordering
        box_positions = tuple(sorted(map_obj.positions_of_boxes.keys()))
        return (player_pos, box_positions)