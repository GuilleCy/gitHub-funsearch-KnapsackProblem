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
    # This pass prioritizes items by density and adds them if they fit.
    for density, value, weight, original_index in item_data:
        if current_total_weight + weight <= capacity:
            current_selected_items_indices.append(original_index)
            current_total_weight += weight
            current_total_value += value
            is_selected[original_index] = True

    # --- Step 2: Improved Local Improvement - Second Greedy Pass for Remaining Capacity ---
    # The initial greedy pass might leave some remaining capacity if the next densest item
    # is too large. The original code only tried to add *one* single most valuable item.
    # This improved step performs a second greedy pass on the *unselected* items,
    # prioritizing by density, to fill any remaining capacity with multiple smaller items
    # if they fit, which can lead to better knapsack filling and higher total value.
    remaining_capacity = capacity - current_total_weight
    
    if remaining_capacity > 0:
        # Iterate through the *already sorted* item_data again.
        # This ensures we pick the densest available items that fit the *current remaining* space.
        for density, value, weight, original_index in item_data:
            if not is_selected[original_index]:  # Only consider items not already in the knapsack
                if weight <= remaining_capacity: # Check if the item fits the *current remaining* capacity
                    current_selected_items_indices.append(original_index)
                    current_total_weight += weight
                    current_total_value += value
                    is_selected[original_index] = True
                    remaining_capacity -= weight # Crucially, update remaining capacity after adding the item
                    # Continue to fill as much as possible with other items
                    # until remaining_capacity is 0 or no more items fit.

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