from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from langchain_ollama import ChatOllama
from typing import Callable
import logging
log = logging.getLogger(__name__)

from roadgpt.road import RoadStart, RoadSegment, road_start_to_dict
from roadgpt.refining_agent import RefiningAgent


@wrap_model_call
def peek_request(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:

    log.debug(f"Agent invoked with request:\n{request.messages}")

    return handler(request)


class OllamaRefiningAgent(RefiningAgent):

    def __init__(self, map_size: int):
        super().__init__(map_size)
        self.model = ChatOllama(
            model="llama3.2",
            temperature=0.6,
        )
        self.segment_agent = None


    def _invoke_starting_point_agent(self, messages: list[dict]) -> dict:
        start_agent = create_agent(self.model, response_format=RoadStart)
        starting_point_result = start_agent.invoke({'messages': self._to_langchain_messages(messages)})
        return road_start_to_dict(starting_point_result['structured_response'])


    def _invoke_segment_agent(self, messages: list[dict]) -> dict:
        if self.segment_agent is None:
            self.segment_agent = create_agent(self.model, response_format=RoadSegment) #, middleware=[peek_request])
        segment_result = self.segment_agent.invoke({'messages': self._to_langchain_messages(messages)})
        return segment_result['structured_response'].model_dump()


    def _to_langchain_messages(self, messages: list[dict]) -> list:
        role_map = {
            'system': SystemMessage,
            'user': HumanMessage,
            'assistant': AIMessage
        }
        return [role_map[message['role']](content=message['content']) for message in messages]
