import pandas as pd


def leer_excel_a_dataframe(ruta_archivo, nombre_hoja):
    df = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja, skiprows=1)
    return df


if __name__ == "__main__":
    # Ejemplo de uso
    ruta_archivo = "/home/luis/git/cmpc-europe-flushing-2023-12/STOCK.xlsx"
    nombre_hoja = "Format"
    dataframe = leer_excel_a_dataframe(ruta_archivo, nombre_hoja)

    print(dataframe)
