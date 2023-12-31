import time
import pulp

model = pulp.LpProblem("Optimizacion_de_Distribucion",
                       pulp.LpMaximize)

# -------------------------------- CONJUNTOS --------------------------------
# Definir el conjunto de clientes
Clients = [f"Client{i}" for i in range(13)]

# Definir el conjunto de productos
Products = [f"Product{i}" for i in range(3)]

# Definir el conjunto de lotes
Batches = [f"Batch{i}" for i in range(80)]

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
# Si el cliente es apto o no para recibir un lite particular
A_lc = {  # TODO: Placeholder
    batch: {
        client: 1
        for client in Clients
    }
    for batch in Batches
}

# Masa del lote
M_l = {  # TODO: Placeholder
    batch: 1000
    for batch in Batches
}

# Demanda que el cliente "c" tiene por el producto "p".
DDA_cp = {  # TODO: Placeholder
    client: {
        product: 100
        for product in Products
    }
    for client in Clients
}

# Prioridad del cliente "c".
I_c = {  # TODO: Placeholder
    client: 1
    for client in Clients
}

# Fecha de arribo (epoch) del lote "l"
F_l = {  # TODO: Placeholder
    batch: T_f - 2
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

