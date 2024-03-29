import numpy as np

from gekko import GEKKO
from pandas import DataFrame
from time import time

from tables import get_raw_data  # Dict

from tables import (get_all_clients as getClients,  # List
                    get_all_locations as getLocations,  # List
                    get_all_products as getProducts,  # List
                    get_all_batches as getBatches)  # List

from tables import (get_sales_table as salesTable,  # DataFrame
                    get_clients_locations_table as clientLocationTable,  # DataFrame
                    get_clients_data_table as clientDataTable,  # DataFrame
                    get_clients_priorities_table as clientPriorityTable,  # DataFrame
                    get_batches_volumes_table as batchesVolumesTable,  # DataFrame
                    get_batches_locations_table as batchesLocationsTable,  # DataFrame
                    get_compatibility_client_batch_table as compatibilityTable)  # DataFrame

# -------------===================== MODELO =====================------------ #

# Inicializa el modelo Gekko
model = GEKKO(remote=False)

# -------------=================== CONJUNTOS ====================------------ #
raw_data = get_raw_data()
batches_data = raw_data["batches"]
requests_data = raw_data["requests"]
importance_data = raw_data["importance"]

# Conjunto de clientes (ID).
Clients = getClients(batches_data, requests_data)
# Conjunto de ubicaciones.
Locations = getLocations(batches_data, requests_data)
# Conjunto de productos (ID).
Products = getProducts(batches_data, requests_data)
# Conjunto de lotes (ID).
Batches = getBatches(batches_data)

# -------------=================== CONSTANTES ===================------------ #
# Máxima cantidad en toneladas que se puede exceder en el despacho respecto a
# la demanda del cliente.
sale_excess = 15

# Factor de importancia de egreso de lotes
batch_egress_weight = 7

# -------------=================== PARÁMETROS ===================------------ #
# Prioridad de ventas para el cliente c ∈ C.
P_c = {
    (row['client_id'], ): row['priority']
    for _, row in clientPriorityTable(batches_data,
                                      requests_data,
                                      importance_data).iterrows()
}

for client in Clients:
    P_c.setdefault((client, ), 0)

# -------------------------

# Indica si el lote b ∈ B es apto para el cliente c ∈ C.
A_cb = {
    (row['client_id'], row['batch_id']): row['apt']
    for _, row in compatibilityTable(batches_data,
                                     requests_data).iterrows()
}

for client in Clients:
    for batch in Batches:
        A_cb.setdefault((client, batch), 0)

# -------------------------

#  Volumen disponible en el lote b ∈ B.
V_b = {
    (row['batch_id'], ): row['quantity']
    for _, row in batchesVolumesTable(batches_data).iterrows()
}

for batch in Batches:
    V_b.setdefault((batch, ), 0)

# -------------------------

# Demanda del cliente c ∈ C para el producto p ∈ P.
D_cp = {
    (row['client_id'], row['product_id']): row['demand']
    for _, row in salesTable(requests_data).iterrows()
}

for client in Clients:
    for product in Products:
        D_cp.setdefault((client, product), 0)

# -------------------------

# Antigüedad del lote b ∈ B en días.
now = time()

T_b = {
    (row['batch_id'], ): (now - row['ship_date_epoch']) // (24 * 3600)
    for _, row in batchesVolumesTable(batches_data).iterrows()
}

for batch in Batches:
    T_b.setdefault((batch, ), 1)

# -------------------------

# Variable binaria que indica si el cliente c ∈ C está en la ubicación u ∈ U.
LC_cl = {
    (row['client_id'], row['client_location']): 1
    for _, row in clientLocationTable(requests_data).iterrows()
}

for client in Clients:
    for location in Locations:
        LC_cl.setdefault((client, location), 0)

# -------------------------

# Variable binaria que indica si el lote c ∈ C está en la ubicación l ∈ L.
LB_b = {
    (row['batch_id'], row['batch_location']): 1
    for _, row in batchesLocationsTable(batches_data).iterrows()
}

for batch in Batches:
    for location in Locations:
        LB_b.setdefault((batch, location), 0)

# -------------============== VARIABLES AUXILIARES ==============------------ #

# # Despenalización por no acercarse a la demanda
# W_cp = {(client, product): model.Var(lb=0, ub=1, integer=False)
#         for client in Clients for product in Products}

# # Satisfacción de la demanda del cliente c ∈ C por el producto p ∈ P.
# S_cp = {(client, product): model.Var(lb=0, ub=1, integer=True)
#         for client in Clients for product in Products}

# -------------============= VARIABLES DE DECISIÓN ==============------------ #

# Indica si el lote b ∈ B está asignado al cliente c ∈ C.
X_cb = {(client, batch): model.Var(lb=0, ub=1, integer=True)
        for client in Clients for batch in Batches}

# -------------================= RESTRICCIONES ==================------------ #

# # Ver si podemos entregar un lote a un cliente
# # Aptitud del lote (Compatibilidad Cliente-Lote):
# # X_cb <= A_cb          ∀ c ∈ C, b ∈ B
# for client in Clients:
#     for batch in Batches:
#         model.Equation(
#             X_cb[(client, batch)] <= A_cb[(client, batch)]
#         )

# # Cada lote puede ser enviado hasta una sola vez.
# # Unicidad del lote (Asignación Única):
# # Σ_c (X_cb) <= 1       ∀ b ∈ B
for batch in Batches:
    model.Equation(
        model.sum([X_cb[(client, batch)] for client in Clients]) <= 1
    )

# # No se puede vender más de `sale_excess` toneladas por sobre lo que un cliente pide.
# # Σ_b (X_bp * V_b) <= D_cp + sale_excess    ∀ c ∈ C, p ∈ P
for client in Clients:
    for product in Products:
        model.Equation(
            sum(X_cb[(client, batch)] * V_b[(batch, )]
                for batch in Batches) >= D_cp[(client, product)] + sale_excess
        )


# -------------================ FUNCIÓN OBJETIVO ================------------ #
# Maximizar la prioridad de los clientes y la satisfacción de la demanda,
# mientras se minimiza la antigüedad de los lotes asignados, considerando la
# ubicación de los lotes. Este objetivo busca un equilibrio entre atender a
# los clientes más importantes y gestionar eficientemente el inventario de
# lotes.

model.Maximize(
    model.sum([
        X_cb[(c, b)]
        for c in Clients
        for b in Batches
    ])
)

# -------------=================== EJECUCIÓN ====================------------ #
# Soluciona el problema
model.solve(disp=True)

count = 0

# Resultados
for c in Clients:
    for b in Batches:
        if X_cb[(c, b)].value[0] >= 0.5:  # Asumiendo una pequeña tolerancia
            count += 1
            print(f"Lote {b} asignado a Cliente {c}: {X_cb[(c, b)].value[0]}")

print(count)