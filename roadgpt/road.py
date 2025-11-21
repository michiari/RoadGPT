from pydantic import BaseModel, Field
from typing import Literal

class RoadStart(BaseModel):
    x: int = Field(..., description="X-coordinate of the starting point.")
    y: int = Field(..., description="Y-coordinate of the starting point.")
    z: int = Field(..., description="Z-coordinate of the starting point.")
    theta: int = Field(..., description="Initial heading in degrees (azimuth/compass angle from the x-axis, in degrees).")

class RoadSegment(BaseModel):
    distance: int = Field(..., description="Length of the segment in meters.")
    direction: Literal['left', 'right', 'straight'] = Field(..., description="Direction of the segment.")
    incline: int = Field(..., description="Incline angle in degrees (positive for uphill, negative for downhill, zero for flat).")
    turn_degrees: int = Field(..., description="Turn in degrees from the previous direction (positive/right, negative/left).")


def road_start_to_dict(road_start: RoadStart) -> dict:
    return {
        'starting_point': (road_start.x, road_start.y, road_start.z),
        'theta': road_start.theta
    }


starting_point_schema = {
    "type": "object",
    "title": "starting_point",
    "description": "Schema for the starting point of the road",
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
            "type": "integer",
            "description": "Initial heading in degrees (azimuth/compass angle from the x-axis, in degrees)."
        }
    },
    "additionalProperties": False
}

segment_schema = {
    "type": "object",
    "title": "road_segment",
    "description": "A road segment",
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
