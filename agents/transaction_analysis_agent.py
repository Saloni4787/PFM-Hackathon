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
            self.transactions_df = self.transactions_df[self.transactions_df["Transaction Status"].isin(["Completed","Pending"])]
            self.transactions_df = self.transactions_df[self.transactions_df["Transaction Type"].isin(["Withdrawal","Payment", "Transfer", "Purchase", "Deposit"])]
            
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
            },
            # Event-based nudges
            "salary_deposit": {
                "name": "Salary Deposit Detected",
                "description": "Detection of recurring salary deposits",
                "check_function": self._check_salary_deposit
            },
            "bill_payment": {
                "name": "Bill Payment Reminder",
                "description": "Reminders for upcoming bill payments",
                "check_function": self._check_bill_payment
            },
            "recurring_charge": {
                "name": "Recurring Charge Change",
                "description": "Detection of changes in recurring charge amounts",
                "check_function": self._check_recurring_charge_change
            },
            "unusual_activity": {
                "name": "Unusual Account Activity",
                "description": "Detection of unusual spending patterns or transactions",
                "check_function": self._check_unusual_activity
            },
            "overdraft_fee": {
                "name": "Overdraft Fee",
                "description": "Alert when overdraft fees are charged",
                "check_function": self._check_overdraft_fee
            },
            "goal_milestone": {
                "name": "Financial Goal Milestone",
                "description": "Notification when a financial goal milestone is reached",
                "check_function": self._check_goal_milestone
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
        
        # # Simple implementation - in real system would be more sophisticated
        # if len(customer_txns) > 0:
        #     # Check if any transaction is over $200
        #     return any(customer_txns['Transaction Amount'] > 200)
        # return False
        
      
        if not customer_txns.empty:
            # Group by category and check if any category has transactions over $200
            high_spending = customer_txns.groupby('Merchant Category')['Transaction Amount'].max() > 200

            # Return True if any category has high spending
            return high_spending.any()
        
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
        # return len(customer_txns) > 5
        # Count transactions per merchant category
        category_counts = customer_txns['Merchant Category'].value_counts()

        # Filter categories with more than 3 transactions
        high_freq_categories = category_counts[category_counts >= 3].index.tolist()

        return any(high_freq_categories)
    
    # Event-based nudge check functions
    def _check_salary_deposit(self, customer_id: str) -> bool:
        """Check for recurring salary deposits."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        if not customer_txns.empty:
            # Look for deposits with employment indicators
            potential_salary = customer_txns[
                (customer_txns['Transaction Type'] == 'Deposit') & 
                (customer_txns['Transaction Amount'] > 1000) &
                (
                    (customer_txns['Payment Mode'] == 'Direct Deposit') |
                    (customer_txns['Merchant Name'].str.contains('employer|payroll|salary', case=False, na=False))
                )
            ]
            return len(potential_salary) > 0
        return False
    
    def _check_bill_payment(self, customer_id: str) -> bool:
        """Check for upcoming bill payments based on historical patterns."""
        # For MVP, we'll check if there are any transactions with "bill", "payment", or "utility" in description
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        if not customer_txns.empty:
            bill_related = customer_txns['Description'].str.contains('bill|payment|utility', case=False)
            return bill_related.any()
        return False
    
    def _check_recurring_charge_change(self, customer_id: str) -> bool:
        """Check for changes in recurring charge amounts."""
        # This would normally compare current subscription costs to previous months
        # For MVP, we'll assume this applies if customer has subscriptions
        customer_subs = self.subscription_df[self.subscription_df['Customer ID'] == customer_id]
        return not customer_subs.empty
    
    def _check_unusual_activity(self, customer_id: str) -> bool:
        """Check for unusual activity based on transaction amount using IQR method."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # In a real system, this would be more sophisticated with statistical analysis
        # For now, consider transactions over $300 as unusual
        if not customer_txns.empty:
            return any(customer_txns['Transaction Amount'] > 300)
        return False
    
    def _check_overdraft_fee(self, customer_id: str) -> bool:
        """Check if customer has been charged overdraft fees."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # Look for transactions with "overdraft fee" or "overdraft charge" in description
        if not customer_txns.empty:
            overdraft_txns = customer_txns['Description'].str.contains('overdraft', case=False)
            return overdraft_txns.any()
        return False
    
    def _check_goal_milestone(self, customer_id: str) -> bool:
        """Check if customer has reached a milestone for any financial goal."""
        customer_goals = self.financial_goals_df[self.financial_goals_df['Customer ID'] == customer_id.lower()]
        
        # For MVP, assume milestone is reached if goal is at least 50% complete
        if not customer_goals.empty:
            return any(customer_goals['Progress (%)'] >= 50)
        return False
    
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
    
    def check_unusual_activity(self, customer_id: str) -> bool:
        """Check for unusual activity based on transaction amount using IQR method."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
                
        # Calculate IQR for transaction amounts
        amounts = customer_txns['Transaction Amount']
        q1 = amounts.quantile(0.25)
        q3 = amounts.quantile(0.75)
        iqr = q3 - q1
        
        # Define upper bound for outliers (Q3 + 1.5*IQR)
        upper_bound = q3 + 1.5 * iqr
        
        # Find transactions that exceed the upper bound
        unusual_txns = customer_txns[amounts > upper_bound]
        
        # Return True if any unusual transactions are found
        return unusual_txns
        
    def check_high_category_spending(self, customer_id: str) -> str:
        """Return the category with the highest spending if over $200, else return None."""
        # Get customer transactions
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]

        if not customer_txns.empty:
            # Group by category and find the max transaction amount per category
            category_max_spending = customer_txns.groupby('Merchant Category')['Transaction Amount'].max()

            # Filter categories where spending is above $200
            high_spending_categories = category_max_spending[category_max_spending > 200]

            if not high_spending_categories.empty:
                # Return the category with the highest spending
                print(high_spending_categories.idxmax())
                return high_spending_categories.idxmax()
                    
    def check_large_transactions(self, customer_id: str) -> bool:
        """Check for unusually large transactions."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        # Look for transactions over $400
        largest_transaction = customer_txns.loc[customer_txns['Transaction Amount'].idxmax()]

        return largest_transaction
    
    def check_transaction_frequency(self, customer_id: str) -> bool:
        """Check for high frequency of transactions in any category."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # If more than 5 transactions, consider this applicable
        # return len(customer_txns) > 5
        # Count transactions per merchant category
        category_counts = customer_txns['Merchant Category'].value_counts()

        # Filter categories with more than 5 transactions
        high_freq_categories = category_counts[category_counts > 3].index.tolist()
        highest_freq_category = category_counts.idxmax()

        return highest_freq_category

    
    def check_salary_deposit(self, customer_id: str) -> bool:
        """Check for recurring salary deposits."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        if not customer_txns.empty:
            # Look for deposits with employment indicators
            potential_salary = customer_txns[
                (customer_txns['Transaction Type'] == 'Deposit') & 
                (customer_txns['Transaction Amount'] > 1000) &
                (
                    (customer_txns['Payment Mode'] == 'Direct Deposit') |
                    (customer_txns['Merchant Name'].str.contains('employer|payroll|salary', case=False, na=False))
                )
            ]
            return potential_salary
    def check_overdraft_fee(self, customer_id: str) -> bool:
        """Check if customer has been charged overdraft fees."""
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        # Look for transactions with "overdraft fee" or "overdraft charge" in description
        if not customer_txns.empty:
            overdraft_txns = customer_txns['Description'].str.contains('overdraft', case=False)
            return overdraft_txns
     
    def check_bill_payment(self, customer_id: str) -> bool:
        """Check for upcoming bill payments based on historical patterns."""
        # For MVP, we'll check if there are any transactions with "bill", "payment", or "utility" in description
        customer_txns = self.transactions_df[self.transactions_df['Customer ID'] == customer_id]
        
        if not customer_txns.empty:
            bill_related = customer_txns['Description'].str.contains('bill|payment|utility', case=False)
            return bill_related 
    
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
        
        # Add explicit formatting guidelines to the prompt
        nudge_prompt += "\n\n" + TransactionAnalysisPrompts.TRANSACTION_FORMATTING_GUIDE
        nudge_prompt += "\n\nThese formatting requirements are CRITICAL and must be applied consistently throughout your response."
        
        # Enhanced system prompt with explicit formatting requirements
        system_prompt = TransactionAnalysisPrompts.SYSTEM_PROMPT + """

CRITICAL FORMATTING REQUIREMENTS:
1. ALWAYS format monetary values as "$ 123.45" with a space after the dollar sign
2. ALWAYS add spaces between words - never allow words to run together
3. ALWAYS format transaction IDs with a space after them: "TX12345 "
4. NEVER allow character-by-character spacing in the output (like "1 0 0")
5. ALWAYS use proper spacing in descriptive phrases (like "per month" not "permonth")
6. ALWAYS format parenthetical amounts as " ($ 123.45) " with spaces inside and outside
7. ALWAYS format numbers with proper digit grouping (e.g., "$ 1,200" not "$ 1200")

These formatting standards are non-negotiable and must be followed perfectly.
"""
        
        # Call the LLM to generate nudges
        nudge_response = generate_text(
            prompt=nudge_prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=3000
        )
        
        # Format the final response with explicit formatting instructions
        formatting_prompt = TransactionAnalysisPrompts.RESPONSE_FORMATTING_PROMPT + """

REMINDER - These formatting requirements are ABSOLUTELY CRITICAL:
1. EVERY monetary amount must be formatted as "$ 123.45" (with a space after the $ sign)
2. EVERY transaction ID must have a space after it: "TX12345 " not "TX12345"
3. ALL words must have proper spacing between them - NO words should run together
4. ALL parenthetical amounts must be formatted as " ($ 123.45) " (with spaces inside and outside)
5. EVERY descriptive phrase must have proper spaces: "per month" not "permonth"
6. NEVER output text with character-by-character spacing (like "1 0 0" or "p e r")
7. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"

The quality of your response will be primarily judged on whether you follow these formatting rules perfectly.
Make sure to ONLY OUTPUT THE DOCUMENT
"""
        
        final_response = generate_text(
            prompt=f"{formatting_prompt}\n\nNudges to format (ONLY for these applicable types: {', '.join(applicable_nudges)}):\n{nudge_response}",
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=2000
        )
        
        # One quick check to verify the formatting is correct
        verification_prompt = """
        This is a verification pass to make sure the document follows the critical formatting requirements.
        
        Check EVERY INSTANCE of these elements and fix ANY that don't conform:
        
        1. ALL monetary amounts: Must be "$ 123.45" with a space after the dollar sign
        2. ALL transaction IDs: Must have a space after them, like "TX12345 "
        3. ALL words: Must have proper spacing - no run-together words
        4. ALL parenthetical amounts: Must be " ($ 123.45) " with spaces
        5. ALL numeric values in text: Must have proper spacing "$ 100 per month"
        
        If you see ANY formatting issues at all, fix them.
        
        Document to verify:
        
        {response}
        
        ONLY OUTPUT THE DOCUMENT
        """
        
        # Run a verification to catch any remaining issues
        final_response = generate_text(
            prompt=verification_prompt.format(response=final_response),
            system_prompt="You are a financial document formatting expert. Your only job is to ensure the document follows the required formatting rules EXACTLY as specified.",
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
        
        # Add important formatting reminder
        specialized_sections.append("""
        REMEMBER: All monetary values MUST be formatted as "$ 123.45" with a space after the dollar sign.
        All transaction IDs MUST have a space after them (e.g., "TX12345 ").
        All words in descriptive phrases MUST have proper spacing (e.g., "per month" not "permonth").
        All parenthetical amounts MUST be formatted as " ($ 123.45) " with spaces inside and outside.
        NEVER allow words to run together without spaces.
        NEVER allow character-by-character spacing in the output.
        """)
        
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
                This is the highest category spending transactions {self.check_high_category_spending}. 
                Analyze the transaction and identify categories with unusually high spending. 
                Explain about the transaction and why it is considered high. Output the highest transaction.
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
                This is the largest transactions {self.check_large_transactions}
                Analyze and Explain about the transactions and why it is considered large transaction.
                
                Budget Data:
                {formatted_data["budget_data"]}
                
                Generate a large transaction nudge that:
                1. Identifies specific large transactions by date, amount, and merchant
                2. Provides context on how these transactions compare to the customer's usual spending
                3. Connects these transactions to budget categories where applicable
                4. Offers relevant financial advice related to these large expenditures
                5. If these transactions impact financial goals, highlight the connection
            """,
            "transaction_frequency": f"""
                {self.check_transaction_frequency}
                This is the transaction with highest category frequency.
                Analyse and Explain about the transaction and why it is considered high frequency.
                
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
            """,
            # Event-based nudge prompts
            "salary_deposit": f"""
                {self.check_salary_deposit}
                This is the salary deposit transaction.
                                
                User Profile:
                {formatted_data["user_profile"]}
                
                Financial Goals:
                {formatted_data["financial_goals"]}
                
                Generate a salary deposit nudge that:
                1. Identifies the recent salary deposit(s) with amount and date
                2. Suggests optimal allocation of this income based on their goals
                3. Recommends specific actions that align with their financial priorities
                4. If applicable, suggests automating transfers to savings or investment accounts
                5. Relates the recommendations to their budget categories and goal progress
            """,
            "bill_payment": f"""
                {self.check_bill_payment}
                This is the recurring bill payments transaction.
                
                User Profile:
                {formatted_data["user_profile"]}
                
                Budget Data:
                {formatted_data["budget_data"]}
                
                Generate a bill payment reminder nudge that:
                1. Identifies upcoming bill payments based on historical patterns
                2. Provides the specific dates and expected amounts
                3. Alerts if there might be insufficient funds for any upcoming payments
                4. Suggests budget adjustments if needed
                5. Offers recommendations for managing bill payments more effectively
            """,
            "recurring_charge_change": TransactionAnalysisPrompts.RECURRING_CHARGE_PROMPT.format(
                customer_id=customer_id,
                subscription_data=formatted_data["subscription_data"],
                transaction_data=formatted_data["transaction_data"]
            ),
            "unusual_activity": f"""
                {self.check_unusual_activity}
                These are the unusual activity transaction. Explain about the transaction and why it is considered unusual.
                
                User Profile:
                {formatted_data["user_profile"]}
                
                Generate an unusual activity nudge that:
                1. Identifies specific transactions that appear unusual (based on amount, merchant, location, etc.)
                2. Explains why these transactions stand out from normal patterns
                3. Asks if these transactions were authorized
                4. Provides guidance on monitoring account activity
                5. Suggests security measures if appropriate
            """,
            "overdraft_fee": f"""
                {self.check_overdraft_fee}
                This is the overdraft fee transaction.
                
                User Profile:
                {formatted_data["user_profile"]}
                
                Generate an overdraft fee alert nudge that:
                1. Identifies the specific overdraft fee charge(s) with date and amount
                2. Explains the circumstances that led to the overdraft
                3. Calculates the total amount paid in overdraft fees
                4. Provides specific strategies to avoid future overdrafts
                5. If applicable, suggests account types or settings that could prevent overdrafts
            """,
            "goal_milestone": TransactionAnalysisPrompts.GOAL_MILESTONE_PROMPT.format(
                customer_id=customer_id,
                financial_goals=formatted_data["financial_goals"]
            )
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
        
        # Add final reminder about formatting requirements
        specialized_sections.append("""
        FINAL CRITICAL REMINDER: 
        - ALL monetary values MUST be formatted as "$ 123.45" with a space after the dollar sign
        - ALL transaction IDs MUST have a space after them like "TX12345 "
        - NEVER allow character-by-character spacing in your output
        - NEVER allow words to run together like "permonth" instead of "per month"
        - ALWAYS format ranges with proper spacing: "$ 200 - $ 500" not "$200-$500"
        - ALWAYS format parenthetical amounts as " ($ 123.45) " with spaces inside and outside
        
        The quality of your response will be primarily judged by whether you format ALL text elements correctly.
        
        ONLY OUTPUT THE NUDGES
        """)
        
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
    print(f"large transactions : {agent.check_large_transactions(customer_id)}")
    print(f"high category spending : {agent.check_high_category_spending(customer_id)}")
        
    # Generate nudges
    nudges = agent.generate_nudges(customer_id)
    large_t = agent.check_large_transactions(customer_id)
    high_t = agent.check_high_category_spending(customer_id)
    
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