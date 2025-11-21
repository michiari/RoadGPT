agent_description = r"""
You are a road designer, who designs roads to test the lane keeping functionality of self driving vehicles.
People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments.
These descriptions are then turned into coordinates, so keep the coordinate values in mind.

Here are some ground rules:
- The roads should be diverse: given the same description don't create the same road (Start in different directions, etc.)
- The car should cover as many directions on the map as possible
- The car should face as many directions as possible while using your road
- First, return a starting point in the field starting_point, with coordinates (x, y, z), and consider your starting point when you build the road
- Give me an integer heading angle theta between 0 and 360 to show which way the road is starting. (0 = along the y axis).
- Then, describe the road in segments in the road_segments array.
- Each segment contains the distance of the end point of the segment to the end point of the previous segment in meters, the direction (e.g. right turn), the incline in % and the degrees of the turn
- Make sure that no point is out of bounds: every x and y value must be greater than 0 and lower than 200 (0 <= x,y <= 200)
- The z axis can never be lower than -28.0 every segment needs!
- Only return 'left', 'right' or 'straight' for the direction!
- Only return numbers for the distance, incline and the degrees of the turn.
- Write declines in height and the degrees of right turns as negative numbers!
- The maximum incline is 15%
- The turn degrees of one segment should not exceed 70 degrees. If you want to create a turn with more degrees split it into two segments!
- Given the same prompt you should never return the same road description and your descriptions should be as diverse as possible (don't start with the same theta every time, don't start with a right turn every time, don't start at the same point, etc.)
- Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.)
- Keep track of where you are going since you are not allowed to go outside of the map boundaries!
"""

road_schema_array = {
    "type": "object",
    "title": "road_description",
    "description": "Schema for road description",
    "properties": {
        "starting_point": {
            "type": "array",
            "description": "The 3D coordinates of the starting point [x, y, z].",
            "items": {
                "type": "integer",
                "description": "Coordinate value.",
                "minItems": 3,
                "maxItems": 3
            }
        },
        "theta": {
            "type": "number",
            "description": "Initial heading in degrees (azimuth/compass angle from the x-axis, in degrees)."
        },
        "road_segments": {
            "type": "array",
            "description": "Array of road segments.",
            "items": {
                "type": "object",
                "description": "The road segments after the starting point.",
                "properties": {
                    "distance": {
                        "type": "integer",
                        "description": "Length of the segment in meters."
                    },
                    "direction": {
                        "type": "string",
                        "description": "Direction of the segment (one of 'left', 'right', 'straight')."
                    },
                    "incline": {
                        "type": "integer",
                        "description": "Incline angle in degrees (positive for uphill, negative for downhill, zero for flat)."
                    },
                    "turn_degrees": {
                        "type": "integer",
                        "description": "Turn in degrees from the previous direction (positive = right, negative = left)."
                    }
                },
                "required": [
                    "distance",
                    "direction",
                    "incline",
                    "turn_degrees"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": [
        "starting_point",
        "theta",
        "road_segments"
    ],
    "additionalProperties": False
}


agent_description_old = r"""
You are a road designer, who designs roads to test the lane keeping functionality of self driving vehicles.
People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments.
These descriptions are then turned into coordinates, so keep the coordinate values in mind.
Since you are testing the lane keeping functionality of self driving vehicles, you want to stress it.

Here are some ground rules:
- The roads should be diverse: given the same description don't create the same road (Start in different directions, etc.)
- The car should cover as many directions on the map as possible
- The car should face as many directions as possible while using your road
- before the first segment give me a starting point (x, y, z), consider your starting point when you build the road since the x and y values are not allowed to be less than 0 or greater than 200
- Give me an angle between 0 and 360 to show which way the road is starting. (0 = along the y axis). The value has to be an integer.
- make sure that no point is out of bounds: every x and y value is greater than 0 and less than 200
- the z axis can't be lower than -28.0 every segment needs the distance of the end point of the segment to the end point of the previous segment in meters, direction (e.g. right turn), the incline in % and the degrees of the turn!
- Only return 'left', 'right' or 'straight' for the direction
- Only return numbers for the distance, incline and the degrees of the turn.
- Write declines in height and the degrees of right turns as negative numbers!
- The maximum incline is 15%
- The turn degrees of one segment should not exceed 70 degrees. If you want to create a turn with more degrees split it into two segments!
- Return the road description in json format
- Given the same prompt you should never return the same road description and your descriptions should be as diverse as possible (don't start with the same theta every time, don't start with a right turn every time, don't start at the same point, etc.)
- Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.)
- Keep track of where you are going since you are not allowed to go outside of the map boundaries!
"""

road_schema_old = {
  "type": "object",
  "description": "Schema for road description",
  "name": "road_description",
  "properties": {
    "starting_point": {
      "type": "array",
      "description": "The 3D coordinates of the starting point [x, y, z].",
      "prefixItems": [
        {
          "type": "number",
          "description": "X-coordinate of the starting point."
        },
        {
          "type": "number",
          "description": "Y-coordinate of the starting point."
        },
        {
          "type": "number",
          "description": "Z-coordinate of the starting point."
        }
      ],
      "items": {
        "type": "number"
      }
    },
    "theta": {
      "type": "number",
      "description": "Initial heading in degrees (azimuth/compass angle from the x-axis, in degrees)."
    }
  },
  "pattern_properties": {
    "^road_segment": {
      "type": "object",
      "description": "The first road segment after the starting point.",
      "properties": {
        "distance": {
          "type": "integer",
          "description": "Length of the segment in meters."
        },
        "direction": {
          "type": "string",
          "description": "Direction of the segment (one of 'left', 'right', 'straight')."
        },
        "incline": {
          "type": "integer",
          "description": "Incline angle in degrees (positive for uphill, negative for downhill, zero for flat)."
        },
        "turn_degrees": {
          "type": "integer",
          "description": "Turn in degrees from the previous direction (positive = right, negative = left)."
        }
      },
      "required": [
        "distance",
        "direction",
        "incline",
        "turn_degrees"
      ],
      "additionalProperties": False
    }
  },
  "required": [
    "starting_point",
    "theta"
  ],
  "additionalProperties": False
}
