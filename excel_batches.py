import pandas as pd
from collections import defaultdict


class Batch:
    def __init__(self,
                 center_name, mill,
                 shipping_date,
                 batch_id, product_id,
                 arrived_mass, mass_in_transit,
                 sellable_clients):
        self.center_name = str(center_name).title()
        self.mill = str(mill).title()

        shipping_date_timestamp = pd.to_datetime(shipping_date)
        self.shipping_date_epoch = int(shipping_date_timestamp.timestamp())
        self.batch_id = str(batch_id).upper()
        self.product_id = str(product_id).upper()

        self.mass = float(arrived_mass + mass_in_transit)

        self.sellable_clients = defaultdict(bool)

        for client_number_code, sellable in sellable_clients.items():
            self.sellable_clients[client_number_code] = sellable

    def __str__(self):
        return f"""
Nombre Centro: {self.center_name}
Planta: {self.mill}
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
    path = stocks_path
    sheet = stocks_sheet
    df = pd.read_excel(path, sheet_name=sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=["Lote"])

    clients_number_code = [
        col
        for col in dataframe.columns
        if str(col).isdigit()
        and str(col).isdigit() != "0"
    ]

    batches = {
        str(dataframe["Lote"][row]): Batch(
            center_name=dataframe["Nombre Centro"][row],
            mill=dataframe["Planta"][row],
            shipping_date=dataframe["Fecha Nave"][row],
            batch_id=dataframe["Lote"][row],
            product_id=dataframe["Material"][row],
            arrived_mass=dataframe["Net Arrib (LU)"][row],
            mass_in_transit=dataframe["Net en Tráns"][row],
            sellable_clients={
                int(client_number_code):
                    any(
                        character.isdigit()
                        for character in str(dataframe[client_number_code][row])
                    )
                for client_number_code in clients_number_code
            }
        )
        for row in range(len(dataframe["Lote"]))
    }

    return batches


if __name__ == "__main__":
    data = get_batches_from_stocks()
    print(data)

    for entry in data:
        print(entry, data[entry])
