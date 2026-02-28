'''Scatter/Bubble chart visual for Power BI dashboards.
    Use the add_scatter() method on a _Page instance.
'''

import json

from powerbpy.visual import _Visual


class _Scatter(_Visual):
    """Scatter/Bubble chart — X measure, Y measure, Category (details), optional Size."""

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
                 x_measure,
                 y_measure,
                 x_position,
                 y_position,
                 height,
                 width,
                 tab_order,
                 z_position,
                 parent_group_id,
                 background_color,
                 background_color_alpha,
                 alt_text="A scatter chart",
                 category_column=None,
                 size_measure=None,
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
        self.visual_json["visual"]["visualType"] = "scatterChart"

        # Build query — scatter uses X + Y (both Measures) + Category + Size
        query_state = {
            "X": {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": x_measure
                            }
                        },
                        "queryRef": f"{data_source}.{x_measure}",
                        "nativeQueryRef": x_measure
                    }
                ]
            },
            "Y": {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": y_measure
                            }
                        },
                        "queryRef": f"{data_source}.{y_measure}",
                        "nativeQueryRef": y_measure
                    }
                ]
            }
        }

        # Optional Category (column identifying each point)
        if category_column is not None:
            query_state["Category"] = {
                "projections": [
                    {
                        "field": {
                            "Column": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": category_column
                            }
                        },
                        "queryRef": f"{data_source}.{category_column}",
                        "nativeQueryRef": category_column,
                        "active": True
                    }
                ]
            }

        # Optional Size (bubble size measure)
        if size_measure is not None:
            query_state["Size"] = {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": size_measure
                            }
                        },
                        "queryRef": f"{data_source}.{size_measure}",
                        "nativeQueryRef": size_measure
                    }
                ]
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
