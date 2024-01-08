def excel2dataframe(file_path, sheet_name, skip_rows=0):
    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip_rows)
    return df