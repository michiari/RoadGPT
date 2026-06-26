from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_openai import ChatOpenAI

from roadgpt.schema import agent_description, road_schema_array

class OpenAIChatAgent:

    def __init__(self, base_url=None, model="gpt-4.1"):
        if model is None:
            model = "gpt-4.1"
        model = ChatOpenAI(
            model=model,
            temperature=1.0,
            base_url=base_url
            # max_tokens=1000,
            # timeout=30
        )
        self.agent = create_agent(
            model=model,
            system_prompt=agent_description,
            response_format=road_schema_array
        )

    def prompt(self, prompt: str) -> dict:
        return self.agent.invoke(HumanMessage(prompt))['structured_response']
