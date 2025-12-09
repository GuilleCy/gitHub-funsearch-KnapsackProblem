def heuristic(items_state):
    import time
    start_time = time.time()
    weights = items_state["weights"]
    values = items_state["values"]
    capacity = items_state["capacity"]
    n = len(weights)

    # Calcular densidad para cada ítem.
    # Si el peso es cero:
    #   - Si el valor es positivo, la densidad es infinita (ítem muy deseable).
    #   - Si el valor es cero o negativo, la densidad es 0 (ítem no deseable).
    density = []
    for v, w in zip(values, weights):
        if w == 0:
            density.append(float('inf') if v > 0 else 0)
        else:
            density.append(v / w)

    # Crear una lista de tuplas (densidad, valor, peso, índice_original).
    # Esto permite ordenar los ítems y mantener el rastro de su índice original.
    item_data = []
    for i in range(n):
        item_data.append((density[i], values[i], weights[i], i))

    # Ordenar los ítems por densidad de mayor a menor.
    # Para empates de densidad, priorizar ítems con mayor valor para desempate.
    item_data.sort(key=lambda x: (x[0], x[1]), reverse=True) # x[0]=density, x[1]=value

    total_value = 0
    total_weight = 0
    selected_indices_set = set() # Para búsquedas rápidas (O(1)) de ítems seleccionados.
    selected_items_list = [] # La lista final de índices de ítems seleccionados.

    # Primera Pasada: Selección voraz inicial basada en densidad.
    # Iterar sobre los ítems ya ordenados por densidad (y valor para desempates)
    # y añadir todos los que quepan hasta llenar la mochila o agotar ítems que quepan.
    for _, v, w, original_index in item_data:
        if total_weight + w <= capacity:
            selected_items_list.append(original_index)
            selected_indices_set.add(original_index)
            total_weight += w
            total_value += v

    # Segunda Pasada: Local Search - Drop-and-Fill (1-drop, K-fill).
    # Este es el componente principal de mejora heurística.
    # Intentar remover un ítem seleccionado y luego llenar el espacio liberado
    # (más la capacidad restante) con ítems no seleccionados,
    # priorizando por densidad/valor, para ver si se mejora el valor total.
    # El bucle externo se repite mientras se encuentren mejoras en el valor total.
    improved = True
    while improved:
        improved = False # Asumimos que no habrá mejora en esta iteración del bucle.
        best_gain = 0
        best_swap_out_idx = -1
        best_add_in_indices = [] # Índices de ítems a añadir si se realiza el mejor intercambio.

        # Pre-calcular y ordenar la lista de ítems actualmente no seleccionados.
        # Estos son los candidatos para ser añadidos.
        # Esta lista debe ser fresca en cada iteración del bucle 'while improved'
        # para reflejar los cambios en selected_indices_set.
        current_unselected_items_for_fill = []
        for j in range(n):
            if j not in selected_indices_set:
                current_unselected_items_for_fill.append((density[j], values[j], weights[j], j))
        
        # Ordenar estos ítems potenciales por densidad (y valor para desempates).
        # Esto es crucial para la estrategia voraz de llenado en el local search.
        current_unselected_items_for_fill.sort(key=lambda x: (x[0], x[1]), reverse=True)

        # Iterar sobre cada ítem actualmente seleccionado para considerar removerlo (i_out).
        # Convertir a lista para iterar de forma segura (copia del set en este momento).
        for i_out in list(selected_indices_set): 
            # Calcular el estado hipotético si removemos i_out.
            value_if_out_removed = total_value - values[i_out]
            weight_if_out_removed = total_weight - weights[i_out]
            
            # Capacidad total disponible para nuevos ítems después de remover i_out.
            available_space_for_fill = capacity - weight_if_out_removed
            
            temp_added_value = 0
            temp_added_weight = 0
            temp_added_indices = [] # Índices de ítems que se añadirían en este escenario.

            # Llenar vorazmente el espacio disponible con ítems no seleccionados.
            # Los ítems en current_unselected_items_for_fill ya están ordenados por densidad/valor.
            for _, v_add, w_add, idx_add in current_unselected_items_for_fill:
                # El ítem a añadir (idx_add) no estará en selected_indices_set por construcción
                # de current_unselected_items_for_fill, así que no puede ser i_out.
                if temp_added_weight + w_add <= available_space_for_fill:
                    temp_added_weight += w_add
                    temp_added_value += v_add
                    temp_added_indices.append(idx_add)
                    # Optimización: si el espacio se ha llenado completamente, no hay necesidad de buscar más.
                    if temp_added_weight == available_space_for_fill:
                        break # Salir del bucle de llenado voraz para este i_out.
            
            # Calcular el valor total si se realiza este intercambio hipotético.
            new_total_value_candidate = value_if_out_removed + temp_added_value
            
            # Calcular la ganancia neta para esta operación de 'drop-and-fill'.
            gain = new_total_value_candidate - total_value

            # Si esta operación produce una mejora, registrarla como la mejor hasta ahora.
            if gain > best_gain:
                best_gain = gain
                best_swap_out_idx = i_out
                best_add_in_indices = temp_added_indices

        # Después de evaluar todas las posibles remociones de 'i_out', si se encontró una ganancia positiva.
        if best_gain > 0:
            improved = True # Se encontró una mejora, el bucle 'while improved' debe continuar.
            
            # Aplicar la mejor mejora encontrada en esta pasada.
            # 1. Remover el ítem que se intercambia.
            selected_indices_set.remove(best_swap_out_idx)
            total_value -= values[best_swap_out_idx]
            total_weight -= weights[best_swap_out_idx]
            
            # 2. Añadir los nuevos ítems.
            for idx_add in best_add_in_indices:
                selected_indices_set.add(idx_add)
                total_value += values[idx_add]
                total_weight += weights[idx_add]
            
            # Reconstruir la lista de ítems seleccionados para mantener la consistencia.
            selected_items_list = list(selected_indices_set)
            # El bucle 'while' ahora reevaluará para buscar más mejoras.
    
    # Tercera Pasada: Final check para llenar cualquier capacidad restante.
    # Después del local search, podría quedar un pequeño espacio que un solo ítem podría llenar.
    # Priorizar por densidad (y valor para desempates) para este último intento.
    remaining_capacity = capacity - total_weight
    if remaining_capacity > 0:
        best_single_item_to_add_idx = -1
        max_single_item_density = -1.0 # Usar -1.0 para asegurar que cualquier densidad válida sea mejor.
        max_single_item_value_for_tiebreak = -1 # Para desempates de densidad.

        for i in range(n):
            # Solo considerar ítems no seleccionados que quepan en la capacidad restante.
            if i not in selected_indices_set and weights[i] <= remaining_capacity:
                # Priorizar el ítem con la densidad más alta, luego el valor más alto para desempates.
                if density[i] > max_single_item_density:
                    max_single_item_density = density[i]
                    max_single_item_value_for_tiebreak = values[i]
                    best_single_item_to_add_idx = i
                elif density[i] == max_single_item_density and values[i] > max_single_item_value_for_tiebreak:
                    max_single_item_value_for_tiebreak = values[i]
                    best_single_item_to_add_idx = i
        
        # Si se encontró un ítem para añadir en esta pasada final.
        if best_single_item_to_add_idx != -1:
            selected_items_list.append(best_single_item_to_add_idx)
            selected_indices_set.add(best_single_item_to_add_idx)
            total_weight += weights[best_single_item_to_add_idx]
            total_value += values[best_single_item_to_add_idx]
    
    end_time = time.time()

    return {
        "items": selected_items_list,
        "total_value": total_value,
        "total_peso_usado": total_weight,
        "solve_time": end_time - start_time
    }#