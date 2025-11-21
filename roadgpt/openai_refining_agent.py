import logging
log = logging.getLogger(__name__)

from langchain_openai import ChatOpenAI

from roadgpt.refining_agent import RefiningAgent
from roadgpt.road import starting_point_schema, segment_schema


class OpenAIRefiningAgent(RefiningAgent):

    def __init__(self, map_size: int):
        super().__init__(map_size)
        self.model = ChatOpenAI(
            model="gpt-4.1",
            temperature=1.0,
            max_tokens=None,
            timeout=None
        )

    def _invoke_starting_point_agent(self, messages: list[dict]) -> dict:
        struct_model = self.model.with_structured_output(starting_point_schema, method='json_schema', strict=True)
        starting_point_result = struct_model.invoke(messages)
        log.debug(starting_point_result)
        return starting_point_result

    def _invoke_segment_agent(self, messages: list[dict]) -> dict:
        struct_model = self.model.with_structured_output(segment_schema, method='json_schema', strict=True)
        segment_result = struct_model.invoke(messages)
        log.debug(segment_result)
        return segment_result
