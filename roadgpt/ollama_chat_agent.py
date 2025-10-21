from langchain.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from roadgpt.schema import agent_description, road_schema_array


class OllamaChatAgent:

    def __init__(self):
        model = ChatOllama(
            model="gemma3",
            temperature=1.0,
        )
        self.model = model.with_structured_output(road_schema_array, method="json_schema")

    def prompt(self, prompt: str) -> dict:
        messages = [
            SystemMessage(content=agent_description),
            HumanMessage(content=prompt)
        ]
        return self.model.invoke(messages)
