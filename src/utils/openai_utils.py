import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

def chat_with_llm(user_message):
    
    API_KEY =  os.getenv("API_KEY")
    LLM_API_URL =  os.getenv("LLM_API_URL")
    MODEL = os.getenv("MODEL")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = "You are a friendly chatbot."
    
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