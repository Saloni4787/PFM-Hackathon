import os
import requests
import json
from dotenv import load_dotenv
from src.utils.io_utils import load_prompt

load_dotenv()

def chat_with_llm(user_message, system_prompt_file= "prompts/system_prompt.txt"):
    
    API_KEY =  os.getenv("API_KEY")
    LLM_API_URL =  os.getenv("LLM_API_URL")
    MODEL = os.getenv("MODEL")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = load_prompt(system_prompt_file)
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }
    
    response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.status_code}, {response.text}"