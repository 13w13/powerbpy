"""A class representing Deneb (Vega/Vega-Lite) visuals in Power BI"""

import json

from powerbpy.visual import _Visual


# Aggregation function codes used by Power BI query model
_AGG_FUNCTIONS = {
    "Sum": 0,
    "Count": 1,
    "Min": 2,
    "Max": 3,
    "Average": 4,
    "CountNonNull": 5,
}

DENEB_VISUAL_TYPE = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"


class _Deneb(_Visual):
    """A class representing Deneb (Vega/Vega-Lite) custom visuals.

    Deneb lets you write Vega or Vega-Lite specifications directly inside
    Power BI.  This class generates the visual.json that PBI Desktop
    expects when it opens a .pbip project containing a Deneb visual.
    """

    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-arguments

    def __init__(
        self,
        page,
        *,
        visual_id,
        data_source,
        spec,
        columns=None,
        measures=None,
        dax_measures=None,
        provider="vegaLite",
        vega_config=None,
        render_mode="svg",
        enable_tooltips=True,
        enable_context_menu=True,
        enable_highlight=True,
        enable_selection=True,
        selection_mode="simple",
        x_position,
        y_position,
        height,
        width,
        chart_title=None,
        chart_title_font_size=17,
        parent_group_id=None,
        background_color=None,
        background_color_alpha=None,
        title_font_color=None,
        title_font_family=None,
        title_bold=None,
        border_color=None,
        border_width=None,
        tooltip_page=None,
        tab_order=-1001,
        z_position=6000,
        alt_text="A Deneb visualization",
    ):
        """Create a Deneb visual on a Power BI page.

        Data binding
        ------------
        Power BI pre-aggregates data before sending it to Deneb.  The
        visual receives a flat table where each row is a unique
        combination of all dimension values, with measures already
        aggregated.  This table is exposed to the Vega/Vega-Lite spec
        as a named dataset called ``"dataset"``.

        **Critical**: the ``"field"`` references in your Vega spec must
        match the ``nativeQueryRef`` exactly:

        - *columns* → ``nativeQueryRef`` = column name as-is
        - *measures (3-tuple)* → ``nativeQueryRef`` = ``display_name``
        - *measures (2-tuple)* → ``nativeQueryRef`` = ``"{agg} of {col}"``

        Always prefer the 3-tuple form so field names are predictable.

        Deneb auto-injects metadata fields: ``__row__`` (row index),
        ``__selected__`` (``"on"``/``"off"``/``"neutral"`` for cross-
        filter), and per-measure ``__highlight``/``__highlightStatus``/
        ``__highlightComparator`` fields for cross-highlighting.

        Do NOT re-aggregate in the spec (no ``"aggregate": "sum"`` in
        encoding) — PBI already did it.  Transforms like ``aggregate``,
        ``fold``, ``pivot``, ``window`` break cross-filter because they
        destroy row context.

        Parameters
        ----------
        visual_id : str
            Unique identifier for this visual.
        data_source : str
            Name of the Power BI table to bind data from.
        spec : dict
            A Vega or Vega-Lite specification as a Python dictionary.
            This is serialised to JSON and stored inside the visual.
            If ``"data"`` is not present, ``{"name": "dataset"}`` is
            injected automatically so Deneb can read PBI data.
        columns : list of str, optional
            Column names from *data_source* to add to the Deneb "dataset"
            data role.  These appear as grouping dimensions.  The column
            name becomes the ``nativeQueryRef`` — use the same string
            as the ``"field"`` in your Vega spec.
        measures : list of tuple, optional
            Each element is a 2-tuple ``(column_name, aggregation)`` or a
            3-tuple ``(column_name, aggregation, display_name)``.

            *aggregation* is one of ``"Sum"``, ``"Count"``, ``"Min"``,
            ``"Max"``, ``"Average"``, ``"CountNonNull"``.

            *display_name* (3rd element) controls the ``nativeQueryRef``
            — the field name Deneb sees.  **Use the same string as the
            ``"field"`` reference in your Vega spec.**  If omitted
            (2-tuple), defaults to ``"{agg} of {column}"``.

            Note: Power BI Desktop may ignore the aggregation function
            and ``nativeQueryRef`` from the projection, using the column's
            ``summarizeBy`` from TMDL instead and generating its own
            display name.  Prefer ``dax_measures`` for reliable naming.
        dax_measures : list of str, optional
            Names of DAX measures defined in *data_source* (via
            ``dataset.add_measure()``).  Each name becomes both the
            ``queryRef`` and ``nativeQueryRef`` — use the same string
            as the ``"field"`` reference in your Vega spec.

            This is the **recommended** approach for Deneb measures
            because PBI always respects DAX measure names, unlike
            aggregated columns where PBI may override the display name.
        provider : str
            ``"vegaLite"`` (default) or ``"vega"``.
        vega_config : dict, optional
            A Vega/Vega-Lite config object (theming, defaults).
        render_mode : str
            ``"svg"`` (default, sharper) or ``"canvas"`` (faster, use
            for >10K data points).
        enable_tooltips : bool
            Enable Power BI tooltip integration.  Default ``True``.
        enable_context_menu : bool
            Enable right-click context menu.  Default ``True``.
        enable_highlight : bool
            Enable cross-highlight support.  Default ``True``.
        enable_selection : bool
            Enable cross-filter/selection support.  Default ``True``.
        selection_mode : str
            ``"simple"`` (default) or ``"advanced"``.
        chart_title : str, optional
            Title shown above the visual.
        chart_title_font_size : int
            Font size for the title.  Default 17.
        x_position, y_position : int
            Top-left position on the page (in pixels).
        height, width : int
            Dimensions of the visual (in pixels).
        """

        super().__init__(
            page=page,
            visual_id=visual_id,
            visual_title=chart_title,
            visual_title_font_size=chart_title_font_size,
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
            border_width=border_width,
            tooltip_page=tooltip_page,
        )

        # --- visual type & schema ------------------------------------------
        self.visual_json["visual"]["visualType"] = DENEB_VISUAL_TYPE
        self.visual_json["$schema"] = (
            "https://developer.microsoft.com/json-schemas/fabric/"
            "item/report/definition/visualContainer/2.3.0/schema.json"
        )

        # --- query: bind columns/measures to the "dataset" data role -------
        projections = []

        if columns:
            for col in columns:
                projections.append(
                    {
                        "field": {
                            "Column": {
                                "Expression": {
                                    "SourceRef": {"Entity": data_source}
                                },
                                "Property": col,
                            }
                        },
                        "queryRef": f"{data_source}.{col}",
                        "nativeQueryRef": col,
                        "active": True,
                    }
                )

        if measures:
            for measure in measures:
                if len(measure) == 3:
                    col_name, agg_type, display_name = measure
                elif len(measure) == 2:
                    col_name, agg_type = measure
                    display_name = f"{agg_type} of {col_name}"
                else:
                    raise ValueError(
                        "Each measure must be a 2-tuple (column, agg) "
                        "or 3-tuple (column, agg, display_name)"
                    )

                agg_code = _AGG_FUNCTIONS.get(agg_type)
                if agg_code is None:
                    raise ValueError(
                        f"Unknown aggregation '{agg_type}'. "
                        f"Choose from: {list(_AGG_FUNCTIONS.keys())}"
                    )
                projections.append(
                    {
                        "field": {
                            "Aggregation": {
                                "Expression": {
                                    "Column": {
                                        "Expression": {
                                            "SourceRef": {"Entity": data_source}
                                        },
                                        "Property": col_name,
                                    }
                                },
                                "Function": agg_code,
                            }
                        },
                        "queryRef": f"{agg_type}({data_source}.{col_name})",
                        "nativeQueryRef": display_name,
                        "active": True,
                    }
                )

        if dax_measures:
            for measure_name in dax_measures:
                projections.append(
                    {
                        "field": {
                            "Measure": {
                                "Expression": {
                                    "SourceRef": {"Entity": data_source}
                                },
                                "Property": measure_name,
                            }
                        },
                        "queryRef": f"{data_source}.{measure_name}",
                        "nativeQueryRef": measure_name,
                        "active": True,
                    }
                )

        if projections:
            self.visual_json["visual"]["query"] = {
                "queryState": {
                    "dataset": {"projections": projections}
                }
            }

        # --- objects: Deneb stores everything under "vega" -----------------
        # Deneb requires "data": {"name": "dataset"} in the spec so that
        # the Vega runtime reads rows from the Power BI data role.
        # Inject it automatically if the user didn't include it.
        spec = dict(spec)  # shallow copy to avoid mutating caller's dict
        if "data" not in spec:
            spec["data"] = {"name": "dataset"}

        spec_json = json.dumps(spec, ensure_ascii=False)
        config_json = json.dumps(vega_config or {}, ensure_ascii=False)

        vega_props = {
            "provider": {
                "expr": {"Literal": {"Value": f"'{provider}'"}}
            },
            "jsonSpec": {
                "expr": {"Literal": {"Value": f"'{spec_json}'"}}
            },
            "jsonConfig": {
                "expr": {"Literal": {"Value": f"'{config_json}'"}}
            },
            "isNewDialogOpen": {
                "expr": {"Literal": {"Value": "false"}}
            },
            "enableTooltips": {
                "expr": {
                    "Literal": {
                        "Value": "true" if enable_tooltips else "false"
                    }
                }
            },
            "enableContextMenu": {
                "expr": {
                    "Literal": {
                        "Value": "true" if enable_context_menu else "false"
                    }
                }
            },
            "enableHighlight": {
                "expr": {
                    "Literal": {
                        "Value": "true" if enable_highlight else "false"
                    }
                }
            },
            "enableSelection": {
                "expr": {
                    "Literal": {
                        "Value": "true" if enable_selection else "false"
                    }
                }
            },
            "selectionMaxDataPoints": {
                "expr": {"Literal": {"Value": "50D"}}
            },
            "selectionMode": {
                "expr": {"Literal": {"Value": f"'{selection_mode}'"}}
            },
            "renderMode": {
                "expr": {"Literal": {"Value": f"'{render_mode}'"}}
            },
        }

        self.visual_json["visual"]["objects"]["vega"] = [
            {"properties": vega_props}
        ]

        # Deneb developer metadata (visual version)
        self.visual_json["visual"]["objects"]["developer"] = [
            {
                "properties": {
                    "version": {
                        "expr": {"Literal": {"Value": "'1.9.0.0'"}}
                    }
                }
            }
        ]

        # --- register the custom visual GUID in report.json ---------------
        self.dashboard._register_custom_visual(DENEB_VISUAL_TYPE)

        # --- write visual.json ---------------------------------------------
        with open(self.visual_json_path, "w", encoding="utf-8") as file:
            json.dump(self.visual_json, file, indent=2)
