#!/usr/bin/env python3

#%module
#% description: Adds the values of two rasters (A + B)
#% keyword: raster
#% keyword: algebra
#% keyword: sum
#%end
#%option G_OPT_V_INPUT
#%end
#%option G_OPT_F_OUTPUT
#%end
#%option G_OPT_DB_COLUMN
#% key: color_column
#% label: Column to be used for color
#%end
#%option G_OPT_DB_COLUMN
#% key: stroke_color_column
#% label: Column to be used for stroke color
#%end
#%option G_OPT_DB_COLUMN
#% key: height_column
#% label: Column to be used for height
#%end
#%option G_OPT_DB_COLUMNS
#%end
#%option
#% key: title
#% description: Title of the resulting map
#% answer: Generated by v.out.keplergl
#%end
#%option
#% key: zoom
#% label: Zoom level of the web map
#% description: Center of the map is determined from the computational region
#% answer: 5
#%end
#%option
#% key: label
#% label: Label of the data (layer)
#% description: Defaults to map title or name (TODO)
#%end
#%option G_OPT_F_INTPUT
#% key: style
#% label: JSON style of the layer
#%end

import sys
import json

from keplergl import KeplerGl
from in_place import InPlace

import grass.script as gs


def load_key_value_file(filename):
    """Load nested dict structure from a file.

    Supported formats are JSON, YAML, and Python literals.
    Formats are distinguised by extension.
    Extension for Python literals is `.py` or `.dict`.

    This function lazy imports all non-standard dependencies.
    """
    # We don't want to depend on the packages when we don't need them.
    # pylint: disable=import-outside-toplevel
    lower = filename.lower()
    if lower.endswith(".json"):
        import json

        with open(filename) as file:
            return json.loads(file.read())
    elif lower.endswith(".yaml") or lower.endswith(".yml"):
        import yaml

        with open(filename) as file:
            if hasattr(yaml, "full_load"):
                return yaml.full_load(file)
            return yaml.load(file)
    elif lower.endswith(".py") or lower.endswith(".dict"):
        import ast

        with open(filename) as file:
            return ast.literal_eval(file.read())


def create_base_configuration():
    return {
        "version": "v1",
        "config": {
            "visState": {
                "filters": [],
                "layers": [],
                "interactionConfig": {
                    "tooltip": {"fieldsToShow": {}, "enabled": True},
                    "brush": {"size": 0.5, "enabled": False},
                    "geocoder": {"enabled": False},
                    "coordinate": {"enabled": False},
                },
                "layerBlending": "normal",
                "splitMaps": [],
                "animationConfig": {"currentTime": None, "speed": 1},
            },
            "mapState": None,
            "mapStyle": {
                "styleType": "dark",
                "topLayerGroups": {},
                "visibleLayerGroups": {
                    "label": False,
                    "road": True,
                    "border": False,
                    "building": True,
                    "water": True,
                    "land": True,
                    "3d building": False,
                },
                "threeDBuildingColor": [
                    9.665468314072013,
                    17.18305478057247,
                    31.1442867897876,
                ],
                "mapStyles": {},
            },
        },
    }


def add_layer(config, data_id, label, visual_channels):
    layer = {
        "id": "m1vnv5v",
        "type": "geojson",
        "config": {
            "dataId": data_id,
            "label": label,
            "color": [136, 87, 44],
            "columns": {"geojson": "_geojson"},
            "isVisible": True,
            "visConfig": {},
            "hidden": False,
            "textLabel": [
                {
                    "field": None,
                    "color": [255, 255, 255],
                    "size": 18,
                    "offset": [0, 0],
                    "anchor": "start",
                    "alignment": "center",
                }
            ],
        },
        "visualChannels": visual_channels,
    }
    config["config"]["visState"]["layers"].append(layer)


def create_visual_channels(config, color_column, stroke_color_column, height_column):
    visual_channels = {
        "colorField": None,
        "colorScale": "quantize",
        "sizeField": None,
        "sizeScale": "linear",
        "strokeColorField": None,
        "strokeColorScale": "quantize",
        "heightField": None,
        "heightScale": "linear",
        "radiusField": None,
        "radiusScale": "linear",
    }
    if color_column:
        visual_channels["colorField"] = {"name": color_column, "type": "integer"}
    if stroke_color_column:
        visual_channels["strokeColorField"] = {
            "name": stroke_color_column,
            "type": "integer",
        }
    if height_column:
        visual_channels["heightField"] = {
            "name": height_column,
            "type": "integer",
        }
    return visual_channels


def add_map_state(config, zoom):
    center = gs.parse_command("g.region", flags="cg")
    longitude = float(center["center_easting"])
    latitude = float(center["center_northing"])

    map_state = {
        "bearing": 0,
        "dragRotate": False,
        "latitude": latitude,
        "longitude": longitude,
        "pitch": 0,
        "zoom": float(zoom),
        "isSplit": False,
    }
    config["config"]["mapState"] = map_state


def main():
    options, flags = gs.parser()
    vector_input = options["input"]
    output_html = options["output"]
    title = options["title"]

    # TODO: Use map name.
    data_id = vector_input.replace("@", "__at__")

    # TODO: Use map title if present, then map name as defaults.
    data_label = options["label"]

    config = create_base_configuration()

    visual_channels = create_visual_channels(
        config,
        color_column=options["color_column"],
        stroke_color_column=options["stroke_color_column"],
        height_column=options["height_column"],
    )

    add_layer(
        config, data_id=data_id, label=data_label, visual_channels=visual_channels
    )

    style_file = options["style"]
    if style_file:
        style = load_key_value_file(style_file)
        for key, value in style.items():
            # Assuming only one layer here.
            config["config"]["visState"]["layers"][0]["config"]["visConfig"][
                key
            ] = value

    # Maybe move to add_columns_to_show(config,... function.
    if options["columns"]:
        # TODO: Check for column presence is needed here. (parser does not know which map to check)
        show_columns = options["columns"].split(",")
    else:
        # TODO: Get all columns if needed to display all.
        show_columns = []
    config["config"]["visState"]["interactionConfig"]["tooltip"]["fieldsToShow"][
        data_id
    ] = show_columns

    add_map_state(config, zoom=options["zoom"])

    geojson_file = "/tmp/file.json"
    gs.run_command(
        "v.out.ogr",
        input=vector_input,
        output=geojson_file,
        format="GeoJSON",
        flags="s",
    )

    print("Using configuration (JSON syntax):")
    print(json.dumps(config, indent=2))
    kepler = KeplerGl(config=config)
    kepler.add_data(data=open(geojson_file).read(), name=data_id)
    kepler.save_to_html(file_name=output_html)

    # Add map title and creator
    with InPlace(output_html) as file:
        for line in file:
            line = line.replace(
                "<title>Kepler.gl</title>",
                f"<title>{title} &ndash; GRASS GIS Kepler.gl</title>",
            )
            line = line.replace("Kepler.gl Jupyter", title)
            file.write(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
