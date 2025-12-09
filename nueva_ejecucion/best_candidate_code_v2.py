def heuristic(items_state):
    import time

    start_time = time.time()
    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    num_items = len(weights)

    # Calculate density (value/weight) and store original indices
    # density_data: (density, weight, value, original_idx)
    density_data = []
    item_densities = [0.0] * num_items # Store densities for quick lookup later
    for i in range(num_items):
        if weights[i] > 0:
            density = values[i] / weights[i]
            density_data.append((density, weights[i], values[i], i))
            item_densities[i] = density
        else:
            # Handle zero weight items: infinite density if value > 0, else 0 density.
            # If value is also 0, density is effectively 0 (or undefined, but 0 for sorting purposes)
            density = float('inf') if values[i] > 0 else 0
            density_data.append((density, weights[i], values[i], i))
            item_densities[i] = density

    # Sort by density (descending), then by value (descending) for ties, then by weight (ascending) for ties
    # This greedy choice prioritizes items that give the most value per unit of weight.
    # For ties in density, higher value is preferred. For ties in density and value, lower weight is preferred.
    density_data.sort(key=lambda x: (x[0], x[2], -x[1]), reverse=True)

    current_total_value = 0
    current_total_weight = 0
    current_selected_items_indices = set()
    unselected_items_set = set(range(num_items)) # Maintain unselected items as a set for O(1) operations

    # Initial Greedy Selection: Fill the knapsack based on sorted density
    for density, w, v, original_idx in density_data:
        if current_total_weight + w <= capacity:
            current_selected_items_indices.add(original_idx)
            current_total_weight += w
            current_total_value += v
            unselected_items_set.remove(original_idx) # Update unselected set

    # --- Perturbation Phase: Remove inefficient items to escape local optima ---
    # This phase aims to free up space by removing a few items that are relatively "bad" (low density, high weight)
    # and then re-greedily filling the knapsack.
    # Apply only if the knapsack is reasonably full and has enough items selected to perturb.
    # Increased capacity threshold to 75% for less frequent but potentially more impactful perturbations.
    if len(current_selected_items_indices) > 5 and current_total_weight > 0.75 * capacity:
        selected_items_for_perturb = []
        for idx in current_selected_items_indices:
            item_weight = weights[idx]
            item_value = values[idx]
            item_density = item_densities[idx] # Use pre-calculated density for efficiency
            selected_items_for_perturb.append((item_density, item_weight, item_value, idx))
        
        # Sort selected items for removal:
        # Prioritize removing items with:
        # 1. Lowest density first (ascending x[0])
        # 2. Heaviest among those with same density (descending -x[1])
        # 3. Lowest value among those with same density and weight (ascending x[2])
        # This strategy aims to remove the "least efficient" items that also take up significant space.
        selected_items_for_perturb.sort(key=lambda x: (x[0], -x[1], x[2]))
        
        # Determine number of items to remove: between 3 and 20, max 30% of selected items.
        # This allows for a more significant perturbation on larger instances.
        num_to_remove = min(max(3, int(len(selected_items_for_perturb) * 0.30)), 20)
        
        removed_count = 0
        # Iterate through the sorted list and remove items
        while removed_count < num_to_remove and selected_items_for_perturb:
            # Pop the item with the lowest density, then heaviest, then lowest value
            _, _, _, idx_to_remove = selected_items_for_perturb.pop(0)
            if idx_to_remove in current_selected_items_indices: # Ensure it's still selected
                current_selected_items_indices.remove(idx_to_remove)
                current_total_weight -= weights[idx_to_remove]
                current_total_value -= values[idx_to_remove]
                unselected_items_set.add(idx_to_remove) # Update unselected set
                removed_count += 1

        # Greedily re-fill the knapsack with available items after perturbation
        # This considers ALL items, prioritizing those not currently selected,
        # maintaining the greedy order from density_data.
        for density, w, v, original_idx in density_data:
            if original_idx in unselected_items_set: # Check if it's currently unselected
                if current_total_weight + w <= capacity:
                    current_selected_items_indices.add(original_idx)
                    current_total_weight += w
                    current_total_value += v
                    unselected_items_set.remove(original_idx) # Update unselected set
    # --- End Perturbation Phase ---

    # Local Search (Best Improvement): Find the best single improvement (direct add or 1-1 swap) in each iteration
    # Continue as long as an improvement is found in a full pass.
    while True:
        best_delta_value = 0 # Stores the maximum value increase found in this pass
        best_action = None   # 'add' or 'swap'
        action_details = {}  # Stores indices for the best action

        # --- Phase 1: Check for direct additions (1-opt) ---
        # Iterate over a copy of unselected_items_set to avoid issues if set is modified during iteration
        for potential_add_idx in list(unselected_items_set):
            weight_add = weights[potential_add_idx]
            value_add = values[potential_add_idx]

            if current_total_weight + weight_add <= capacity:
                # Only consider if it increases total value and is better than current best_delta_value
                if value_add > best_delta_value:
                    best_delta_value = value_add
                    best_action = 'add'
                    action_details = {'add_idx': potential_add_idx}

        # --- Phase 2: Check for single-item swaps (1-1 swap) ---
        # Iterate over copies of sets for safe iteration
        selected_items_list_for_swap = list(current_selected_items_indices)
        unselected_items_list_for_swap = list(unselected_items_set)

        for potential_add_idx in unselected_items_list_for_swap:
            weight_add = weights[potential_add_idx]
            value_add = values[potential_add_idx]

            for potential_remove_idx in selected_items_list_for_swap:
                # Skip if trying to swap an item with itself (should not happen as sets are disjoint)
                if potential_add_idx == potential_remove_idx:
                    continue

                weight_remove = weights[potential_remove_idx]
                value_remove = values[potential_remove_idx]

                # Calculate potential new state after swap
                new_weight = current_total_weight - weight_remove + weight_add
                delta_value = value_add - value_remove

                # Check if swap is valid (within capacity) and improves value
                if new_weight <= capacity and delta_value > best_delta_value:
                    best_delta_value = delta_value
                    best_action = 'swap'
                    action_details = {'add_idx': potential_add_idx, 'remove_idx': potential_remove_idx}
        
        # --- Apply the best found action for this pass ---
        if best_action is not None and best_delta_value > 0: # Ensure there's a positive improvement
            if best_action == 'add':
                add_idx = action_details['add_idx']
                current_selected_items_indices.add(add_idx)
                unselected_items_set.remove(add_idx) # Update unselected set
                current_total_weight += weights[add_idx]
                current_total_value += values[add_idx]
            elif best_action == 'swap':
                add_idx = action_details['add_idx']
                remove_idx = action_details['remove_idx']
                current_selected_items_indices.remove(remove_idx)
                unselected_items_set.add(remove_idx) # Update unselected set
                current_selected_items_indices.add(add_idx)
                unselected_items_set.remove(add_idx) # Update unselected set
                current_total_weight = current_total_weight - weights[remove_idx] + weights[add_idx]
                current_total_value = current_total_value - values[remove_idx] + values[add_idx]
            # The loop continues to find further improvements in the new state
        else:
            # No improvement found in this full pass, so we've reached a local optimum
            break

    end_time = time.time()

    return {
        "items": list(current_selected_items_indices),
        "total_value": current_total_value,
        "total_peso_usado": current_total_weight,
        "solve_time": end_time - start_time
    }#