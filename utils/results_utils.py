import pandas
from io import BytesIO


def convert_list_of_dict_to_json(data_list, drop_columns=None):
    df = pandas.DataFrame(data_list)
    if data_list:
        df = df[list(data_list[0].keys())]
        if drop_columns:
            df = df.drop(columns=drop_columns)
    return df.to_json()

def convert_list_of_dict_to_excel_table(data_list, drop_columns=None):
    df = pandas.DataFrame(data_list)
    if data_list:
        df = df[list(data_list[0].keys())]
        if drop_columns:
            df = df.drop(columns=drop_columns)
    output = BytesIO()
    with pandas.ExcelWriter(output) as writer:
        df.to_excel(writer)
    output.seek(0)
    return output


def convert_list_of_dict_to_csv(data_list, drop_columns=None):
    df = pandas.DataFrame(data_list)
    if data_list:
        df = df[list(data_list[0].keys())]
        if drop_columns:
            df = df.drop(columns=drop_columns)
    output = BytesIO()
    df.to_csv(output)
    output.seek(0)
    return output
