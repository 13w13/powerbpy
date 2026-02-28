'''Dataset classes for web-based data sources.

Two classes:
- _WebCsv: for APIs returning CSV (e.g. SurveyCTO /datasets/data/csv/)
  Uses Csv.Document(Web.Contents(url)) — same pattern PBI Desktop generates.
- _WebJson: for APIs returning JSON arrays (e.g. SurveyCTO /forms/data/wide/json/)
  Uses Json.Document(Web.Contents(url)) with record expansion.

Authentication is handled by Power BI's credential manager — on first
refresh, PBI Desktop prompts for credentials (Basic, OAuth2, API Key, etc.).

You should never call these classes directly; use Dashboard.add_web_csv()
or Dashboard.add_web_json().
'''

import os

import pandas as pd  # pylint: disable=import-error

from powerbpy.data_set import _DataSet
from powerbpy.dataset_csv import _ENCODING_CODES


class _WebCsv(_DataSet):
    '''Dataset connected to a CSV API endpoint.

    Generates Csv.Document(Web.Contents(url)) M code — the exact same
    pattern Power BI Desktop produces when you use Get Data → Web on a
    CSV endpoint. Reuses the same Promoted Headers / Changed Type steps
    as local CSV files.
    '''

    # pylint: disable=too-many-arguments

    def __init__(self,
                 dashboard,
                 table_name,
                 url,
                 sample_csv_path,
                 encoding="utf-8"):
        '''Create a dataset connected to a CSV API endpoint.

        Parameters
        ----------
        dashboard : Dashboard
            The parent dashboard instance.
        table_name : str
            Name for the table in the Power BI model.
        url : str
            Full API endpoint URL. Must return CSV data.
        sample_csv_path : str
            Path to a sample CSV for column type detection.
            The CSV data is NOT included in the dashboard.
        encoding : str
            Encoding for reading the sample CSV and for the PQ encoding
            parameter. Default "utf-8".
        '''

        # Build a fake path so _DataSet derives dataset_name = table_name
        fake_path = os.path.join(
            os.path.dirname(os.path.abspath(sample_csv_path)),
            f"{table_name}.csv"
        )
        super().__init__(dashboard, fake_path)

        self.url = url
        self.pq_encoding = _ENCODING_CODES.get(encoding.lower(), 65001)

        # Load sample CSV for column detection
        self.dataset = pd.read_csv(sample_csv_path, encoding=encoding)

        # Build TMDL column definitions (reuses parent's method)
        self._create_tmdl()

        # Write M code — same as _LocalCsv but Web.Contents instead of File.Contents
        replacement_values = '", "'.join(self.col_attributes["col_names"])
        formatted_column_details = ', '.join(map(str, self.col_attributes["col_deets"]))

        with open(self.dataset_file_path, 'a', encoding="utf-8") as file:
            file.write(f'\tpartition {self.dataset_name} = m\n')
            file.write('\t\tmode: import\n\t\tsource =\n\t\t\t\tlet\n')
            file.write(f'\t\t\t\t\tSource = Csv.Document(Web.Contents("{self.url}"),'
                        f'[Delimiter=",", Columns={len(self.dataset.columns)}, '
                        f'Encoding={self.pq_encoding}, QuoteStyle=QuoteStyle.Csv]),\n')
            file.write('\t\t\t\t\t#"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n')
            file.write(f'\t\t\t\t\t#"Replaced Value" = Table.ReplaceValue(#"Promoted Headers","NA",null,Replacer.ReplaceValue,{{"{ replacement_values  }"}}),\n')
            file.write(f'\t\t\t\t\t#"Changed Type" = Table.TransformColumnTypes(#"Replaced Value",{{  {  formatted_column_details  }   }})\n')
            file.write('\t\t\t\tin\n\t\t\t\t\t#"Changed Type"\n\n')
            file.write('\tannotation PBI_ResultType = Table\n\n\tannotation PBI_NavigationStepName = Navigation\n\n')


class _WebJson(_DataSet):
    '''Dataset connected to a JSON API endpoint.

    Generates Json.Document(Web.Contents(url)) M code with automatic
    record expansion. Use for APIs that return a JSON array of objects.
    '''

    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 dashboard,
                 table_name,
                 url,
                 sample_csv_path,
                 type_transforms=None,
                 encoding="utf-8"):
        '''Create a dataset connected to a JSON API endpoint.

        Parameters
        ----------
        dashboard : Dashboard
            The parent dashboard instance.
        table_name : str
            Name for the table in the Power BI model.
        url : str
            Full API endpoint URL. Must return a JSON array of objects.
        sample_csv_path : str
            Path to a sample CSV for column type detection.
            The CSV data is NOT included in the dashboard.
        type_transforms : list of dict, optional
            Custom M code type transforms applied after JSON expansion.
            Each dict: {"step_name": str, "columns": [{"name": str, "type": str}]}
            If not provided, transforms are auto-generated from the sample CSV types.
        encoding : str
            Encoding for reading the sample CSV. Default "utf-8".
        '''

        # Build a fake path so _DataSet derives dataset_name = table_name
        fake_path = os.path.join(
            os.path.dirname(os.path.abspath(sample_csv_path)),
            f"{table_name}.csv"
        )
        super().__init__(dashboard, fake_path)

        self.url = url
        self.user_type_transforms = type_transforms

        # Load sample CSV for column detection
        self.dataset = pd.read_csv(sample_csv_path, encoding=encoding)

        # Build TMDL column definitions (reuses parent's method)
        self._create_tmdl()

        # Write the JSON API M code partition
        self._write_api_partition()


    def _auto_type_transforms(self):
        '''Auto-generate M code type transform steps from pandas dtypes.'''
        date_cols = []
        number_cols = []

        for col in self.dataset.columns:
            dtype = str(self.dataset[col].dtype)
            if "datetime" in dtype:
                date_cols.append(col)
            elif dtype in ("int64", "float64"):
                number_cols.append(col)

        transforms = []
        if date_cols:
            transforms.append({
                "step_name": "TypedDates",
                "columns": [{"name": c, "type": "type datetimezone"} for c in date_cols]
            })
        if number_cols:
            transforms.append({
                "step_name": "TypedNumbers",
                "columns": [{"name": c, "type": "type number"} for c in number_cols]
            })

        return transforms


    def _write_api_partition(self):
        '''Write the M code partition that fetches from the JSON API.'''

        transforms = self.user_type_transforms or self._auto_type_transforms()

        # Build M code steps
        steps = []
        steps.append(f'\t\t\t\t\turl = "{self.url}"')
        steps.append('\t\t\t\t\tSource = Json.Document(Web.Contents(url))')
        steps.append('\t\t\t\t\tToTable = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error)')
        steps.append('\t\t\t\t\tFirstRow = ToTable{0}[Column1]')
        steps.append('\t\t\t\t\tColumnNames = Record.FieldNames(FirstRow)')
        steps.append('\t\t\t\t\tExpanded = Table.ExpandRecordColumn(ToTable, "Column1", ColumnNames)')

        # Type transform steps
        prev_step = "Expanded"
        for t in transforms:
            step_name = t["step_name"]
            col_specs = ", ".join(
                f'{{"{c["name"]}", {c["type"]}}}'
                for c in t["columns"]
            )
            steps.append(
                f'\t\t\t\t\t{step_name} = Table.TransformColumnTypes({prev_step}, {{\n'
                f'\t\t\t\t\t\t{col_specs}\n'
                f'\t\t\t\t\t}})'
            )
            prev_step = step_name

        # Build the let...in block
        m_code_body = ",\n".join(steps)
        last_step = prev_step

        with open(self.dataset_file_path, 'a', encoding="utf-8") as file:
            file.write(f'\tpartition {self.dataset_name} = m\n')
            file.write('\t\tmode: import\n')
            file.write('\t\tsource =\n')
            file.write('\t\t\t\tlet\n')
            file.write(m_code_body + '\n')
            file.write('\t\t\t\tin\n')
            file.write(f'\t\t\t\t\t{last_step}\n\n')
            file.write('\tannotation PBI_ResultType = Table\n\n')
            file.write('\tannotation PBI_NavigationStepName = Navigation\n\n')
