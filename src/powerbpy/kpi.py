'''KPI visual for Power BI dashboards.
    Use the add_kpi() method on a _Page instance.
'''

import json
import uuid

from powerbpy.visual import _Visual


class _Kpi(_Visual):
    """KPI visual — indicator value + optional goal + optional trend line."""

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
                 alt_text="A KPI",
                 goal_measure=None,
                 trend_column=None,
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
        self.visual_json["visual"]["visualType"] = "kpi"

        # Build query — KPI uses "Indicator" + "Goal" + "TrendLine"
        # Role names reverse-engineered from PBI Desktop .pbip output
        indicator_field = {
            "Measure": {
                "Expression": {
                    "SourceRef": {
                        "Entity": data_source
                    }
                },
                "Property": measure_name
            }
        }
        query_state = {
            "Indicator": {
                "projections": [
                    {
                        "field": indicator_field,
                        "queryRef": f"{data_source}.{measure_name}",
                        "nativeQueryRef": measure_name
                    }
                ]
            }
        }

        # filterConfig — PBI requires an Advanced filter entry per field
        filters = [
            {
                "name": uuid.uuid4().hex[:20],
                "field": indicator_field,
                "type": "Advanced"
            }
        ]

        # Optional Goal (target measure)
        if goal_measure is not None:
            goal_field = {
                "Measure": {
                    "Expression": {
                        "SourceRef": {
                            "Entity": data_source
                        }
                    },
                    "Property": goal_measure
                }
            }
            query_state["Goal"] = {
                "projections": [
                    {
                        "field": goal_field,
                        "queryRef": f"{data_source}.{goal_measure}",
                        "nativeQueryRef": goal_measure
                    }
                ]
            }
            filters.append({
                "name": uuid.uuid4().hex[:20],
                "field": goal_field,
                "type": "Advanced"
            })

        # Optional TrendLine (date/time column)
        if trend_column is not None:
            trend_field = {
                "Column": {
                    "Expression": {
                        "SourceRef": {
                            "Entity": data_source
                        }
                    },
                    "Property": trend_column
                }
            }
            query_state["TrendLine"] = {
                "projections": [
                    {
                        "field": trend_field,
                        "queryRef": f"{data_source}.{trend_column}",
                        "nativeQueryRef": trend_column
                    }
                ]
            }
            filters.append({
                "name": uuid.uuid4().hex[:20],
                "field": trend_field,
                "type": "Advanced"
            })

        # KPI has NO sortDefinition (unlike other visuals)
        self.visual_json["visual"]["query"] = {
            "queryState": query_state
        }

        # Add filterConfig
        self.visual_json["filterConfig"] = {
            "filters": filters
        }

        # Write out the json
        with open(self.visual_json_path, "w", encoding="utf-8") as file:
            json.dump(self.visual_json, file, indent=2)
