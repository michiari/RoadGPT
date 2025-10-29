import logging
from roadgpt.ollama_refining_agent import OllamaRefiningAgent
from roadgpt.llamacpp_refining_agent import LlamaCppRefiningAgent

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    #agent = OllamaRefiningAgent(200)
    agent = LlamaCppRefiningAgent(200, model_path="/home/michele/Software/llama-b6853-ubuntu-vulkan-x64/LiquidAI_LFM2-VL-3B-F16/LiquidAI_LFM2-VL-3B-GGUF_LFM2-VL-3B-F16.gguf")
    prompt = "Design a mountain road with serpentines"
    response = agent.prompt(prompt)
    print("Response from agent:")
    print(response)
