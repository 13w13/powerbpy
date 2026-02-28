'''Matrix (pivot table) visual for Power BI dashboards.
    Use the add_matrix() method on a _Page instance.
'''

import json

from powerbpy.visual import _Visual

# Power BI SQExpr aggregation Function codes
_AGGREGATION_FUNCTION_CODES = {
    "Sum": 0,
    "Min": 1,
    "Max": 2,
    "Count": 3,
    "LongCount": 4,
    "DistinctCount": 5,
    "CountDistinct": 5,
    "Average": 6,
    "Avg": 6,
}


class _Matrix(_Visual):
    """Matrix (pivot table) visual — Rows + Columns + Values.

    Each role accepts multiple fields. Values can be measures or columns
    with aggregation (same dict format as multi_row_card).
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments
    # pylint: disable=duplicate-code

    def __init__(self,
                 page,
                 *,
                 visual_id,
                 data_source,
                 visual_title,
                 rows,
                 values,
                 x_position,
                 y_position,
                 height,
                 width,
                 tab_order,
                 z_position,
                 parent_group_id,
                 background_color,
                 background_color_alpha,
                 alt_text="A matrix",
                 columns=None,
                 title_font_color=None,
                 title_font_family=None,
                 title_bold=None,
                 border_color=None,
                 border_width=None):
        '''
        Parameters
        ----------
        rows : list of dict
            Row grouping fields. Each dict: {"column": "col_name"}.
        values : list of dict
            Value fields. Two formats:
            - Measure: {"measure": "Total Colonies"}
            - Column with aggregation: {"column": "col", "aggregation": "Sum"}
        columns : list of dict, optional
            Column pivot fields. Each dict: {"column": "col_name"}.
        '''

        super().__init__(page=page,
                  visual_id=visual_id,
                  visual_title=visual_title,
                  height=height,
                  width=width,
                  x_position=x_position,
                  y_position=y_position,
                  z_position=z_position,
                  tab_order=tab_order,
                  parent_group_id=parent_group_id,
                  alt_text=alt_text,
                  background_color=background_color,
                  background_color_alpha=background_color_alpha,
                  title_font_color=title_font_color,
                  title_font_family=title_font_family,
                  title_bold=title_bold,
                  border_color=border_color,
                  border_width=border_width)

        # Set visual type
        self.visual_json["visual"]["visualType"] = "pivotTable"

        # Build Rows projections (Column references)
        row_projections = []
        for field_def in rows:
            col_name = field_def["column"]
            row_projections.append({
                "field": {
                    "Column": {
                        "Expression": {
                            "SourceRef": {
                                "Entity": data_source
                            }
                        },
                        "Property": col_name
                    }
                },
                "queryRef": f"{data_source}.{col_name}",
                "nativeQueryRef": col_name,
                "active": True
            })

        # Build Values projections (Measure or Aggregation)
        value_projections = []
        for field_def in values:
            if "measure" in field_def:
                measure_name = field_def["measure"]
                value_projections.append({
                    "field": {
                        "Measure": {
                            "Expression": {
                                "SourceRef": {
                                    "Entity": data_source
                                }
                            },
                            "Property": measure_name
                        }
                    },
                    "queryRef": f"{data_source}.{measure_name}",
                    "nativeQueryRef": measure_name
                })
            elif "column" in field_def:
                col_name = field_def["column"]
                agg_type = field_def.get("aggregation", "Sum")
                func_code = _AGGREGATION_FUNCTION_CODES.get(agg_type, 0)
                value_projections.append({
                    "field": {
                        "Aggregation": {
                            "Expression": {
                                "Column": {
                                    "Expression": {
                                        "SourceRef": {
                                            "Entity": data_source
                                        }
                                    },
                                    "Property": col_name
                                }
                            },
                            "Function": func_code
                        }
                    },
                    "queryRef": f"{agg_type}({data_source}.{col_name})",
                    "nativeQueryRef": f"{agg_type} of {col_name}"
                })

        query_state = {
            "Rows": {
                "projections": row_projections
            },
            "Values": {
                "projections": value_projections
            }
        }

        # Optional Columns pivot
        if columns is not None:
            col_projections = []
            for field_def in columns:
                col_name = field_def["column"]
                col_projections.append({
                    "field": {
                        "Column": {
                            "Expression": {
                                "SourceRef": {
                                    "Entity": data_source
                                }
                            },
                            "Property": col_name
                        }
                    },
                    "queryRef": f"{data_source}.{col_name}",
                    "nativeQueryRef": col_name,
                    "active": True
                })
            query_state["Columns"] = {
                "projections": col_projections
            }

        self.visual_json["visual"]["query"] = {
            "queryState": query_state,
            "sortDefinition": {
                "isDefaultSort": True
            }
        }

        # Write out the json
        with open(self.visual_json_path, "w", encoding="utf-8") as file:
            json.dump(self.visual_json, file, indent=2)
