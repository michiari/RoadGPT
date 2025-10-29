import logging
log = logging.getLogger(__name__)
import json

from roadgpt.refining_agent import RefiningAgent

from llama_cpp import Llama

class LlamaCppRefiningAgent(RefiningAgent):
    def __init__(self, map_size: int, model_path: str, verbose=False):
        super().__init__(map_size)
        self.model = Llama(model_path=model_path, n_ctx=0, verbose=verbose)
        self.temperature = 0.9


    def _invoke_starting_point_agent(self, messages: list[dict]) -> dict:
        starting_point_result = self.model.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            response_format={
                "type": "json_object",
                "schema": LlamaCppRefiningAgent.starting_point_schema
            }
        )
        log.debug(starting_point_result)
        return json.loads(starting_point_result['choices'][0]['message']['content'])


    def _invoke_segment_agent(self, messages: list[dict]) -> dict:
        self.model.reset()
        segment_result = self.model.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            response_format={
                "type": "json_object",
                "schema": LlamaCppRefiningAgent.segment_schema
            }
        )
        log.debug(segment_result)
        return json.loads(segment_result['choices'][0]['message']['content'])


    starting_point_schema = {
        "type": "object",
        "description": "Schema for the starting point of the road",
        "name": "starting_point",
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
        }
    }

    segment_schema = {
        "type": "object",
        "description": "A road segment",
        "name": "road_segment",
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
