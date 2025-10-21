from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI

from roadgpt.schema import road_schema

class RoadGPTAgent:

    def __init__(self, _model_name):
        model = ChatOpenAI(
            model="gpt-4.1",
            temperature=1.0,
            # max_tokens=1000,
            # timeout=30
        )

        self.agent = create_agent(
            model=model,
            system_prompt=RoadGPTAgent.agent_description,
            response_format=road_schema
        )

    def prompt(self, prompt: str) -> dict:
        return self.agent.invoke(HumanMessage(prompt))

    agent_description = r'''
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
    '''
