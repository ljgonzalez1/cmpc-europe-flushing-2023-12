import pandas as pd
from collections import defaultdict
from typing import Dict, Union

from settings import config


class Batch:
    """
    Representa un lote de productos, incluyendo información detallada sobre el centro, planta,
    fecha de envío, y otros detalles relevantes.

    Parámetros
    ----------
    center_name : str
        Nombre del centro de distribución.
    mill : str
        Nombre de la planta de producción.
    shipping_date : str
        Fecha de envío del lote.
    batch_id : Union[str, int]
        Identificador del lote.
    product_id : Union[str, int]
        Identificador del producto.
    arrived_mass : Union[float, str, int]
        Masa del producto que ha llegado.
    mass_in_transit : Union[float, str, int]
        Masa del producto en tránsito.
    sellable_clients : Dict[int, bool]
        Diccionario que indica si el producto es vendible a cada cliente (identificado por su código numérico).

    Métodos
    -------
    __str__()
        Devuelve una representación en cadena de la instancia de Batch.

    Ejemplo
    -------
    >>> batch = Batch("Centro A", "Planta 1", "2023-01-01", "1234", "Prod456", 1000, 500, {1001: True, 1002: False})
    >>> print(batch)
    Nombre Centro: Centro A
    Planta: Planta 1
    Fecha Nave: 1672531200
    Lote: 1234
    Material: PROD456
    Masa neto (LU): 1500.0
    Clientes aptos para venta: defaultdict(<class 'bool'>, {1001: True, 1002: False})
    """
    def __init__(self,
                 center_name: str,
                 mill: str,
                 shipping_date: str,
                 batch_id: Union[str, int],
                 product_id: Union[str, int],
                 arrived_mass: Union[float, str, int],
                 mass_in_transit: Union[float, str, int],
                 sellable_clients: Dict[int, bool]) -> None:
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

    def __str__(self) -> str:
        return f"""Nombre Centro: {self.center_name}
Planta: {self.mill}
Fecha Nave: {self.shipping_date_epoch}
Lote: {self.batch_id}
Material: {self.product_id}
Masa neto (LU): {self.mass}
Clientes aptos para venta: {self.sellable_clients}"""


def get_batches_from_stocks(
    stocks_path: str = config.batches.file.path,
    stocks_sheet: str = config.batches.file.sheet,
    skip_rows: int = config.batches.file.extra_rows,
) -> Dict[str, Batch]:
    """
    Carga datos de lotes de un archivo Excel y los convierte en un diccionario de objetos Batch.

    Parámetros
    ----------
    stocks_path : str, opcional
        Ruta al archivo Excel con los datos de los lotes de stock.
    stocks_sheet : str, opcional
        Nombre de la hoja de cálculo a leer.
    skip_rows : int, opcional
        Número de filas a omitir al principio del archivo.

    Devuelve
    -------
    Dict[str, Batch]
        Un diccionario con identificadores de lote como claves y objetos Batch como valores.

    Ejemplo
    -------
    >>> batches = get_batches_from_stocks()
    >>> for batch_id, batch in batches.items():
    ...     print(f"Batch ID: {batch_id}, Batch: {batch}")
    """

    path = stocks_path
    sheet = stocks_sheet
    df = pd.read_excel(path, sheet_name=sheet, skiprows=skip_rows)
    dataframe = df.dropna(subset=[config.batches.columns.guide_column])

    clients_number_code = [
        col
        for col in dataframe.columns
        if str(col).isdigit()
        and str(col).isdigit() != "0"
    ]

    batches = {
        str(dataframe[config.batches.columns.guide_column][row]): Batch(
            center_name=dataframe[config.batches.columns.center_name][row],
            mill=dataframe[config.batches.columns.mill][row],
            shipping_date=dataframe[config.batches.columns.ship_date][row],
            batch_id=dataframe[config.batches.columns.batch_id][row],
            product_id=dataframe[config.batches.columns.product_id][row],
            arrived_mass=dataframe[config.batches.columns.arrived_mass][row],
            mass_in_transit=dataframe[config.batches.columns.mass_in_transit][row],
            sellable_clients={
                int(client_number_code):
                    any(
                        character.isdigit()
                        for character in str(dataframe[client_number_code][row])
                    )
                for client_number_code in clients_number_code
            }
        )
        for row in range(len(dataframe[config.batches.columns.guide_column]))
    }

    return batches


if __name__ == "__main__":
    data = get_batches_from_stocks()
    print(data)

    for entry in data:
        print(entry, data[entry])
