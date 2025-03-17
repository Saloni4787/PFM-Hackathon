"""
Transaction Analysis Agent

This script implements the Transaction Analysis Agent for the Personal Finance Manager,
which analyzes customer transaction data and generates relevant financial nudges.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Any
from dotenv import load_dotenv

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Compute the path to the project root (one level up from the 'agents' folder)
project_root = os.path.join(current_dir, '..')

# Add the project root to sys.path
sys.path.append(project_root)

# Import the LLM utility and prompts
from utils.llm_response import generate_text, DekaLLMClient
from prompts.transaction_agent_prompts import TransactionAnalysisPrompts

# Load environment variables
load_dotenv()

class TransactionAnalysisAgent:
    """
    Analyzes customer financial data and generates personalized nudges.
    
    This agent uses predefined prompts to analyze transaction data, detect patterns,
    and generate financial nudges aligned with customer goals.
    """
    
    def __init__(self, data_path: str = "./synthetic_data"):
        """
        Initialize the Transaction Analysis Agent.
        
        Args:
            data_path: Path to directory containing CSV data files
        """
        self.data_path = data_path
        self.llm_client = DekaLLMClient()
        self.nudge_definitions = self._load_nudge_definitions()
        
        # Load all data files
        self._load_data_files()
        
        print("Transaction Analysis Agent initialized successfully.")
    
    def _load_data_files(self):
        """Load all necessary data files from the data directory."""
        try:
            # Load transactions data
            self.transactions_df = pd.read_csv(f"{self.data_path}/transactions_data.csv")
            
            # Load user profiles
            self.user_profiles_df = pd.read_csv(f"{self.data_path}/user_profile_data.csv")
            
            # Load financial goals
            self.financial_goals_df = pd.read_csv(f"{self.data_path}/financial_goals_data.csv")
            
            # Load budget data
            self.budget_df = pd.read_csv(f"{self.data_path}/budget_data.csv")
            
            # Load subscription data
            self.subscription_df = pd.read_csv(f"{self.data_path}/subscription_data.csv")
            
            print("All data files loaded successfully.")
        except Exception as e:
            print(f"Error loading data files: {str(e)}")
            raise
    
    def _load_nudge_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Load predefined nudge definitions.
        
        Returns:
            Dictionary of nudge definitions with pattern detection criteria
        """
        # This would ideally be loaded from a JSON file or database,
        # but for simplicity we'll define it here
        return {
            "high_category_spending": {
                "name": "High Category Spending",
                "description": "Unusually high spending in a specific category",
                "threshold_percentage": 30,  # 30% higher than average
                "check_function": self._check_high_category_spending,
                "categories": ["dining", "entertainment", "shopping", "groceries", "utilities"]
            },
            "recurring_subscriptions": {
                "name": "Recurring Subscriptions",
                "description": "Identification of recurring subscription payments",
                "check_function": self._check_subscription_burden
            },
            "budget_threshold": {
                "name": "Budget Threshold Alert",
                "description": "Notification when approaching budget limit",
                "threshold_percentage": 80,  # % of budget
                "check_function": self._check_budget_threshold
            },
            "goal_progress": {
                "name": "Goal Progress",
                "description": "Update on progress towards financial goals",
                "check_function": self._check_goal_progress
            },
            "low_balance_alert": {
                "name": "Low Balance Alert",
                "description": "Alert when account balance falls below threshold",
                "threshold_amount": 200,
                "check_function": self._check_low_balance
            },
            "savings_opportunity": {
                "name": "Savings Opportunity",
                "description": "Potential to save money based on spending patterns",
                "categories": ["dining", "entertainment", "shopping"],
                "check_function": self._check_savings_opportunity
            },
            "large_transaction": {
                "name": "Large Transaction",
                "description": "Detection of unusually large transactions",
                "check_function": self._check_large_transactions
            },
            "transaction_frequency": {
                "name": "High Transaction Frequency",
                "description": "Unusually high number of transactions in a category",
                "check_function": self._check_transaction_frequency
            }
        }
    
    def get_applicable_nudges(self, customer_id: str) -> List[str]:
        """
        Determine which nudges are applicable for a specific customer.
        
        Args:
            customer_id: The ID of the customer to analyze
            
        Returns:
            List of nudge IDs that are applicable to the customer
        """
        applicable_nudges = []
        
        for nudge_id, nudge_def in self.nudge_definitions.items():
            # Call the check function for this nudge type
            if nudge_def["check_function"](customer_id):
                applicable_nudges.append(nudge_id)
        
        return applicable_nudges
    
    def _check_high_category_spending(self, customer_id: str) -> bool:
        """Check if customer has unusually high spending in any category."""
        # Get customer transactions
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # Simple implementation - in real system would be more sophisticated
        if len(customer_txns) > 0:
            # Check if any transaction is over $200
            return any(customer_txns['Transaction Amount'] > 200)
        return False
    
    def _check_subscription_burden(self, customer_id: str) -> bool:
        """Check if customer has multiple subscriptions."""
        customer_subs = self.subscription_df[self.subscription_df['Customer ID'] == customer_id]
        # If customer has more than 1 subscription, this nudge is applicable
        return len(customer_subs) > 1
    
    def _check_budget_threshold(self, customer_id: str) -> bool:
        """Check if any budget category is approaching threshold."""
        customer_budgets = self.budget_df[self.budget_df['Customer ID'] == customer_id]
        
        # Check if any budget category is over 80% utilized
        return any(customer_budgets['% Utilized'] > 80)
    
    def _check_goal_progress(self, customer_id: str) -> bool:
        """Check if customer has any active financial goals."""
        customer_goals = self.financial_goals_df[self.financial_goals_df['Customer ID'] == customer_id.lower()]
        # If customer has any goals, this nudge is applicable
        return len(customer_goals) > 0
    
    def _check_low_balance(self, customer_id: str) -> bool:
        """Check if customer account balance is low."""
        # Get customer profile
        customer_profile = self.user_profiles_df[self.user_profiles_df['Customer ID'] == customer_id]
        
        if not customer_profile.empty:
            # Check if checking balance is below threshold ($500)
            return customer_profile['Checking Balance'].values[0] < 500
        return False
    
    def _check_savings_opportunity(self, customer_id: str) -> bool:
        """Check if there are savings opportunities based on spending patterns."""
        # For MVP, we'll assume this is applicable for all customers
        return True
    
    def _check_large_transactions(self, customer_id: str) -> bool:
        """Check for unusually large transactions."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # Look for transactions over $400
        return any(customer_txns['Transaction Amount'] > 400)
    
    def _check_transaction_frequency(self, customer_id: str) -> bool:
        """Check for high frequency of transactions in any category."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # If more than 5 transactions, consider this applicable
        return len(customer_txns) > 5
    
    def _format_data_for_prompt(self, customer_id: str) -> Dict[str, str]:
        """
        Format customer data for use in prompts.
        
        Args:
            customer_id: ID of the customer to analyze
            
        Returns:
            Dictionary with formatted data strings for each data type
        """
        # Get customer-specific data
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        customer_profile = self.user_profiles_df[self.user_profiles_df['Customer ID'] == customer_id]
        customer_goals = self.financial_goals_df[self.financial_goals_df['Customer ID'] == customer_id.lower()]
        customer_budgets = self.budget_df[self.budget_df['Customer ID'] == customer_id]
        customer_subs = self.subscription_df[self.subscription_df['Customer ID'] == customer_id]
        
        # Format each dataset as a string
        formatted_data = {
            "transaction_data": customer_txns.to_string(index=False) if not customer_txns.empty else "No transaction data available.",
            "user_profile": customer_profile.to_string(index=False) if not customer_profile.empty else "No profile data available.",
            "financial_goals": customer_goals.to_string(index=False) if not customer_goals.empty else "No financial goals set.",
            "budget_data": customer_budgets.to_string(index=False) if not customer_budgets.empty else "No budget data available.",
            "subscription_data": customer_subs.to_string(index=False) if not customer_subs.empty else "No subscription data available."
        }
        
        return formatted_data
    
    def generate_nudges(self, customer_id: str) -> str:
        """
        Generate personalized financial nudges for a customer.
        
        Args:
            customer_id: ID of the customer to analyze
            
        Returns:
            Formatted nudge response as a string
        """
        print(f"Generating nudges for customer {customer_id}...")
        
        # Get applicable nudge types for this customer
        applicable_nudges = self.get_applicable_nudges(customer_id)
        
        if not applicable_nudges:
            return "No relevant nudges found for this customer at this time."
        
        print(f"Applicable nudge types: {', '.join(applicable_nudges)}")
        print(f"Number of applicable nudges: {len(applicable_nudges)}")
        
        # Format customer data for prompts
        formatted_data = self._format_data_for_prompt(customer_id)
        
        # Create a specialized prompt based on applicable nudges
        nudge_prompt = self._create_specialized_nudge_prompt(customer_id, applicable_nudges, formatted_data)
        
        # Call the LLM to generate nudges
        system_prompt = TransactionAnalysisPrompts.SYSTEM_PROMPT
        nudge_response = generate_text(
            prompt=nudge_prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=3000
        )
        
        # Format the final response
        formatting_prompt = TransactionAnalysisPrompts.RESPONSE_FORMATTING_PROMPT
        final_response = generate_text(
            prompt=f"{formatting_prompt}\n\nNudges to format (ONLY for these applicable types: {', '.join(applicable_nudges)}):\n{nudge_response}",
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=2000
        )
        
        return final_response
    
    def _create_specialized_nudge_prompt(
        self, 
        customer_id: str, 
        applicable_nudges: List[str],
        formatted_data: Dict[str, str]
    ) -> str:
        """
        Create a specialized prompt based on applicable nudge types.
        
        Args:
            customer_id: ID of the customer
            applicable_nudges: List of applicable nudge types
            formatted_data: Dictionary with formatted customer data
            
        Returns:
            Specialized prompt text
        """
        # Start with basic analysis prompt
        base_prompt = TransactionAnalysisPrompts.TRANSACTION_ANALYSIS_PROMPT.format(
            customer_id=customer_id,
            transaction_data=formatted_data["transaction_data"],
            user_profile=formatted_data["user_profile"],
            financial_goals=formatted_data["financial_goals"],
            budget_data=formatted_data["budget_data"],
            subscription_data=formatted_data["subscription_data"]
        )
        
        # If no applicable nudges, add a clear message
        if not applicable_nudges:
            return base_prompt + "\n\nBased on analysis, there are no applicable nudges for this customer at this time."
        
        # Add instruction to focus only on applicable nudges
        specialized_sections = [
            f"Focus ONLY on generating the following types of nudges that are relevant to this customer: {', '.join(applicable_nudges)}."
        ]
        
        # Create a mapping of nudge types to their specialized prompts
        nudge_prompt_mapping = {
            "budget_threshold": TransactionAnalysisPrompts.BUDGET_ALERT_PROMPT.format(
                customer_id=customer_id,
                budget_data=formatted_data["budget_data"]
            ),
            "recurring_subscriptions": TransactionAnalysisPrompts.SUBSCRIPTION_ANALYSIS_PROMPT.format(
                customer_id=customer_id,
                subscription_data=formatted_data["subscription_data"]
            ),
            "goal_progress": TransactionAnalysisPrompts.GOAL_ALIGNMENT_PROMPT.format(
                customer_id=customer_id,
                financial_goals=formatted_data["financial_goals"],
                transaction_data=formatted_data["transaction_data"]
            ),
            "high_category_spending": f"""
                Analyze the transaction data for {customer_id} and identify categories with unusually high spending.
                Compare spending in each category against typical patterns and highlight significant increases.
                Connect this insight to the customer's goals and suggest actionable ways to manage category spending.
            """,
            "savings_opportunity": f"""
                Review the transaction data for {customer_id} and identify potential savings opportunities.
                Look for areas where spending could be optimized or reduced.
                Quantify the potential savings and relate them to the customer's financial goals.
            """,
            "low_balance_alert": f"""
                Review the following account balance information for {customer_id}:
                
                User Profile:
                {formatted_data["user_profile"]}
                
                The safe threshold for checking account balance is $500.
                This customer's checking balance is below this threshold.
                
                Generate a low balance alert nudge that:
                1. Specifies the current checking balance amount
                2. Alerts the customer to potential issues this might cause
                3. Considers any upcoming transactions or payments visible in the transaction data
                4. Provides specific actionable recommendations to address the low balance
                5. If applicable, connects this situation to their financial goals
            """,
            "large_transaction": f"""
                Analyze the following transaction data for {customer_id} to identify unusually large transactions:
                
                Transaction Data:
                {formatted_data["transaction_data"]}
                
                Budget Data:
                {formatted_data["budget_data"]}
                
                For this analysis, consider transactions over $400 as "large transactions."
                
                Generate a large transaction nudge that:
                1. Identifies specific large transactions by date, amount, and merchant
                2. Provides context on how these transactions compare to the customer's usual spending
                3. Connects these transactions to budget categories where applicable
                4. Offers relevant financial advice related to these large expenditures
                5. If these transactions impact financial goals, highlight the connection
            """,
            "transaction_frequency": f"""
                Analyze the following transaction data for {customer_id} to identify categories with high transaction frequency:
                
                Transaction Data:
                {formatted_data["transaction_data"]}
                
                User Profile:
                {formatted_data["user_profile"]}
                
                Financial Goals:
                {formatted_data["financial_goals"]}
                
                Generate a transaction frequency nudge that:
                1. Identifies specific categories where the customer has made frequent transactions
                2. Provides the exact count of transactions in these categories
                3. Compares this to what would be considered a normal frequency
                4. Highlights any potential impact on their budget or financial goals
                5. Offers actionable suggestions that could optimize their transaction behavior
            """
        }
        
        # Add specialized sections only for applicable nudges
        for nudge_type in applicable_nudges:
            if nudge_type in nudge_prompt_mapping:
                specialized_sections.append(nudge_prompt_mapping[nudge_type])
        
        # Add instructions to omit non-applicable nudges
        non_applicable = [nudge for nudge in self.nudge_definitions.keys() if nudge not in applicable_nudges]
        if non_applicable:
            specialized_sections.append(
                f"Do NOT generate nudges for the following types, as they are not applicable to this customer at this time: {', '.join(non_applicable)}."
            )
        
        # Combine all prompt sections
        full_prompt = base_prompt + "\n\n" + "\n\n".join(specialized_sections)
        
        return full_prompt


def main():
    """Main function to demonstrate the Transaction Analysis Agent."""
    # Initialize the agent
    agent = TransactionAnalysisAgent()
    
    # Process one customer as example
    customer_id = "CUSTOMER1"
    
    # First show which nudges are applicable for this customer
    applicable_nudges = agent.get_applicable_nudges(customer_id)
    
    print("\n" + "="*50)
    print(f"ANALYSIS FOR CUSTOMER: {customer_id}")
    print("="*50)
    print(f"All possible nudge types: {', '.join(agent.nudge_definitions.keys())}")
    print(f"Applicable nudge types: {', '.join(applicable_nudges)}")
    print(f"Number of applicable nudges: {len(applicable_nudges)}")
    print("="*50)
    
    # Generate nudges
    nudges = agent.generate_nudges(customer_id)
    
    # Print the results
    print("\n" + "="*50)
    print(f"FINANCIAL NUDGES FOR {customer_id}")
    print("="*50)
    print(nudges)
    print("="*50)
    
    # Uncomment to process all customers
    """
    print("\nProcessing all customers...")
    for customer_id in available_customers:
        applicable_nudges = agent.get_applicable_nudges(customer_id)
        print(f"\nCustomer {customer_id}: {len(applicable_nudges)} applicable nudges")
        print(f"Applicable types: {', '.join(applicable_nudges)}")
    """


if __name__ == "__main__":
    main()