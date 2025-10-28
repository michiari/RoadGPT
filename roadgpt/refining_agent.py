from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain_ollama import ChatOllama
from typing import Callable, Tuple

from code_pipeline.validation import ValidationResult, TestValidator
from roadgpt.road import RoadStart, RoadSegment
from roadgpt.road_generator import RoadGenerator


@wrap_model_call
def peek_output(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:

    print(request.messages)

    return handler(request)

class RefiningAgent:

    def __init__(self, map_size: int):
        self.model = ChatOllama(
            model="llama3.2",
            temperature=0.8,
        )
        self.validator = TestValidator(map_size)
        self.segment_agent = None


    def prompt(self, prompt: str, max_attempts: int = 3) -> dict:
        starting_point = self._get_starting_point(prompt)

        segments = []
        for _ in range(6):
            print("\n\nStarting new segment")
            segments.append(self._get_segment(prompt, starting_point, segments, max_attempts))
            print(segments[-1])

        return self._to_dict(starting_point, segments)


    def _get_starting_point(self, prompt: str) -> RoadStart:
        start_agent = create_agent(self.model, response_format=RoadStart)
        messages = [
            SystemMessage(content=RefiningAgent.agent_description),
            SystemMessage(content=RefiningAgent.start_prompt),
            HumanMessage(content=prompt)
        ]
        starting_point_result = start_agent.invoke({'messages': messages})
        print('Starting point: ', starting_point_result['structured_response'])
        return starting_point_result['structured_response']


    def _get_segment(self, prompt: str, starting_point: RoadStart, previous_segments: list[RoadSegment], max_attempts: int) -> RoadSegment:
        if self.segment_agent is None:
            self.segment_agent = create_agent(self.model, response_format=RoadSegment) #, middleware=[peek_output])
        messages = [
            SystemMessage(content=RefiningAgent.agent_description),
            HumanMessage(content=prompt),
            AIMessage(content=f"Starting point: {starting_point}."),
            HumanMessage(content=RefiningAgent.segment_prompt)
        ]
        if previous_segments:
            messages.extend([
                AIMessage(content=f"Previously generated segments: {previous_segments}."),
                HumanMessage(content=f"Remember that my prompt was: {prompt}. Please provide the next road segment.")
            ])
        else:
            messages.append(HumanMessage(content="Please provide the first road segment."))

        segment_result = self.segment_agent.invoke({'messages': messages})
        print(f"Segment result: {segment_result}")
        segments = previous_segments + [segment_result['structured_response']]

        is_valid, msg = self._validate(starting_point, segments)
        attempts = 0
        while not is_valid and attempts < max_attempts:
            print("Segment generated an invalid road:", msg)
            print(f"Refining segment (attempt {attempts + 1})...")
            refinement_messages = messages + [
                AIMessage(content=f"Previously generated segments: {segments}."),
                HumanMessage(content=f"The previous segment resulted in an invalid road because {msg}. Please provide a corrected road segment.")
            ]
            refined_segment_result = self.segment_agent.invoke({'messages': refinement_messages})
            print(refined_segment_result)
            segments[-1] = refined_segment_result['structured_response']
            is_valid, msg = self._validate(starting_point, segments)
            attempts += 1
            print("After refinement, is the road valid?", is_valid, msg)

        if not is_valid:
            raise ValueError(f"Failed to generate a valid road after refining the segment {max_attempts} times.")
        
        return segments[-1]


    def _validate(self, starting_point: RoadStart, segments: list[RoadSegment]) -> Tuple[bool, str]:
        partial_dict = self._to_dict(starting_point, segments)
        self.road_generator = RoadGenerator(partial_dict['starting_point'], partial_dict['theta'], partial_dict['road_segments'])
        self.road_generator.translate_to_nodes()
        road_test = self.road_generator.create_road_test()
        return self.validator.validate_test(road_test)


    def _to_dict(self, starting_point: RoadStart, segments: list[RoadSegment]) -> dict:
        return {
            'starting_point': (starting_point.x, starting_point.y, starting_point.z),
            'theta': starting_point.theta,
            'road_segments': [segment.model_dump() for segment in segments]
        }


    def _get_correction_message(self, validation_result: ValidationResult) -> str:
        match validation_result:
            case ValidationResult.NOT_ENOUGH_POINTS:
                return "The road has not enough points"
            case ValidationResult.TOO_MANY_POINTS:
                return "The road has too many points"
            case ValidationResult.NOT_INSIDE_MAP:
                return "The road goes outside of the map boundaries because the segment is too long. Please return a shorter segment."
            case ValidationResult.INTERSECTS_BOUNDARY:
                return "The road intersects the map boundary because the segment is too long. Please return a shorter segment."
            case ValidationResult.INVALID_POLYGON:
                return "The road polygon is invalid"
            case ValidationResult.NOT_MINIMUM_LENGTH:
                return "The road is not long enough. Please return a longer segment."
            case ValidationResult.TOO_SHARP:
                return "The road has turns that are too sharp. Please return segment with smaller turn degrees."
            case ValidationResult.TOO_STEEP:
                return "The road has inclines that are too steep"
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
- The z axis can never be lower than -28.0 every segment needs!
- Only return 'left', 'right' or 'straight' for the direction!
- Only return numbers for the distance, incline and the degrees of the turn.
- Write declines in height and the degrees of right turns as negative numbers!
- The maximum incline is 15%
- The turn degrees of one segment should not exceed 70 degrees. If you want to create a turn with more degrees split it into two segments!
- Make the roads as diverse as possible (longer turns, shorter turns, incline, decline, etc.)
- Keep track of where you are going since you are not allowed to go outside of the map boundaries!
Now give me the next road segment by providing the distance, direction, incline and turn_degrees.
"""
