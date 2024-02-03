import pandas as pd
from collections.abc import Hashable
from typing import Dict, Union

from settings import config


class Priority:
    """
    Representa la prioridad asignada a un cliente.

    Atributos
    ----------
    client_id : int
        Identificador del cliente.
    importance : float
        Nivel de importancia o prioridad asignada al cliente.

    Métodos
    -------
    __str__()
        Representación en cadena del objeto Priority.

    Ejemplo
    -------
    >>> priority = Priority(123, 5.0)
    >>> print(priority)
    ID de cliente: 123
    Importancia del cliente: 5.0
    """

    def __init__(self,
                 client_id: Union[int, str],
                 priority: Union[float, int] = 0) -> None:
        self.client_id = int(client_id)
        self.importance = float(priority)

    def __str__(self) -> str:
        return f"""ID de cliente: {self.client_id}
Importancia del cliente: {self.importance}"""


def get_client_priority_data(
    file_path: str = config.priority.file.path,
    file_sheet: str = config.priority.file.sheet,
    clients_col: str = config.priority.columns.client_id,
    skip_rows: int = 0
) -> Dict[Hashable, Priority]:
    """
    Lee un archivo Excel y extrae datos de prioridad de clientes.

    Parámetros
    ----------
    file_path : str, opcional
        Ruta al archivo Excel con los datos de prioridad.
    file_sheet : str, opcional
        Nombre de la hoja de cálculo a leer.
    clients_col : str, opcional
        Nombre de la columna que contiene los identificadores de los clientes.
    skip_rows : int, opcional
        Número de filas a omitir al principio del archivo.

    Devuelve
    -------
    Dict[int, Priority]
        Un diccionario con índices de fila como claves y objetos Priority como valores.

    Ejemplo
    -------
    >>> data = get_client_priority_data()
    >>> for index, priority in data.items():
    ...     print(f"Index: {index}, Cliente: {priority.client_id}, Importancia: {priority.importance}")
    """

    df = pd.read_excel(file_path, sheet_name=file_sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=[clients_col])

    priority = {
        index: Priority(
            client_id=row[clients_col],
            priority=row[config.priority.columns.importance]
        )
        for index, row in dataframe.iterrows()
    }

    return priority


if __name__ == "__main__":
    data = get_client_priority_data()
    print(data)

    for entry in data:
        print(entry, data[entry], '\n', sep='\n')
