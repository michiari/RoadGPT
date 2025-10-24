from roadgpt.refining_agent import RefiningAgent

if __name__ == "__main__":
    agent = RefiningAgent(200)
    prompt = "Design a mountain road with serpentines"
    response = agent.prompt(prompt)
    print("Response from OllamaAgent:")
    print(response)
