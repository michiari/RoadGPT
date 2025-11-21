import logging
log = logging.getLogger(__name__)
import json
from llama_cpp import Llama

from roadgpt.schema import agent_description, road_schema_array


class LlamaCppChatAgent:

    def __init__(self, model_path: str, verbose: bool = False):
        self.model = Llama(model_path=model_path, n_ctx=0, verbose=verbose)
        self.temperature = 1.0

    def prompt(self, prompt: str) -> dict:
        messages = [
            { 'role': 'system', 'content': agent_description },
            { 'role': 'user', 'content': prompt }
        ]

        result = self.model.create_chat_completion(
            messages=messages,
            temperature=self.temperature,
            response_format={
                "type": "json_object",
                "schema": road_schema_array
            }
        )
        log.debug(result)
        return json.loads(result['choices'][0]['message']['content'])
