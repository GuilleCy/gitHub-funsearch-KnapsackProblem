def heuristic(items_state):
    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    num_items = len(weights)

    # Handle edge cases: no items or zero capacity
    # As per rule 7, the function must return a numerical value.
    if num_items == 0 or capacity == 0:
        return 0.0

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
    current_selected_items_indices = set()
    
    # Use a dictionary for unselected items for efficient O(1) add/remove by index.
    # Maps original_index -> (density, value, weight, original_index)
    unselected_items_dict = {} 

    # --- Initial Greedy Selection Pass ---
    # Iterate through sorted items and add them if they fit within capacity.
    for density, value, weight, original_index in item_data:
        if current_total_weight + weight <= capacity:
            current_selected_items_indices.add(original_index)
            current_total_weight += weight
            current_total_value += value
        else:
            unselected_items_dict[original_index] = (density, value, weight, original_index)
            
    # --- Local Search: Iterative 1-for-1 Swaps ---
    # This phase attempts to improve the solution by swapping an unselected item
    # with a selected item if it increases the total value without exceeding capacity.
    # It continues iterating until a full pass yields no improvements.
    
    improvement_made = True
    while improvement_made:
        improvement_made = False
        
        # Prepare lists for efficient iteration and sorting within this iteration.
        # Selected items are sorted by value ascending (candidates for removal).
        temp_selected_item_info = []
        for idx in current_selected_items_indices:
            temp_selected_item_info.append((values[idx], weights[idx], idx))
        temp_selected_item_info.sort(key=lambda x: x[0]) 

        # Unselected items are sorted by value descending (candidates for addition).
        # Convert dictionary values to a list for sorting.
        temp_unselected_items_list = list(unselected_items_dict.values())
        temp_unselected_items_list.sort(key=lambda x: x[1], reverse=True) 
        
        # Iterate through unselected items (highest value first)
        for unsel_density, unsel_value, unsel_weight, unsel_idx in temp_unselected_items_list:
            # Skip if this item was already selected in a previous swap within this 'while' iteration.
            # This is necessary because temp_unselected_items_list is a snapshot.
            if unsel_idx in current_selected_items_indices:
                continue
            
            # Special handling for 0-weight items with positive value: add directly if not selected.
            # This item should always be added if not already, as it doesn't consume capacity.
            if unsel_weight == 0 and unsel_value > 0:
                current_selected_items_indices.add(unsel_idx)
                current_total_value += unsel_value
                # O(1) removal from dictionary.
                del unselected_items_dict[unsel_idx]
                improvement_made = True
                # Break from current loop and restart the 'while' loop to re-evaluate state.
                break 
            
            # Optimization: If unselected item cannot fit even if knapsack is empty, skip it.
            if unsel_weight > capacity:
                continue
            
            # Try 1-for-1 swap with selected items (lowest value first)
            for sel_value, sel_weight, sel_idx in temp_selected_item_info:
                # Skip if this item was already unselected in a previous swap within this 'while' iteration.
                # This is necessary because temp_selected_item_info is a snapshot.
                if sel_idx not in current_selected_items_indices:
                    continue

                # Calculate the potential new total weight and value after the swap
                weight_change = unsel_weight - sel_weight
                value_change = unsel_value - sel_value

                # Check if the swap is valid (fits capacity) and improves value
                if current_total_weight + weight_change <= capacity and value_change > 0:
                    # Perform the swap
                    current_selected_items_indices.remove(sel_idx)
                    current_selected_items_indices.add(unsel_idx)
                    current_total_weight += weight_change
                    current_total_value += value_change # FIX: Corrected typo from 'value_value'
                    
                    # O(1) updates for unselected_items_dict.
                    # Remove the newly selected item from unselected_items_dict.
                    del unselected_items_dict[unsel_idx] 
                    # Add the newly unselected item back to unselected_items_dict.
                    sel_item_density = values[sel_idx] / weights[sel_idx] if weights[sel_idx] > 0 else (float('inf') if values[sel_idx] > 0 else 0.0)
                    unselected_items_dict[sel_idx] = (sel_item_density, values[sel_idx], weights[sel_idx], sel_idx)
                    
                    improvement_made = True
                    break # Break from inner loop (selected items) to restart the while loop
            if improvement_made:
                break # Break from outer loop (unselected items) to restart the while loop

    # As per rule 7, the function must return a numerical value (float or int).
    # The most relevant numerical value is the total value found.
    return float(current_total_value)
#