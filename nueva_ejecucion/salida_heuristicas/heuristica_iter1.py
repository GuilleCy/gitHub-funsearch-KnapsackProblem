def heuristic(items_state):
    # Placeholder for start_time, as 'time' module imports are forbidden.
    # The problem statement requires 'solve_time' in the output, so these variables are defined.
    start_time = 0.0 

    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    num_items = len(weights)

    # Prepare item data: (density, value, weight, original_index)
    # Density is calculated as value/weight. Handle zero-weight items:
    # - If weight is 0 and value is positive, assign infinite density (always take).
    # - If weight is 0 and value is 0, assign zero density (useless).
    # - Otherwise, calculate v/w.
    item_data = []
    for i in range(num_items):
        if weights[i] > 0:
            density = values[i] / weights[i]
        elif values[i] > 0:
            density = float('inf')  # Infinitely dense, prioritize
        else:
            density = 0.0  # Useless item, lowest priority
        item_data.append((density, values[i], weights[i], i))

    # Sort items by density in descending order.
    # This is the core of the greedy strategy.
    item_data.sort(key=lambda x: x[0], reverse=True)

    current_total_value = 0
    current_total_weight = 0
    current_selected_items_indices = []
    
    # Use a boolean array to quickly track selected items by their original index.
    is_selected = [False] * num_items

    # --- Step 1: Initial Greedy Selection based on density ---
    for density, value, weight, original_index in item_data:
        if current_total_weight + weight <= capacity:
            current_selected_items_indices.append(original_index)
            current_total_weight += weight
            current_total_value += value
            is_selected[original_index] = True

    # --- Step 2: Local Improvement - Fill the remaining capacity with the most valuable single item ---
    # This step tries to improve knapsack filling by utilizing any remaining capacity
    # that the initial greedy pass might have left due to items being too large.
    remaining_capacity = capacity - current_total_weight
    
    if remaining_capacity > 0:
        best_fill_item_idx = -1
        max_fill_value = -1

        # Iterate through all items to find the best unselected item that fits the remaining capacity.
        for i in range(num_items):
            if not is_selected[i]:  # Only consider items not already in the knapsack
                if weights[i] <= remaining_capacity:
                    if values[i] > max_fill_value:
                        max_fill_value = values[i]
                        best_fill_item_idx = i
        
        # If a suitable item is found, add it to the knapsack.
        if best_fill_item_idx != -1:
            current_selected_items_indices.append(best_fill_item_idx)
            current_total_weight += weights[best_fill_item_idx]
            current_total_value += values[best_fill_item_idx]
            is_selected[best_fill_item_idx] = True # Mark as selected

    # Placeholder for end_time, as 'time' module imports are forbidden.
    end_time = 0.0

    # The function must return a dictionary with specific keys.
    return {
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": end_time - start_time  # Will be 0.0 due to placeholders
    }
#