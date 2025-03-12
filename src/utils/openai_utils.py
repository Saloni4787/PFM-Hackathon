import os
import requests
import json
from dotenv import load_dotenv
from src.utils.io_utils import load_prompt

load_dotenv()

conversation_history = []

def chat_with_llm(user_message, system_prompt_file="prompts/system_prompt.txt"):
    global conversation_history
    
    API_KEY = os.getenv("API_KEY")
    LLM_API_URL = os.getenv("LLM_API_URL")
    MODEL = os.getenv("MODEL")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = load_prompt(system_prompt_file)
    
    if not conversation_history:
        conversation_history.append({"role": "system", "content": system_prompt})
    
    conversation_history.append({"role": "user", "content": user_message})
    
    # # Print the conversation history to verify it's growing
    # print("\n--- Conversation History ---")
    # for msg in conversation_history:
    #     print(f"{msg['role'].capitalize()}: {msg['content']}")
    # print("---------------------------\n")
    
    
    payload = {
        "model": MODEL,
        "messages": conversation_history
    }
    
    response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        assistant_message = response.json()["choices"][0]["message"]["content"]
        conversation_history.append({"role": "assistant", "content": assistant_message})
        return assistant_message
    else:
        return f"Error: {response.status_code}, {response.text}"

