import os
import requests
import json
from dotenv import load_dotenv
from src.utils.io_utils import load_prompt

load_dotenv()

#Classifying if the user is asking general query or spending related query
def classify_query(user_message):
    """
    Uses LLM to classify whether the query is spending-related.
    """
    API_KEY = os.getenv("API_KEY")
    LLM_API_URL = os.getenv("LLM_API_URL")
    MODEL = os.getenv("MODEL")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = "Classify the following user query as 'spending-related' or 'general'. Respond with only one word: 'spending-related' or 'general'."

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return "general"  
    
    
def chat_with_llm(user_message, conversation_history,system_prompt_file="prompts/system_prompt.txt"):
    """
    Calls the LLM for normal chatbot responses while maintaining conversation history.
    """
    API_KEY = os.getenv("API_KEY")
    LLM_API_URL = os.getenv("LLM_API_URL")
    MODEL = os.getenv("MODEL")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = load_prompt(system_prompt_file)

    messages = [{"role": "system", "content": system_prompt}] + conversation_history + [{"role": "user", "content": user_message}]

    payload = {
        "model": MODEL,
        "messages": messages
    }

    response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Error: {response.status_code}, {response.text}"

   
# Function to generate a nudge message
def generate_nudge(row):
    return f"Hi, we noticed an unusual ₹{row['Transaction Amount']:.2f} transaction at {row['Merchant Name']} on {row['Transaction Date and Time']}. If this wasn’t you, please check your account."

# Function to detect unusual spending (IQR-based)
def detect_unusual_spending(transactions_df):
    Q1 = transactions_df['Transaction Amount'].quantile(0.25)
    Q3 = transactions_df['Transaction Amount'].quantile(0.75)
    IQR = Q3 - Q1
    threshold = Q3 + 1.5 * IQR  # Anything above this is "unusual"

    unusual_transactions = transactions_df[transactions_df['Transaction Amount'] > threshold]

    if not unusual_transactions.empty:
        # Generate nudge for the first unusual transaction
        nudge_message = generate_nudge(unusual_transactions.iloc[0])
        # print(f"[DEBUG] Generated Nudge: {nudge_message}")
        return nudge_message
    
    return None  # No unusual spending
