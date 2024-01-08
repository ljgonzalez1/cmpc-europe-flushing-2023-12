import pandas as pd
from collections import defaultdict


class Priority:

    def __init__(self,
                 client_id: int or str,
                 priority: float or int = 0):
        self.client_id = int(client_id)
        self.importance = float(priority)
    def __str__(self) -> str:
        return f"""
ID de cliente: {self.client_id}
Importancia del cliente: {self.importance}
        """


def get_client_priority_data(
    file_path: str = "./PRIORIDADES.xlsx",
    file_sheet: str = "Hoja1",
    clients_col: str = "client_id",
    skip_rows: int = 0
) -> dict:

    df = pd.read_excel(file_path, sheet_name=file_sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=[clients_col])

    priority = {
        index: Priority(
            client_id=row[clients_col],
            priority=row["importance"]
        )
        for index, row in dataframe.iterrows()
    }

    return priority


if __name__ == "__main__":
    data = get_client_priority_data()
    print(data)

    for entry in data:
        print(entry, data[entry])
