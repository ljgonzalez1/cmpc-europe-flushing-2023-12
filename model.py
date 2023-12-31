import time
import pulp

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










