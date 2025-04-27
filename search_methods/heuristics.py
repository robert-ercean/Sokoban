from scipy.optimize import linear_sum_assignment
from sokoban.map import Map

import numpy as np
from collections import deque

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def min_weight_euclidean(map_obj: Map) -> float | int:

    if map_obj.is_deadlock():
        return float('inf')

    box_positions = list(map_obj.positions_of_boxes.keys())
    target_positions = list(map_obj.targets)

    num_boxes = len(box_positions)
    cost_matrix = np.full((num_boxes, num_boxes), float('inf'))

    # Populate the cost matrix with Euclidean distances
    for i, b_pos in enumerate(box_positions):
        for j, t_pos in enumerate(target_positions):
            dist = np.linalg.norm(np.array(b_pos) - np.array(t_pos))
            cost_matrix[i, j] = dist

    # Find the min cost matching
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    min_total_distance = cost_matrix[row_ind, col_ind].sum()

    return min_total_distance

def min_weight_manhattan(map_obj: Map) -> float | int:
    """
    Combines deadlock check with min-weight matching using the Manhattan distance
    """
    if map_obj.is_deadlock():
        return float('inf')

    box_positions = list(map_obj.positions_of_boxes.keys())
    target_positions = list(map_obj.targets)


    # Create the cost matrix
    num_boxes = len(box_positions)
    cost_matrix = np.full((num_boxes, num_boxes), float('inf'))

    # Populate the cost matrix with Manhattan distances
    for i, b_pos in enumerate(box_positions):
        for j, t_pos in enumerate(target_positions):
            # Manhattan distance
            dist = abs(b_pos[0] - t_pos[0]) + abs(b_pos[1] - t_pos[1])
            cost_matrix[i, j] = dist

    # Find the min cost matching
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    # final heuristic value is the sum of the min cost matching
    min_total_distance = cost_matrix[row_ind, col_ind].sum()

    return min_total_distance

def min_weight_manhattan_with_player(map_obj: Map) -> float | int:
    """
    Improved min_weight: considers both box-target distances and player-box distances.
    """
    if map_obj.is_deadlock():
        return float('inf')

    box_positions = list(map_obj.positions_of_boxes.keys())
    target_positions = list(map_obj.targets)
    player_position = (map_obj.player.x, map_obj.player.y)

    # Create the cost matrix for boxes to targets
    num_boxes = len(box_positions)
    cost_matrix = np.full((num_boxes, num_boxes), float('inf'))

    for i, b_pos in enumerate(box_positions):
        for j, t_pos in enumerate(target_positions):
            dist = abs(b_pos[0] - t_pos[0]) + abs(b_pos[1] - t_pos[1])
            cost_matrix[i, j] = dist

    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    min_total_distance = cost_matrix[row_ind, col_ind].sum()

    # player-to-box proximity penalty
    min_player_distance = min(
        abs(player_position[0] - b[0]) + abs(player_position[1] - b[1])
        for b in box_positions
    )

    # the number of total steps returned by the solution seems to be
    # proportionate to the player-to-box prximity penalty
    # up until a value of 1.5 which seems to be the sweet spot
    return min_total_distance + 1.5 * min_player_distance

def bfs_player_to_nearest_box_adjacent(map_obj: Map, player_pos: tuple, box_positions: list) -> float | int:
    """
    Finds the shortest distance from the player to any square adjacent
    to any box, considering walls. Returns float('inf') if unreachable.
    """
    q = deque([(player_pos, 0)]) # ((row, col), distance)
    visited = {player_pos}
    box_pos_set = set(box_positions)

    target_adj_squares = set()
    # pre-calc all valid squares adjacent to any box
    for (br, bc) in box_positions:
        for dr, dc in DIRS:
            adj_r, adj_c = br + dr, bc + dc
            # check bounds and if it's not a wall or another box
            if (0 <= adj_r < map_obj.length and
                0 <= adj_c < map_obj.width and
                not map_obj.is_wall(adj_r, adj_c) and
                (adj_r, adj_c) not in box_pos_set):
                 target_adj_squares.add((adj_r, adj_c))

    # the player starts on a target adjacent square
    if player_pos in target_adj_squares:
         return 0

    while q:
        (r, c), dist = q.popleft()

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc

            if not (0 <= nr < map_obj.length and 0 <= nc < map_obj.width):
                continue

            neighbor_pos = (nr, nc)

            if map_obj.is_wall(nr, nc) or neighbor_pos in visited or neighbor_pos in box_pos_set:
                continue

            if neighbor_pos in target_adj_squares:
                return dist + 1

            visited.add(neighbor_pos)
            q.append((neighbor_pos, dist + 1))

    return float('inf') # Player cannot reach any position adjacent to a box

def min_weight_bfs_with_player(map_obj: Map):
    """
    Calculates the min-weight matching using BFS for box-target distances
    """

    if map_obj.is_deadlock():
        return float('inf')

    box_positions = list(map_obj.positions_of_boxes.keys())
    target_positions = list(map_obj.targets)

    num_boxes = len(box_positions)
    num_targets = len(target_positions)
    cost_matrix = np.full((num_boxes, num_targets), float(0xffffff))

    # Populate the cost matrix with the BFS dist from each box to all targets
    for i, start in enumerate(box_positions):
        visited = set()
        queue = deque()
        queue.append((start, 0))  # (pos, dist)

        targets_found = set()

        while queue and len(targets_found) < num_targets:
            (x, y), dist = queue.popleft()

            if (x, y) in target_positions:
                j = target_positions.index((x, y))
                cost_matrix[i, j] = dist
                targets_found.add((x, y))
                continue  # can still expand this node to find targets

            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < map_obj.length) and (0 <= ny < map_obj.width):
                    if (nx, ny) not in visited and  not map_obj.is_wall(nx, ny):
                        visited.add((nx, ny))
                        queue.append(((nx, ny), dist + 1))


    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    min_total_distance = cost_matrix[row_ind, col_ind].sum()

    player_position = (map_obj.player.x, map_obj.player.y)

    # player-to-box proximity penalty
    min_player_distance = bfs_player_to_nearest_box_adjacent(map_obj, player_position, box_positions)

    return min_total_distance + 0.5 * min_player_distance

def min_weight_bfs(map_obj: Map):
    """
    Faster heuristic: one BFS per box finds distances to all targets.
    """

    if map_obj.is_deadlock():
        return float('inf')

    box_positions = list(map_obj.positions_of_boxes.keys())
    target_positions = list(map_obj.targets)

    num_boxes = len(box_positions)
    num_targets = len(target_positions)
    cost_matrix = np.full((num_boxes, num_targets), float(0xffffff))

    # Popoluate the cost matrix with the BFS dist from each box to all targets
    for i, start in enumerate(box_positions):
        visited = set()
        queue = deque()
        queue.append((start, 0))  # (pos, dist)

        targets_found = set()

        while queue and len(targets_found) < num_targets:
            (x, y), dist = queue.popleft()

            if (x, y) in target_positions:
                j = target_positions.index((x, y))
                cost_matrix[i, j] = dist
                targets_found.add((x, y))
                continue  # can still expand this node to find targets

            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < map_obj.length) and (0 <= ny < map_obj.width):
                    if (nx, ny) not in visited and  not map_obj.is_wall(nx, ny):
                        visited.add((nx, ny))
                        queue.append(((nx, ny), dist + 1))


    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    min_total_distance = cost_matrix[row_ind, col_ind].sum()

    return min_total_distance
