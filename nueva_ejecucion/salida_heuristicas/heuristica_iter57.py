def heuristic(items_state):
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
    # Store all item properties for quick lookup by original_index
    # item_properties[original_index] = (density, value, weight)
    item_properties = {} 
    for i in range(num_items):
        if weights[i] == 0:
            density = float('inf') if values[i] > 0 else 0.0
        else:
            density = values[i] / weights[i]
        item_data.append((density, values[i], weights[i], i))
        item_properties[i] = (density, values[i], weights[i]) # Store for O(1) lookup later

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
            
    # --- Local Search: Iterative 1-for-1, 1-for-k, and 2-for-1 Swaps ---
    # This phase attempts to improve the solution by exploring different swap neighborhoods.
    # It continues iterating until a full pass yields no improvements across all phases.
    
    improvement_made = True
    while improvement_made:
        improvement_made = False # Reset for each iteration of the outer while loop
        
        # Prepare snapshots of selected and unselected items for the current iteration.
        # These lists are sorted to prioritize candidates for removal or addition.
        
        # Selected items are sorted by value ascending (candidates for removal).
        temp_selected_item_info = []
        for idx in current_selected_items_indices:
            temp_selected_item_info.append((values[idx], weights[idx], idx))
        temp_selected_item_info.sort(key=lambda x: x[0]) 

        # Unselected items are sorted by value descending (candidates for addition in 1-for-1 and 2-for-1).
        temp_unselected_items_list_by_value = list(unselected_items_dict.values())
        temp_unselected_items_list_by_value.sort(key=lambda x: x[1], reverse=True) 
        
        # Unselected items are sorted by density descending for greedy filling in 1-for-k.
        temp_unselected_items_list_by_density = list(unselected_items_dict.values())
        temp_unselected_items_list_by_density.sort(key=lambda x: x[0], reverse=True) 


        # --- Phase 1: 0-weight item check & 1-for-1 swaps ---
        # Iterate through unselected items (highest value first) to find potential additions.
        for unsel_density, unsel_value, unsel_weight, unsel_idx in temp_unselected_items_list_by_value:
            # Skip if this item was already selected in a previous swap within this 'while' iteration
            # or if it was removed due to a 2-for-1 swap and is now selected.
            if unsel_idx in current_selected_items_indices:
                continue
            
            # Special handling for 0-weight items with positive value: add directly if not selected.
            # These items don't consume capacity and always improve the solution if added.
            if unsel_weight == 0 and unsel_value > 0:
                current_selected_items_indices.add(unsel_idx)
                current_total_value += unsel_value
                del unselected_items_dict[unsel_idx] # Remove from unselected as it's now selected
                improvement_made = True
                break # Improvement found, restart the 'while' loop to re-evaluate state.
            
            # Optimization: If an unselected item cannot fit even if the knapsack is empty, skip it.
            if unsel_weight > capacity:
                continue
            
            # Try 1-for-1 swap with selected items (lowest value first)
            for sel_value, sel_weight, sel_idx in temp_selected_item_info:
                # Skip if this item was already unselected in a previous swap within this 'while' iteration.
                # This is necessary because temp_selected_item_info is a snapshot.
                if sel_idx not in current_selected_items_indices:
                    continue

                # Pruning: If the unselected item's value is not greater than the selected item's value,
                # no value improvement is possible by swapping them.
                # Since temp_selected_item_info is sorted by sel_value ascending,
                # if unsel_value <= sel_value, then for all subsequent sel_items, unsel_value will also be <= their value.
                # So we can break this inner loop.
                if unsel_value <= sel_value:
                    break # No improvement possible with this unsel_item and remaining sel_items

                # Calculate the potential new total weight and value after the swap
                weight_change = unsel_weight - sel_weight
                value_change = unsel_value - sel_value

                # Check if the swap is valid (fits capacity) and strictly improves value
                if current_total_weight + weight_change <= capacity and value_change > 0:
                    # Perform the swap
                    current_selected_items_indices.remove(sel_idx)
                    current_selected_items_indices.add(unsel_idx)
                    current_total_weight += weight_change
                    current_total_value += value_change
                    
                    # Update unselected_items_dict: remove the newly selected item, add the newly unselected item
                    del unselected_items_dict[unsel_idx] 
                    # Use item_properties for O(1) lookup
                    sel_item_density, sel_item_value, sel_item_weight = item_properties[sel_idx]
                    unselected_items_dict[sel_idx] = (sel_item_density, sel_item_value, sel_item_weight, sel_idx)
                    
                    improvement_made = True
                    break # Break from inner loop (selected items) to restart the while loop
            if improvement_made:
                break # Break from outer loop (unselected items) to restart the while loop

        if improvement_made:
            continue # Restart the main while loop if any improvement was made in Phase 1

        # --- Phase 2: 1-for-k swaps ---
        # This phase is executed only if Phase 1 did not find any improvement in the current iteration.
        
        # Iterate through selected items, trying to replace each with multiple unselected items
        for sel_value, sel_weight, sel_idx in temp_selected_item_info:
            # Skip if this item was already unselected in a previous swap within this 'while' iteration.
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
            for unsel_density, unsel_value, unsel_weight, unsel_idx_to_add in temp_unselected_items_list_by_density:
                # Skip if already selected or if it's the item just removed (sel_idx)
                if unsel_idx_to_add in current_selected_items_indices or unsel_idx_to_add == sel_idx:
                    continue
                
                # Optimization: 0-weight items should always be added if they provide value
                if unsel_weight == 0 and unsel_value > 0:
                    # Only add if not already in potential additions
                    if unsel_idx_to_add not in potential_add_indices: 
                        potential_add_indices.add(unsel_idx_to_add)
                        potential_add_value += unsel_value
                    continue # Don't consume capacity, continue to next item
                
                if potential_add_weight + unsel_weight <= available_capacity:
                    potential_add_indices.add(unsel_idx_to_add)
                    potential_add_weight += unsel_weight
                    potential_add_value += unsel_value
        
            # Check if this 1-for-k swap is an improvement
            # The primary check is if the total value increases, and we actually added items.
            if potential_add_indices and (temp_current_total_value + potential_add_value > current_total_value):
                # Perform the swap
                current_selected_items_indices.remove(sel_idx)
                for add_idx in potential_add_indices:
                    current_selected_items_indices.add(add_idx)
                    # Remove from unselected_items_dict as it's now selected
                    if add_idx in unselected_items_dict: 
                        del unselected_items_dict[add_idx] 
                
                # Add the removed item (sel_idx) back to unselected_items_dict
                # Use item_properties for O(1) lookup
                sel_item_density, sel_item_value, sel_item_weight = item_properties[sel_idx]
                unselected_items_dict[sel_idx] = (sel_item_density, sel_item_value, sel_item_weight, sel_idx)

                current_total_value = temp_current_total_value + potential_add_value
                current_total_weight = temp_current_total_weight + potential_add_weight
                
                improvement_made = True
                break # Break from inner loop (selected items) to restart the while loop
        
        if improvement_made:
            continue # Restart the main while loop if any improvement was made in Phase 2

        # --- Phase 3: 2-for-1 swaps ---
        # This phase is executed only if Phase 1 and Phase 2 did not find any improvement in the current iteration.
        
        # Iterate through pairs of selected items (s1, s2) to remove
        for i in range(len(temp_selected_item_info)):
            sel1_value, sel1_weight, sel1_idx = temp_selected_item_info[i]
            # Ensure sel1_idx is still selected in the current solution
            if sel1_idx not in current_selected_items_indices:
                continue

            for j in range(i + 1, len(temp_selected_item_info)):
                sel2_value, sel2_weight, sel2_idx = temp_selected_item_info[j]
                # Ensure sel2_idx is still selected in the current solution
                if sel2_idx not in current_selected_items_indices:
                    continue
                
                # Calculate total removed weight/value
                removed_weight = sel1_weight + sel2_weight
                removed_value = sel1_value + sel2_value

                # Iterate through unselected items (u) to add
                for unsel_density, unsel_value, unsel_weight, unsel_idx in temp_unselected_items_list_by_value:
                    # Pruning: If the unselected item's value is not greater than the removed value,
                    # no value improvement is possible.
                    # Since temp_unselected_items_list_by_value is sorted by unsel_value descending,
                    # if unsel_value <= removed_value, then for all subsequent unsel_items, unsel_value will also be <= removed_value.
                    # So we can break this inner loop.
                    if unsel_value <= removed_value:
                        break # No improvement possible with this pair of removed items and remaining unsel_items

                    # Skip if already selected or one of the items just conceptually removed (sel1_idx, sel2_idx)
                    if unsel_idx in current_selected_items_indices or unsel_idx == sel1_idx or unsel_idx == sel2_idx:
                        continue
                    
                    # Calculate potential new total weight and value
                    potential_new_weight = current_total_weight - removed_weight + unsel_weight
                    potential_new_value = current_total_value - removed_value + unsel_value

                    # Check if swap is valid (fits capacity) and strictly improves value
                    if potential_new_weight <= capacity and potential_new_value > current_total_value:
                        # Perform the swap
                        current_selected_items_indices.remove(sel1_idx)
                        current_selected_items_indices.remove(sel2_idx)
                        current_selected_items_indices.add(unsel_idx)
                        
                        current_total_weight = potential_new_weight
                        current_total_value = potential_new_value

                        # Update unselected_items_dict: remove added item, add removed items
                        del unselected_items_dict[unsel_idx]
                        
                        # Use item_properties for O(1) lookup
                        sel1_density, sel1_val, sel1_w = item_properties[sel1_idx]
                        unselected_items_dict[sel1_idx] = (sel1_density, sel1_val, sel1_w, sel1_idx)
                        
                        sel2_density, sel2_val, sel2_w = item_properties[sel2_idx]
                        unselected_items_dict[sel2_idx] = (sel2_density, sel2_val, sel2_w, sel2_idx)

                        improvement_made = True
                        break # Improvement found, restart outer 'while' loop
                if improvement_made:
                    break
            if improvement_made:
                break
        # If improvement_made is True here, the outer while loop will restart.
        # If it's still False after all three phases, the while loop terminates.

    # As per the "REQUIRED_FINAL_FUNCTION" block, return a dictionary.
    return {
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": 0.0 # Placeholder as time.time() is forbidden
    }
#