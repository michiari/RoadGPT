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
