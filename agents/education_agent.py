"""
Education Agent

This script implements the Education Agent for the Personal Finance Manager,
which provides educational content on financial concepts to other agents.
"""

import os
import sys
from typing import Dict, List, Any, Optional

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Compute the path to the project root (one level up from the 'agents' folder)
project_root = os.path.join(current_dir, '..')

# Add the project root to sys.path
sys.path.append(project_root)

# Import the LLM utility and prompts
from utils.llm_response import generate_text, DekaLLMClient
from prompts.education_agent_prompts import EducationPrompts

class EducationAgent:
    """
    Provides educational content on financial concepts.
    
    This agent acts as a shared service for other agents in the system,
    providing consistent educational content across the application.
    """
    
    def __init__(self, data_path: str = "./synthetic_data"):
        """
        Initialize the Education Agent.
        
        Args:
            data_path: Path to directory containing reference data
        """
        self.data_path = data_path
        self.llm_client = DekaLLMClient()
        
        # Load any necessary reference data
        self._load_data_files()
        
        print("Education Agent initialized successfully.")
    
    def _load_data_files(self):
        """Load any necessary reference data files."""
        try:
            # For MVP, we don't need to load any specific data files
            # The agent will primarily use the LLM's knowledge base
            
            # In a production system, we might load:
            # - Financial concept definitions
            # - Glossary of terms
            # - Educational content templates
            pass
            
        except Exception as e:
            print(f"Error loading data files: {str(e)}")
            raise
    
    def get_educational_content(self, 
                               topic: str, 
                               user_context: Dict[str, Any],
                               complexity: str = "beginner",
                               max_length: int = 300) -> str:
        """
        Generate educational content on a financial topic.
        
        Args:
            topic: The financial concept or topic to explain
            user_context: User information to personalize the content
            complexity: Level of detail (beginner, intermediate, advanced)
            max_length: Maximum length of the content in words
            
        Returns:
            Educational content as formatted text
        """
        print(f"Generating educational content on '{topic}' at {complexity} level")
        
        # Extract relevant context
        customer_id = user_context.get("customer_id", "")
        risk_profile = user_context.get("risk_profile", "")
        goal_type = user_context.get("goal_type", "")
        goal_timeline = user_context.get("goal_timeline", "")
        
        # Create a specialized prompt
        prompt = self._create_education_prompt(
            topic=topic,
            risk_profile=risk_profile,
            goal_type=goal_type,
            goal_timeline=goal_timeline,
            complexity=complexity,
            max_length=max_length
        )
        
        # Generate educational content using LLM
        system_prompt = EducationPrompts.SYSTEM_PROMPT
        response = generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=1500
        )
        
        return response
    
    def _create_education_prompt(self,
                                topic: str,
                                risk_profile: str,
                                goal_type: str,
                                goal_timeline: str,
                                complexity: str,
                                max_length: int) -> str:
        """
        Create a specialized prompt for educational content.
        
        Args:
            topic: Financial topic to explain
            risk_profile: User's risk profile
            goal_type: Type of financial goal (if applicable)
            goal_timeline: Timeline for goal (if applicable)
            complexity: Desired complexity level
            max_length: Maximum content length
            
        Returns:
            Formatted prompt for LLM
        """
        # Base education prompt
        prompt = EducationPrompts.EDUCATION_CONTENT_PROMPT.format(
            topic=topic,
            complexity=complexity,
            max_length=max_length
        )
        
        # Add context-specific sections if available
        if risk_profile:
            prompt += EducationPrompts.RISK_PROFILE_CONTEXT.format(
                risk_profile=risk_profile
            )
        
        if goal_type and goal_timeline:
            prompt += EducationPrompts.GOAL_CONTEXT.format(
                goal_type=goal_type,
                goal_timeline=goal_timeline
            )
        
        return prompt
    
    def explain_investment_term(self, term: str) -> str:
        """
        Provide a concise explanation of an investment term.
        
        Args:
            term: The investment term to explain
            
        Returns:
            Brief explanation of the term
        """
        prompt = EducationPrompts.INVESTMENT_TERM_PROMPT.format(term=term)
        system_prompt = EducationPrompts.SYSTEM_PROMPT
        
        response = generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=500
        )
        
        return response
    
    def explain_goal_strategy(self, 
                             goal_type: str, 
                             goal_timeline: str,
                             risk_profile: str) -> str:
        """
        Explain strategy for a specific type of financial goal.
        
        Args:
            goal_type: Type of financial goal
            goal_timeline: Timeline for goal
            risk_profile: User's risk profile
            
        Returns:
            Strategic explanation for the goal
        """
        prompt = EducationPrompts.GOAL_STRATEGY_PROMPT.format(
            goal_type=goal_type,
            goal_timeline=goal_timeline,
            risk_profile=risk_profile
        )
        
        system_prompt = EducationPrompts.SYSTEM_PROMPT
        response = generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=800
        )
        
        return response
    
    def explain_allocation_recommendation(self,
                                         allocation: Dict[str, float],
                                         risk_profile: str,
                                         goal_type: str,
                                         goal_timeline: str) -> str:
        """
        Explain the rationale behind an asset allocation recommendation.
        
        Args:
            allocation: Dictionary of asset classes and percentages
            risk_profile: User's risk profile
            goal_type: Type of financial goal
            goal_timeline: Timeline for goal
            
        Returns:
            Explanation of the allocation recommendation
        """
        # Format the allocation for the prompt
        allocation_text = "\n".join([f"- {asset}: {pct}%" for asset, pct in allocation.items()])
        
        prompt = EducationPrompts.ALLOCATION_EXPLANATION_PROMPT.format(
            allocation=allocation_text,
            risk_profile=risk_profile,
            goal_type=goal_type,
            goal_timeline=goal_timeline
        )
        
        system_prompt = EducationPrompts.SYSTEM_PROMPT
        response = generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=800
        )
        
        return response


def main():
    """Main function to demonstrate the Education Agent."""
    # Initialize the agent
    agent = EducationAgent()
    
    # Test getting educational content
    topic = "compound interest"
    user_context = {
        "customer_id": "CUSTOMER1",
        "risk_profile": "Growth",
        "goal_type": "Retirement",
        "goal_timeline": "Long-term"
    }
    
    educational_content = agent.get_educational_content(
        topic=topic,
        user_context=user_context,
        complexity="beginner"
    )
    
    print("\n" + "="*50)
    print(f"EDUCATIONAL CONTENT ON: {topic.upper()}")
    print("="*50)
    print(educational_content)
    print("="*50)
    
    # Test explaining an investment term
    term = "dollar-cost averaging"
    term_explanation = agent.explain_investment_term(term)
    
    print("\n" + "="*50)
    print(f"EXPLANATION OF: {term.upper()}")
    print("="*50)
    print(term_explanation)
    print("="*50)


if __name__ == "__main__":
    main()