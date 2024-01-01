import time
import pulp

import excel_data

model = pulp.LpProblem("Optimizacion_de_Distribucion",
                       pulp.LpMaximize)

# -------------------------------- CONJUNTOS --------------------------------
# Definir el conjunto de clientes
Clients = [client for client in excel_data.get_clients()]

# Definir el conjunto de productos
Products = [product for product in excel_data.get_products()]

# Definir el conjunto de lotes
Batches = [batch for batch in excel_data.get_batches()]

# -------------------------------- CONSTANTES --------------------------------
# Máximo tiempo de espera en bodega en días
T_max = 120
# Fecha actual
T_f = time.time() // (3600 * 24)
# Importancia de satisfacer la demanda del cliente.
W_s = 1073741824
# Importancia de minimizar el exceso o la falta de producto para un cliente.
W_diff = 65536
# Base de la potencia para la prioridad de embarque de lotes.
B = 1.1

# -------------------------------- PARÁMETROS --------------------------------
# Si el cliente es apto o no para recibir un lote particular
client_batch_compatibility = excel_data.get_client_batch_compatibility()
A_lc = {
    batch: {
        client: client_batch_compatibility[(client, batch)]
        for client in Clients
    }
    for batch in Batches
}

batch_objects = excel_data.get_batches()
# Masa del lote
M_l = {
    batch: batch_objects[batch].mass
    for batch in Batches
}

# Demanda que el cliente "c" tiene por el producto "p".
client_demands = excel_data.get_client_product_demand()
DDA_cp = {
    client: {
        product: client_demands[(client, product)]
        for product in Products
    }
    for client in Clients
}

# Prioridad del cliente "c".
I_c = {  # TODO: Placeholder
    client: 1
    for client in Clients
}

# Fecha de arribo (epoch convertido a días) del lote "l"
batch_objects = excel_data.get_batches()
F_l = {
    batch: batch_objects[batch].shipping_date_epoch // (3600 * 24)
    for batch in Batches
}

# --------------------------- VARIABLES AUXILIARES ---------------------------

# Tiempo en días que el lote "l" lleva en espera.
T_l = {
    batch: max(0, T_f - F_l[batch])
    for batch in Batches
}

# Si el lote "l" incorpora el producto "p" en su cargamento
Pr_lp = pulp.LpVariable.dicts("Pr", ((batch, product)
                                     for batch in Batches
                                     for product in Products),
                              cat='Binary')

# Cantidad efectivamente despachada al cliente "c" del producto "p".
D_cp = pulp.LpVariable.dicts("D", ((client, product)
                                   for client in Clients
                                   for product in Products),
                             lowBound=0,
                             cat='Continuous')

# Si se satisface la demanda de producto "p" para el cliente "c".
S_cp = pulp.LpVariable.dicts("S", ((client, product)
                                   for client in Clients
                                   for product in Products),
                             cat='Binary')

# Prioridad por entregar un lote.
# Aumenta a medida adquiere antigüedad
R_l = {
    batch: B ** T_l[batch]
    for batch in Batches
}

# -------------------------

# Definir variables para la parte positiva y negativa de la diferencia entre
# exportaciones y demandas
Diff_Pos = pulp.LpVariable.dicts("Diff_Pos", ((client, product)
                                              for client in Clients for
                                              product in Products),
                                 lowBound=0,
                                 cat='Continuous')
Diff_Neg = pulp.LpVariable.dicts("Diff_Neg", ((client, product)
                                              for client in Clients
                                              for product in Products),
                                 lowBound=0,
                                 cat='Continuous')

# -------------------------- VARIABLES DE DECISIÓN --------------------------
# Indica si se envía el lote "l" al cliente "c" este mes
E_lc = pulp.LpVariable.dicts("E", ((batch, client)
                                   for batch in Batches
                                   for client in Clients),
                             cat='Binary')

# ------------------------------ RESTRICCIONES -------------------------------
# 1. Cada lote trae un y solo un producto:
for l in Batches:
    model += (pulp.lpSum(Pr_lp[(l, p)]
                         for p in Products) == 1,
              f"Un_producto_por_lote_{l.replace(' ', '_')}")

# 2. Definición cantidad despachada al cliente "c" del producto "p":
for c in Clients:
    for p in Products:
        model += (
            pulp.lpSum(E_lc[(l, c)] * M_l[l]
                       for l in Batches) == D_cp[(c, p)],
            f"Cantidad_despachada_a_cliente_{c.replace(' ', '_')}_de_"
            f"producto_{p.replace(' ', '_')}"
        )

# 3. Cumplimiento de la demanda del cliente "c" por el producto "p":
for c in Clients:
    for p in Products:
        model += (
            D_cp[(c, p)] >= DDA_cp[c][p] * S_cp[(c, p)],
            f"Satisfaccion_dda_cliente_{c.replace(' ', '_')}_producto_"
            f"{p.replace(' ', '_')}")

# 4. Cada lote puede ser despachado a un solo cliente
for l in Batches:
    model += (pulp.lpSum(E_lc[(l, c)] for c in Clients) <= 1,
              f"Un_client_por_lote_{l}")

# 5. Un lote puede no ser despachado este mes
for l in Batches:
    model += (pulp.lpSum(E_lc[(l, c)] for c in Clients) >= 0,
              f"Un_lote_puede_no_ser_despachado_{l}")

# 7. Tiempo Máximo de Lote en Espera de cada lote
for l in Batches:
    model += (T_l[l] * (1 - pulp.lpSum(E_lc[(l, c)]
                                       for c in Clients)) <= T_max,
              f"Tiempo_espera_max_lote_{l}")

# 9. Posibilidad de venta del lote l al cliente c
for l in Batches:
    for c in Clients:
        model += (A_lc[l][c] >= E_lc[(l, c)],
                  f"Sale_Possibility_Batch_{l}_Client_{c}")

# Agregar restricciones para definir la parte positiva y
# negativa de la diferencia de demanda y oferta
for c in Clients:
    for p in Products:
        model += (DDA_cp[c][p] - D_cp[(c, p)] ==
                  Diff_Pos[(c, p)] - Diff_Neg[(c, p)],
                  f"Difference_Pos_Neg_{c}_{p}")

# 11. Si un cliente no pide nada de un producto, no se le puede vender dicho
# producto.
for c in Clients:
    for p in Products:
        model += (pulp.lpSum(E_lc[(l, c)] for l in Batches)
                  <= DDA_cp[c][p] * 999999999999999999999999999999999999999999,
                  f"No_vender_al_que_no_quiere_{c}_{p}")
# -------------------------- FUNCIÓN OBJETIVO --------------------------
objective = (
        # Primer término: Importancia del cliente por satisfacción de demanda
        pulp.lpSum(
            W_s * S_cp[(c, p)] * I_c[c]
            for c in Clients
            for p in Products) -

        # Segundo término: Penalización por la diferencia entre la demanda y
        # la cantidad despachada
        pulp.lpSum(W_diff * (Diff_Pos[(c, p)] + Diff_Neg[(c, p)])
                   for c in Clients
                   for p in Products) +

        # Tercer término: Valor del lote enviado ponderado por la prioridad
        # del lote
        pulp.lpSum(R_l[l] * E_lc[(l, c)]
                   for l in Batches
                   for c in Clients)
)

# Establecer la función objetivo en el modelo
model += (objective, "Total_Value")


# -----------------------------------------------------------------------------

# Resolver el problema
model.solve()

# Verificar el estado de la solución
if pulp.LpStatus[model.status] == 'Optimal':
    print("Solución óptima encontrada!")
    # Aquí podrías imprimir los valores de las variables de decisión y otros detalles relevantes
    for v in model.variables():
        print(f"{v.name} = {v.varValue}")
else:
    print("No se encontró una solución óptima. Estado:", pulp.LpStatus[model.status])