import logging
log = logging.getLogger(__name__)
import json

from roadgpt.refining_agent import RefiningAgent
from roadgpt.road import starting_point_schema, segment_schema

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
                "schema": starting_point_schema
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
                "schema": segment_schema
            }
        )
        log.debug(segment_result)
        return json.loads(segment_result['choices'][0]['message']['content'])
