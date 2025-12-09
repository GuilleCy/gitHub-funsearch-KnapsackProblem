def heuristic(items_state):
    import time
    start_time = time.time()
    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    num_items = len(weights)

    # Calcular densidad, manejando ítems con peso cero.
    # Asignar float('inf') a ítems con peso 0 y valor positivo para priorizarlos.
    # Asignar 0.0 a ítems con peso 0 y valor 0 (o negativo, aunque no esperado).
    # Asignar v/w para ítems con peso positivo.
    densities = []
    for i in range(num_items):
        if weights[i] == 0:
            if values[i] > 0:
                densities.append(float('inf')) # Estos ítems siempre deben ser seleccionados primero
            else:
                densities.append(0.0) # Estos ítems no añaden valor ni peso, pueden ser ignorados o seleccionados sin prioridad
        else:
            densities.append(values[i] / weights[i])

    # Crear una lista de tuplas (densidad, índice) para ordenar
    # indexed_densities will be sorted by density DESCENDING
    indexed_densities = [(densities[i], i) for i in range(num_items)]
    indexed_densities.sort(key=lambda x: x[0], reverse=True)

    total_value = 0
    total_weight = 0
    is_selected = [False] * num_items # Array booleano para rastrear ítems seleccionados

    # Selección voraz (greedy) basada en la densidad ordenada
    for density_val, i in indexed_densities:
        if total_weight + weights[i] <= capacity:
            total_weight += weights[i]
            total_value += values[i]
            is_selected[i] = True

    # --- Mejora por Búsqueda Local: Intercambio 1-swap Iterativo con relleno en cada iteración ---
    # Continuar realizando el mejor intercambio 1-swap posible y rellenando la mochila
    # hasta que no haya más mejoras en una iteración completa.
    improved_overall = True
    # Define un límite para el número de ítems a considerar en el swap para acelerar la búsqueda local.
    # Esto es una heurística para evitar que O(N^2) sea demasiado lento para N grande.
    # Ajuste del límite de búsqueda para explorar más opciones en instancias grandes.
    SWAP_SEARCH_LIMIT = max(50, min(num_items // 8, 500)) 

    while improved_overall:
        improved_overall = False # Asumimos que no habrá mejora en esta pasada

        # --- Fase 1: Buscar el mejor 1-swap ---
        best_swap_gain = 0
        best_swap_in_idx = -1
        best_swap_out_idx = -1
        best_swap_weight_diff = float('inf') # Inicializar para el desempate: preferir menor incremento de peso o mayor decremento
        best_swap_out_density = -float('inf') # Inicializar para el desempate: preferir mayor densidad para el ítem añadido
        best_swap_in_density = float('inf')   # Inicializar para el desempate: preferir menor densidad para el ítem removido

        # Crear listas dinámicas para ítems seleccionados y no seleccionados para una iteración eficiente del swap
        # selected_for_removal: (densidad, índice) ordenado por densidad ASCENDENTE
        selected_for_removal = []
        # unselected_for_addition: (densidad, índice) ordenado por densidad DESCENDENTE
        unselected_for_addition = []

        for density_val, idx in indexed_densities:
            if is_selected[idx]:
                selected_for_removal.append((density_val, idx))
            else:
                unselected_for_addition.append((density_val, idx))
        
        # selected_for_removal está inicialmente ordenado de forma descendente (de indexed_densities),
        # invertirlo para que esté ordenado de forma ascendente para una eliminación eficiente de ítems de baja densidad.
        selected_for_removal.reverse() 

        # Limitar el número de ítems considerados para el swap para acelerar la búsqueda.
        limited_selected_for_removal = selected_for_removal[:min(len(selected_for_removal), SWAP_SEARCH_LIMIT)]
        limited_unselected_for_addition = unselected_for_addition[:min(len(unselected_for_addition), SWAP_SEARCH_LIMIT)]

        # Iterar a través de ítems seleccionados (para remover), priorizando ítems de menor densidad
        for density_val_in, i_in_idx in limited_selected_for_removal:
            # Considerar temporalmente la eliminación del ítem i_in_idx
            weight_after_removal = total_weight - weights[i_in_idx]
            value_after_removal = total_value - values[i_in_idx]

            # Iterar a través de ítems no seleccionados (para añadir), priorizando ítems de mayor densidad
            for density_val_out, j_out_idx in limited_unselected_for_addition:
                # Verificar si añadir el ítem j_out_idx cabe en la capacidad restante
                if (weight_after_removal + weights[j_out_idx] <= capacity):
                    potential_new_value = value_after_removal + values[j_out_idx]
                    gain = potential_new_value - total_value
                    current_weight_diff = weights[j_out_idx] - weights[i_in_idx] # Diferencia neta de peso

                    # Si este intercambio produce un mejor valor, registrarlo
                    if gain > best_swap_gain:
                        best_swap_gain = gain
                        best_swap_in_idx = i_in_idx
                        best_swap_out_idx = j_out_idx
                        best_swap_weight_diff = current_weight_diff
                        best_swap_out_density = density_val_out
                        best_swap_in_density = density_val_in
                    elif gain == best_swap_gain:
                        # Reglas de desempate:
                        # 1. Preferir el intercambio que resulte en un menor incremento de peso (o mayor decremento).
                        if current_weight_diff < best_swap_weight_diff:
                            best_swap_in_idx = i_in_idx
                            best_swap_out_idx = j_out_idx
                            best_swap_weight_diff = current_weight_diff
                            best_swap_out_density = density_val_out
                            best_swap_in_density = density_val_in
                        # 2. Si la diferencia de peso es la misma, preferir el ítem añadido con mayor densidad.
                        elif current_weight_diff == best_swap_weight_diff:
                            if density_val_out > best_swap_out_density:
                                best_swap_in_idx = i_in_idx
                                best_swap_out_idx = j_out_idx
                                best_swap_weight_diff = current_weight_diff
                                best_swap_out_density = density_val_out
                                best_swap_in_density = density_val_in
                            # 3. Si la densidad del ítem añadido también es la misma, preferir el ítem removido con menor densidad.
                            elif density_val_out == best_swap_out_density:
                                if density_val_in < best_swap_in_density:
                                    best_swap_in_idx = i_in_idx
                                    best_swap_out_idx = j_out_idx
                                    best_swap_weight_diff = current_weight_diff
                                    best_swap_out_density = density_val_out
                                    best_swap_in_density = density_val_in

        # Si se encontró un intercambio beneficioso, aplicarlo
        if best_swap_gain > 0:
            is_selected[best_swap_in_idx] = False
            is_selected[best_swap_out_idx] = True
            
            total_weight = total_weight - weights[best_swap_in_idx] + weights[best_swap_out_idx]
            total_value = total_value - values[best_swap_in_idx] + values[best_swap_out_idx]
            improved_overall = True # Se realizó un swap, lo que es una mejora.

        # --- Fase 2: Relleno de capacidad restante con ítems pequeños ---
        # Después de un posible swap (o si no hubo swap), intentar añadir ítems no seleccionados.
        # Esto puede aprovechar la capacidad liberada por un swap o simplemente llenar huecos.
        # Iterar sobre todos los ítems, ordenados por densidad (de mayor a menor).
        # Intentar añadir ítems no seleccionados para rellenar la capacidad restante.
        for density_val, k_add_idx in indexed_densities:
            if not is_selected[k_add_idx]: # Solo considerar ítems no seleccionados
                # Solo considerar ítems con densidad positiva para el relleno.
                # Esto cubre ítems con valor > 0 y peso > 0, o ítems con valor > 0 y peso 0 (densidad infinita).
                if density_val > 0: 
                     if total_weight + weights[k_add_idx] <= capacity:
                        total_weight += weights[k_add_idx]
                        total_value += values[k_add_idx]
                        is_selected[k_add_idx] = True
                        improved_overall = True # Se añadió un ítem, lo que es una mejora.

    # Construir la lista final de índices de ítems seleccionados
    final_selected_items = [i for i in range(num_items) if is_selected[i]]

    end_time = time.time()

    return {
        "items": final_selected_items,
        "total_value": total_value,
        "total_peso_usado": total_weight,
        "solve_time": end_time - start_time
    }#