from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy
from langchain_ollama import ChatOllama
from typing import Callable, Union

from code_pipeline.validation import TestValidator
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
            #temperature=1.0,
        )
        self.validator = TestValidator(map_size)

    def prompt(self, prompt: str) -> dict:
        start_agent = create_agent(self.model, response_format=RoadStart)
        messages = [
            SystemMessage(content=RefiningAgent.agent_description),
            SystemMessage(content=RefiningAgent.start_prompt),
            HumanMessage(content=prompt)
        ]
        starting_point_result = start_agent.invoke({'messages': messages})
        print(starting_point_result)
        starting_point = starting_point_result['structured_response']

        segment_agent = create_agent(self.model, response_format=RoadSegment) #, middleware=[peek_output])
        messages = [
            SystemMessage(content=RefiningAgent.agent_description),
            HumanMessage(content=prompt),
            AIMessage(content=f"Starting point: {starting_point}."),
            HumanMessage(content=RefiningAgent.segment_prompt)
        ]
        first_segment_result = segment_agent.invoke({'messages': messages})
        print(first_segment_result)
        segments = [first_segment_result['structured_response']]

        partial_dict = self._to_dict(starting_point, segments)
        self.road_generator = RoadGenerator(partial_dict['starting_point'], partial_dict['theta'], partial_dict['road_segments'])
        self.road_generator.translate_to_nodes()
        road_test = self.road_generator.create_road_test()
        is_valid, msg =self.validator.validate_test(road_test)

        if not is_valid:
            print("First segment generated an invalid road:", msg)
            print("Refining the first segment...")
            refinement_messages = messages + [
                AIMessage(content=f"Previously generated segments: {segments}."),
                HumanMessage(content=f"The previous segment resulted in an invalid road: {msg}. Please provide a corrected road segment.")
            ]
            refined_segment_result = segment_agent.invoke({'messages': refinement_messages})
            print(refined_segment_result)
            segments[0] = refined_segment_result['structured_response']
            partial_dict = self._to_dict(starting_point, segments)
            self.road_generator = RoadGenerator(partial_dict['starting_point'], partial_dict['theta'], partial_dict['road_segments'])
            self.road_generator.translate_to_nodes()
            road_test = self.road_generator.create_road_test()
            is_valid, msg =self.validator.validate_test(road_test)
            print("After refinement, is the road valid?", is_valid, msg)

        for _ in range(2):
            print("\n\nStarting new segment")
            next_messages = messages + [
                AIMessage(content=f"Previously generated segments: {segments}."),
                HumanMessage(content="Please provide the next road segment.")
            ]
            result = segment_agent.invoke({'messages': next_messages})
            segments.append(result['structured_response'])
            print(result)

        return self._to_dict(starting_point, segments)


    def _to_dict(self, starting_point: RoadStart, segments: list[RoadSegment]) -> dict:
        return {
            'starting_point': (starting_point.x, starting_point.y, starting_point.z),
            'theta': starting_point.theta,
            'road_segments': [segment.model_dump() for segment in segments]
        }

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
