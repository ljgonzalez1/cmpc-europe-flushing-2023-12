import pandas as pd

def leer_excel_a_dataframe(ruta_archivo, nombre_hoja):
    df = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja, skiprows=2)
    return df

# Ejemplo de uso
ruta_archivo = "ruta/a/tu/archivo.xlsx"
nombre_hoja = "Nombre de Hoja"
dataframe = leer_excel_a_dataframe(ruta_archivo, nombre_hoja)

print(dataframe)
