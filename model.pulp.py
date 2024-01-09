from time import time
import pulp

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

model = pulp.LpProblem("Optimizacion_de_Distribucion",
                       pulp.LpMaximize)

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

# Factor de importancia de egreso de lotes (Hay que ir jugando con este valor)
batch_egress_weight = 7


# Número muy grnade
M = 1000000


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

# Variable binaria que indica si el cliente c ∈ C está en la ubicación l ∈ L.
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

# Despenalización por no alejarse de la demanda
W_cp = pulp.LpVariable.dicts("W", ((client, product)
                                   for client in Clients
                                   for product in Products),
                             lowBound=0,
                             cat=pulp.LpContinuous)

# Satisfacción de la demanda del cliente c ∈ C por el producto p ∈ P.
S_cp = pulp.LpVariable.dicts("S", ((client, product)
                                   for client in Clients
                                   for product in Products),
                             cat=pulp.LpBinary)


# -------------============= VARIABLES DE DECISIÓN ==============------------ #
# Indica si el lote b ∈ B está asignado al cliente c ∈ C.
X_cb = pulp.LpVariable.dicts("X", ((client, batch)
                                   for batch in Batches
                                   for client in Clients),
                             cat=pulp.LpBinary)

# -------------================= RESTRICCIONES ==================------------ #

# Ver si podemos entregar un lote a un cliente
# X_cb <= A_cb          ∀ c ∈ C, b ∈ B
for client in Clients:
    for batch in Batches:
        model += (
            X_cb[(client, batch)] <= A_cb[(client, batch)],
            f"Aptitud del lote {batch} (Compatibilidad Cliente {client}, Lote {batch})"
        )

# Cada lote puede ser enviado hasta una sola vez.
# Σ_c (X_cb) <= 1       ∀ b ∈ B
for batch in Batches:
    model += (
        pulp.lpSum(X_cb[(client, batch)] for client in Clients) <= 1,
        f"Unicidad del lote {batch} (Asignación única)"
    )

# No se puede vender más de `sale_excess` toneladas por sobre lo que un cliente pide.
# Σ_b (X_bp * V_b) <= D_cp + sale_excess    ∀ c ∈ C, p ∈ P
for client in Clients:
    for product in Products:
        model += (
            pulp.lpSum(X_cb[(client, batch)] * V_b[(batch, )] for batch in Batches) <=
            D_cp[(client, product)] + sale_excess,
            f"Límite de despacho del producto {product} al cliente {client}"
        )



# -------------================ FUNCIÓN OBJETIVO ================------------ #
objective = (
    pulp.lpSum(
        [X_cb[(c, b)]
         for c in Clients
         for b in Batches]
    )
)

# Establecer la función objetivo en el modelo
model += (objective, "Total_Value")


# -------------=================== EJECUCIÓN ====================------------ #

for nombre_restriccion in model.constraints:
    if nombre_restriccion.startswith("Límite"):
        print(f"{nombre_restriccion}: {model.constraints[nombre_restriccion]}")

# Resolver el problema
solver = pulp.PULP_CBC_CMD(timeLimit=5)
model.solve(solver)

# Verificar el estado de la solución
if pulp.LpStatus[model.status] == 'Optimal':
    print("Solución óptima encontrada!")

    count = 0

    # Filtrar e imprimir solo las variables que comienzan con "E_" y no son 0
    for v in model.variables():
        # Filtrar por nombre y valor
        if v.name.startswith("X_") and v.varValue != 0:
            count += 1
            print(f"{v.name} = {v.varValue}")

    print(count)

else:
    print("No se encontró una solución óptima. Estado:",
          pulp.LpStatus[model.status])