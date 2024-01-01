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

        self.mass = arrived_mass + mass_in_transit

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


if __name__ == "__main__":
    # Ejemplo de uso
    path = "/home/luis/git/cmpc-europe-flushing-2023-12/STOCK.xlsx"
    sheet = "Format"
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
        if dataframe["Lote"][row] not in ("", "NaN", "nan", None)
    }

    for batch in batches:
        print(str(batches[batch]))


