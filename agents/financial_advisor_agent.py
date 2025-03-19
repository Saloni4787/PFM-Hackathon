"""
Financial Advisor Agent

This script implements the Financial Advisor Agent for the Personal Finance Manager,
which serves as the central coordinator for all specialized agents and provides
holistic financial guidance to users.

This updated version includes formatting improvements for financial data.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Any
import re

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Compute the path to the project root (one level up from the 'agents' folder)
project_root = os.path.join(current_dir, '..')

# Add the project root to sys.path
sys.path.append(project_root)

# Import the LLM utility and prompts
from utils.llm_response import generate_text, DekaLLMClient
from prompts.financial_advisor_agent_prompts import FinancialAdvisorPrompts

# Import all specialized agents
from agents.transaction_analysis_agent import TransactionAnalysisAgent
from agents.goal_planning_agent import GoalPlanningAgent
from agents.asset_allocation_agent import AssetAllocationAgent
from agents.education_agent import EducationAgent


class FinancialAdvisorAgent:
    """
    Central coordinator for all specialized agents in the Personal Finance Manager.
    
    This agent routes user queries to the appropriate specialized agent and provides
    holistic financial guidance by integrating responses from multiple agents.
    """
    
    def __init__(self, data_path: str = "./data"):
        """
        Initialize the Financial Advisor Agent.
        
        Args:
            data_path: Path to directory containing CSV data files
        """
        self.data_path = data_path
        self.llm_client = DekaLLMClient()
        
        # Use improved system prompt with formatting instructions
        self.system_prompt = FinancialAdvisorPrompts.SYSTEM_PROMPT
        self.enhanced_system_prompt = FinancialAdvisorPrompts.SYSTEM_PROMPT
        
        # Initialize specialized agents
        self.education_agent = EducationAgent(data_path)
        self.asset_allocation_agent = AssetAllocationAgent(data_path)
        self.goal_planning_agent = GoalPlanningAgent(
            data_path=data_path,
            asset_allocation_agent=self.asset_allocation_agent,
            education_agent=self.education_agent
        )
        self.transaction_agent = TransactionAnalysisAgent(data_path)
        
        # Load necessary data files
        self._load_data_files()
        
        print("Financial Advisor Agent initialized successfully.")
    
    def _load_data_files(self):
        """Load all necessary data files from the data directory."""
        try:
            # Load user profiles
            self.user_profiles_df = pd.read_csv(f"{self.data_path}/user_profile_data.csv")
            
            # Load financial goals
            self.financial_goals_df = pd.read_csv(f"{self.data_path}/financial_goals_data.csv")
            
            # Load transactions
            self.transactions_df = pd.read_csv(f"{self.data_path}/transactions_data.csv")
            
            print("All financial advisor data files loaded successfully.")
        except Exception as e:
            print(f"Error loading data files: {str(e)}")
            raise
    
    def process_query(self, user_query: str, customer_id: str) -> str:
        """
        Process a user query and generate a response using the appropriate agent(s).
        
        Args:
            user_query: User's question or request
            customer_id: ID of the customer
            
        Returns:
            Response to the user query
        """
        print(f"Processing query for customer {customer_id}: {user_query}")
        
        try:
            # Get user context
            user_context = self._get_user_context(customer_id)
            
            # Classify the query to determine which agent(s) should handle it
            classification = self._classify_query(user_query, user_context)
            print(f"Query classification: {classification}")
            
            # Get responses from the appropriate agent(s)
            agent_responses = self._get_agent_responses(
                classification=classification,
                user_query=user_query,
                customer_id=customer_id,
                user_context=user_context
            )
            
            # Generate the final response
            final_response = self._generate_final_response(
                classification=classification,
                user_query=user_query,
                agent_responses=agent_responses,
                user_context=user_context
            )
            
            return final_response
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            return f"I apologize, but I'm having trouble processing your request at the moment. Please try again or ask a different question. Error details: {str(e)}"
    
    def process_query_with_formatting(self, user_query: str, customer_id: str) -> str:
        """
        Process a user query with enhanced formatting.
        
        Args:
            user_query: User's question or request
            customer_id: ID of the customer
            
        Returns:
            Properly formatted response to the user query
        """
        # Get the initial response
        response = self.process_query(user_query, customer_id)
        
        # Apply formatting fix if needed
        formatting_indicators = ['$', '%', 'goal', 'target', 'progress', 'complete', 
                              'budget', 'saving', 'investment', 'allocation']
        
        # If the response contains financial data that might need formatting fixes
        if any(indicator in response.lower() for indicator in formatting_indicators):
            # Look for specific formatting issues
            has_formatting_issues = (
                re.search(r'\$\d+[^,.]', response) or  # Missing commas in dollar amounts
                re.search(r'\d+%', response) or  # Missing space before percentage
                re.search(r'\d+\.\d+(?!%|\s|$)', response) or  # Decimal without formatting
                re.search(r'[a-zA-Z][\d$]', response) or  # Text running into numbers
                re.search(r'[\d%][a-zA-Z]', response)  # Numbers running into text
            )
            
            if has_formatting_issues:
                # Apply a second pass with formatting prompt
                formatting_prompt = FinancialAdvisorPrompts.FORMATTING_FIX_PROMPT.format(
                    original_text=response
                )
                
                # Generate a fixed version
                fixed_response = generate_text(
                    prompt=formatting_prompt,
                    system_prompt=self.enhanced_system_prompt,
                    temperature=1e-8,
                    max_tokens=len(response) + 200  # Allow some extra tokens for formatting
                )
                
                return fixed_response
        
        # Return the original response if no formatting fix is needed
        return response
    
    def _get_user_context(self, customer_id: str) -> Dict[str, Any]:
        """
        Get context information about the user.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Dictionary containing user context information
        """
        try:
            # Get user profile
            user_profile = self.user_profiles_df[
                self.user_profiles_df['Customer ID'] == customer_id
            ]
            
            if user_profile.empty:
                print(f"No user profile found for customer {customer_id}")
                return {"customer_id": customer_id}
            
            # Get goals for the customer
            customer_goals = self.financial_goals_df[
                self.financial_goals_df['Customer ID'] == customer_id.lower()
            ]
            
            # Get recent transactions
            recent_transactions = self.transactions_df[
                self.transactions_df['Customer ID'] == customer_id
            ].sort_values('Transaction Date and Time', ascending=False).head(5)
            
            # Extract user profile information
            profile_row = user_profile.iloc[0]
            
            # Create context dictionary
            context = {
                "customer_id": customer_id,
                "name": profile_row['Name'],
                "age": profile_row['Age'],
                "income": profile_row['Income'],
                "risk_profile": profile_row['Risk Profile'],
                "preferred_language": profile_row['Preferred Language'],
                "savings_balance": profile_row['Savings Balance'],
                "checking_balance": profile_row['Checking Balance'],
                "marital_status": profile_row['Marital Status'],
                "employment_type": profile_row['Employment Type'],
                "goal_count": len(customer_goals),
                "has_investments": True if not customer_goals.empty else False,
                "recent_transactions": self._format_recent_transactions(recent_transactions)
            }
            
            return context
            
        except Exception as e:
            print(f"Error getting user context: {str(e)}")
            return {"customer_id": customer_id}
    
    def _format_recent_transactions(self, transactions_df: pd.DataFrame) -> str:
        """Format recent transactions for display in context."""
        if transactions_df.empty:
            return "No recent transactions"
        
        # Format transaction details
        transaction_details = []
        for _, row in transactions_df.iterrows():
            transaction_details.append(
                f"{row['Merchant Name']} (${row['Transaction Amount']:.2f})"
            )
        
        return ", ".join(transaction_details)
    
    def _classify_query(self, user_query: str, user_context: Dict[str, Any]) -> List[str]:
        """
        Classify the user query to determine which agent(s) should handle it.
        
        Args:
            user_query: User's question or request
            user_context: Context information about the user
            
        Returns:
            List of agent categories in priority order
        """
        # For a production system, this would use a more sophisticated classifier
        # For demo purposes, we'll use a simpler heuristic approach first
        # and then refine with LLM classification
        
        # Simple heuristic classification based on keywords
        query_lower = user_query.lower()
        
        # Initial classification
        categories = []
        
        # Transaction Analysis keywords
        transaction_keywords = [
            "spend", "spending", "transaction", "purchase", "bought", "buy", 
            "budget", "expense", "money", "cost", "bill", "subscription", "paid"
        ]
        if any(keyword in query_lower for keyword in transaction_keywords):
            categories.append("Transaction Analysis")
        
        # Goal Planning keywords
        goal_keywords = [
            "goal", "save", "saving", "target", "planning", "retire", "retirement",
            "college", "education", "house", "home", "car", "travel", "vacation", "wedding"
        ]
        if any(keyword in query_lower for keyword in goal_keywords):
            categories.append("Goal Planning")
        
        # Asset Allocation keywords
        investment_keywords = [
            "invest", "investing", "investment", "portfolio", "stock", "bond", 
            "asset", "allocation", "fund", "etf", "mutual fund", "risk", "return"
        ]
        if any(keyword in query_lower for keyword in investment_keywords):
            categories.append("Asset Allocation")
        
        # Education keywords
        education_keywords = [
            "what is", "how does", "explain", "define", "mean", "difference between",
            "understand", "works", "concept"
        ]
        if any(keyword in query_lower for keyword in education_keywords):
            categories.append("Education")
        
        # If no categories matched or if the query is complex, use LLM classification
        if not categories or len(query_lower.split()) > 10:
            # Use LLM for more sophisticated classification
            categories = self._classify_with_llm(user_query, user_context)
        
        # If still no categories, default to General Financial Advice
        if not categories:
            categories = ["General Financial Advice"]
        
        # Add General Financial Advice as a fallback if not already included
        if "General Financial Advice" not in categories:
            categories.append("General Financial Advice")
        
        return categories
    
    def _classify_with_llm(self, user_query: str, user_context: Dict[str, Any]) -> List[str]:
        """
        Use LLM to classify the user query into agent categories.
        
        Args:
            user_query: User's question or request
            user_context: Context information about the user
            
        Returns:
            List of agent categories in priority order
        """
        try:
            # Create prompt for classification
            prompt = FinancialAdvisorPrompts.QUERY_CLASSIFICATION_PROMPT.format(
                user_query=user_query,
                goal_count=user_context.get("goal_count", 0),
                recent_transactions=user_context.get("recent_transactions", "None"),
                has_investments=user_context.get("has_investments", False),
                risk_profile=user_context.get("risk_profile", "Unknown")
            )
            
            # Generate classification
            system_prompt = FinancialAdvisorPrompts.SYSTEM_PROMPT
            classification_response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,
                max_tokens=500
            )
            
            # Extract the classification
            classification_match = re.search(
                r"CLASSIFICATION: (.*?)(?:\n|$)", 
                classification_response
            )
            
            if classification_match:
                # Parse the classification list
                classification_str = classification_match.group(1)
                categories = [
                    cat.strip() for cat in classification_str.split(",")
                ]
                
                # Validate categories
                valid_categories = [
                    "Transaction Analysis", "Goal Planning", 
                    "Asset Allocation", "Education", "General Financial Advice"
                ]
                
                categories = [cat for cat in categories if cat in valid_categories]
                
                return categories
            
            # Default to General Financial Advice if parsing fails
            return ["General Financial Advice"]
            
        except Exception as e:
            print(f"Error in LLM classification: {str(e)}")
            return ["General Financial Advice"]
    
    def _get_agent_responses(self, 
                           classification: List[str],
                           user_query: str,
                           customer_id: str,
                           user_context: Dict[str, Any]) -> Dict[str, str]:
        """
        Get responses from the appropriate specialized agents.
        
        Args:
            classification: List of agent categories in priority order
            user_query: User's question or request
            customer_id: ID of the customer
            user_context: Context information about the user
            
        Returns:
            Dictionary mapping agent categories to their responses
        """
        agent_responses = {}
        
        # Get responses from each applicable agent
        for category in classification:
            if category == "Transaction Analysis":
                # Get response from Transaction Analysis Agent
                nudges = self.transaction_agent.generate_nudges(customer_id)
                agent_responses["Transaction Analysis"] = nudges
                
            elif category == "Goal Planning":
                # Get response from Goal Planning Agent
                goal_response = self.goal_planning_agent.handle_goal_request(
                    request=user_query,
                    user_context=user_context
                )
                
                # Format the response based on type
                if isinstance(goal_response, dict) and goal_response.get("success", False):
                    response_type = goal_response.get("response_type", "")
                    
                    if response_type == "goal_created":
                        agent_responses["Goal Planning"] = (
                            f"Goal created successfully:\n"
                            f"Goal ID: {goal_response['goal_id']}\n"
                            f"Type: {goal_response['goal_data']['goal_type']}\n"
                            f"Target Amount: ${goal_response['goal_data']['target_amount']:,.2f}\n"
                            f"Monthly Contribution: ${goal_response['goal_data']['monthly_contribution']:,.2f}\n"
                            f"Timeline: {goal_response['goal_data']['goal_timeline']}\n\n"
                            f"{goal_response['strategy_explanation']}"
                        )
                    elif response_type == "all_goals":
                        goals_list = goal_response.get("goals", [])
                        if goals_list:
                            goals_text = "\n".join([
                                f"- {goal['Goal Type']}: ${goal['Target Amount']:,.2f} "
                                f"({goal['Progress (%)']:.1f}% complete, target: {goal['Target Date']})"
                                for goal in goals_list
                            ])
                            agent_responses["Goal Planning"] = f"Current financial goals:\n{goals_text}"
                        else:
                            agent_responses["Goal Planning"] = "No financial goals found."
                    elif response_type == "goal_recommendations":
                        agent_responses["Goal Planning"] = goal_response.get("recommendations", "")
                    else:
                        # For other response types, use the content if available
                        agent_responses["Goal Planning"] = goal_response.get("content", str(goal_response))
                else:
                    agent_responses["Goal Planning"] = str(goal_response)
                
            elif category == "Asset Allocation":
                # Get the customer's risk profile
                risk_profile = user_context.get("risk_profile", "Medium")
                
                # Default to a general allocation explanation if no specific request
                allocation_explanation = self.asset_allocation_agent.explain_allocation_strategy(
                    risk_profile=risk_profile,
                    goal_timeline="Medium-term"
                )
                
                agent_responses["Asset Allocation"] = allocation_explanation
                
            elif category == "Education":
                # Extract educational topic
                topic = self._extract_education_topic(user_query)
                
                # Get educational content
                educational_content = self.education_agent.get_educational_content(
                    topic=topic,
                    user_context=user_context
                )
                
                agent_responses["Education"] = educational_content
                
            elif category == "General Financial Advice":
                # Generate general financial advice
                general_advice = self._generate_general_advice(
                    user_query=user_query,
                    user_context=user_context
                )
                
                agent_responses["General Financial Advice"] = general_advice
        
        return agent_responses
    
    def _extract_education_topic(self, query: str) -> str:
        """Extract the educational topic from a query."""
        # Look for patterns like "explain X", "what is X", "tell me about X"
        explain_patterns = [
            r'explain (?:to me )?(?:what|how) (.*?)(?:is|works|means)(?:\?|$|\.)',
            r'explain (?:to me )?(?:about )?(.*?)(?:\?|$|\.)',
            r'what (?:is|are) (.*?)(?:\?|$|\.)',
            r'tell me about (.*?)(?:\?|$|\.)',
            r'how (?:does|do) (.*?) work(?:\?|$|\.)'
        ]
        
        for pattern in explain_patterns:
            match = re.search(pattern, query.lower())
            if match:
                # Captured topic might need cleaning
                topic = match.group(1).strip()
                # Remove filler words
                filler_words = ["the ", "a ", "an "]
                for word in filler_words:
                    if topic.startswith(word):
                        topic = topic[len(word):]
                return topic
        
        # Use a simpler approach if no pattern matches
        query_words = query.lower().split()
        if "what" in query_words and "is" in query_words:
            # Try to extract the topic after "what is"
            what_index = query_words.index("what")
            if what_index + 1 < len(query_words) and query_words[what_index + 1] == "is":
                # Extract the topic after "what is"
                topic_words = query_words[what_index + 2:]
                # Remove question mark if present
                if topic_words and topic_words[-1].endswith("?"):
                    topic_words[-1] = topic_words[-1][:-1]
                return " ".join(topic_words)
        
        # If no specific topic can be extracted, return a general term
        return "personal finance"
    
    def _generate_general_advice(self, user_query: str, user_context: Dict[str, Any]) -> str:
        """
        Generate general financial advice for the user.
        
        Args:
            user_query: User's question or request
            user_context: Context information about the user
            
        Returns:
            General financial advice as text
        """
        try:
            # Create prompt for general advice
            prompt = FinancialAdvisorPrompts.GENERAL_FINANCIAL_ADVICE_PROMPT.format(
                user_query=user_query,
                customer_id=user_context.get("customer_id", ""),
                age=user_context.get("age", "Unknown"),
                income=user_context.get("income", "Unknown"),
                risk_profile=user_context.get("risk_profile", "Unknown"),
                goal_count=user_context.get("goal_count", 0),
                savings_balance=user_context.get("savings_balance", 0),
                checking_balance=user_context.get("checking_balance", 0)
            )
            
            # Generate advice
            system_prompt = FinancialAdvisorPrompts.SYSTEM_PROMPT
            advice = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,
                max_tokens=1000
            )
            
            return advice
            
        except Exception as e:
            print(f"Error generating general advice: {str(e)}")
            return "I apologize, but I'm having trouble generating specific advice at the moment. Please try asking a more specific question about your finances."
    
    def _generate_final_response(self,
                               classification: List[str],
                               user_query: str,
                               agent_responses: Dict[str, str],
                               user_context: Dict[str, Any]) -> str:
        """
        Generate the final response by integrating responses from multiple agents.
        
        Args:
            classification: List of agent categories in priority order
            user_query: User's question or request
            agent_responses: Dictionary mapping agent categories to their responses
            user_context: Context information about the user
            
        Returns:
            Final integrated response
        """
        # If only one agent was used, return its response directly
        if len(agent_responses) == 1:
            category, response = next(iter(agent_responses.items()))
            
            # Add follow-up suggestions if appropriate
            follow_ups = self._generate_follow_up_suggestions(
                user_query=user_query,
                topic=category,
                focus_areas=category
            )
            
            return f"{response}\n\n{follow_ups}"
        
        # If multiple agents were used, integrate their responses
        try:
            # Format agent responses for the prompt
            transaction_response = agent_responses.get("Transaction Analysis", "No transaction analysis available.")
            goal_planning_response = agent_responses.get("Goal Planning", "No goal planning information available.")
            asset_allocation_response = agent_responses.get("Asset Allocation", "No asset allocation advice available.")
            education_response = agent_responses.get("Education", "No educational content available.")
            
            # Create prompt for response integration
            prompt = FinancialAdvisorPrompts.COMBINED_RESPONSE_PROMPT.format(
                user_query=user_query,
                transaction_response=transaction_response,
                goal_planning_response=goal_planning_response,
                asset_allocation_response=asset_allocation_response,
                education_response=education_response
            )
            
            # Generate integrated response
            system_prompt = FinancialAdvisorPrompts.SYSTEM_PROMPT
            integrated_response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,
                max_tokens=1500
            )
            
            # Add follow-up suggestions
            focus_areas = ", ".join(classification[:2])  # Use top two classifications
            follow_ups = self._generate_follow_up_suggestions(
                user_query=user_query,
                topic=classification[0],
                focus_areas=focus_areas
            )
            
            return f"{integrated_response}\n\n{follow_ups}"
            
        except Exception as e:
            print(f"Error generating final response: {str(e)}")
            
            # Fallback to concatenating responses
            combined_response = ""
            for category, response in agent_responses.items():
                combined_response += f"\n\n{category}:\n{response}"
            
            return combined_response.strip()
    
    def _generate_follow_up_suggestions(self, user_query: str, topic: str, focus_areas: str) -> str:
        """
        Generate suggested follow-up questions for the user.
        
        Args:
            user_query: User's original question
            topic: Main topic of the response
            focus_areas: Areas focused on in the response
            
        Returns:
            Formatted follow-up suggestions
        """
        try:
            # Create prompt for follow-up suggestions
            prompt = FinancialAdvisorPrompts.FOLLOW_UP_SUGGESTION_PROMPT.format(
                user_query=user_query,
                topic=topic,
                focus_areas=focus_areas
            )
            
            # Generate suggestions
            system_prompt = FinancialAdvisorPrompts.SYSTEM_PROMPT
            suggestions = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Use slightly higher temperature for variety
                max_tokens=300
            )
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating follow-up suggestions: {str(e)}")
            return ""


def main():
    """Main function to demonstrate the Financial Advisor Agent."""
    # Initialize the agent
    agent = FinancialAdvisorAgent()
    
    # Test processing a query
    customer_id = "CUSTOMER1"
    
    # Test queries for different specialized agents
    test_queries = [
        "How am I doing with my spending this month?",
        "What are my current financial goals?",
        "How should I invest my money based on my risk profile?",
        "Can you explain what compound interest is?",
        "Should I focus on saving for retirement or paying off my debt first?"
    ]
    
    for query in test_queries:
        print("\n" + "="*80)
        print(f"QUERY: {query}")
        print("="*80)
        
        response = agent.process_query_with_formatting(query, customer_id)
        
        print("\nRESPONSE:")
        print(response)
        print("="*80)


if __name__ == "__main__":
    main()