from scipy.optimize import linear_sum_assignment
from sokoban.map import Map

import numpy as np

def manhattan(map_obj: Map) -> float | int:
    """
        Combines a simple deadlock check with a simple manhattan distance heuristic,
        pairing each box with the corresponding target in pseudo-random order i.e.
        the order in which they are stored in the map object.
    """
    if map_obj.is_deadlock():
        return float(0xffffff)
    ## 2. Manhattan Distance Heuristic
    # Calculate the Manhattan distance from each box to its target position
    # and sum them up
    total_distance = 0
    for box_pos, target_pos in zip(map_obj.positions_of_boxes.keys(), map_obj.targets):
        total_distance += abs(box_pos[0] - target_pos[0]) + abs(box_pos[1] - target_pos[1])

    return total_distance

def min_weight(map_obj: Map) -> float | int:
    """
    Combines a simple deadlock check with min-weight matching using the Manhattan distance
    """
    if map_obj.is_deadlock():
        return float(0xffffff)

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
    # Sum up the total minimum distance between each box and its assigned target
    min_total_distance = cost_matrix[row_ind, col_ind].sum()

    return min_total_distance
