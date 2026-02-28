'''Treemap visual for Power BI dashboards.
    Use the add_treemap() method on a _Page instance.
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

class _Treemap(_Visual):
    """Treemap visual — uses Group + Values query roles."""

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
                 group_var,
                 value_var,
                 value_aggregation_type,
                 x_position,
                 y_position,
                 height,
                 width,
                 tab_order,
                 z_position,
                 parent_group_id,
                 background_color,
                 background_color_alpha,
                 alt_text="A treemap",
                 detail_var=None,
                 show_data_labels=False,
                 title_font_color=None,
                 title_font_family=None,
                 title_bold=None,
                 border_color=None,
                 border_width=None):

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
        self.visual_json["visual"]["visualType"] = "treemap"

        # Build query — treemap uses "Group" + "Values" roles
        query_state = {
            "Group": {
                "projections": [
                    {
                        "field": {
                            "Column": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": group_var
                            }
                        },
                        "queryRef": f"{data_source}.{group_var}",
                        "nativeQueryRef": group_var,
                        "active": True
                    }
                ]
            },
            "Values": {
                "projections": [
                    {
                        "field": {
                            "Aggregation": {
                                "Expression": {
                                    "Column": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": data_source
                                            }
                                        },
                                        "Property": value_var
                                    }
                                },
                                "Function": _AGGREGATION_FUNCTION_CODES.get(value_aggregation_type, 0)
                            }
                        },
                        "queryRef": f"{value_aggregation_type}({data_source}.{value_var})",
                        "nativeQueryRef": f"{value_aggregation_type} of {value_var}"
                    }
                ]
            }
        }

        # Optional Details role (sub-category for drill-down)
        if detail_var is not None:
            query_state["Details"] = {
                "projections": [
                    {
                        "field": {
                            "Column": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": detail_var
                            }
                        },
                        "queryRef": f"{data_source}.{detail_var}",
                        "nativeQueryRef": detail_var,
                        "active": True
                    }
                ]
            }

        self.visual_json["visual"]["query"] = {
            "queryState": query_state,
            "sortDefinition": {
                "sort": [
                    {
                        "field": {
                            "Aggregation": {
                                "Expression": {
                                    "Column": {
                                        "Expression": {
                                            "SourceRef": {
                                                "Entity": data_source
                                            }
                                        },
                                        "Property": value_var
                                    }
                                },
                                "Function": _AGGREGATION_FUNCTION_CODES.get(value_aggregation_type, 0)
                            }
                        },
                        "direction": "Descending"
                    }
                ],
                "isDefaultSort": True
            }
        }

        # Data labels
        if show_data_labels:
            self.visual_json["visual"]["objects"]["labels"] = [
                {
                    "properties": {
                        "show": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        }
                    }
                }
            ]

        # Write out the json
        with open(self.visual_json_path, "w", encoding="utf-8") as file:
            json.dump(self.visual_json, file, indent=2)
