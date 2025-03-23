"""
Financial Advisor Agent

This script implements the Financial Advisor Agent for the Personal Finance Manager,
which serves as the central coordinator for all specialized agents and provides
holistic financial guidance to users.

This updated version includes context management to maintain conversation history
and rewrite context-dependent queries.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Any, Tuple
import traceback
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
from utils.context_management import ContextManager

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
        
        # Initialize context manager for conversation context
        self.context_manager = ContextManager(max_history=5)
        
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
    
    def process_query(self, user_query: str, customer_id: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Process a user query and generate a response using the appropriate agent(s).
        Now with context management to maintain conversation continuity.
        
        Args:
            user_query: User's question or request
            customer_id: ID of the customer
            chat_history: List of previous conversation turns (optional)
            
        Returns:
            Response to the user query
        """
        print(f"Processing query for customer {customer_id}: {user_query}")
        
        try:
            # Apply context management if chat history is provided
            rewritten_query = user_query
            query_rewritten = False
            
            if chat_history and len(chat_history) > 0:
                print(f"Applying context management with {len(chat_history)} history items")
                rewritten_query, query_rewritten = self.context_manager.rewrite_query(user_query, chat_history)
                
                if query_rewritten:
                    print(f"Query rewritten: '{user_query}' -> '{rewritten_query}'")
            
            # Get user context
            user_context = self._get_user_context(customer_id)
            
            # First, directly check if this is a goal-focused request using LLM
            is_goal_focused = self._is_goal_related_request(rewritten_query)
            print(f"Is goal-focused (LLM check): {is_goal_focused}")
            
            # If it's explicitly a goal creation/modification request, route directly to Goal Planning
            if is_goal_focused:
                # Goal-focused requests should prioritize Goal Planning
                classification = ["Goal Planning"]
                print("Goal-focused request detected, prioritizing Goal Planning agent")
            else:
                # If not explicitly goal-focused, use standard classification
                classification = self._classify_query(rewritten_query, user_context)
                print(f"Query classification: {classification}")
            
            # Log the classification
            print(f"Request classification: {classification}")
            
            # Get responses from the appropriate agent(s)
            agent_responses = self._get_agent_responses(
                classification=classification,
                user_query=rewritten_query,  # Use the rewritten query
                customer_id=customer_id,
                user_context=user_context,
                is_goal_focused=is_goal_focused
            )
            
            # Generate the final response
            final_response = self._generate_final_response(
                classification=classification,
                user_query=rewritten_query,  # Use the rewritten query
                agent_responses=agent_responses,
                user_context=user_context
            )
            
            return final_response
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")
            print(traceback.print_exc())
            return f"I apologize, but I'm having trouble processing your request at the moment. Please try again or ask a different question. Error details: {str(e)}"
    
    def process_query_with_formatting(self, user_query: str, customer_id: str, chat_history: List[Dict[str, str]] = None) -> str:
        """
        Process a user query with enhanced formatting.
        
        Args:
            user_query: User's question or request
            customer_id: ID of the customer
            chat_history: List of previous conversation turns (optional)
            
        Returns:
            Properly formatted response to the user query
        """
        # Get the initial response
        response = self.process_query(user_query, customer_id, chat_history)
        
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
    
    def _is_goal_related_request(self, user_query: str) -> bool:
        """
        Use LLM to directly check if this is a goal-related request.
        This is a dedicated check for goal intents to improve classification accuracy.
        
        Args:
            user_query: User's question or request
            
        Returns:
            bool: True if the query is goal-related, False otherwise
        """
        try:
            # Create a prompt specifically for goal intent detection
            prompt = """
Determine if the user's query is explicitly about creating, updating, or managing a financial goal.

Examples of goal-related requests:
- "I want to create a new goal for retirement"
- "Set up an emergency fund for $5000"
- "I need to save $20,000 for a house"
- "Create a vacation savings goal of $3000 by next summer"
- "Save for my child's education"
- "Start a car purchase fund"
- "Make a new goal for $10,000"
- "Update my emergency fund goal"
- "Delete my vacation goal"

User query: "{query}"

Is the user specifically asking to create, modify, or manage a financial goal? Answer with only YES or NO.
""".format(query=user_query)
            
            # Get the classification
            system_prompt = "You are a helpful assistant that classifies financial queries."
            
            response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,  # Use 0 temperature for deterministic output
                max_tokens=10   # Very few tokens needed
            )
            
            # Check if the response is YES
            return response.strip().upper() == "YES"
            
        except Exception as e:
            print(f"Error in goal intent detection: {str(e)}")
            # Fall back to regex in case of error
            goal_creation_patterns = [
                r"create (?:a |new |)goal",
                r"set up (?:a |new |)goal",
                r"start (?:a |new |)goal",
                r"establish (?:a |new |)goal",
                r"save for",
                r"emergency fund",
                r"retirement fund",
                r"education fund",
                r"home purchase",
                r"travel fund",
                r"car fund",
                r"wedding fund",
                r"medical expense"
            ]
            
            query_lower = user_query.lower()
            return any(re.search(pattern, query_lower) for pattern in goal_creation_patterns)
    
    def _classify_query(self, user_query: str, user_context: Dict[str, Any]) -> List[str]:
        """
        Classify the user query to determine which agent(s) should handle it.
        Now uses LLM-first approach with regex as fallback.
        
        Args:
            user_query: User's question or request
            user_context: Context information about the user
            
        Returns:
            List of agent categories in priority order
        """
        # Use LLM classification as primary method
        llm_categories = self._classify_with_llm(user_query, user_context)
        
        if llm_categories:
            return llm_categories
        
        # Fall back to heuristic classification if LLM fails
        print("LLM classification failed, falling back to heuristic classification")
        
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
        
        # Goal Planning keywords - expanded to include more variations
        goal_keywords = [
            "goal", "save", "saving", "target", "planning", "retire", "retirement",
            "college", "education", "house", "home", "car", "travel", "vacation", "wedding",
            "emergency fund", "fund", "emergency", "medical", "expense", "purchase"
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
        
        # If no categories matched, default to General Financial Advice
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
            # Create prompt for classification - enhanced to better handle goal detection
            prompt = """
Based on the user's query and their context information, classify this query into one or more of the following categories in priority order (most relevant first):

1. "Transaction Analysis" - For queries about spending, expenses, transaction history, budgeting, or subscriptions
2. "Goal Planning" - For queries about financial goals, saving for specific purposes, creating goals, tracking progress
3. "Asset Allocation" - For queries about investments, portfolio allocation, risk management
4. "Education" - For queries asking for explanations of financial concepts
5. "General Financial Advice" - For any other general financial queries

User Query: "{user_query}"

User Context:
- Goal Count: {goal_count}
- Recent Transactions: {recent_transactions}
- Has Investments: {has_investments}
- Risk Profile: {risk_profile}

Give extra consideration to Goal Planning for queries that mention:
- Creating or setting up new goals
- Saving for specific purposes (emergency fund, house, education, car, etc.)
- Target amounts, dates or timelines
- Current progress toward goals

Provide your classification as a comma-separated list of categories, starting with the most relevant.
CLASSIFICATION: 
""".format(
                user_query=user_query,
                goal_count=user_context.get("goal_count", 0),
                recent_transactions=user_context.get("recent_transactions", "None"),
                has_investments=user_context.get("has_investments", False),
                risk_profile=user_context.get("risk_profile", "Unknown")
            )
            
            # Generate classification
            system_prompt = """You are a financial query classification system that accurately categorizes user queries into the most appropriate financial domains. You prioritize accuracy and relevance in your classifications."""
            
            classification_response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,  # Use 0 for deterministic output
                max_tokens=100
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
            
            # Default to empty list if parsing fails
            return []
            
        except Exception as e:
            print(f"Error in LLM classification: {str(e)}")
            return []
            
    # Asset allocation related methods
    def _classify_allocation_intent_with_llm(self, user_query: str) -> str:
        """
        Use LLM to classify the specific intent of an asset allocation query.
        
        Args:
            user_query: User's question or request
            
        Returns:
            Classification of intent: "current_allocation", "recommended_allocation", 
            "allocation_comparison", "rebalancing_advice", or "allocation_education"
        """
        try:
            # Create a prompt for classification
            prompt = """
Determine the specific intent of this user query about investment asset allocation.
Classify it into exactly ONE of these categories:

1. "current_allocation" - User is asking about their CURRENT asset allocation, what they currently have invested
2. "recommended_allocation" - User is asking what allocation is RECOMMENDED for them, what they SHOULD have
3. "allocation_comparison" - User wants to COMPARE their current allocation to what's recommended
4. "rebalancing_advice" - User wants specific advice on HOW TO CHANGE their current allocation
5. "allocation_education" - User wants general information about asset allocation concepts

Examples:
- "What is my current asset allocation?" -> current_allocation
- "How are my investments allocated right now?" -> current_allocation
- "What asset allocation should I have?" -> recommended_allocation
- "What's the ideal allocation for my risk profile?" -> recommended_allocation
- "How does my allocation compare to what's recommended?" -> allocation_comparison
- "Is my portfolio aligned with my goals?" -> allocation_comparison
- "How should I rebalance my portfolio?" -> rebalancing_advice
- "What changes should I make to my investments?" -> rebalancing_advice
- "Explain asset allocation to me" -> allocation_education
- "What is diversification?" -> allocation_education

User query: "{query}"

Respond with ONLY ONE category from the list above, no explanation.
""".format(query=user_query)
            
            # Get the classification
            system_prompt = "You are a financial query classification system that accurately categorizes user queries into the most appropriate financial domain."
            
            response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,  # Use 0 temperature for deterministic output
                max_tokens=20   # Very few tokens needed
            )
            
            # Clean up the response
            response = response.strip().lower()
            
            # Validate the response
            valid_categories = [
                "current_allocation", "recommended_allocation", 
                "allocation_comparison", "rebalancing_advice", 
                "allocation_education"
            ]
            
            # Check if response is a valid category
            for category in valid_categories:
                if category in response:
                    return category
            
            # If no valid category found, use fallback classification with regex
            print(f"LLM classification failed with response: {response}, falling back to regex")
            return self._classify_allocation_intent_with_regex(user_query)
                
        except Exception as e:
            print(f"Error in LLM allocation intent classification: {str(e)}")
            # Fallback to regex classification
            return self._classify_allocation_intent_with_regex(user_query)

    def _classify_allocation_intent_with_regex(self, user_query: str) -> str:
        """
        Use regex patterns to classify the specific intent of an asset allocation query.
        
        Args:
            user_query: User's question or request
            
        Returns:
            Classification of intent
        """
        query_lower = user_query.lower()
        
        # Current allocation patterns
        current_patterns = ["my current", "how are my assets", "my portfolio", "my investments", 
                           "what's my allocation", "what is my allocation", "list my", "show me my"]
        
        # Recommended allocation patterns
        recommended_patterns = ["should have", "recommended", "ideal", "optimal", "best allocation", 
                               "should my", "what allocation do i need"]
        
        # Comparison patterns
        comparison_patterns = ["compare", "alignment", "aligned", "match", "how does my", 
                              "difference between", "versus", "vs", "against"]
        
        # Rebalancing patterns
        rebalancing_patterns = ["rebalance", "adjust", "change", "modify", "update", 
                               "improvements", "improve", "optimize"]
        
        # Check patterns in order of specificity
        if any(pattern in query_lower for pattern in current_patterns):
            return "current_allocation"
        elif any(pattern in query_lower for pattern in comparison_patterns):
            return "allocation_comparison"
        elif any(pattern in query_lower for pattern in rebalancing_patterns):
            return "rebalancing_advice"
        elif any(pattern in query_lower for pattern in recommended_patterns):
            return "recommended_allocation"
        else:
            return "allocation_education"  # Default

    def _handle_asset_allocation_query(self, user_query: str, customer_id: str, user_context: Dict[str, Any]) -> str:
        """
        Handle asset allocation queries by determining specific intent and routing to the appropriate handler.
        
        Args:
            user_query: User's question or request
            customer_id: ID of the customer
            user_context: Context information about the user
            
        Returns:
            Response to the asset allocation query
        """
        # Determine specific asset allocation intent using LLM
        allocation_intent = self._classify_allocation_intent_with_llm(user_query)
        print(f"Allocation query intent classification: {allocation_intent}")
        
        # Get the customer's risk profile and other context
        risk_profile = user_context.get("risk_profile", "Medium")
        # Default to Medium-term if not specified in the query
        goal_timeline = "Medium-term"
        
        # Extract timeline from query if present
        timeline_indicators = {
            "short term": "Short-term",
            "short-term": "Short-term",
            "medium term": "Medium-term",
            "medium-term": "Medium-term",
            "long term": "Long-term",
            "long-term": "Long-term"
        }
        
        for indicator, timeline in timeline_indicators.items():
            if indicator in user_query.lower():
                goal_timeline = timeline
                break
        
        # Route to appropriate handler based on intent
        if allocation_intent == "current_allocation":
            return self._handle_current_allocation(customer_id)
        elif allocation_intent == "recommended_allocation":
            return self._handle_recommended_allocation(risk_profile, goal_timeline)
        elif allocation_intent == "allocation_comparison":
            return self._handle_allocation_comparison(customer_id, risk_profile, goal_timeline)
        elif allocation_intent == "rebalancing_advice":
            return self._handle_rebalancing_advice(customer_id, risk_profile, goal_timeline)
        else:  # Default to educational content
            return self._handle_allocation_education(risk_profile, goal_timeline)

    def _handle_current_allocation(self, customer_id: str) -> str:
        """
        Handle queries about current asset allocation.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Formatted information about current allocation
        """
        # Get actual current allocation
        current_allocation = self.asset_allocation_agent.get_current_allocation(customer_id)
        
        if not current_allocation:
            return "I couldn't find your current asset allocation information. Please check back later or contact customer support."
        
        # Format the allocation for display
        formatted_allocation = self._format_allocation_for_display(current_allocation)
        
        # Get the last rebalanced date if available
        last_rebalanced = "N/A"
        try:
            customer_allocation = self.asset_allocation_agent.current_allocations_df[
                self.asset_allocation_agent.current_allocations_df['Customer ID'] == customer_id
            ]
            if not customer_allocation.empty:
                last_rebalanced = customer_allocation.iloc[0].get('Last Rebalanced', 'N/A')
        except:
            pass
        
        # Get portfolio value if available
        portfolio_value = "N/A"
        try:
            customer_allocation = self.asset_allocation_agent.current_allocations_df[
                self.asset_allocation_agent.current_allocations_df['Customer ID'] == customer_id
            ]
            if not customer_allocation.empty:
                portfolio_value = customer_allocation.iloc[0].get('Total Portfolio Value', 'N/A')
                if isinstance(portfolio_value, (int, float)):
                    portfolio_value = f"${portfolio_value:,.2f}"
        except:
            pass
        
        # Create response about current allocation
        response = f"""
**Your Current Asset Allocation**

Here's how your investment portfolio (value: {portfolio_value}) is currently allocated:

{formatted_allocation}

This represents your actual asset allocation as of your last portfolio update ({last_rebalanced}).

Would you like to see how this compares to the recommended allocation for your risk profile?
"""
        
        return response.strip()

    def _handle_recommended_allocation(self, risk_profile: str, goal_timeline: str) -> str:
        """
        Handle queries about recommended asset allocation.
        
        Args:
            risk_profile: User's risk profile
            goal_timeline: Timeline for goal (Short-term, Medium-term, Long-term)
            
        Returns:
            Formatted information about recommended allocation
        """
        # Get recommended allocation
        recommended_allocation = self.asset_allocation_agent.get_allocation_recommendation(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline
        )
        
        # Format the allocation for display
        formatted_allocation = self._format_allocation_for_display(recommended_allocation)
        
        # Get explanation of the strategy
        strategy_explanation = self.asset_allocation_agent.explain_allocation_strategy(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline
        )
        
        # Create response about recommended allocation
        response = f"""
**Recommended Asset Allocation**

Based on your {risk_profile} risk profile and {goal_timeline} investment horizon, here's the recommended asset allocation:

{formatted_allocation}

{strategy_explanation}

Would you like to see how this compares to your current allocation?
"""
        
        return response.strip()

    def _handle_allocation_comparison(self, customer_id: str, risk_profile: str, goal_timeline: str) -> str:
        """
        Handle queries comparing current and recommended allocations.
        
        Args:
            customer_id: ID of the customer
            risk_profile: User's risk profile
            goal_timeline: Timeline for goal
            
        Returns:
            Comparison between current and recommended allocations
        """
        # Get both current and recommended allocations
        current_allocation = self.asset_allocation_agent.get_current_allocation(customer_id)
        recommended_allocation = self.asset_allocation_agent.get_allocation_recommendation(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline
        )
        
        if not current_allocation:
            return self._handle_recommended_allocation(risk_profile, goal_timeline) + "\n\nNote: I couldn't find your current allocation data to make a comparison."
        
        # Format the allocations for display
        current_formatted = self._format_allocation_for_display(current_allocation)
        recommended_formatted = self._format_allocation_for_display(recommended_allocation)
        
        # Calculate and format the differences
        differences = []
        for asset in recommended_allocation:
            current_pct = current_allocation.get(asset, 0)
            recommended_pct = recommended_allocation[asset]
            diff = recommended_pct - current_pct
            if abs(diff) >= 0.5:  # Only include meaningful differences
                direction = "higher" if diff > 0 else "lower"
                differences.append(f"- {asset}: Your allocation is {abs(diff):.1f}% {direction} than recommended")
        
        difference_text = "\n".join(differences) if differences else "Your current allocation is well-aligned with the recommendations for your risk profile."
        
        # Create response comparing allocations
        response = f"""
**Asset Allocation Comparison**

**Your Current Allocation:**
{current_formatted}

**Recommended Allocation** (based on {risk_profile} risk profile, {goal_timeline}):
{recommended_formatted}

**Key Differences:**
{difference_text}

Would you like specific advice on how to rebalance your portfolio to better align with the recommendations?
"""
        
        return response.strip()

    def _handle_rebalancing_advice(self, customer_id: str, risk_profile: str, goal_timeline: str) -> str:
        """
        Handle queries requesting rebalancing advice.
        
        Args:
            customer_id: ID of the customer
            risk_profile: User's risk profile
            goal_timeline: Timeline for goal
            
        Returns:
            Specific rebalancing recommendations
        """
        # Get both current and recommended allocations
        current_allocation = self.asset_allocation_agent.get_current_allocation(customer_id)
        
        if not current_allocation:
            return "I couldn't find your current allocation data to provide rebalancing advice. Please ensure your portfolio information is up to date."
        
        # Generate rebalancing recommendations
        rebalancing_rec = self.asset_allocation_agent.generate_rebalancing_recommendations(
            goal_id="general",  # Use a general identifier if not goal-specific
            customer_id=customer_id,
            goal_type="general investing",
            goal_timeline=goal_timeline,
            risk_profile=risk_profile,
            current_allocation=current_allocation
        )
        
        return rebalancing_rec

    def _handle_allocation_education(self, risk_profile: str, goal_timeline: str) -> str:
        """
        Handle queries requesting education about asset allocation.
        
        Args:
            risk_profile: User's risk profile
            goal_timeline: Timeline for goal
            
        Returns:
            Educational content about asset allocation
        """
        # Try to get educational content from the education agent first
        try:
            education_content = self.education_agent.get_educational_content(
                topic="asset allocation",
                risk_profile=risk_profile
            )
            
            if education_content:
                return education_content
        except:
            pass
        
        # Fall back to explanation from the asset allocation agent
        return self.asset_allocation_agent.explain_allocation_strategy(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline
        )

    def _format_allocation_for_display(self, allocation: Dict[str, float]) -> str:
        """
        Format an allocation dictionary for display.
        
        Args:
            allocation: Dictionary mapping asset classes to allocation percentages
            
        Returns:
            Formatted text representation of the allocation
        """
        if not allocation:
            return "Allocation data not available."
        
        # Sort by allocation percentage (descending)
        sorted_items = sorted(allocation.items(), key=lambda x: x[1], reverse=True)
        
        formatted_lines = []
        for asset, percentage in sorted_items:
            formatted_lines.append(f"* {asset}: {percentage:.1f}%")
        
        return "\n".join(formatted_lines)
    
    def _get_agent_responses(self, 
                             classification: List[str],
                             user_query: str,
                             customer_id: str,
                             user_context: Dict[str, Any],
                             is_goal_focused: bool = False) -> Dict[str, str]:
        """
        Get responses from the appropriate specialized agents.
        
        Args:
            classification: List of agent categories in priority order
            user_query: User's question or request
            customer_id: ID of the customer
            user_context: Context information about the user
            is_goal_focused: Flag indicating if this is explicitly a goal-related query
            
        Returns:
            Dictionary mapping agent categories to their responses
        """
        agent_responses = {}
        
        # Log the classification and goal focus detection
        print(f"Request classification: {classification}")
        print(f"Is goal-focused: {is_goal_focused}")
        
        # If this is a goal-focused query, prioritize the Goal Planning Agent
        if is_goal_focused and "Goal Planning" not in classification:
            classification.insert(0, "Goal Planning")
            print("Added Goal Planning to classification due to goal focus detection")
        
        # Get responses from each applicable agent
        for category in classification:
            if category == "Goal Planning":
                # Get response from Goal Planning Agent for goal-focused queries
                try:
                    print(f"Processing goal planning request: '{user_query}'")
                    goal_response = self.goal_planning_agent.handle_goal_request(
                        request=user_query,
                        user_context=user_context
                    )
                    
                    # Format the response based on type
                    if isinstance(goal_response, dict) and goal_response.get("success", False):
                        response_type = goal_response.get("response_type", "")
                        
                        if response_type == "goal_created":
                            agent_responses["Goal Planning"] = (
                                f"Goal created successfully!\n\n"
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
                    
                    # For goal-focused queries with successful responses, we can return early
                    if is_goal_focused and agent_responses["Goal Planning"]:
                        return agent_responses
                        
                except Exception as e:
                    print(f"Error processing goal planning request: {str(e)}")
                    agent_responses["Goal Planning"] = "I encountered an issue processing your goal-related request."
                    
            elif category == "Transaction Analysis":
                # Only generate nudges if this isn't explicitly a goal-focused query
                if not is_goal_focused:
                    # Get response from Transaction Analysis Agent
                    try:
                        print(f"Generating nudges for customer {customer_id}")
                        nudges = self.transaction_agent.generate_nudges(customer_id)
                        agent_responses["Transaction Analysis"] = nudges
                    except Exception as e:
                        print(f"Error generating nudges: {str(e)}")
                        agent_responses["Transaction Analysis"] = "Unable to generate transaction insights at this time."
                else:
                    print(f"Skipping nudge generation for goal-focused query: '{user_query}'")
                    
            elif category == "Asset Allocation":
                try:
                    # Use the asset allocation query handler
                    print(f"Processing asset allocation query: '{user_query}'")
                    allocation_response = self.asset_allocation_agent.handle_query(
                        user_query=user_query,
                        customer_id=customer_id,
                        user_context=user_context
                    )
                    
                    agent_responses["Asset Allocation"] = allocation_response
                except Exception as e:
                    print(f"Error processing asset allocation query: {str(e)}")
                    print(traceback.format_exc())
                    agent_responses["Asset Allocation"] = "I'm unable to provide allocation advice at this time due to a technical issue."
                    
            elif category == "Education":
                try:
                    # Extract educational topic
                    topic = self._extract_education_topic(user_query)
                    print(f"Extracting educational content for topic: {topic}")
                    
                    # Get educational content
                    educational_content = self.education_agent.get_educational_content(
                        topic=topic,
                        user_context=user_context
                    )
                    
                    agent_responses["Education"] = educational_content
                except Exception as e:
                    print(f"Error generating educational content: {str(e)}")
                    agent_responses["Education"] = f"I'd be happy to explain about {topic}, but I'm having trouble accessing that information right now."
                    
            elif category == "General Financial Advice":
                try:
                    # Generate general financial advice
                    print("Generating general financial advice")
                    general_advice = self._generate_general_advice(
                        user_query=user_query,
                        user_context=user_context
                    )
                    
                    agent_responses["General Financial Advice"] = general_advice
                except Exception as e:
                    print(f"Error generating general advice: {str(e)}")
                    agent_responses["General Financial Advice"] = "I'd be happy to provide financial advice, but I'm having trouble generating personalized recommendations at the moment."
        
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
    agent = FinancialAdvisorAgent(data_path="./synthetic_data")
    
    # Test processing a query
    customer_id = "CUSTOMER1"
    
    # Simulate a conversation with context
    chat_history = [
        {"role": "user", "content": "I want to set up a travel goal"},
        {"role": "assistant", "content": "Great! Let's set up a travel goal for you. Can you tell me the target amount you'd like to save?"},
        {"role": "user", "content": "I want to save $5000"},
        {"role": "assistant", "content": "That's a good target for your travel goal. When would you like to achieve this goal by?"}
    ]
    
    # Process a context-dependent query
    context_dependent_query = "December 31, 2026"
    print("\n" + "="*80)
    print(f"CONTEXT-DEPENDENT QUERY: {context_dependent_query}")
    print("="*80)
    
    response = agent.process_query_with_formatting(context_dependent_query, customer_id, chat_history)
    
    print("\nRESPONSE:")
    print(response)
    print("="*80)

if __name__ == "__main__":
    main()