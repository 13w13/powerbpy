'''Multi-row card visual for Power BI dashboards.
    Use the add_multi_row_card() method on a _Page instance.
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


class _MultiRowCard(_Visual):
    """Multi-row card — displays multiple fields as card rows.

    Each field in the Values role becomes a row in the card.
    Fields can be raw columns (with aggregation) or DAX measures.
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
                 fields,
                 x_position,
                 y_position,
                 height,
                 width,
                 tab_order,
                 z_position,
                 parent_group_id,
                 background_color,
                 background_color_alpha,
                 alt_text="A multi-row card",
                 title_font_color=None,
                 title_font_family=None,
                 title_bold=None,
                 border_color=None,
                 border_width=None):
        '''
        Parameters
        ----------
        fields : list of dict
            Each dict describes a field to show. Two formats:
            - Column with aggregation: {"column": "colony_n", "aggregation": "Sum"}
            - DAX measure: {"measure": "Total Colonies"}
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
        self.visual_json["visual"]["visualType"] = "multiRowCard"

        # Build projections from fields list
        projections = []
        for field_def in fields:
            if "measure" in field_def:
                # DAX measure reference
                measure_name = field_def["measure"]
                projections.append({
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
                # Column with aggregation
                col_name = field_def["column"]
                agg_type = field_def.get("aggregation", "Sum")
                func_code = _AGGREGATION_FUNCTION_CODES.get(agg_type, 0)
                projections.append({
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

        self.visual_json["visual"]["query"] = {
            "queryState": {
                "Values": {
                    "projections": projections
                }
            },
            "sortDefinition": {
                "isDefaultSort": True
            }
        }

        # Write out the json
        with open(self.visual_json_path, "w", encoding="utf-8") as file:
            json.dump(self.visual_json, file, indent=2)
