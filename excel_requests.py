import pandas as pd
from collections.abc import Hashable
from typing import Dict, Union

from settings import config


class Request:
    """
    Representa una solicitud de venta, incluyendo detalles sobre el cliente y el producto.

    Parámetros
    ----------
    client_description : str
        Descripción del cliente.
    client_id : Union[int, str]
        Identificador del cliente, puede ser un número o una cadena.
    client_group_description : str
        Descripción del grupo al que pertenece el cliente.
    location : str
        Ubicación del cliente.
    product_id : str
        Identificador del producto solicitado.
    requested : Union[int, float]
        Cantidad del producto solicitado.

    Métodos
    -------
    __str__()
        Devuelve una representación en cadena de la instancia de Request.

    Ejemplo
    -------
    >>> request = Request("Empresa XYZ", 123, "Grupo A", "Ciudad", "Prod123", 10)
    >>> print(request)
    Descripción del cliente: Empresa Xyz
    ID de cliente: 123
    Descripción del grupo de cliente: Grupo A
    Ubicación: Ciudad
    ID de producto: PROD123
    Cantidad demandada: 10.0
    """
    def __init__(self,
                 client_description: str,
                 client_id: str or int,
                 client_group_description: str,
                 location: str,
                 product_id: str,
                 requested: Union[int, float]) -> None:
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
    file_path: str = config.requests.file.path,
    file_sheet: str = config.requests.file.sheet,
    this_month_col: str = config.requests.columns.this_month,
    skip_rows: int = 0
) -> Dict[Hashable, Request]:
    """
    Carga datos de ventas desde un archivo Excel y los convierte en un diccionario de objetos Request.

    Parámetros
    ----------
    file_path : str, opcional
        Ruta al archivo Excel con los datos de ventas.
    file_sheet : str, opcional
        Nombre de la hoja de cálculo a leer.
    this_month_col : str, opcional
        Nombre de la columna que contiene la cantidad solicitada este mes.
    skip_rows : int, opcional
        Número de filas a omitir al principio del archivo.

    Devuelve
    -------
    Dict[Hashable, Request]
        Un diccionario con índices de fila como claves y objetos Request como valores.

    Ejemplo
    -------
    >>> sales_data = get_sales_data()
    >>> for index, request in sales_data.items():
    ...     print(f"Index: {index}, Request: {request}")
    """
    df = pd.read_excel(file_path, sheet_name=file_sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=[this_month_col])

    sales = {
        index: Request(
            client_description=row[config.requests.columns.client_description],
            client_id=row[config.requests.columns.client_id],
            client_group_description=row[config.requests.columns.client_group_description],
            location=row[config.requests.columns.location],
            product_id=row[config.requests.columns.product_id],
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
