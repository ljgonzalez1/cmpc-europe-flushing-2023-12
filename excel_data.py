import pandas as pd
from collections import defaultdict


def excel2dataframe(file_path, sheet_name, skip_rows=0):
    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)
    return df


class Batch:
    """
    This class represents a batch of material that has been shipped from a mill to a ship. It contains information about the center where the material was produced, the mill where it was produced, the ship that it was shipped on, the date it was shipped, the batch ID, the product ID, the total mass of the batch (including the mass that is in transit), and a dictionary that indicates which clients are eligible to purchase the batch.

    Args:
        center_name (str): The name of the center where the material was produced.
        mill (str): The name of the mill where the material was produced.
        ship (str): The name of the ship that the material was shipped on.
        shipping_date (str): The date that the material was shipped, in the format "MM/DD/YYYY".
        batch_id (str): The ID of the batch.
        product_id (str): The ID of the product that the batch contains.
        arrived_mass (str): The mass of the batch that arrived at the destination mill, in pounds.
        mass_in_transit (str): The mass of the batch that is still in transit, in pounds.
        sellable_clients (dict): A dictionary that maps client IDs to booleans, indicating whether the client is eligible to purchase the batch. The keys of the dictionary are the client IDs, and the values are True if the client is eligible, and False if they are not.

    Attributes:
        center_name (str): The name of the center where the material was produced.
        mill (str): The name of the mill where the material was produced.
        ship (str): The name of the ship that the material was shipped on.
        shipping_date_epoch (int): The timestamp of the date that the material was shipped, in seconds since the Unix epoch.
        batch_id (str): The ID of the batch.
        product_id (str): The ID of the product that the batch contains.
        mass (int): The total mass of the batch (including the mass that is in transit), in pounds.
        sellable_clients (dict): A dictionary that maps client IDs to booleans, indicating whether the client is eligible to purchase the batch. The keys of the dictionary are the client IDs, and the values are True if the client is eligible, and False if they are not.
    """

    def __init__(self,
                 center_name, mill,
                 ship, shipping_date,
                 batch_id, product_id,
                 arrived_mass, mass_in_transit,
                 sellable_clients):
        self.center_name = str(center_name)
        self.mill = str(mill)
        self.ship = str(ship)

        shipping_date_timestamp = pd.to_datetime(shipping_date)
        self.shipping_date_epoch = int(shipping_date_timestamp.timestamp())
        self.batch_id = str(batch_id)
        self.product_id = str(product_id)

        self.mass = int(arrived_mass + mass_in_transit)

        self.sellable_clients = defaultdict(bool)

        for client_number_code, sellable in sellable_clients.items():
            self.sellable_clients[client_number_code] = sellable

    def __str__(self):
        return f"""
Nombre Centro: {self.center_name}
Planta: {self.mill}
Nave: {self.ship}
Fecha Nave: {self.shipping_date_epoch}
Lote: {self.batch_id}
Material: {self.product_id}
Masa neto (LU): {self.mass}
Clientes aptos para venta: {self.sellable_clients}
        """


def get_batches_from_stocks(
    stocks_path: str = "./STOCK.xlsx",
    stocks_sheet: str = "Format",
    skip_rows: int = 1,
) -> dict:
    """
    This function reads data from an Excel file and returns a dictionary of Batch objects, where the keys are the batch IDs and the values are Batch objects.

    Args:
        stocks_path (str, optional): The path to the Excel file containing the stock data. Defaults to "./STOCK.xlsx".
        stocks_sheet (str, optional): The name of the sheet containing the stock data. Defaults to "Format".
        skip_rows (int, optional): The number of rows at the top of the sheet to skip. Defaults to 1.

    Returns:
        dict: A dictionary of Batch objects, where the keys are the batch IDs and the values are Batch objects.
    """
    path = stocks_path
    sheet = stocks_sheet
    df = pd.read_excel(path, sheet_name=sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=["Lote"])

    clients_number_code = [
        col for col in dataframe.columns if str(col).isdigit()
    ]

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
                    any(
                        character.isdigit()
                        for character in str(dataframe[client_number_code][row])
                    )
                for client_number_code in clients_number_code
            },
        )
        for row in range(len(dataframe["Lote"]))
    }

    return batches


def get_client_requests_from_sales(
    sales_path: str = "./VENTAS.xlsx",
    sales_sheet: str = "Ventas",
    this_month: str = "VENTAS_PROGRAMA",
) -> dict:
    """
    This function reads data from an Excel file and returns a dictionary of client requests, where the keys are tuples of (client ID, product ID) and the values are dictionaries containing information about the client request.

    Args:
        sales_path (str, optional): The path to the Excel file containing the sales data. Defaults to "./VENTAS.xlsx".
        sales_sheet (str, optional): The name of the sheet containing the sales data. Defaults to "Ventas".
        this_month (str, optional): The name of the column in the Excel file that contains the sales data for the current month. Defaults to "VENTAS_PROGRAMA".

    Returns:
        dict: A dictionary of client requests, where the keys are tuples of (client ID, product ID) and the values are dictionaries containing information about the client request.
    """
    dataframe = excel2dataframe(sales_path, sales_sheet, skip_rows=0)
    df = dataframe.dropna(subset=["ID de cliente CMPC"])

    client_requests = {
        (str(df["ID de cliente CMPC"][row]), str(df["ID de producto"][row])): {
            "client_description": str(df["Descripción de cliente 2"][row]),
            "client_id": str(df["ID de cliente CMPC"][row]),
            "client_group": str(df["Descripción del grupo de cliente"][row]),
            "product": str(df["ID de producto"][row]),
            "requested_amount": int(df[this_month][row]),
        }
        for row in range(len(df["ID de cliente CMPC"]))
    }

    return client_requests


def get_products():
    """
    This function returns a set of all product IDs that are present in the sales and stocks data.

    Returns:
        set: A set of all product IDs.
    """
    product_ids = set()
    sales = get_client_requests_from_sales()
    batches = get_batches_from_stocks()

    for entry in sales:
        product_ids.add(str(sales[entry]["product"]))

    for entry in batches:
        product_ids.add(str(batches[entry].product_id))

    return product_ids


def get_clients():
    """
    This function returns a set of all client IDs that are present in the sales and stocks data.

    Returns:
        set: A set of all client IDs.
    """
    client_ids = set()
    sales = get_client_requests_from_sales()
    batches = get_batches_from_stocks()

    for entry in sales:
        client_ids.add(str(sales[entry]["client_id"]))

    for entry in batches:
        for key in batches[entry].sellable_clients.keys():
            client_ids.add(str(key))

    return client_ids


def get_batches():
    return {str(key) for key in get_batches_from_stocks().keys()}


def get_client_batch_compatibility() -> dict:
    """
    This function returns a dictionary containing the compatibility between batches and clients.

    Returns:
        dict: A dictionary containing the compatibility between batches and clients, where the keys are tuples of (client ID, batch ID) and the values are integers indicating the compatibility (1 if the batch is compatible with the client, and 0 if it is not).
    """
    compatibility_data = defaultdict(int)
    batches_objects = get_batches_from_stocks()
    clients = get_clients()

    for batch in batches_objects:
        for client in clients:
            compatibility_data[(client, batch)] = 1 \
                if batches_objects[batch].sellable_clients[client] \
                else 0

    return compatibility_data


def get_client_product_demand() -> dict:
    """
    This function returns a dictionary containing the demand for each product by each client.

    Returns:
        dict: A dictionary containing the demand for each product by each client, where the keys are tuples of (client ID, product ID) and the values are integers indicating the demand.
    """
    demand_data = defaultdict(int)
    clients_data_dict = get_client_requests_from_sales()

    for client, product in clients_data_dict:
        demand_data[(client, product)] = clients_data_dict[
            (client, product)]["requested_amount"]

    return demand_data

# ------------------------------------------


if __name__ == "__main__":
    print(get_batches_from_stocks())
    a = get_batches_from_stocks()
    for i in a:
        print(f"{i}: {a[i]}")


    print(get_client_batch_compatibility())
    a = get_client_batch_compatibility()
    for i in a:
        print(f"{i}: {a[i]}")
