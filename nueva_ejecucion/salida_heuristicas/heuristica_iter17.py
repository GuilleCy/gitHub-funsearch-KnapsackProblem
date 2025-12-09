def heuristic(items_state):
    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    num_items = len(weights)

    # Handle edge cases: no items or zero capacity
    # As per the "REQUIRED_FINAL_FUNCTION" block, the function must return a dictionary.
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
            
    # --- Local Search: Iterative 1-for-1 and 1-for-k Swaps ---
    # This phase attempts to improve the solution by swapping items.
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

        # Unselected items are sorted by value descending (candidates for addition in 1-for-1).
        temp_unselected_items_list_by_value = list(unselected_items_dict.values())
        temp_unselected_items_list_by_value.sort(key=lambda x: x[1], reverse=True) 
        
        # --- Phase 1: 0-weight item check & 1-for-1 swaps ---
        # Iterate through unselected items (highest value first)
        for unsel_density, unsel_value, unsel_weight, unsel_idx in temp_unselected_items_list_by_value:
            # Skip if this item was already selected in a previous swap within this 'while' iteration.
            if unsel_idx in current_selected_items_indices:
                continue
            
            # Special handling for 0-weight items with positive value: add directly if not selected.
            if unsel_weight == 0 and unsel_value > 0:
                current_selected_items_indices.add(unsel_idx)
                current_total_value += unsel_value
                del unselected_items_dict[unsel_idx]
                improvement_made = True
                break # Break from current loop to restart the 'while' loop
            
            # Optimization: If unselected item cannot fit even if knapsack is empty, skip it.
            if unsel_weight > capacity:
                continue
            
            # Try 1-for-1 swap with selected items (lowest value first)
            for sel_value, sel_weight, sel_idx in temp_selected_item_info:
                # Skip if this item was already unselected in a previous swap within this 'while' iteration.
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
                    current_total_value += value_change # Corrected typo from 'value_value'
                    
                    # Update unselected_items_dict: remove the newly selected item, add the newly unselected item
                    del unselected_items_dict[unsel_idx] 
                    sel_item_density = values[sel_idx] / weights[sel_idx] if weights[sel_idx] > 0 else (float('inf') if values[sel_idx] > 0 else 0.0)
                    unselected_items_dict[sel_idx] = (sel_item_density, values[sel_idx], weights[sel_idx], sel_idx)
                    
                    improvement_made = True
                    break # Break from inner loop (selected items) to restart the while loop
            if improvement_made:
                break # Break from outer loop (unselected items) to restart the while loop

        # --- Phase 2: 1-for-k swaps (only if no 1-for-1 improvement in this iteration) ---
        # This phase is executed only if Phase 1 did not find any improvement in the current iteration.
        # If an improvement was made in Phase 1, the 'while' loop restarts, and Phase 1 will run again.
        if not improvement_made:
            # Prepare unselected items sorted by density descending for greedy filling
            temp_unselected_items_list_by_density = list(unselected_items_dict.values())
            temp_unselected_items_list_by_density.sort(key=lambda x: x[0], reverse=True) 

            # Iterate through selected items, trying to replace each with multiple unselected items
            for sel_value, sel_weight, sel_idx in temp_selected_item_info:
                # Skip if this item was already unselected in a previous swap within this 'while' iteration.
                # This check is crucial because temp_selected_item_info is a snapshot.
                if sel_idx not in current_selected_items_indices:
                    continue

                # Temporarily remove sel_idx to calculate available capacity and value
                temp_current_total_weight = current_total_weight - sel_weight
                temp_current_total_value = current_total_value - sel_value
                
                # Available capacity after removing sel_idx
                available_capacity = capacity - temp_current_total_weight
                
                # Track items to be added in this potential swap
                potential_add_indices = set()
                potential_add_weight = 0
                potential_add_value = 0

                # Greedily fill available_capacity with unselected items
                # We need to iterate over unselected items, but exclude the one we just conceptually "removed" (sel_idx)
                for unsel_density, unsel_value, unsel_weight, unsel_idx_to_add in temp_unselected_items_list_by_density:
                    # Skip if already selected or if it's the item just removed (sel_idx)
                    # The unsel_idx_to_add in current_selected_items_indices check is important
                    # because temp_unselected_items_list_by_density is a snapshot.
                    if unsel_idx_to_add in current_selected_items_indices or unsel_idx_to_add == sel_idx:
                        continue
                    
                    # Optimization: 0-weight items should always be added if they provide value
                    if unsel_weight == 0 and unsel_value > 0:
                        potential_add_indices.add(unsel_idx_to_add)
                        potential_add_value += unsel_value
                        continue # Don't consume capacity, continue to next item
                    
                    if potential_add_weight + unsel_weight <= available_capacity:
                        potential_add_indices.add(unsel_idx_to_add)
                        potential_add_weight += unsel_weight
                        potential_add_value += unsel_value
            
                # Check if this 1-for-k swap is an improvement
                # The primary check is if the total value increases.
                if temp_current_total_value + potential_add_value > current_total_value:
                    # Perform the swap
                    current_selected_items_indices.remove(sel_idx)
                    for add_idx in potential_add_indices:
                        current_selected_items_indices.add(add_idx)
                        # Remove from unselected_items_dict as it's now selected
                        if add_idx in unselected_items_dict: # Check needed as 0-weight items might not be in dict
                            del unselected_items_dict[add_idx] 
                    
                    # Add the removed item (sel_idx) back to unselected_items_dict
                    sel_item_density = values[sel_idx] / weights[sel_idx] if weights[sel_idx] > 0 else (float('inf') if values[sel_idx] > 0 else 0.0)
                    unselected_items_dict[sel_idx] = (sel_item_density, values[sel_idx], weights[sel_idx], sel_idx)

                    current_total_value = temp_current_total_value + potential_add_value
                    current_total_weight = temp_current_total_weight + potential_add_weight
                    
                    improvement_made = True
                    break # Break from inner loop (selected items) to restart the while loop
            # If improvement_made is True here, the outer while loop will restart.
            # If it's still False after both phases, the while loop terminates.

    # As per the "REQUIRED_FINAL_FUNCTION" block, return a dictionary.
    return {
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": 0.0 # Placeholder as time.time() is forbidden
    }
#