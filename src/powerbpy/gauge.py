'''Gauge visual for Power BI dashboards.
    Use the add_gauge() method on a _Page instance.
'''

import json

from powerbpy.visual import _Visual


class _Gauge(_Visual):
    """Gauge visual — uses Value (measure) + optional TargetValue, MinValue, MaxValue."""

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
                 measure_name,
                 x_position,
                 y_position,
                 height,
                 width,
                 tab_order,
                 z_position,
                 parent_group_id,
                 background_color,
                 background_color_alpha,
                 alt_text="A gauge",
                 target_measure=None,
                 min_value=None,
                 max_value=None,
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
        self.visual_json["visual"]["visualType"] = "gauge"

        # Build query — gauge uses "Y" role internally (PBI UI labels it "Value")
        query_state = {
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
                                "Property": measure_name
                            }
                        },
                        "queryRef": f"{data_source}.{measure_name}",
                        "nativeQueryRef": measure_name
                    }
                ]
            }
        }

        # Optional TargetValue (target line on the gauge)
        if target_measure is not None:
            query_state["TargetValue"] = {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": target_measure
                            }
                        },
                        "queryRef": f"{data_source}.{target_measure}",
                        "nativeQueryRef": target_measure
                    }
                ]
            }

        # Optional MinValue
        if min_value is not None:
            query_state["MinValue"] = {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": min_value
                            }
                        },
                        "queryRef": f"{data_source}.{min_value}",
                        "nativeQueryRef": min_value
                    }
                ]
            }

        # Optional MaxValue
        if max_value is not None:
            query_state["MaxValue"] = {
                "projections": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {
                                        "Entity": data_source
                                    }
                                },
                                "Property": max_value
                            }
                        },
                        "queryRef": f"{data_source}.{max_value}",
                        "nativeQueryRef": max_value
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
