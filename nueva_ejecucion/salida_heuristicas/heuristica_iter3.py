def heuristic(items_state):
    # No external imports allowed, so time.time() cannot be used.
    # start_time = time.time() 

    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    num_items = len(weights)

    # Handle edge cases: no items or zero capacity
    if num_items == 0 or capacity == 0:
        return {
            "items": [],
            "total_value": 0,
            "total_peso_usado": 0,
            "solve_time": 0.0 # Placeholder as time.time() is forbidden
        }

    # Prepare item data: (density, value, weight, original_index)
    # Density calculation handles zero-weight items:
    # - If weight is 0 and value > 0, assign infinite density (highest priority).
    # - If weight is 0 and value is 0, assign 0 density (lowest priority).
    # - Otherwise, calculate value/weight.
    item_data = []
    for i in range(num_items):
        if weights[i] == 0:
            density = float('inf') if values[i] > 0 else 0.0
        else:
            density = values[i] / weights[i]
        item_data.append((density, values[i], weights[i], i))

    # Sort items:
    # 1. By density in descending order (highest density first).
    # 2. For items with equal density, by value in descending order (more valuable first).
    # This tie-breaking helps in selecting better items when densities are similar.
    item_data.sort(key=lambda x: (x[0], x[1]), reverse=True)

    current_total_value = 0
    current_total_weight = 0
    # Use a set for selected items for efficient additions and removals during local search
    current_selected_items_indices = set()
    # Store unselected items with their full data for potential swaps
    unselected_items_data = [] # (density, value, weight, original_index)

    # --- Initial Greedy Selection Pass ---
    # Iterate through sorted items and add them if they fit within capacity.
    for density, value, weight, original_index in item_data:
        if current_total_weight + weight <= capacity:
            current_selected_items_indices.add(original_index)
            current_total_weight += weight
            current_total_value += value
        else:
            unselected_items_data.append((density, value, weight, original_index))
            
    # --- Local Search: Iterative 1-for-1 Swaps ---
    # This phase attempts to improve the solution by swapping an unselected item
    # with a selected item if it increases the total value without exceeding capacity.
    # It continues iterating until a full pass yields no improvements.
    
    improvement_made = True
    while improvement_made:
        improvement_made = False
        
        # Create temporary lists for iteration to avoid modifying collections while iterating
        # and to allow re-sorting based on current state.
        temp_selected_indices = list(current_selected_items_indices)
        temp_unselected_items_data = list(unselected_items_data)

        # Sort unselected items by value (descending) to prioritize more valuable additions.
        temp_unselected_items_data.sort(key=lambda x: x[1], reverse=True)
        
        # Sort selected items by value (ascending) to easily find less valuable candidates for removal.
        temp_selected_indices.sort(key=lambda idx: values[idx]) 
        
        # Iterate through unselected items
        for unsel_density, unsel_value, unsel_weight, unsel_idx in temp_unselected_items_data:
            # Optimization: If unselected item cannot fit even if knapsack is empty, skip it.
            if unsel_weight > capacity:
                continue
            
            # Special handling for 0-weight items: if an unselected 0-weight item with positive value
            # is not yet selected, add it directly. This can happen if it was replaced in a previous swap.
            if unsel_weight == 0 and unsel_value > 0 and unsel_idx not in current_selected_items_indices:
                current_selected_items_indices.add(unsel_idx)
                current_total_value += unsel_value
                # No change to current_total_weight as weight is 0
                improvement_made = True
                # Remove this item from unselected_items_data
                unselected_items_data = [item for item in unselected_items_data if item[3] != unsel_idx]
                break # Restart the while loop to re-evaluate with the new state
            
            # Try 1-for-1 swap with selected items
            for sel_idx in temp_selected_indices:
                # Skip if the item is already selected (should not happen with proper set management)
                if sel_idx == unsel_idx:
                    continue

                # Calculate the potential new total weight and value after the swap
                weight_change = unsel_weight - weights[sel_idx]
                value_change = unsel_value - values[sel_idx]

                # Check if the swap is valid (fits capacity) and improves value
                if current_total_weight + weight_change <= capacity and value_change > 0:
                    # Perform the swap
                    current_selected_items_indices.remove(sel_idx)
                    current_selected_items_indices.add(unsel_idx)
                    current_total_weight += weight_change
                    current_total_value += value_change
                    
                    # Update unselected_items_data: remove the newly selected item, add the newly unselected item
                    unselected_items_data = [item for item in unselected_items_data if item[3] != unsel_idx]
                    # Recalculate density for the item being added back to unselected_items_data
                    sel_item_density = values[sel_idx] / weights[sel_idx] if weights[sel_idx] > 0 else (float('inf') if values[sel_idx] > 0 else 0.0)
                    unselected_items_data.append((sel_item_density, values[sel_idx], weights[sel_idx], sel_idx))
                    
                    improvement_made = True
                    break # Break from inner loop (selected items) to restart the while loop
            if improvement_made:
                break # Break from outer loop (unselected items) to restart the while loop

    # end_time = time.time() # Cannot use time.time()

    return {
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": 0.0 # Placeholder as time.time() is forbidden
    }
#