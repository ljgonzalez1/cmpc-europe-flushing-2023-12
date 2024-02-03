import tables
from pandas import ExcelWriter

raw_data = tables.get_raw_data()
request_data_dict = raw_data["requests"]
batches_data_dict = raw_data["batches"]
importance_data_dict = raw_data["importance"]

sales_table = tables.get_sales_table(request_data_dict)
client_locations_table = tables.get_clients_locations_table(request_data_dict)
clients_data_table = tables.get_clients_data_table(batches_data_dict, request_data_dict)
clients_priorities_table = tables.get_clients_priorities_table(batches_data_dict, request_data_dict, importance_data_dict)
batches_volumes_table = tables.get_batches_volumes_table(batches_data_dict)
batches_locations_table = tables.get_batches_locations_table(batches_data_dict)
compatibility_client_batch_table = tables.get_compatibility_client_batch_table(batches_data_dict, request_data_dict)

with ExcelWriter('tablas.xlsx') as writer:
    # Guarda cada DataFrame en una hoja diferente
    sales_table.to_excel(writer, sheet_name='Ventas', index=False)
    client_locations_table.to_excel(writer, sheet_name='Ubicaciones_Clientes', index=False)
    clients_data_table.to_excel(writer, sheet_name='Datos_Clientes', index=False)
    clients_priorities_table.to_excel(writer, sheet_name='Prioridades_Clientes', index=False)
    batches_volumes_table.to_excel(writer, sheet_name='Volúmenes_Lotes', index=False)
    batches_locations_table.to_excel(writer, sheet_name='Ubicaciones_Lotes', index=False)
    compatibility_client_batch_table.to_excel(writer, sheet_name='Compatibilidad_Cliente_Lote', index=False)