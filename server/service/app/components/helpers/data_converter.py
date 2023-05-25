import pandas as pd
import datetime


def convert(
        data: list[dict],
        file_path: str,
        header_list: list = None,
        index: str = None,
        in_format: str = 'xlsx'
) -> str:
    if file_path is None or data is None or len(data) == 0:
        return ''

    file_name = '{date:%Y-%m-%d_%H-%M-%S}'.format(date=datetime.datetime.now())

    file = file_path + file_name + '.' + in_format if in_format is not None else 'xlsx'

    df = pd.DataFrame(data)
    if header_list is not None and len(header_list) > 0:
        df.columns = header_list

    if index is not None:
        df.index = df[index]
        df.drop(index, axis=1, inplace=True)

    if in_format == 'csv':
        df.to_csv(file)
    elif in_format == 'html':
        df.to_html(file)
    else:
        df.to_excel(file)

    return file
