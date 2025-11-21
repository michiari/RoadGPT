from typing import Tuple
import logging
log = logging.getLogger(__name__)

from code_pipeline.validation import MIN_ELEVATION, ValidationResult, TestValidator
from roadgpt.road_generator import RoadGenerator


class RefiningAgent:

    def __init__(self, map_size: int):
        self.validator = TestValidator(map_size)


    def prompt(self, prompt: str, max_attempts: int = 5) -> dict:
        starting_point = self._get_starting_point(prompt)

        segments = []
        for _ in range(6):
            log.info("Querying new segment...")
            segments.append(self._get_segment(prompt, starting_point, segments, max_attempts))
            log.info(f"Segment result: {segments[-1]}")

        starting_point['road_segments'] = segments
        return starting_point


    def _get_starting_point(self, prompt: str) -> dict:
        messages = [
            { 'role': 'system', 'content': RefiningAgent.agent_description },
            { 'role': 'system', 'content': RefiningAgent.start_prompt },
            { 'role': 'user', 'content': prompt }
        ]
        starting_point_result = self._invoke_starting_point_agent(messages)
        log.info(f"Starting point: {starting_point_result}")
        return starting_point_result


    def _get_segment(self, prompt: str, starting_point: dict, previous_segments: list[dict], max_attempts: int) -> dict:
        messages = [
            { 'role': 'system', 'content': RefiningAgent.agent_description },
            { 'role': 'user', 'content': prompt },
            { 'role': 'assistant', 'content': f"Starting point: {starting_point}." },
            { 'role': 'user', 'content': RefiningAgent.segment_prompt }
        ]
        if previous_segments:
            messages.extend([
                { 'role': 'assistant', 'content': f"Previously generated segments: {previous_segments}." },
                { 'role': 'user', 'content': f"Remember that my prompt was: {prompt}. Please provide the next road segment." }
            ])
        else:
            messages.append({ 'role': 'user', 'content': "Please provide the first road segment." })

        log.debug(f"Invoking segment agent with messages: {messages}")
        segment_result = self._invoke_segment_agent(messages)
        log.info(f"Segment result: {segment_result}")
        segments = previous_segments + [segment_result]

        is_valid, reason = self._validate(starting_point, segments)
        attempts = 0
        while not is_valid and attempts < max_attempts:
            log.info(f"Segment generated an invalid road: {reason.value}")
            log.info(f"Refining segment (attempt {attempts + 1})...")
            refinement_messages = messages + [
                { 'role': 'user', 'content': f"The last segment you generated {segments[-1]} resulted in an invalid road because {self._get_correction_message(reason)}. Please provide a corrected road segment." }
            ]
            log.debug(f"Invoking segment agent with messages: {refinement_messages}")
            refined_segment_result = self._invoke_segment_agent(refinement_messages)
            log.info(f"Refined segment result: {refined_segment_result}")
            segments[-1] = refined_segment_result
            is_valid, reason = self._validate(starting_point, segments)
            attempts += 1
            log.info(f"After refinement, is the road valid? {is_valid}, {reason.value}")

        if not is_valid:
            raise ValueError(f"Failed to generate a valid road after refining the segment {max_attempts} times.")
        
        return segments[-1]


    def _validate(self, starting_point: dict, segments: list[dict]) -> Tuple[bool, str]:
        self.road_generator = RoadGenerator(starting_point['starting_point'], starting_point['theta'], segments)
        self.road_generator.translate_to_nodes()
        road_test = self.road_generator.create_road_test()
        return self.validator.validate_test(road_test)


    def _get_correction_message(self, validation_result: ValidationResult) -> str:
        match validation_result:
            case ValidationResult.NOT_ENOUGH_POINTS:
                return "The road has not enough points"
            case ValidationResult.TOO_MANY_POINTS:
                return "The road has too many points"
            case ValidationResult.NOT_INSIDE_MAP:
                return "The road goes outside of the map boundaries because the segment is too long. Please return a segment with a shorter distance"
            case ValidationResult.INTERSECTS_BOUNDARY:
                return "The road intersects the map boundary because the segment is too long. Please return a segment with a shorter distance"
            case ValidationResult.INVALID_POLYGON:
                return "The road polygon is invalid"
            case ValidationResult.NOT_MINIMUM_LENGTH:
                return "The road is not long enough. Please return a longer segment"
            case ValidationResult.TOO_SHARP:
                return "The road has turns that are too sharp. Please return segment with smaller turn degrees"
            case ValidationResult.TOO_STEEP:
                return "The road has inclines that are too steep"
            case ValidationResult.UNDERGROUND:
                return f"The road goes underground: please provide a segment with an elevation higher than {MIN_ELEVATION}"
            case _:
                return "An unknown validation error occurred"


    agent_description = """You are a road designer, who designs roads to test the lane-keeping functionality of self-driving vehicles.
People give you descriptions of roads and you create more detailed descriptions of novel roads, where you split the road into segments.
These descriptions are then turned into coordinates.
"""
    start_prompt = """The description starts from a starting point in 3D space (x, y, z) and an initial heading angle theta between 0 and 360 in degrees (0 = along the y axis).
The coordinates x, y, z must be within the bounds of the simulation area (0 <= x,y <= 200, z >= -28.0).
Now, start by giving me only the three coordinates x, y, z for the starting point and theta.
"""

    segment_prompt = """Now you'll design the next road segments.
Here are some ground rules:
- The car should cover as many directions on the map as possible
- The car should face as many directions as possible while using your road
- Each segment consists of the distance of the end point of the segment to the end point of the previous segment in meters, the direction (e.g. right turn), the incline in % and the degrees of the turn
- Make sure that no point is out of bounds: every x and y value must be greater than 0 and lower than 200 (0 <= x,y <= 200)
- The z axis can never be lower than -28.0!
- Only return 'left', 'right' or 'straight' for the direction!
- Only return numbers for the distance, incline and the degrees of the turn.
- Write declines in height and the degrees of right turns as negative numbers!
- The maximum incline is 15%
- The turn degrees of one segment should not exceed 70 degrees. If you want to create a turn with more degrees split it into two segments!
- Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.)
- Keep track of where you are going since you are not allowed to go outside of the map boundaries!
Now give me the next road segment by providing the distance, direction, incline and turn_degrees.
"""
