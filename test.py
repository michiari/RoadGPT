from roadgpt.ollama_refining_agent import OllamaRefiningAgent

if __name__ == "__main__":
    agent = OllamaRefiningAgent(200)
    prompt = "Design a mountain road with serpentines"
    response = agent.prompt(prompt)
    print("Response from OllamaAgent:")
    print(response)
