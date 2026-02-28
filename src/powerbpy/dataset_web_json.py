'''Dataset class for JSON API sources (Web.Contents + Json.Document).

Connects Power BI to any REST API that returns a JSON array of objects.
Uses a sample CSV for column type detection, but generates M code that
fetches data from the API URL at refresh time.

Authentication is handled by Power BI's credential manager — on first
refresh, PBI Desktop prompts for credentials (Basic, OAuth2, API Key, etc.).

You should never call this class directly; use Dashboard.add_web_json().
'''

import uuid

import pandas as pd  # pylint: disable=import-error

from powerbpy.data_set import _DataSet


class _WebJson(_DataSet):

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
            Name for the table in the Power BI model (e.g. "syr_rehab_assessment").
        url : str
            Full API endpoint URL. Must return a JSON array of objects.
            Example: "https://server.surveycto.com/api/v2/forms/data/wide/json/form_id?date=0"
        sample_csv_path : str
            Path to a sample CSV file used to detect column names and types.
            The CSV is NOT included in the dashboard — only used for schema inference.
        type_transforms : list of dict, optional
            Custom M code type transforms applied after JSON expansion.
            Each dict: {"step_name": str, "columns": [{"name": str, "type": str}]}
            where type is a Power Query type: "type number", "type text",
            "type date", "type datetimezone", etc.
            If not provided, transforms are auto-generated from the sample CSV types.
        encoding : str
            Encoding for reading the sample CSV. Default "utf-8".
        '''

        import os

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
        '''Auto-generate M code type transform steps from pandas dtypes.

        Returns a list of transform step dicts that can be written as M code.
        Groups columns by target PQ type to minimize the number of steps.
        '''
        date_cols = []
        number_cols = []

        for col in self.dataset.columns:
            dtype = str(self.dataset[col].dtype)
            if "datetime" in dtype:
                date_cols.append(col)
            elif dtype in ("int64", "float64"):
                number_cols.append(col)
            # strings don't need transforms — PQ default is text

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
