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
    
    # Use a boolean array to quickly track selected items by their original index.
    is_selected = [False] * num_items

    # --- Step 1: Initial Greedy Selection based on density ---
    # This pass prioritizes items by density and adds them if they fit.
    for density, value, weight, original_index in item_data:
        if current_total_weight + weight <= capacity:
            current_total_weight += weight
            current_total_value += value
            is_selected[original_index] = True

    # --- Step 2: Second Greedy Pass for Remaining Capacity (after initial fill) ---
    # The initial greedy pass might leave some remaining capacity if the next densest item
    # is too large. This step performs a second greedy pass on the *unselected* items,
    # prioritizing by density, to fill any remaining capacity with multiple smaller items
    # if they fit, which can lead to better knapsack filling and higher total value.
    remaining_capacity = capacity - current_total_weight
    
    if remaining_capacity > 0:
        # Iterate through the *already sorted* item_data again.
        # This ensures we pick the densest available items that fit the *current remaining* space.
        for density, value, weight, original_index in item_data:
            if not is_selected[original_index]:  # Only consider items not already in the knapsack
                if weight <= remaining_capacity: # Check if the item fits the *current remaining* capacity
                    current_total_weight += weight
                    current_total_value += value
                    is_selected[original_index] = True
                    remaining_capacity -= weight # Crucially, update remaining capacity after adding the item

    # --- Step 3: Local Search (Best 1-for-1 Swap/Exchange Heuristic) ---
    # Attempt to improve the solution by finding the best possible 1-for-1 swap
    # in each pass. This is a "best improving" strategy, which is more robust
    # than "first improving" for escaping local optima within a limited number of passes.
    # The 2-for-1 swap has been removed to reduce execution time complexity from O(N^3) to O(N^2).
    
    has_improved_in_pass = True # Flag to indicate if any improvement was made in a full pass
    max_swap_passes = 3 # Number of full passes for local search. Can be tuned for time/quality trade-off.

    pass_count = 0
    while has_improved_in_pass and pass_count < max_swap_passes:
        has_improved_in_pass = False # Assume no improvement in this pass until one is found
        pass_count += 1
        
        best_gain = 0
        best_i_to_remove_original_idx = -1
        best_j_to_add_original_idx = -1

        # Iterate through items currently selected (item_i) to find one to remove.
        # Prioritize removing low-density items first, as they are more likely to be replaced by better ones.
        # item_data is sorted by density DESC, so iterate in reverse (from lowest density to highest).
        for i_data_idx in range(num_items - 1, -1, -1):
            density_i, item_i_value, item_i_weight, i_original_idx = item_data[i_data_idx]
            
            if is_selected[i_original_idx]: # Only consider items currently in the knapsack
                
                # Iterate through items NOT currently selected (item_j) to find one to add.
                # Prioritize adding high-density items first.
                # item_data is sorted by density DESC, so iterate normally (from highest density to lowest).
                for j_data_idx in range(num_items):
                    density_j, item_j_value, item_j_weight, j_original_idx = item_data[j_data_idx]
                    
                    if not is_selected[j_original_idx]: # Only consider items NOT in the knapsack
                        
                        # Calculate potential new weight if item i_original_idx is replaced by item j_original_idx
                        potential_new_weight = current_total_weight - item_i_weight + item_j_weight
                        
                        # Calculate direct value gain for the swap
                        current_gain_for_swap = item_j_value - item_i_value

                        # Check if the swap is valid (fits capacity) and improves the total value
                        if potential_new_weight <= capacity and current_gain_for_swap > best_gain:
                            best_gain = current_gain_for_swap
                            best_i_to_remove_original_idx = i_original_idx
                            best_j_to_add_original_idx = j_original_idx
            
        # After checking all possible 1-for-1 swaps in this pass, apply the best one if any improvement was found.
        if best_gain > 0:
            # Apply the best swap found using the original item properties for consistency.
            item_to_remove_weight = weights[best_i_to_remove_original_idx]
            item_to_remove_value = values[best_i_to_remove_original_idx]
            item_to_add_weight = weights[best_j_to_add_original_idx]
            item_to_add_value = values[best_j_to_add_original_idx]

            current_total_weight = current_total_weight - item_to_remove_weight + item_to_add_weight
            current_total_value = current_total_value - item_to_remove_value + item_to_add_value
            
            is_selected[best_i_to_remove_original_idx] = False # Mark item i as removed
            is_selected[best_j_to_add_original_idx] = True  # Mark item j as added
            
            has_improved_in_pass = True # An improvement was made, so another pass might find more improvements.

    # --- Step 4: Final Greedy Pass for Remaining Capacity (after swaps) ---
    # It's crucial to re-run a greedy pass after swaps, as swaps might
    # have freed up space or changed the knapsack contents such that new small items fit.
    remaining_capacity = capacity - current_total_weight
    
    if remaining_capacity > 0:
        # Iterate through the *already sorted* item_data again.
        for density, value, weight, original_index in item_data:
            if not is_selected[original_index]:
                if weight <= remaining_capacity:
                    current_total_weight += weight
                    current_total_value += value
                    is_selected[original_index] = True
                    remaining_capacity -= weight 

    # Rebuild the list of selected indices from the boolean array for the final output
    current_selected_items_indices = [idx for idx, selected in enumerate(is_selected) if selected]

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