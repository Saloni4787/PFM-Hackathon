"""
DekaLLM Utility Module

This module provides utility functions to interact with the DekaLLM API 
from dekallm.cloudeka.ai for the Personal Finance Manager application.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DekaLLMClient:
    """
    Client for interacting with the DekaLLM API.
    
    This class handles authentication, request formatting, and error handling 
    for API calls to dekallm.cloudeka.ai.
    """
    
    def __init__(self):
        """Initialize the DekaLLM client with API credentials from environment variables."""
        self.api_url = os.getenv("DEKA_LLM_API_URL")
        self.api_key = os.getenv("DEKA_LLM_API_KEY")
        self.model_name = os.getenv("DEKA_LLM_MODEL_NAME")
        
        if not self.api_url or not self.api_key or not self.model_name:
            raise ValueError(
                "Missing required environment variables. "
                "Please ensure DEKA_LLM_API_URL, DEKA_LLM_API_KEY, and DEKA_LLM_MODEL_NAME "
                "are set in your .env file."
            )
        
        # Set default headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1e-8,
        max_tokens: int = 1000,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response from the DekaLLM API.
        
        Args:
            prompt: The user prompt or query
            system_prompt: Optional system instructions to guide the model's behavior
            temperature: Controls randomness in the response (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            chat_history: Optional list of previous messages for context
        
        Returns:
            Dictionary containing the API response with generated text
        
        Raises:
            Exception: If the API request fails
        """
        # Prepare the messages list
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Add the current user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Prepare the request payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            # Send the request to the API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60  # Set a reasonable timeout
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse and return the JSON response
            return response.json()
            
        except requests.exceptions.HTTPError as http_err:
            error_message = f"HTTP error occurred: {http_err}"
            try:
                error_detail = response.json()
                error_message += f"\nAPI Error: {json.dumps(error_detail)}"
            except:
                error_message += f"\nResponse text: {response.text}"
            raise Exception(error_message)
            
        except requests.exceptions.ConnectionError:
            raise Exception("Connection error: Failed to connect to the DekaLLM API")
            
        except requests.exceptions.Timeout:
            raise Exception("Timeout error: The request to DekaLLM API timed out")
            
        except requests.exceptions.RequestException as err:
            raise Exception(f"Error making request to DekaLLM API: {err}")
            
        except json.JSONDecodeError:
            raise Exception(f"Error parsing API response: {response.text}")

    def extract_text_response(self, response: Dict[str, Any]) -> str:
        """
        Extract the text content from the API response.
        
        Args:
            response: The full API response dictionary
        
        Returns:
            The extracted text content from the assistant's response
        
        Raises:
            ValueError: If response format is unexpected or invalid
        """
        try:
            # Extract the assistant's message from the response
            # This may need adjustment based on the actual API response format
            if "choices" in response and len(response["choices"]) > 0:
                if "message" in response["choices"][0]:
                    return response["choices"][0]["message"]["content"]
            
            # If the expected structure is not found, look for alternatives
            if "output" in response:
                return response["output"]
            
            if "generated_text" in response:
                return response["generated_text"]
            
            # If we can't find the expected fields, return the full response for debugging
            return f"Unexpected response format. Full response: {json.dumps(response)}"
            
        except Exception as e:
            raise ValueError(f"Error extracting text from response: {str(e)}")
    
# Simple utility function to make calls easier
def generate_text(
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 1e-8,
        max_tokens: int = 1000,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
    """
    Utility function to generate text from DekaLLM with minimal setup.
    
    Args:
        prompt: The user prompt or query
        system_prompt: Optional system instructions to guide the model
        temperature: Controls randomness (0.0 to 1.0)
        max_tokens: Maximum tokens to generate
        chat_history: Optional list of previous messages
    
    Returns:
        Generated text as a string
    """
    client = DekaLLMClient()
    response = client.generate_response(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        chat_history=chat_history
    )
    return client.extract_text_response(response)