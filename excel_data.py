import pandas as pd
from collections import defaultdict


def excel2dataframe(file_path, sheet_name, skip_rows=0):
    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)
    return df


class Batch:
    def __init__(self,
                 center_name, mill,
                 ship, shipping_date,
                 batch_id, product_id,
                 arrived_mass, mass_in_transit,
                 sellable_clients):
        self.center_name = center_name
        self.mill = mill
        self.ship = ship

        self.shipping_date = shipping_date
        self.batch_id = batch_id
        self.product_id = product_id

        self.mass = int(arrived_mass + mass_in_transit)

        self.sellable_clients = defaultdict(bool)

        for client_number_code, sellable in sellable_clients.items():
            self.sellable_clients[client_number_code] = sellable

    def __str__(self):
        return f"""
Nombre Centro: {self.center_name}
Planta: {self.mill}
Nave: {self.ship}
Fecha Nave: {self.shipping_date}
Lote: {self.batch_id}
Material: {self.product_id}
Masa neto (LU): {self.mass}
Clientes aptos para venta: {self.sellable_clients}
        """


def get_batches_from_stocks(
        stocks_path="/home/luis/git/cmpc-europe-flushing-2023-12/STOCK.xlsx",
        stocks_sheet="Format"):
    path = stocks_path
    sheet = stocks_sheet
    df = excel2dataframe(path, sheet, skip_rows=1)
    dataframe = df.dropna(subset=['Lote'])

    clients_number_code = [col for col in dataframe.columns if
                          str(col).isdigit()]

    batches = {
        str(dataframe["Lote"][row]): Batch(
            center_name=dataframe["Nombre Centro"][row],
            mill=dataframe["Planta"][row],
            ship=dataframe["Nave"][row],
            shipping_date=dataframe["Fecha Nave"][row],
            batch_id=dataframe["Lote"][row],
            product_id=dataframe["Material"][row],
            arrived_mass=dataframe["Net Arrib (LU)"][row],
            mass_in_transit=dataframe["Net en Tráns"][row],
            sellable_clients={
                str(client_number_code):
                    [any(character.isdigit()
                         for character
                         in str(dataframe[client_number_code][row]))]
                for client_number_code in clients_number_code
            },
        )
        for row in range(len(dataframe["Lote"]))
    }

    return batches


def get_client_requests_from_sales(
        sales_path="/home/luis/git/cmpc-europe-flushing-2023-12/VENTAS.xlsx",
        sales_sheet="Ventas",
        this_month="VENTAS_PROGRAMA"):

    dataframe = excel2dataframe(sales_path, sales_sheet, skip_rows=0)
    df = dataframe.dropna(subset=['ID de cliente CMPC'])

    client_requests = {
        (df["ID de cliente CMPC"][row], df["ID de producto"][row]):

            {"client_description": df["Descripción de cliente 2"][row],
             "client_id": df["ID de cliente CMPC"][row],
             "client_group": df["Descripción del grupo de cliente"][row],
             "product": df["ID de producto"][row],
             "requested_amount": int(df["VENTAS_PROGRAMA"][row])}
        for row in range(len(df["ID de cliente CMPC"]))
    }

    return client_requests


def get_products():
    product_ids = set()
    sales = get_client_requests_from_sales()
    batches = get_batches_from_stocks()

    for entry in sales:
        product_ids.add(sales[entry]["product"])

    for entry in batches:
        product_ids.add(batches[entry].product_id)

    return product_ids


def get_clients():
    client_ids = set()
    sales = get_client_requests_from_sales()
    batches = get_batches_from_stocks()

    for entry in sales:
        client_ids.add(sales[entry]["client_id"])

    for entry in batches:
        for key in batches[entry].sellable_clients.keys():
            client_ids.add(key)

    return client_ids


def get_batches():
    return {key for key in get_batches_from_stocks().keys()}


def get_client_batch_compatibility():
    compatibility_data = dict()
    batches_objects = get_batches_from_stocks()
    clients = get_clients()

    for batch in batches_objects:
        for client in clients:
            compatibility_data[(client, batch)] = 1 \
                if batches_objects[batch].sellable_clients[client] \
                else 0

    return compatibility_data


def get_client_product_demand():
    demand_data = dict()
    clients_data_dict = get_client_requests_from_sales()

    for client, product in clients_data_dict:
        demand_data[(client, product)] = clients_data_dict[
            (client, product)]["requested_amount"]

    return demand_data

# ------------------------------------------


print(get_client_product_demand())
a = get_client_product_demand()
for i in a:
    print(f"{i}: {a[i]}")


