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

    # Helper function for greedy fill (nested to avoid global scope/imports)
    # This function attempts to fill any remaining capacity with available items,
    # prioritizing by density. It modifies the selected_arr in place.
    def _greedy_fill_internal(current_val, current_wt, selected_arr, sorted_item_data, max_capacity):
        remaining_cap = max_capacity - current_wt
        if remaining_cap <= 0:
            return current_val, current_wt, selected_arr
        
        # Iterate through items sorted by density, picking unselected items that fit
        for d, v, w, original_idx in sorted_item_data:
            if not selected_arr[original_idx]:  # Only consider items not already in the knapsack
                if w <= remaining_cap: # Check if the item fits the *current remaining* capacity
                    current_val += v
                    current_wt += w
                    selected_arr[original_idx] = True
                    remaining_cap -= w  # Crucially, update remaining capacity after adding the item
        return current_val, current_wt, selected_arr

    # --- Step 1: Initial Greedy Selection based on density (consolidated) ---
    # This replaces the original Step 1 and Step 2 by using the consolidated helper.
    current_total_value, current_total_weight, is_selected = _greedy_fill_internal(
        current_total_value, current_total_weight, is_selected, item_data, capacity
    )

    # --- Step 2: Local Search (Best 1-for-1 Swap/Exchange Heuristic) ---
    # Attempt to improve the solution by finding the best possible 1-for-1 swap
    # in each pass. This is a "best improving" strategy.
    
    has_improved_in_pass = True # Flag to indicate if any improvement was made in a full pass
    max_swap_passes = 3 # Number of full passes for local search. Tuned for better value/time balance.

    pass_count = 0
    while has_improved_in_pass and pass_count < max_swap_passes:
        has_improved_in_pass = False # Assume no improvement in this pass until one is found
        pass_count += 1
        
        best_gain = 0
        best_i_to_remove_original_idx = -1
        best_j_to_add_original_idx = -1

        # Iterate through items currently selected (item_i) to find one to remove.
        # Prioritize removing low-density items first.
        for i_data_idx in range(num_items - 1, -1, -1): # Reverse iteration for low-density first
            density_i, item_i_value, item_i_weight, i_original_idx = item_data[i_data_idx]
            
            if is_selected[i_original_idx]: # Only consider items currently in the knapsack
                
                # Iterate through items NOT currently selected (item_j) to find one to add.
                # Prioritize adding high-density items first.
                for j_data_idx in range(num_items): # Normal iteration for high-density first
                    density_j, item_j_value, item_j_weight, j_original_idx = item_data[j_data_idx]
                    
                    if not is_selected[j_original_idx]: # Only consider items NOT in the knapsack
                        
                        # Calculate potential new weight if item i_original_idx is replaced by item j_original_idx
                        potential_new_weight = current_total_weight - item_i_weight + item_j_weight
                        current_gain_for_swap = item_j_value - item_i_value # Direct value gain

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

            # Intermediate Greedy Pass after 1-for-1 swaps:
            # Re-fill any newly available capacity with other unselected items.
            current_total_value, current_total_weight, is_selected = _greedy_fill_internal(
                current_total_value, current_total_weight, is_selected, item_data, capacity
            )

    # --- Step 3: Local Search (Best 1-for-Many Swap/Exchange Heuristic - Single Pass) ---
    # This O(N^2) operation replaces the O(N^3) 2-for-1 and 1-for-2 swaps.
    # It aims to find potentially larger improvements by removing one item and
    # then greedily filling the freed space with any number of other items.
    
    best_gain_1_for_many = 0
    best_is_selected_after_swap = None # Store the entire state after the best swap

    # Iterate through items currently selected (item_i) to find one to remove.
    # Prioritize removing low-density items first.
    for i_data_idx in range(num_items - 1, -1, -1):
        density_i, item_i_value, item_i_weight, i_original_idx = item_data[i_data_idx]
        
        if is_selected[i_original_idx]: # Only consider items currently in the knapsack
            
            # Temporarily remove item_i
            temp_val = current_total_value - item_i_value
            temp_wt = current_total_weight - item_i_weight
            temp_is_selected = list(is_selected) # Create a copy to modify
            temp_is_selected[i_original_idx] = False

            # Perform a greedy fill with the new remaining capacity
            val_after_fill, wt_after_fill, selected_after_fill = _greedy_fill_internal(
                temp_val, temp_wt, temp_is_selected, item_data, capacity
            )

            current_gain_for_swap_1_for_many = val_after_fill - current_total_value

            # Check if this swap and subsequent fill improves the total value
            # _greedy_fill_internal ensures capacity is not exceeded.
            if current_gain_for_swap_1_for_many > best_gain_1_for_many:
                best_gain_1_for_many = current_gain_for_swap_1_for_many
                best_is_selected_after_swap = selected_after_fill # Store the state

    # Apply the best 1-for-many swap if an improvement was found.
    if best_gain_1_for_many > 0:
        # The best_is_selected_after_swap already contains the final state
        # after removing the item and greedily filling.
        is_selected = best_is_selected_after_swap
        
        # Recalculate current_total_value and current_total_weight from the new is_selected
        # This is safer than trying to track it incrementally, especially with _greedy_fill_internal
        # modifying multiple items.
        current_total_value = 0
        current_total_weight = 0
        for idx in range(num_items):
            if is_selected[idx]:
                current_total_value += values[idx]
                current_total_weight += weights[idx]

    # --- Final Greedy Pass for Remaining Capacity (after all swaps) ---
    # This ensures any remaining small capacity after all local searches is optimally filled.
    current_total_value, current_total_weight, is_selected = _greedy_fill_internal(
        current_total_value, current_total_weight, is_selected, item_data, capacity
    )

    # Rebuild the list of selected indices from the boolean array for the final output
    current_selected_items_indices = [idx for idx, selected in enumerate(is_selected) if selected]

    # Placeholder for end_time, as 'time' module imports are forbidden.
    end_time = 0.0

    # The function must return a dictionary with specific keys.
    return {
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": end_time - start_time
    }
#