import time
import pulp

import excel_data

model = pulp.LpProblem("Optimizacion_de_Distribucion",
                       pulp.LpMaximize)

# -------------------------------- CONJUNTOS --------------------------------
# Definir el conjunto de clientes
Clients = {str(client) for client in set(excel_data.get_clients())}

# Definir el conjunto de productos
Products = {str(product) for product in set(excel_data.get_products())}

# Definir el conjunto de lotes
Batches = {str(batch) for batch in set(excel_data.get_batches())}

# -------------------------------- CONSTANTES --------------------------------
# Fecha actual
T_f = time.time()
# Importancia de satisfacer la demanda del cliente.
W_s = 1073741824
# Importancia de minimizar el exceso o la falta de producto para un cliente.
W_diff = 65536
# Base de la potencia para la prioridad de embarque de lotes.
B = 1.1

# Un número suficientemente grande, debe ser mayor que cualquier valor de D_cp
# y DDA_cp
M = 134217728


# -------------------------------- PARÁMETROS --------------------------------
# Si el cliente es apto o no para recibir un lote particular
client_batch_compatibility = excel_data.get_client_batch_compatibility()
A_lc = {
    (l, c): client_batch_compatibility[(c, l)]
    for l in Batches
    for c in Clients
}

client_product_compatibility = excel_data.get_client_product_demand()
X_cp = {
    client: {
        product: client_product_compatibility[(client, product)]
        for product in Products
    }
    for client in Clients
}

batch_product_match = excel_data.get_batch_product_binary()
P_lp = {
    (l, p): batch_product_match[(l, p)]
    for p in Products
    for l in Batches
}

batch_objects = excel_data.get_batches_from_stocks()
# Masa del lote
M_l = {
    (l, ): batch_objects[l].mass
    for l in Batches
}

# Demanda que el cliente "c" tiene por el producto "p".
client_demands = excel_data.get_client_product_demand()
DDA_cp = {
    (c, p): client_demands[(c, p)]
    for p in Products
    for c in Clients
}

# Prioridad del cliente "c".
I_c = {  # TODO: Placeholder
    (c, ): 1
    for c in Clients
}

# Fecha de arribo (epoch convertido a días) del lote "l"
batch_objects = excel_data.get_batches_from_stocks()
F_l = {
    (l, ): batch_objects[l].shipping_date_epoch
    for l in Batches
}

# --------------------------- VARIABLES AUXILIARES ---------------------------

# Tiempo en días que el lote "l" lleva en espera.
T_l: dict

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
    batch: max(B ** T_l[batch], 0)
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

Diff = pulp.LpVariable.dicts("Diff", ((client, product)
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
### DEFINICIONES

# 1. Definición de D_cp:
for c in Clients:
    for p in Products:
        model += (
            D_cp[(c, p)] == pulp.lpSum(E_lc[(l, c)] * M_l[l] for l in Batches),
            f"Definición cantidad despachada al cliente {c} del producto {p}"
        )

# 2. Definición
T_l = {
    (l, ): max(0, int((T_f - F_l[l]) // (24 * 3600)))
    for l in Batches
}



# 2. Definición cantidad despachada al cliente "c" del producto "p":
# for c in Clients:
#     for p in Products:
#         model += (
#             pulp.lpSum(E_lc[(l, c)] * M_l[l]
#                        for l in Batches) == D_cp[(c, p)],
#             f"Cantidad_despachada_a_cliente_{c}_de_"
#             f"producto_{p.replace(' ', '_')}"
#         )

# 3. Cumplimiento de la demanda del cliente "c" por el producto "p":
### for c in Clients:
###     for p in Products:
###         model += (
###             D_cp[(c, p)] >= DDA_cp[c][p] * S_cp[(c, p)],
###             f"Satisfaccion_dda_cliente_{c}_producto_"
###             f"{p.replace(' ', '_')}_p1")
###
### for c in Clients:
###     for p in Products:
###         model += (
###             D_cp[(c, p)] * (1 - S_cp[(c, p)]) < DDA_cp[c][p],
###             f"Satisfaccion_dda_cliente_{c}_producto_"
###             f"{p.replace(' ', '_')}_p2")
# for c in Clients:
#     for p in Products:
#         # Si S_cp es 1 (demanda satisfecha), esta restricción es siempre satisfecha.
#         # Si S_cp es 0, fuerza D_cp < DDA_cp
#         model += (D_cp[(c, p)] >= DDA_cp[c][p] - M * (1 - S_cp[(c, p)]),
#                   f"Satisfaccion_dda_cliente_{c}_producto_{p.replace(' ', '_')}_p1")
#
# for c in Clients:
#     for p in Products:
#         # Si S_cp es 0 (demanda no satisfecha), esta restricción es siempre satisfecha.
#         # Si S_cp es 1, fuerza D_cp >= DDA_cp
#         model += (D_cp[(c, p)] <= DDA_cp[c][p] + M * S_cp[(c, p)],
#                   f"Satisfaccion_dda_cliente_{c}_producto_{p.replace(' ', '_')}_p2")


# 4. Cada lote puede ser despachado a un solo cliente
# for l in Batches:
#     model += (pulp.lpSum(E_lc[(l, c)] for c in Clients) <= 1,
#               f"Un_client_por_lote_{l}")

# 5. Un lote puede no ser despachado este mes
# for l in Batches:
#     model += (pulp.lpSum(E_lc[(l, c)] for c in Clients) >= 0,
#               f"Un_lote_puede_no_ser_despachado_{l}")

# 7. Tiempo Máximo de Lote en Espera de cada lote
# for l in Batches:
#     model += (T_l[l] * (1 - pulp.lpSum(E_lc[(l, c)]
#                                        for c in Clients)) <= T_max,
#               f"Tiempo_espera_max_lote_{l}")

# 9. Posibilidad de venta del lote l al cliente c
# for l in Batches:
#     for c in Clients:
#         model += (A_lc[l][c] >= E_lc[(l, c)],
#                   f"Sale_Possibility_Batch_{l}_Client_{c}")

# Agregar restricciones para definir la parte positiva y
# negativa de la diferencia de demanda y oferta
# for c in Clients:
#     for p in Products:
#         model += (DDA_cp[c][p] - D_cp[(c, p)] ==
#                   Diff_Pos[(c, p)] - Diff_Neg[(c, p)],
#                   f"Difference_Pos_Neg_{c}_{p}")

# 10. Si un cliente no pide nada de un producto, no se le puede vender dicho producto.
# for c in Clients:
#     for p in Products:
#         model += (X_cp[c][p] * M >= D_cp[(c, p)],
#                   f"No_vender_al_que_no_quiere_{c}_{p}")



# ¿?  --  Estoy cansado, esoero acordarme
## Pr_{lp} \cdot DDA_{cp} \geq E_{lc}

# for c in Clients:
#     for p in Products:
#         for l in Batches:
#             model += (X_cp[c][p] * Pr_lp[l][p] >= E_lc[(l, c)],
#                       f"Pr_lp \cdot DDA_cp \geq E_lc___{c}_{p}_{l}")


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
solver = pulp.PULP_CBC_CMD(timeLimit=5)
model.solve(solver)

# Verificar el estado de la solución
if pulp.LpStatus[model.status] == 'Optimal':
    print("Solución óptima encontrada!")
    # Filtrar e imprimir solo las variables que comienzan con "E_" y no son 0
    for v in model.variables():
        # Filtrar por nombre y valor
        if v.name.startswith("E_") and v.varValue != 0:
            print(f"{v.name} = {v.varValue}")
else:
    print("No se encontró una solución óptima. Estado:",
          pulp.LpStatus[model.status])