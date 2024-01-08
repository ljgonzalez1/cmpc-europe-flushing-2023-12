import pandas
from collections import defaultdict

from excel_batches import get_batches_from_stocks
from excel_requests import get_sales_data
from excel_priority import get_client_priority_data


def get_raw_data():
    return {"batches": get_batches_from_stocks(),
            "requests": get_sales_data(),
            "importance": get_client_priority_data()}

# ------------------------------------------------------------


def get_all_clients(batches_data, requests_data):
    # Clientes de la tabla de ventas
    clients = set(requests_data[key].client_id for key in requests_data.keys())

    # Clientes de la tabla de stocks
    for entry in batches_data:
        for client in batches_data[entry].sellable_clients.keys():
            clients.add(client)

    clients = list(clients)
    clients.sort()

    return clients


def get_all_locations(batches_data, requests_data):
    # Ubicaciones de la tabla de ventas
    locations = set(requests_data[key].location for key in requests_data.keys())

    # Puertos de la tabla de stocks
    for entry in batches_data:
        locations.add(batches_data[entry].mill)

    locations = list(locations)
    locations.sort()

    return locations


def get_all_products(batches_data, requests_data):
    # Productos de la tabla de ventas
    products = set(requests_data[key].product_id for key in requests_data.keys())

    # Productos de la tanbla de stocks
    for entry in batches_data:
        products.add(batches_data[entry].product_id)

    products = list(products)
    products.sort()

    return products


def get_all_batches(batches_data):
    batches = set(batches_data[key].batch_id for key in batches_data.keys())
    batches = list(batches)
    batches.sort()

    return batches

# ------------------------------------------------------------

# ## Tabla de ventas
# | ID Cliente | ID de producto | VENTAS |
# | client_id  | product_id     | demand |
# | ---------- | -------------- | ------ |
# | 18368      | CC3029         | 1350   |
# | 18368      | CC3429         | 900    |
# | 18368      | CC3129         | 0      |
# | 18820      | CC3029         | 3000   |
# | 18375      | CC3129         | 1116   |
# | ...        | ...            | ...    |


def get_sales_table(requests_data):
    data = [{"client_id": requests_data[key].client_id,
             "product_id": requests_data[key].product_id,
             "demand": float(requests_data[key].requested)}
            for key in requests_data.keys()
            ]

    data.sort(key=lambda x: x["client_id"])

    sales_table = pandas.DataFrame({
        "client_id": [entry["client_id"] for entry in data],
        "product_id": [entry["product_id"] for entry in data],
        "demand": [entry["demand"] for entry in data]
    })

    return sales_table


# ------------------------------------------------------------

# ## Tabla ubicación de cliente
# | ID Cliente | Ubicación       |
# | client_id  | client_location |
# | ---------- | --------------- |
# | 18368      | PULP FLUSHING  |
# | 18820      | PULP FLUSHING  |
# | 18820      | PULP BRAKE     |
# | 18375      | PULP BRAKE     |
# | ...        | ...            |
def get_clients_locations_table(requests_data):
    data = list(set((requests_data[key].client_id, requests_data[key].location)
                    for key in requests_data.keys()))

    data.sort(key=lambda x: x[0])

    sales_table = pandas.DataFrame({
        "client_id": [elem[0] for elem in data],
        "client_location": [elem[1] for elem in data]
    })

    return sales_table


# ------------------------------------------------------------

# ## Tabla de clientes
# | ID Cliente | Descripción del grupo de cliente | Descripción de cliente  |
# | client_id  | client_group_name                | client_name             |
# | ---------- | -------------------------------- | ----------------------- |
# | 18368      | KOEHLER                          | KOEHL KEHL              |
# | 18820      | KOEHLER                          | KOEHL OBERK             |
# | 18375      | SAPPI                            | SAPPI ALF               |
# | ...        | ...                              | ...                     |
def get_clients_data_table(batches_data, requests_data):
    clients = get_all_clients(batches_data, requests_data)

    clients_data = dict()

    for client in clients:
        clients_data[client] = {"client_group_name": None,
                                "client_name": None}

    for entry in requests_data:
        clients_data[requests_data[entry].client_id] = {
            "client_group_name": requests_data[entry].client_group_description,
            "client_name": requests_data[entry].client_description
        }

    clients_data_table = pandas.DataFrame({
        "client_id": clients,
        "client_group_name": [clients_data[client]["client_group_name"] for client in clients],
        "client_name": [clients_data[client]["client_name"] for client in clients]
    })

    return clients_data_table


# ------------------------------------------------------------

# ## Tabla de prioridades de clientes
# | ID Cliente | Prioridad de ventas (más es más importante) |
# | client_id  | priority                                    |
# | ---------- | ------------------------------------------- |
# | 18368      | 10                                          |
# | 18820      | 10                                          |
# | 18375      | 1                                           |
# | ...        | ...                                         |
def get_clients_priorities_table(batches_data, request_data, importance_data):
    clients = get_all_clients(batches_data, request_data)
    data = defaultdict(lambda: 0.0)

    for index in importance_data.keys():
        data[importance_data[index].client_id] = importance_data[index].importance

    return pandas.DataFrame({
        "client_id": clients,
        "priority": [data[client]
                     for client in clients]
    })


# ------------------------------------------------------------

# ## Tabla de volúmenes
# | Fecha Nave (Epoch) | Lote     | Material   | Net Arrib (LU) + Net en Tráns |
# | ship_date_epoch    | batch_id | product_id | quantity                      |
# | ------------------ | -------- | ---------- | ----------------------------- |
# | 1684454401         | 551290B  | CC3029     | 56.784                        |
# | 1684454401         | 551291   | CC3029     | 10.075                        |
# | 1684454401         | 551302   | CC3029     | 504.952                       |
# | 1684454401         | 551373   | CC3129     | 95.424                        |
# | 1689120001         | 551375B  | CC4929     | 47.856                        |
# | 1689120001         | 551383B  | CC3029     | 40.04                         |
# | ...                | ...      | ...        | ...                           |
def get_batches_volumes_table(batches_data):
    batches = get_all_batches(batches_data)

    batches_volumes = pandas.DataFrame({
        "batch_id": batches,
        "ship_date_epoch": [batches_data[batch].shipping_date_epoch for batch in batches],
        "product_id": [batches_data[batch].product_id for batch in batches],
        "quantity": [batches_data[batch].mass for batch in batches]
    })

    return batches_volumes


# ------------------------------------------------------------

# ## Tabla ubicación lotes
# | Nombre Centro   | Lote     |
# | batch_location  | batch_id |
# | --------------- | -------- |
# | Pulp Flushing   | 551290B  |
# | Pulp Flushing   | 551291   |
# | Pulp Brake      | 551302   |
# | Pulp Flushing   | 551373   |
# | Pulp Monfalcone | 551375B  |
# | Pulp Flushing   | 551383B  |
# | ...             | ...      |
def get_batches_locations_table(batches_data):
    batches = get_all_batches(batches_data)

    batches_volumes = pandas.DataFrame({
        "batch_id": batches,
        "batch_location": [batches_data[batch].mill for batch in batches]
    })

    return batches_volumes


# ------------------------------------------------------------

# ## Tabla de aptitud para clientes
# | ID Cliente | Lote     | Lote apto para entregar a cliente |
# | client_id  | batch_id | apt                              |
# | ---------- | -------- | --------------------------------- |
# | 18368      | 551290B  | 1                                 |
# | 18820      | 551290B  | 1                                 |
# | 18375      | 551290B  | 0                                 |
# | 18368      | 551291   | 1                                 |
# | 18820      | 551291   | 1                                 |
# | 18375      | 551291   | 0                                 |
# | 18368      | 551302   | 1                                 |
# | 18820      | 551302   | 0                                 |
# | 18375      | 551302   | 1                                 |
# | 18368      | 551373   | 1                                 |
# | 18820      | 551373   | 1                                 |
# | 18375      | 551373   | 0                                 |
# | 18368      | 551375B  | 1                                 |
# | 18820      | 551375B  | 1                                 |
# | 18375      | 551375B  | 1                                 |
# | 18368      | 551383B  | 0                                 |
# | 18820      | 551383B  | 1                                 |
# | 18375      | 551383B  | 1                                 |
# | ...        | ...      | ...                               |
def get_compatibility_client_batch_table(batches_data, requests_data):
    batches = get_all_batches(batches_data)
    clients = get_all_clients(batches_data, requests_data)

    compatibility_dict = dict()

    for batch in batches:
        for client in clients:
            compatibility_dict[(client, batch)] = 0

    for batch in batches_data:
        for client in batches_data[batch].sellable_clients.keys():
            if batches_data[batch].sellable_clients[client]:
                compatibility_dict[(client, batch)] = 1

            else:
                compatibility_dict[(client, batch)] = 0

    compatibility_table = pandas.DataFrame({
        "client_id": [client for client, batch in compatibility_dict.keys()],
        "batch_id": [batch for client, batch in compatibility_dict.keys()],
        "apt": [compatibility_dict[key] for key in compatibility_dict.keys()]
    })

    return compatibility_table

if __name__ == "__main__":
    (request_data_dict,
     batches_data_dict,
     importance_data_dict) = (get_raw_data()["requests"],
                              get_raw_data()["batches"],
                              get_raw_data()["importance"])

    print("Clients", get_all_clients(batches_data_dict, request_data_dict))
    print("Locations", get_all_locations(batches_data_dict, request_data_dict))
    print("Products", get_all_products(batches_data_dict, request_data_dict))
    print("Batches", get_all_batches(batches_data_dict))

    print()
    print()

    print(get_sales_table(request_data_dict))
    print()

    print(get_clients_locations_table(request_data_dict))
    print()

    print(get_clients_data_table(batches_data_dict, request_data_dict))
    print()

    print(get_clients_priorities_table(batches_data_dict, request_data_dict, importance_data_dict))
    print()

    print(get_batches_volumes_table(batches_data_dict))
    print()

    print(get_batches_locations_table(batches_data_dict))
    print()

    print(get_compatibility_client_batch_table(batches_data_dict, request_data_dict))
    print()


