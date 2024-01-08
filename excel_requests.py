import pandas as pd
from collections import defaultdict


class Request:
    def __init__(self,
                 client_description: str,
                 client_id: str or int,
                 client_group_description: str,
                 location: str,
                 product_id: str,
                 requested: int or float):
        self.client_description = client_description.title()
        self.client_id = int(client_id)
        self.client_group_description = client_group_description.title()
        self.location = location.title()
        self.product_id = product_id.upper()
        self.requested = 0.0 if requested < 1 else float(requested)

    def __str__(self) -> str:
        return f"""
Descripción del cliente: {self.client_description}
ID de cliente: {self.client_id}
Descripción del grupo de cliente: {self.client_group_description}
Ubicación: {self.location}
ID de producto: {self.product_id}
Cantidad demandada: {self.requested}
        """


def get_sales_data(
    file_path: str = "./VENTAS.xlsx",
    file_sheet: str = "Ventas",
    this_month_col: str = "JAN 2024",
    skip_rows: int = 0
) -> dict:

    df = pd.read_excel(file_path, sheet_name=file_sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=[this_month_col])

    sales = {
        index: Request(
            client_description=row["Descripción de cliente 2"],
            client_id=row["ID de cliente CMPC"],
            client_group_description=row["Descripción del grupo de cliente"],
            location=row["Ubicación"],
            product_id=row["ID de producto"],
            requested=row[this_month_col]
        )
        for index, row in dataframe.iterrows()
    }

    return sales


if __name__ == "__main__":
    data = get_sales_data()
    print(data)

    for entry in data:
        print(entry, data[entry])
