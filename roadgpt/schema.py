road_schema = {
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
          "description": "Segment cardinal direction (e.g., 'N', 'S', 'E', 'W', or combinations such as 'NE')."
        },
        "incline": {
          "type": "integer",
          "description": "Incline angle in degrees (positive for uphill, negative for downhill, zero for flat)."
        },
        "turn_degrees": {
          "type": "integer",
          "description": "Turn in degrees from the previous direction (right/left, positive/right, negative/left)."
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
