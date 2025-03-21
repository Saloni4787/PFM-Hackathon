"""
utils/context_management.py

Context Management Utility for Personal Finance Manager

This module provides utilities for maintaining conversation context,
detecting context-dependent queries, and rewriting queries to include
necessary context from previous conversation turns.
"""

from typing import List, Dict, Tuple
from utils.llm_response import generate_text

class ContextManager:
    """
    Manages conversation context and query rewriting for the Financial Advisor Agent.
    """
    
    def __init__(self, max_history: int = 5):
        """
        Initialize the ContextManager.
        
        Args:
            max_history: Maximum number of conversation turns to keep in history
        """
        self.max_history = max_history
    
    def should_rewrite_query(self, 
                            current_query: str, 
                            chat_history: List[Dict[str, str]]) -> bool:
        """
        Determine if the current query needs to be rewritten based on conversation history.
        Uses LLM to check if the query seems incomplete and needs context from history.
        
        Args:
            current_query: The current user query
            chat_history: List of previous conversation turns
            
        Returns:
            True if the query should be rewritten, False otherwise
        """
        # If no history, no need to rewrite
        if not chat_history or len(chat_history) < 2:
            return False
        
        # Get relevant chat history (just the last few turns)
        recent_history = chat_history[-min(self.max_history*2, len(chat_history)):]
        
        # Use LLM to determine if the query needs to be rewritten
        return self._llm_should_rewrite(current_query, recent_history)
    
    def _llm_should_rewrite(self, 
                           current_query: str, 
                           chat_history: List[Dict[str, str]]) -> bool:
        """
        Use LLM to determine if query rewriting is needed.
        
        Args:
            current_query: The current user query
            chat_history: List of previous conversation turns
            
        Returns:
            True if the query should be rewritten, False otherwise
        """
        try:
            # Format chat history for the prompt
            formatted_history = self._format_chat_history(chat_history)
            
            # Create prompt for rewrite determination - enhanced for comprehensive detection
            prompt = f"""
You are an AI assistant for a personal finance chatbot helping determine if a user's current query seems incomplete and needs context from the previous conversation to be fully understood.

Previous conversation:
{formatted_history}

Current user query: "{current_query}"

The current query might be incomplete and need additional context if it:
1. Is very short (e.g., just a number, date, or few words)
2. Contains pronouns without clear referents (it, that, this, etc.)
3. Appears to be a direct response to a question from the assistant
4. Contains financial values without clear context (dollar amounts, percentages)
5. Contains dates or timelines that seem to reference an earlier topic
6. Mentions amounts, targets, or values without specifying what they're for
7. Is continuing a previous financial discussion (about goals, investments, etc.)
8. Is a yes/no/maybe type answer that needs the previous question for context

In a financial chatbot, pay particular attention to:
- Numbers or amounts without context ("5000" - what is this amount for?)
- Dates without context ("December 31, 2026" - deadline for what?)
- Short answers that clearly respond to a previous question
- Any reference to a financial goal, amount, or timeline that seems to continue a previous conversation

Does this query need additional context from previous conversation to be properly understood?
Answer with YES if the query seems incomplete and would benefit from rewriting with context.
Answer with NO only if the query is self-contained and complete on its own.

Answer with just YES or NO.
"""
            
            system_prompt = "You are an expert in conversational context analysis for financial chatbots. Your job is to identify when user queries need additional context to be properly understood."
            
            response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,  # Use 0 temperature for deterministic output
                max_tokens=10   # Very few tokens needed
            )
            
            # Check if the response indicates rewriting is needed
            return "YES" in response.upper()
            
        except Exception as e:
            # If there's an error with the LLM, err on the side of caution
            print(f"Error in LLM rewrite determination: {str(e)}")
            # For very short queries, assume context is needed even if LLM fails
            if len(current_query.split()) <= 3:
                print("LLM failed but query is very short, assuming context is needed")
                return True
            return False
    
    def rewrite_query(self, 
                     current_query: str, 
                     chat_history: List[Dict[str, str]]) -> Tuple[str, bool]:
        """
        Rewrite the current query to include context from conversation history.
        
        Args:
            current_query: The current user query
            chat_history: List of previous conversation turns
            
        Returns:
            Tuple of (rewritten query, whether rewriting occurred)
        """
        # Check if rewriting is needed using LLM
        if not self.should_rewrite_query(current_query, chat_history):
            return current_query, False
        
        # Get relevant chat history
        recent_history = chat_history[-min(self.max_history*2, len(chat_history)):]
        
        try:
            # Format chat history for the prompt
            formatted_history = self._format_chat_history(recent_history)
            
            # Create enhanced prompt for query rewriting
            prompt = f"""
You are an AI assistant for a personal finance management chatbot. Your task is to rewrite incomplete user queries to include necessary context from the previous conversation.

Previous conversation:
{formatted_history}

Current user query: "{current_query}"

This query appears to be incomplete or context-dependent. Rewrite it to be a complete, standalone query that incorporates all relevant context from the conversation history.

Specifically for financial conversations:
1. If the user mentioned a number or amount without context (e.g., "5000"), clarify what this amount refers to based on the conversation
2. If the user mentioned a date without explaining what it's for (e.g., "December 31, 2026"), connect it to the relevant goal or deadline
3. If the user is continuing a discussion about a specific financial goal, include the goal type and details
4. If the user is answering a previous question, frame it as a complete statement

Guidelines for rewriting:
- Create a natural-sounding complete query that captures the user's intent
- Include all relevant context (goal types, amounts, timeframes) from previous messages
- Be specific but concise - include only details that were explicitly mentioned
- Ensure the rewritten query would make sense to someone who hasn't seen the previous conversation
- Maintain the user's original intent and meaning

Only include factual details (goal names, amounts, dates, etc.) that were explicitly mentioned in the conversation history.

Rewritten query:
"""
            
            system_prompt = "You are an expert in conversation context management for financial chatbots, specializing in creating coherent, complete queries from fragmented or context-dependent user inputs."
            
            rewritten_query = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,  # Use near-zero temperature for consistent output
                max_tokens=300   # Allow enough tokens for a thorough rewrite
            )
            
            # Clean up the rewritten query
            rewritten_query = rewritten_query.strip()
            
            # If the rewritten query is empty or too similar to the original, return the original
            if not rewritten_query or rewritten_query.lower() == current_query.lower():
                return current_query, False
            
            print(f"Original query: '{current_query}'")
            print(f"Rewritten query: '{rewritten_query}'")
            
            return rewritten_query, True
            
        except Exception as e:
            # If there's an error with the LLM, return the original query
            print(f"Error in query rewriting: {str(e)}")
            return current_query, False
    
    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """
        Format chat history for inclusion in prompts.
        
        Args:
            chat_history: List of previous conversation turns
            
        Returns:
            Formatted chat history as text
        """
        formatted_history = []
        
        for message in chat_history:
            role = message.get("role", "unknown")
            content = message.get("content", "")
            
            if role == "user":
                formatted_history.append(f"User: {content}")
            elif role == "assistant":
                # Truncate assistant responses if they're very long
                if len(content) > 500:
                    content = content[:497] + "..."
                formatted_history.append(f"Assistant: {content}")
        
        return "\n\n".join(formatted_history)