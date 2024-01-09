import pyomo.environ as pyomo

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
                    get_compatibility_client_batch_table as compatibilityTable)

# -------------===================== MODELO =====================------------ #

# Crear un modelo
model = pyomo.ConcreteModel()

# -------------=================== CONJUNTOS ====================------------ #

raw_data = get_raw_data()
batches_data = raw_data["batches"]
requests_data = raw_data["requests"]
importance_data = raw_data["importance"]

# Conjunto de clientes (ID).
Clients = getClients(batches_data, requests_data)
model.Clients = pyomo.Set(initialize=Clients)

# Conjunto de ubicaciones.
Locations = getLocations(batches_data, requests_data)
model.Locations = pyomo.Set(initialize=Locations)

# Conjunto de productos (ID).
Products = getProducts(batches_data, requests_data)
model.Products = pyomo.Set(initialize=Products)

# Conjunto de lotes (ID).
Batches = getBatches(batches_data)
model.Batches = pyomo.Set(initialize=Batches)

# Crear conjunto para índices cruzados
model.ClientBatchPairs = pyomo.Set(initialize=[(c, b) for c in Clients for b in Batches])
model.ClientProductsPairs = pyomo.Set(initialize=[(c, p) for c in Clients for p in Products])
model.ClientLocationPairs = pyomo.Set(initialize=[(c, l) for c in Clients for l in Locations])
model.BatchLocationPairs = pyomo.Set(initialize=[(b, l) for b in Batches for l in Locations])
model.ClientBatchPairs = pyomo.Set(initialize=[(c, b) for c in Clients for b in Batches])


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

model.P_c = pyomo.Param(model.Clients, initialize=P_c)

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

model.A_cb = pyomo.Param(model.ClientBatchPairs, initialize=A_cb)


# -------------------------

#  Volumen disponible en el lote b ∈ B.
V_b = {
    (row['batch_id'], ): row['quantity']
    for _, row in batchesVolumesTable(batches_data).iterrows()
}

for batch in Batches:
    V_b.setdefault((batch, ), 0)

model.V_b = pyomo.Param(model.Batches, initialize=V_b)


# -------------------------

# Demanda del cliente c ∈ C para el producto p ∈ P.
D_cp = {
    (row['client_id'], row['product_id']): row['demand']
    for _, row in salesTable(requests_data).iterrows()
}

for client in Clients:
    for product in Products:
        D_cp.setdefault((client, product), 0)

model.D_cp = pyomo.Param(model.ClientProductsPairs, initialize=D_cp)


# -------------------------

# Antigüedad del lote b ∈ B en días.
now = time()

T_b = {
    (row['batch_id'], ): (now - row['ship_date_epoch']) // (24 * 3600)
    for _, row in batchesVolumesTable(batches_data).iterrows()
}

for batch in Batches:
    T_b.setdefault((batch, ), 1)

model.T_b = pyomo.Param(model.Batches, initialize=T_b)

# -------------------------

# Variable binaria que indica si el cliente c ∈ C está en la ubicación u ∈ U.
LC_cl = {
    (row['client_id'], row['client_location']): 1
    for _, row in clientLocationTable(requests_data).iterrows()
}

for client in Clients:
    for location in Locations:
        LC_cl.setdefault((client, location), 0)

model.LC_cl = pyomo.Param(model.ClientLocationPairs, initialize=LC_cl, within=pyomo.Binary)


# -------------------------

# Variable binaria que indica si el lote c ∈ C está en la ubicación l ∈ L.
LB_b = {
    (row['batch_id'], row['batch_location']): 1
    for _, row in batchesLocationsTable(batches_data).iterrows()
}

for batch in Batches:
    for location in Locations:
        LB_b.setdefault((batch, location), 0)

model.LB_b = pyomo.Param(model.BatchLocationPairs, initialize=LB_b, within=pyomo.Binary)

# -------------============== VARIABLES AUXILIARES ==============------------ #

# -------------============= VARIABLES DE DECISIÓN ==============------------ #
# Indica si el lote b ∈ B está asignado al cliente c ∈ C.
model.X_cb = pyomo.Var(model.ClientBatchPairs, domain=pyomo.Binary)


# -------------================= RESTRICCIONES ==================------------ #
# # Ver si podemos entregar un lote a un cliente
# # Aptitud del lote (Compatibilidad Cliente-Lote):
# # X_cb <= A_cb          ∀ c ∈ C, b ∈ B
def batch_apt_for_client_rule(model, c, b):
    return (
            model.X_cb[c, b] <= model.A_cb[c, b]
    )


model.batch_apt_for_client = pyomo.Constraint(model.Clients, model.Batches,
                                              rule=batch_apt_for_client_rule)


# -------------------------------

# # Cada lote puede ser enviado hasta una sola vez.
# # Unicidad del lote (Asignación Única):
# # Σ_c (X_cb) <= 1       ∀ b ∈ B
def unique_batch_asignation_rule(model, b):
    return (
            sum(model.X_cb[c, b] for c in model.Clients) <= 1
    )


model.unique_batch_asignation_rule = pyomo.Constraint(model.Batches,
                                                      rule=unique_batch_asignation_rule)


# -------------------------------

def max_sale_rule(model, c, p):
    return (
            sum(model.X_cb[c, b] * model.V_b[b] for b in model.Batches) <= model.D_cp[c, p] + sale_excess
    )


model.max_sale = pyomo.Constraint(model.Clients, model.Products, rule=max_sale_rule)


# -------------================ FUNCIÓN OBJETIVO ================------------ #
model.objective = pyomo.Objective(
    expr=sum(model.X_cb[c, b] for c in model.Clients for b in model.Batches),
    sense=pyomo.maximize
)

# -------------=================== EJECUCIÓN ====================------------ #

# Solucionador
glpk_path = r'C:\Users\Luis\Desktop\git\cmpc-europe-flushing-2023-12\winglpk-4.65\glpk-4.65\w64'
solver = pyomo.SolverFactory('glpk', executable=glpk_path + '/glpsol.exe')
solver.solve(model)

# Mostrar resultados
count = 0
for c in model.Clients:
    for b in model.Batches:
        if model.X_cb[c, b].value >= 0.5:  # Asumiendo una pequeña tolerancia
            count += 1
            print(f"Lote {b} asignado a Cliente {c}: {model.X_cb[c, b].value}")

print("Total de lotes asignados:", count)
