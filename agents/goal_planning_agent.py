"""
Goal Planning Agent

This module implements the Goal Planning Agent which handles all goal-related
functionality for the Personal Finance Manager, with LLM-based intent classification
and parameter extraction.
"""

import re
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('GoalPlanningAgent')

# Import the Goal Data Manager
from utils.goal_data_manager import GoalDataManager
from utils.llm_response import generate_text

class GoalPlanningAgent:
    """
    Goal Planning Agent for handling goal-related operations.
    
    This agent is responsible for:
    1. Creating new financial goals
    2. Modifying existing goals
    3. Deleting goals
    4. Providing goal status updates
    5. Generating goal-related recommendations
    """
    
    def __init__(self, data_path="./synthetic_data", asset_allocation_agent=None, education_agent=None, **kwargs):
        """
        Initialize the Goal Planning Agent.
        
        Args:
            data_path (str): Path to the directory containing data files
            asset_allocation_agent: The asset allocation agent for allocation recommendations
            education_agent: The education agent for educational content
            **kwargs: Additional keyword arguments for future compatibility
        """
        self.data_path = data_path
        self.goal_manager = GoalDataManager(data_path)
        self.asset_allocation_agent = asset_allocation_agent
        self.education_agent = education_agent
        
        # Load prompts
        from prompts.goal_planning_agent_prompts import GoalPlanningPrompts
        self.prompts = GoalPlanningPrompts
        
        logger.info("Goal Planning Agent initialized")
    
    def handle_goal_request(self, request, user_context=None):
        """
        Compatibility method to maintain interface with Financial Advisor Agent.
        
        Args:
            request (str): The user's query or request
            user_context (dict, optional): Additional context information
            
        Returns:
            str or dict: The response to the user's query
        """
        # Extract customer_id from user_context
        customer_id = user_context.get('customer_id') if user_context else None
        
        if not customer_id:
            return "I need customer information to process goal-related requests."
        
        # Normalize customer_id to lowercase for our data operations
        formatted_customer_id = customer_id.lower() if isinstance(customer_id, str) else customer_id
        
        # Determine the intent of the request using LLM-based classification
        intent = self._determine_intent(request, formatted_customer_id)
        
        logger.info(f"Request intent: {intent} for customer: {customer_id}")
        
        # Process based on intent - using our own methods directly
        if intent == "create_goal":
            response = self._handle_create_goal(request, formatted_customer_id)
        elif intent == "modify_goal":
            response = self._handle_modify_goal(request, formatted_customer_id)
        elif intent == "delete_goal":
            response = self._handle_delete_goal(request, formatted_customer_id)
        elif intent == "goal_status":
            response = self._handle_goal_status(request, formatted_customer_id)
        elif intent == "goal_recommendations":
            response = self._handle_goal_recommendations(formatted_customer_id)
        else:
            # General goal-related query
            response = self._handle_general_goal_query(request, formatted_customer_id)
        
        # Format response for compatibility with what FinancialAdvisorAgent expects
        # Check if the query is about creating a goal
        if any(term in request.lower() for term in ['create', 'new', 'add', 'set up']):
            # If the response indicates success
            if "successfully" in response.lower() and "goal" in response.lower():
                # Extract any goal ID that might be in the response using regex
                goal_id_match = re.search(r'Goal ID: (GOAL\d+)', response)
                goal_id = goal_id_match.group(1) if goal_id_match else "GOAL_NEW"
                
                # Create a structured response
                return {
                    "success": True,
                    "response_type": "goal_created",
                    "goal_id": goal_id,
                    "goal_data": {
                        "goal_type": self._extract_value("Type", response) or self._extract_goal_type(request),
                        "target_amount": self._extract_amount("Target Amount", response) or 0.0,
                        "monthly_contribution": self._extract_amount("Monthly Contribution", response) or 0.0,
                        "goal_timeline": self._extract_value("Timeline", response) or "Medium-term"
                    },
                    "strategy_explanation": response
                }
        
        # If query is asking for all goals
        if "goals" in request.lower() and any(term in request.lower() for term in ['what', 'list', 'all', 'my']):
            user_goals = self.goal_manager.get_user_goals(formatted_customer_id)
            if not user_goals.empty:
                goals_list = user_goals.to_dict('records')
                return {
                    "success": True,
                    "response_type": "all_goals",
                    "goals": goals_list
                }
        
        # If query is asking for recommendations
        if "recommendations" in request.lower() or "recommend" in request.lower():
            return {
                "success": True,
                "response_type": "goal_recommendations",
                "recommendations": response
            }
        
        # Default response format
        return response
    
    def _determine_intent(self, query, customer_id=None):
        """
        Determine the intent of a goal-related query using LLM as primary method.
        
        Args:
            query (str): The user's query
            customer_id (str, optional): The customer ID for context
            
        Returns:
            str: The determined intent
        """
        # First try LLM-based intent determination - now primary method
        llm_intent = self._determine_intent_with_llm(query, customer_id)
        
        if llm_intent:
            logger.info(f"LLM determined intent: {llm_intent} for query: '{query}'")
            return llm_intent
        
        # Fall back to regex-based intent determination if LLM fails
        logger.info(f"Falling back to regex-based intent determination for query: '{query}'")
        
        return self._determine_intent_with_regex(query)
    
    def _determine_intent_with_llm(self, query, customer_id=None):
        """
        Use LLM to determine the intent of a goal-related query.
        Enhanced with better context about user's existing goals.
        
        Args:
            query (str): The user's query
            customer_id (str, optional): The customer ID for context
            
        Returns:
            str: The determined intent or None if classification failed
        """
        # Get user goals for context if customer_id is provided
        user_goals = None
        if customer_id:
            user_goals = self.goal_manager.get_user_goals(customer_id)
        
        has_goals = user_goals is not None and not user_goals.empty
        goals_context = ""
        
        if has_goals:
            # Format minimal goals info for context
            goals_list = []
            for _, goal in user_goals.iterrows():
                goals_list.append(f"{goal['Goal Name']} (${goal['Target Amount']:,.2f})")
            
            goals_context = f"User has the following goals: {', '.join(goals_list)}."
        else:
            goals_context = "User currently has no financial goals set up."
        
        # Create the enhanced prompt with more examples and details
        prompt = f"""
Classify the user's query about financial goals into one of the following intent categories:

1. create_goal: User wants to create/start/establish a new financial goal
2. modify_goal: User wants to update/change/adjust an existing goal
3. delete_goal: User wants to remove/delete an existing goal
4. goal_status: User wants information about the progress/status of their goals
5. goal_recommendations: User wants advice/recommendations about their goals
6. general_goal_query: Any other goal-related query that doesn't fit the above categories

Examples for create_goal:
- "I want to create a new goal"
- "Help me set up an emergency fund"
- "I need to save for a house"
- "Start a retirement account for me"
- "Create a goal for $10,000 by next year"
- "I want to create an emergency fund of $5000 till 31/03/2026"
- "Save $20,000 for a down payment by 2027"
- "Set up a college fund for my child"

Examples for modify_goal:
- "Update my emergency fund target amount"
- "Change my retirement goal deadline"
- "I want to increase my house down payment goal"
- "Adjust my monthly contribution for my vacation goal"

Examples for delete_goal:
- "Delete my travel goal"
- "Remove my car fund goal"
- "I want to cancel my wedding savings goal"

Examples for goal_status:
- "How am I doing on my goals?"
- "What's the status of my emergency fund?"
- "Show me my progress for retirement"
- "Am I on track with my home purchase goal?"

Examples for goal_recommendations:
- "How can I improve my savings rate for my goals?"
- "What suggestions do you have for my education goal?"
- "Recommend how I should prioritize my goals"

Examples for general_goal_query:
- "What types of goals should I consider?"
- "Tell me about financial goals"
- "How do goals work?"
- "What's a good goal amount for retirement?"

User's query: "{query}"

Additional context: {goals_context}

Carefully analyze the user's intent to determine if they want to create a new goal, modify an existing one, check goal status, or get general information.

Respond with only the category name, nothing else.
"""
        
        # Get the LLM's classification
        try:
            system_prompt = "You are a helpful assistant specializing in financial goal intent classification. Your task is to analyze user queries and determine their intent regarding financial goals. Respond with only the category name, nothing else."
            
            intent_response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,  # Use 0 temperature for deterministic output
                max_tokens=50  # Very few tokens needed for classification
            )
            
            # Clean up the response to get just the intent
            intent_response = intent_response.strip().lower()
            
            # Extract just the intent category if there's additional text
            valid_intents = ["create_goal", "modify_goal", "delete_goal", 
                           "goal_status", "goal_recommendations", "general_goal_query"]
            
            for intent in valid_intents:
                if intent in intent_response:
                    return intent
            
            # If no valid intent found, log and return None
            logger.warning(f"LLM returned invalid intent: {intent_response}")
            return None
        
        except Exception as e:
            logger.error(f"Error in LLM intent determination: {str(e)}")
            return None
    
    def _determine_intent_with_regex(self, query):
        """
        Determine the intent of a goal-related query using regex patterns.
        Used as a fallback when LLM classification fails.
        
        Args:
            query (str): The user's query
            
        Returns:
            str: The determined intent
        """
        query_lower = query.lower()
        
        # Create goal intent
        create_patterns = [
            # Original patterns
            r"create (?:a |new |)goal",
            r"set up (?:a |new |)goal",
            r"start (?:a |new |)goal",
            r"establish (?:a |new |)goal",
            r"add (?:a |new |)goal",
            r"begin (?:a |new |)goal",
            r"want (?:a |to create a |to set up a |to establish a |)(?:new |)goal",
            
            # Help/assist patterns
            r"help (?:me |us |)(?:to |)create (?:a |new |)goal",
            r"help (?:me |us |)(?:to |)set up (?:a |new |)goal",
            r"help (?:me |us |)(?:to |)establish (?:a |new |)goal",
            r"(?:can you |could you |would you |)help (?:me |us |)(?:to |)create (?:a |new |)goal",
            r"assist (?:me |us |)(?:in |with |)(?:creating |setting up) (?:a |new |)goal",
            
            # Goal creation with specific goal types
            r"(?:create|set up|establish|start) (?:a |an |)(?:new |)emergency fund",
            r"(?:create|set up|establish|start) (?:a |an |)(?:new |)retirement (?:goal|fund|account|plan)",
            r"(?:create|set up|establish|start) (?:a |an |)(?:new |)education (?:goal|fund|account|plan)",
            r"(?:create|set up|establish|start) (?:a |an |)(?:new |)home purchase (?:goal|fund|plan)",
            
            # Intent to save for specific purposes
            r"(?:want to|need to|would like to) save (?:money |funds |)for (?:a |an |my |)",
            r"(?:want to|need to|would like to) start saving for (?:a |an |my |)",
        ]
        
        # Check for direct mentions of specific goal types
        goal_type_indicators = [
            "emergency fund", "retirement", "education fund", "college fund", 
            "home purchase", "house fund", "down payment", "travel fund", "vacation fund",
            "car fund", "vehicle fund", "wedding fund", "medical fund", "health fund"
        ]
        
        # If query starts with a goal type, it's likely a creation intent
        for indicator in goal_type_indicators:
            if query_lower.startswith(indicator) or f"new {indicator}" in query_lower:
                return "create_goal"
        
        for pattern in create_patterns:
            if re.search(pattern, query_lower):
                return "create_goal"
        
        # Modify goal intent
        modify_patterns = [
            r"modify (?:my |the |)goal",
            r"update (?:my |the |)goal",
            r"change (?:my |the |)goal",
            r"adjust (?:my |the |)goal",
            r"edit (?:my |the |)goal",
            r"increase (?:my |the |)goal",
            r"decrease (?:my |the |)goal"
        ]
        
        for pattern in modify_patterns:
            if re.search(pattern, query_lower):
                return "modify_goal"
        
        # Delete goal intent
        delete_patterns = [
            r"delete (?:my |the |)goal",
            r"remove (?:my |the |)goal",
            r"cancel (?:my |the |)goal",
            r"get rid of (?:my |the |)goal"
        ]
        
        for pattern in delete_patterns:
            if re.search(pattern, query_lower):
                return "delete_goal"
        
        # Goal status intent
        status_patterns = [
            r"status of (?:my |the |)goal",
            r"progress (?:on|of) (?:my |the |)goal",
            r"how (?:am I|are we) doing (?:on|with) (?:my |the |)goal",
            r"update (?:on|about) (?:my |the |)goal"
        ]
        
        for pattern in status_patterns:
            if re.search(pattern, query_lower):
                return "goal_status"
        
        # Goal recommendations intent
        recommendation_patterns = [
            r"recommend(?:ations|) (?:for|on) (?:my |the |)goal",
            r"advice (?:for|on) (?:my |the |)goal",
            r"suggestions (?:for|on) (?:my |the |)goal",
            r"how (?:can|should) I (?:improve|optimize) (?:my |the |)goal"
        ]
        
        for pattern in recommendation_patterns:
            if re.search(pattern, query_lower):
                return "goal_recommendations"
        
        # If "goal" and any creation-related terms appear together, default to create_goal
        creation_terms = ["create", "new", "set up", "establish", "start", "add", "begin", "help", "assist"]
        if "goal" in query_lower and any(term in query_lower for term in creation_terms):
            return "create_goal"
        
        # Default to general goal query
        return "general_goal_query"
    
    def _extract_goal_parameters_with_llm(self, query):
        """
        Extract goal parameters from a query using LLM for more accurate extraction.
        
        Args:
            query (str): The user's query
                
        Returns:
            dict: Extracted goal parameters
        """
        try:
            # Create prompt for parameter extraction
            prompt = f"""
Extract all the relevant parameters for a financial goal from the user's query. The user may be requesting to create, modify, or get information about a financial goal.

Parameters to extract:
1. goal_type - The type of goal (e.g., "Emergency Fund", "Home Purchase", "Education", "Retirement", "Travel", "Car Purchase", "Wedding", "Medical Expenses")
2. goal_name - The name of the goal (use the goal_type if no specific name is given)
3. target_amount - The amount the user wants to save (in numeric form, e.g., 5000)
4. target_date - The date by when the user wants to achieve the goal (in MM/DD/YYYY format)
5. current_savings - How much the user has already saved towards this goal (0 if not specified)
6. priority - The importance of the goal ("Very High", "High", "Medium", or "Low")
7. monthly_contribution - How much the user wants to contribute monthly (calculate if not specified)

User's query: "{query}"

Instructions:
- Convert any date format to MM/DD/YYYY (e.g., "31/03/2026" becomes "03/31/2026")
- Extract numeric values without currency symbols or commas
- If no specific goal type is mentioned but context suggests one, infer the most likely type
- If an amount is mentioned without clear context, assume it's the target_amount
- If a date is mentioned without clear context, assume it's the target_date

Respond in JSON format with only the extracted parameters. Include only parameters that you can confidently extract or infer from the query.
Example response format:
{{
  "goal_type": "Emergency Fund",
  "goal_name": "Emergency Fund",
  "target_amount": 5000,
  "target_date": "12/31/2025"
}}
"""

            # Get LLM extraction response
            system_prompt = "You are a precise parameter extraction system. Extract only the parameters clearly stated or strongly implied in the user query. Return valid JSON with no additional text."
            
            extraction_response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0,  # Use 0 for deterministic output
                max_tokens=500
            )
            
            # Clean up the response and parse JSON
            extraction_response = extraction_response.strip()
            
            # Handle cases where model adds explanatory text before or after JSON
            json_start = extraction_response.find('{')
            json_end = extraction_response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = extraction_response[json_start:json_end+1]
                params = json.loads(json_str)
            else:
                # No valid JSON found
                logger.warning(f"No valid JSON in extraction response: {extraction_response}")
                params = {}
            
            logger.info(f"LLM extracted parameters: {params}")
            return params
            
        except Exception as e:
            logger.error(f"Error in LLM parameter extraction: {str(e)}")
            logger.error(f"Falling back to regex extraction")
            # Fall back to regex extraction if LLM fails
            return self._extract_goal_parameters(query)
    
    def _extract_goal_parameters(self, query):
        """
        Extract goal parameters from a creation or modification query.
        With improved extraction for target dates and amounts.
        
        Args:
            query (str): The user's query
                
        Returns:
            dict: Extracted goal parameters
        """
        params = {}
        
        # First check for exact phrases that indicate specific goal types without needing "goal" word
        specific_phrases = {
            r"emergency fund": "Emergency Fund",
            r"retirement (?:plan|fund|savings)": "Retirement",
            r"college (?:fund|savings)": "Education",
            r"education (?:fund|savings)": "Education",
            r"house (?:fund|savings|down payment)": "Home Purchase",
            r"home (?:fund|savings|down payment)": "Home Purchase",
            r"vacation (?:fund|savings)": "Travel",
            r"travel (?:fund|savings)": "Travel",
            r"car (?:fund|savings)": "Car Purchase",
            r"vehicle (?:fund|savings)": "Car Purchase",
            r"wedding (?:fund|savings)": "Wedding",
            r"medical (?:fund|savings|expenses)": "Medical Expenses",
            r"health (?:fund|savings)": "Medical Expenses"
        }
        
        for pattern, goal_type in specific_phrases.items():
            if re.search(pattern, query.lower()):
                params["goal_type"] = goal_type
                params["goal_name"] = goal_type
                break
        
        # If no match so far, look for exact goal type matches
        if "goal_type" not in params:
            goal_types = [
                "Retirement", "Home Purchase", "Education", "Emergency Fund",
                "Travel", "Car Purchase", "Wedding", "Medical Expenses"
            ]
            
            for goal_type in goal_types:
                pattern = rf'\b{goal_type.lower()}\b'
                if re.search(pattern, query.lower()):
                    params["goal_type"] = goal_type
                    params["goal_name"] = goal_type
                    break
        
        # If no exact match, look for partial matches with special handling
        if "goal_type" not in params:
            if "emergency" in query.lower() or "fund" in query.lower():
                params["goal_type"] = "Emergency Fund"
                params["goal_name"] = "Emergency Fund"
            elif "home" in query.lower() or "house" in query.lower():
                params["goal_type"] = "Home Purchase"
                params["goal_name"] = "Home Purchase"
            elif "education" in query.lower() or "college" in query.lower() or "school" in query.lower():
                params["goal_type"] = "Education"
                params["goal_name"] = "Education"
            elif "car" in query.lower() or "vehicle" in query.lower() or "auto" in query.lower():
                params["goal_type"] = "Car Purchase"
                params["goal_name"] = "Car Purchase"
            elif "travel" in query.lower() or "vacation" in query.lower() or "trip" in query.lower():
                params["goal_type"] = "Travel"
                params["goal_name"] = "Travel"
            elif "wedding" in query.lower() or "marriage" in query.lower():
                params["goal_type"] = "Wedding"
                params["goal_name"] = "Wedding"
            elif "medical" in query.lower() or "health" in query.lower() or "doctor" in query.lower():
                params["goal_type"] = "Medical Expenses"
                params["goal_name"] = "Medical Expenses"
            elif "retire" in query.lower():
                params["goal_type"] = "Retirement"
                params["goal_name"] = "Retirement"
        
        # Extract target amount - more comprehensive patterns
        amount_patterns = [
            r'\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)',  # $10,000.00
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)(?:\s*dollars|\s*USD)',  # 10,000.00 dollars
            r'(\d+)k',  # 10k
            r'(\d+)\s*thousand',  # 10 thousand
            r'(\d+(?:\.\d+)?)\s*million',  # 1.5 million
            r'save\s*(?:an?\s*)?(?:total\s*)?(?:of\s*)?[^0-9]*(\d+[,\d]*(?:\.\d+)?)',  # save a total of 10000
            r'goal(?:\s*of)?\s*\$?\s*(\d+[,\d]*(?:\.\d+)?)',  # goal of $10000
            r'(\d+[,\d]*(?:\.\d+)?)\s*dollars',  # 10000 dollars
            r'(\d+[,\d]*(?:\.\d+)?)(?:\s*dollar|\s*usd)',  # 10000 dollar or 10000 usd
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, query.lower())
            if match:
                amount_str = match.group(1).replace(',', '')
                # Check for special case patterns
                if 'k' in pattern:
                    params["target_amount"] = float(amount_str) * 1000
                elif 'thousand' in pattern:
                    params["target_amount"] = float(amount_str) * 1000
                elif 'million' in pattern:
                    params["target_amount"] = float(amount_str) * 1000000
                else:
                    params["target_amount"] = float(amount_str)
                break
        
        # Extract target date - more comprehensive patterns, including DD/MM/YYYY format
        date_patterns = [
            # Improved patterns for different date formats
            r'by\s*(\d{1,2}/\d{1,2}/\d{2,4})',  # by 03/31/2025 or by 31/03/2025
            r'till\s*(\d{1,2}/\d{1,2}/\d{2,4})',  # till 03/31/2025 or till 31/03/2025
            r'until\s*(\d{1,2}/\d{1,2}/\d{2,4})',  # until 03/31/2025 or until 31/03/2025
            r'by\s*(\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})',  # by March 31st, 2025
            r'by\s*(\w+\s+\d{4})',  # by March 2025
            
            # End of month, season, year patterns
            r'by\s*(?:the\s*)?end\s*of\s*(\w+(?:\s+\d{4})?)',  # by the end of March or by the end of March 2025
            r'by\s*(?:the\s*)?end\s*of\s*(\d{4})',  # by the end of 2025
            
            # Next month, year, etc.
            r'by\s*(?:the\s*)?(?:next|following)\s*(\w+)',  # by next March
            r'by\s*(?:the\s*)?(?:next|following)\s*(\w+\s+\d{4})',  # by next March 2025
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try various date parsing approaches
                    
                    # Check for DD/MM/YYYY format first (common in many countries)
                    if '/' in date_str:
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            # If first part is likely a day (1-31) and second part is likely a month (1-12)
                            if (1 <= int(parts[0]) <= 31) and (1 <= int(parts[1]) <= 12):
                                # This is likely DD/MM/YYYY format, convert to MM/DD/YYYY
                                date_str = f"{parts[1]}/{parts[0]}/{parts[2]}"
                                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                            else:
                                # Assume MM/DD/YYYY format
                                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                    elif re.match(r'\w+\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}', date_str):
                        # Remove st, nd, rd, th suffixes
                        date_str = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', date_str)
                        date_obj = datetime.strptime(date_str, "%B %d, %Y")
                    elif re.match(r'\w+\s+\d{4}', date_str):
                        # Month Year (assume end of month)
                        date_obj = datetime.strptime(date_str + " 1", "%B %Y %d")
                        # Set to last day of month
                        if date_obj.month == 12:
                            date_obj = datetime(date_obj.year + 1, 1, 1) - timedelta(days=1)
                        else:
                            date_obj = datetime(date_obj.year, date_obj.month + 1, 1) - timedelta(days=1)
                    else:
                        # Handle special cases
                        current_year = datetime.now().year
                        if "end of" in query.lower():
                            if re.match(r'\d{4}', date_str):  # Year only
                                # End of year
                                date_obj = datetime(int(date_str), 12, 31)
                            else:
                                # End of month in current year
                                month_to_num = {month: i+1 for i, month in enumerate([
                                    "january", "february", "march", "april", "may", "june",
                                    "july", "august", "september", "october", "november", "december"
                                ])}
                                
                                for month_name, month_num in month_to_num.items():
                                    if month_name.lower() in date_str.lower():
                                        # Extract year if present
                                        year_match = re.search(r'\d{4}', date_str)
                                        year = int(year_match.group(0)) if year_match else current_year
                                        
                                        # Check for "next year" in the query
                                        if "next year" in query.lower():
                                            year = current_year + 1
                                        
                                        # Get last day of month
                                        if month_num == 12:
                                            date_obj = datetime(year + 1, 1, 1) - timedelta(days=1)
                                        else:
                                            date_obj = datetime(year, month_num + 1, 1) - timedelta(days=1)
                                        break
                        elif "next" in query.lower() or "following" in query.lower():
                            # Handle "next month" or "next year"
                            current_date = datetime.now()
                            
                            if "year" in date_str.lower():
                                date_obj = datetime(current_date.year + 1, 12, 31)
                            else:
                                # Check for month names
                                month_to_num = {month: i+1 for i, month in enumerate([
                                    "january", "february", "march", "april", "may", "june",
                                    "july", "august", "september", "october", "november", "december"
                                ])}
                                
                                for month_name, month_num in month_to_num.items():
                                    if month_name.lower() in date_str.lower():
                                        # If the month is already past this year, use next year
                                        year = current_date.year
                                        if month_num <= current_date.month:
                                            year += 1
                                            
                                        # Extract explicit year if present
                                        year_match = re.search(r'\d{4}', date_str)
                                        if year_match:
                                            year = int(year_match.group(0))
                                            
                                        # Get last day of month
                                        if month_num == 12:
                                            date_obj = datetime(year + 1, 1, 1) - timedelta(days=1)
                                        else:
                                            date_obj = datetime(year, month_num + 1, 1) - timedelta(days=1)
                                        break
                    
                    # Format the date in MM/DD/YYYY format
                    params["target_date"] = date_obj.strftime("%m/%d/%Y")
                    break
                except (ValueError, AttributeError, UnboundLocalError) as e:
                    logger.error(f"Date parsing error: {str(e)} for date string: {date_str}")
                    # Continue to the next pattern if this one fails
        
        # Special handling for "end of March next year" type phrases
        if "target_date" not in params:
            if "next year" in query.lower() and "end of" in query.lower():
                for month in ["january", "february", "march", "april", "may", "june", 
                             "july", "august", "september", "october", "november", "december"]:
                    if month in query.lower():
                        month_num = ["january", "february", "march", "april", "may", "june", 
                                    "july", "august", "september", "october", "november", "december"].index(month) + 1
                        next_year = datetime.now().year + 1
                        
                        # Get last day of month
                        if month_num == 12:
                            date_obj = datetime(next_year + 1, 1, 1) - timedelta(days=1)
                        else:
                            date_obj = datetime(next_year, month_num + 1, 1) - timedelta(days=1)
                        
                        params["target_date"] = date_obj.strftime("%m/%d/%Y")
                        break
        
        # Extract current savings
        savings_patterns = [
            r'current(?:ly)?\s*sav(?:ed|ings)\s*(?:of|is)?\s*\$?\s*(\d+[,\d]*(?:\.\d+)?)',
            r'already\s*(?:have|saved)\s*\$?\s*(\d+[,\d]*(?:\.\d+)?)',
            r'saved\s*\$?\s*(\d+[,\d]*(?:\.\d+)?)\s*(?:so far|already|to date)',
        ]
        
        for pattern in savings_patterns:
            match = re.search(pattern, query.lower())
            if match:
                savings_str = match.group(1).replace(',', '')
                params["current_savings"] = float(savings_str)
                break
        
        # Extract priority
        priority_map = {
            "very high": "Very High",
            "high": "High", 
            "medium": "Medium",
            "low": "Low",
            "very low": "Low"
        }
        
        for priority_lower, priority_value in priority_map.items():
            if re.search(rf'\b{priority_lower}\b\s*priority', query.lower()):
                params["priority"] = priority_value
                break
        
        logger.info(f"Regex extracted parameters: {params}")
        return params
    
    def _extract_goal_id(self, query, customer_id):
        """
        Extract a goal ID from a query, or try to identify which goal is being referenced.
        
        Args:
            query (str): The user's query
            customer_id (str): The customer ID
            
        Returns:
            str or None: The extracted goal ID or None if not found
        """
        # Try to extract explicit goal ID
        goal_id_pattern = r"GOAL\d+"
        goal_id_match = re.search(goal_id_pattern, query, re.IGNORECASE)
        
        if goal_id_match:
            return goal_id_match.group(0)
        
        # If no explicit ID, try to match by goal name or type
        user_goals = self.goal_manager.get_user_goals(customer_id)
        
        if user_goals.empty:
            return None
        
        # Check for goal name or type in the query
        query_lower = query.lower()
        
        for _, goal in user_goals.iterrows():
            goal_name = str(goal['Goal Name']).lower()
            goal_type = str(goal['Goal Type']).lower()
            
            if goal_name in query_lower or goal_type in query_lower:
                return goal['Goal ID']
        
        # If still no match and the user only has one goal, return that
        if len(user_goals) == 1:
            return user_goals.iloc[0]['Goal ID']
        
        return None
    
    def _format_goals_summary(self, goals_df):
        """
        Format a summary of goals for use in prompts.
        
        Args:
            goals_df (pandas.DataFrame): The goals dataframe
            
        Returns:
            str: Formatted goals summary
        """
        if goals_df.empty:
            return "No goals found."
        
        summary = []
        
        for _, goal in goals_df.iterrows():
            goal_summary = (
                f"Goal ID: {goal['Goal ID']}\n"
                f"Goal Name: {goal['Goal Name']}\n"
                f"Goal Type: {goal['Goal Type']}\n"
                f"Target Amount: ${goal['Target Amount']:,.2f}\n"
                f"Current Savings: ${goal['Current Savings']:,.2f} ({goal['Progress (%)']:.1f}%)\n"
                f"Target Date: {goal['Target Date']}\n"
                f"Priority: {goal['Priority']}\n"
                f"Monthly Contribution: ${goal['Monthly Contribution']:,.2f}\n"
            )
            
            summary.append(goal_summary)
        
        return "\n\n".join(summary)
    
    def _handle_create_goal(self, query, customer_id):
        """
        Handle a goal creation query with improved user guidance and LLM parameter extraction.
        
        Args:
            query (str): The user's query
            customer_id (str): The customer ID
            
        Returns:
            str: The response to the user
        """
        logger.info(f"Processing goal creation for query: {query}")
        
        # Check if this is a bare goal creation intent with minimal details
        is_general_intent = any(phrase in query.lower() for phrase in [
            "create a goal", "new goal", "add a goal", "set up a goal", "start a goal", 
            "establish a goal", "want a goal", "would like to create a goal"
        ])
        
        # Extract goal parameters from the query using LLM first, then fall back to regex
        params = self._extract_goal_parameters_with_llm(query)
        
        # If LLM extraction fails or provides minimal results, fall back to regex
        if not params or len(params) <= 1:
            params = self._extract_goal_parameters(query)
        
        logger.info(f"Extracted parameters: {params}")
        
        # Check for minimal details scenario
        if is_general_intent and len(params) <= 1:  # Only has 0 or 1 parameter
            return self._provide_goal_creation_guidance(customer_id)
        
        # Validate required parameters
        required_params = ["goal_name", "target_amount", "target_date"]
        missing_params = [param for param in required_params if param not in params]
        
        if missing_params:
            # Some required parameters are missing - provide helpful guidance
            return self._provide_missing_parameters_guidance(missing_params, params)
        
        # Set defaults for optional parameters
        if "current_savings" not in params:
            params["current_savings"] = 0.0
        
        if "priority" not in params:
            params["priority"] = "Medium"
        
        if "goal_type" not in params:
            params["goal_type"] = params["goal_name"]
        
        # Get asset allocation recommendations if the agent is available
        if self.asset_allocation_agent:
            try:
                # Get risk profile (default to Medium if not available)
                risk_profile = "Medium"
                goal_timeline = "Medium-term"  # Default timeline
                
                # Calculate timeline based on target date
                try:
                    target_date = datetime.strptime(params['target_date'], "%m/%d/%Y")
                    current_date = datetime.now()
                    months_difference = (target_date.year - current_date.year) * 12 + (target_date.month - current_date.month)
                    
                    if months_difference <= 12:
                        goal_timeline = "Short-term"
                    elif months_difference <= 60:
                        goal_timeline = "Medium-term"
                    else:
                        goal_timeline = "Long-term"
                except:
                    # If there's an error calculating timeline, stick with the default
                    pass
                
                # Use explain_allocation_strategy instead of process_query
                allocation_explanation = self.asset_allocation_agent.explain_allocation_strategy(
                    risk_profile=risk_profile,
                    goal_timeline=goal_timeline
                )
                logger.info(f"Got allocation strategy: {allocation_explanation[:50]}...")  # Log the first 50 chars
            except Exception as e:
                # Log the error but continue with goal creation
                logger.error(f"Error getting asset allocation recommendations: {str(e)}")
        
        try:
            logger.info(f"Creating goal with parameters: {params}")
            
            # Create the goal
            goal_id = self.goal_manager.create_goal(
                customer_id=customer_id,
                goal_name=params["goal_name"],
                target_amount=params["target_amount"],
                current_savings=params["current_savings"],
                target_date=params["target_date"],
                goal_type=params["goal_type"],
                priority=params["priority"],
                monthly_contribution=params.get("monthly_contribution")
            )
            
            logger.info(f"Goal created with ID: {goal_id}")
            
            # Get the created goal for the explanation
            created_goal = self.goal_manager.get_goal_by_id(goal_id)
            
            # Fix for Pandas Series truth value issue
            if created_goal is None or (isinstance(created_goal, pd.DataFrame) and created_goal.empty):
                logger.warning("Created goal not found!")
                # Fallback response if goal creation somehow failed
                return f"""
    I've processed your request to create a {params['goal_type']} goal for ${params['target_amount']:,.2f} by {params['target_date']}.

    However, there was an issue retrieving the goal details. Please check your goals list to verify it was created successfully, or try again if needed.
    """
            
            # Convert to dictionary if it's a DataFrame Series
            if isinstance(created_goal, pd.Series):
                created_goal = created_goal.to_dict()
            
            # Generate a simple, clean response first
            simple_response = f"""
    Goal successfully created!

    • Type: {created_goal['Goal Type']}
    • Target Amount: ${created_goal['Target Amount']:,.2f}
    • Target Date: {created_goal['Target Date']}
    • Monthly Contribution: ${created_goal['Monthly Contribution']:,.2f}
    • Priority: {created_goal['Priority']}
    • Timeline: {created_goal['Goal Timeline']}

    Your goal has been saved and you can track your progress in the Goals section.
    """
            
            # Only use LLM for enhanced explanation if needed
            try:
                # Generate an explanation response using the prompt
                prompt = self.prompts.GOAL_CREATION_PROMPT.format(
                    goal_type=created_goal['Goal Type'],
                    target_amount=created_goal['Target Amount'],
                    target_date=created_goal['Target Date'],
                    timeline_type=created_goal['Goal Timeline'],
                    current_savings=created_goal['Current Savings'],
                    monthly_contribution=created_goal['Monthly Contribution'],
                    priority=created_goal['Priority']
                )
                
                system_prompt = self.prompts.SYSTEM_PROMPT
                
                # Use enhanced system prompt with explicit formatting instructions
                enhanced_system_prompt = system_prompt + """

    IMPORTANT FORMATTING INSTRUCTIONS:
    1. Use proper spacing between words and sentences.
    2. Do not run words together without spaces.
    3. Use clear paragraph breaks between sections.
    4. Use bullet points with proper spacing.
    5. Format all dollar amounts consistently (e.g., $1,000.00).
    6. Format all percentages with a space before % (e.g., 50 %).
    7. Keep all text properly separated and readable.
    """
                
                response = generate_text(
                    prompt=prompt,
                    system_prompt=enhanced_system_prompt,
                    temperature=0.4,
                    max_tokens=750
                )
                
                # Check if the response looks properly formatted
                if len(response) > 100 and " " in response:
                    return response
                else:
                    # If response looks suspicious, fall back to simple response
                    return simple_response
                    
            except Exception as e:
                logger.error(f"Error generating LLM response: {str(e)}")
                # Fall back to simple response
                return simple_response
                    
        except Exception as e:
            logger.error(f"Error creating goal: {str(e)}")
            # Return error message
            return f"""
    I apologize, but I couldn't create your {params.get('goal_type', 'goal')} at this time. 

    The error was: {str(e)}

    Please try again with the following format:
    "I want to create a [goal type] goal of $[amount] by [date]"
    """
    
    def _provide_goal_creation_guidance(self, customer_id):
        """
        Provide helpful guidance for creating a goal.
        
        Args:
            customer_id (str): The customer ID
            
        Returns:
            str: Helpful guidance message
        """
        # Get existing goals for context
        user_goals = self.goal_manager.get_user_goals(customer_id)
        has_goals = not user_goals.empty
        
        # Create a tailored response
        if has_goals:
            # User already has goals, reference them
            goal_types = [goal['Goal Type'] for _, goal in user_goals.iterrows()]
            goal_types_text = ", ".join(goal_types)
            
            response = f"""I'd be happy to help you create a new financial goal! 

To set up your goal, I'll need a few key pieces of information:

Required details:
• Goal name or type (e.g., Retirement, Home Purchase, Education, Travel)
• Target amount (how much you need to save)
• Target date (when you want to achieve this goal)

Optional details:
• Current savings (how much you've already saved)
• Priority level (High, Medium, Low)
• Monthly contribution (how much you can save per month)

You currently have goals for {goal_types_text}. What type of new goal would you like to create?

For example, you could say: "I want to save $5,000 for a vacation by December 2025" or "Create a retirement goal of $500,000 by 2045."
"""
        else:
            # User has no goals yet
            response = """I'd be happy to help you create your first financial goal! 

To set up your goal, I'll need a few key pieces of information:

Required details:
• Goal name or type (e.g., Retirement, Home Purchase, Education, Travel)
• Target amount (how much you need to save)
• Target date (when you want to achieve this goal)

Optional details:
• Current savings (how much you've already saved)
• Priority level (High, Medium, Low)
• Monthly contribution (how much you can save per month)

For example, you could say: "I want to save $5,000 for a vacation by December 2025" or "Create a retirement goal of $500,000 by 2045."

What kind of goal would you like to create?
"""
        
        return response
    
    def _provide_missing_parameters_guidance(self, missing_params, provided_params):
        """
        Provide guidance about missing parameters for goal creation.
        
        Args:
            missing_params (list): List of missing parameter names
            provided_params (dict): Parameters that were provided
            
        Returns:
            str: Helpful guidance message
        """
        # Format what we already know
        provided_info = []
        
        if "goal_type" in provided_params or "goal_name" in provided_params:
            goal_name = provided_params.get("goal_name", provided_params.get("goal_type", ""))
            provided_info.append(f"Goal: {goal_name}")
        
        if "target_amount" in provided_params:
            provided_info.append(f"Amount: ${provided_params['target_amount']:,.2f}")
        
        if "target_date" in provided_params:
            provided_info.append(f"Target date: {provided_params['target_date']}")
        
        if "current_savings" in provided_params:
            provided_info.append(f"Current savings: ${provided_params['current_savings']:,.2f}")
        
        if "priority" in provided_params:
            provided_info.append(f"Priority: {provided_params['priority']}")
        
        # Format what's missing
        missing_info = []
        for param in missing_params:
            if param == "goal_name":
                missing_info.append("the goal name or type (e.g., Retirement, Home Purchase)")
            elif param == "target_amount":
                missing_info.append("the target amount you want to save")
            elif param == "target_date":
                missing_info.append("the date by which you want to achieve this goal")
        
        # Combine into a helpful response
        if provided_info:
            provided_text = "Here's what I understand so far:\n• " + "\n• ".join(provided_info)
        else:
            provided_text = "I don't have any details about your goal yet."
        
        missing_text = "To create your goal, I also need:\n• " + "\n• ".join(missing_info)
        
        response = f"""Thanks for starting to create a financial goal! {provided_text}

{missing_text}

Could you please provide the missing information so I can set up your goal properly?
"""
        
        return response
    
    def _handle_modify_goal(self, query, customer_id):
        """
        Handle a goal modification query.
        
        Args:
            query (str): The user's query
            customer_id (str): The customer ID
            
        Returns:
            str: The response to the user
        """
        # Extract the goal ID
        goal_id = self._extract_goal_id(query, customer_id)
        
        if not goal_id:
            # No goal was identified
            return (
                "I'm not sure which goal you want to modify. "
                "Please specify the goal name or ID."
            )
        
        # Get the goal
        goal = self.goal_manager.get_goal_by_id(goal_id)
        
        if goal is None:
            return f"I couldn't find a goal with ID {goal_id}."
        
        # Extract the parameters to update - try LLM first, then fall back to regex
        update_params = self._extract_goal_parameters_with_llm(query)
        
        # If LLM extraction fails or provides minimal results, fall back to regex
        if not update_params or len(update_params) <= 1:
            update_params = self._extract_goal_parameters(query)
        
        if not update_params:
            # No parameters to update were identified
            return (
                f"I understand you want to modify your {goal['Goal Name']} goal, "
                "but I'm not sure what changes you want to make. "
                "Please specify what you'd like to change (e.g., target amount, target date)."
            )
        
        # Track if we're updating the timeline
        timeline_changed = False
        old_target_date = goal['Target Date']
        new_target_date = update_params.get('target_date', old_target_date)
        
        if old_target_date != new_target_date:
            # Timeline is changing
            timeline_changed = True
            
            # Calculate days difference
            old_date = datetime.strptime(old_target_date, "%m/%d/%Y")
            new_date = datetime.strptime(new_target_date, "%m/%d/%Y")
            days_difference = (new_date - old_date).days
        
        logger.info(f"Updating goal {goal_id} with parameters: {update_params}")
        
        # Update the goal
        success = self.goal_manager.update_goal(goal_id, **update_params)
        
        if not success:
            return f"There was an error updating your {goal['Goal Name']} goal."
        
        # Get the updated goal
        updated_goal = self.goal_manager.get_goal_by_id(goal_id)
        
        # Generate a response
        response_elements = [
            f"Your {updated_goal['Goal Name']} goal has been successfully updated."
        ]
        
        # Add details about the changes
        for param, value in update_params.items():
            if param == 'target_amount':
                response_elements.append(f"Target amount updated to: ${value:,.2f}")
            elif param == 'current_savings':
                response_elements.append(f"Current savings updated to: ${value:,.2f}")
            elif param == 'target_date':
                response_elements.append(f"Target date updated to: {value}")
            elif param == 'priority':
                response_elements.append(f"Priority updated to: {value}")
            elif param == 'monthly_contribution':
                response_elements.append(f"Monthly contribution updated to: ${value:,.2f}")
        
        # If timeline changed, provide additional information
        if timeline_changed:
            # Generate a detailed explanation for timeline changes
            prompt = self.prompts.TIMELINE_ADJUSTMENT_PROMPT.format(
                goal_type=updated_goal['Goal Type'],
                original_date=old_target_date,
                new_date=new_target_date,
                days_difference=abs(days_difference),
                original_timeline=goal['Goal Timeline'],
                new_timeline=updated_goal['Goal Timeline'],
                original_contribution=goal['Monthly Contribution'],
                new_contribution=updated_goal['Monthly Contribution'],
                allocation_changed=False  # Simplified for now
            )
            
            system_prompt = self.prompts.SYSTEM_PROMPT
            
            # Use enhanced system prompt with explicit formatting instructions
            enhanced_system_prompt = system_prompt + """

IMPORTANT FORMATTING INSTRUCTIONS:
1. Use proper spacing between words and sentences.
2. Do not run words together without spaces.
3. Use clear paragraph breaks between sections.
4. Use bullet points with proper spacing.
5. Format all dollar amounts consistently (e.g., $1,000.00).
6. Format all percentages with a space before % (e.g., 50 %).
7. Keep all text properly separated and readable.
"""
            
            timeline_explanation = generate_text(
                prompt=prompt,
                system_prompt=enhanced_system_prompt,
                temperature=0.4,
                max_tokens=750
            )
            
            response_elements.append("\n" + timeline_explanation)
        
        return "\n\n".join(response_elements)
    
    def _handle_delete_goal(self, query, customer_id):
        """
        Handle a goal deletion query.
        
        Args:
            query (str): The user's query
            customer_id (str): The customer ID
            
        Returns:
            str: The response to the user
        """
        # Extract the goal ID
        goal_id = self._extract_goal_id(query, customer_id)
        
        if not goal_id:
            # No goal was identified
            return (
                "I'm not sure which goal you want to delete. "
                "Please specify the goal name or ID."
            )
        
        # Get the goal first so we have its name
        goal = self.goal_manager.get_goal_by_id(goal_id)
        
        if goal is None:
            return f"I couldn't find a goal with ID {goal_id}."
        
        goal_name = goal['Goal Name']
        
        logger.info(f"Deleting goal {goal_id} ({goal_name})")
        
        # Delete the goal
        success = self.goal_manager.delete_goal(goal_id)
        
        if not success:
            return f"There was an error deleting your {goal_name} goal."
        
        # Generate a response
        response = (
            f"Your {goal_name} goal has been successfully deleted. "
            "If you ever want to create a new goal, just let me know!"
        )
        
        return response
    
    def _handle_goal_status(self, query, customer_id):
        """
        Handle a goal status query.
        
        Args:
            query (str): The user's query
            customer_id (str): The customer ID
            
        Returns:
            str: The response to the user
        """
        # Extract the goal ID
        goal_id = self._extract_goal_id(query, customer_id)
        
        if not goal_id:
            # No goal was identified, provide status for all goals
            user_goals = self.goal_manager.get_user_goals(customer_id)
            
            if user_goals.empty:
                return "You don't have any financial goals set up yet. Would you like to create one?"
            
            # Generate a summary of all goals
            summary_parts = ["Here's the status of all your financial goals:"]
            
            for _, goal in user_goals.iterrows():
                # Calculate if the goal is on track
                target_date = datetime.strptime(goal['Target Date'], "%m/%d/%Y")
                days_remaining = (target_date - datetime.now()).days
                days_total = (target_date - datetime.strptime(goal['Start Date'], "%m/%d/%Y")).days
                days_elapsed = days_total - days_remaining
                
                expected_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
                actual_progress = goal['Progress (%)']
                
                on_track = actual_progress >= expected_progress if days_elapsed > 0 else True
                
                # Add goal summary
                goal_summary = (
                    f"\n\n## {goal['Goal Name']} ({goal['Goal Type']})\n"
                    f"Progress: {goal['Progress (%)']:.1f}% (${goal['Current Savings']:,.2f} of ${goal['Target Amount']:,.2f})\n"
                    f"Target Date: {goal['Target Date']} ({days_remaining} days remaining)\n"
                    f"Monthly Contribution: ${goal['Monthly Contribution']:,.2f}\n"
                    f"Status: {'On track' if on_track else 'Needs attention'}"
                )
                
                summary_parts.append(goal_summary)
            
            return "\n".join(summary_parts)
        
        # Get details for the specific goal
        goal = self.goal_manager.get_goal_by_id(goal_id)
        
        if goal is None:
            return f"I couldn't find a goal with ID {goal_id}."
        
        # Calculate if the goal is on track
        target_date = datetime.strptime(goal['Target Date'], "%m/%d/%Y")
        days_remaining = (target_date - datetime.now()).days
        days_total = (target_date - datetime.strptime(goal['Start Date'], "%m/%d/%Y")).days
        days_elapsed = days_total - days_remaining
        
        expected_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
        actual_progress = goal['Progress (%)']
        
        on_track = actual_progress >= expected_progress if days_elapsed > 0 else True
        
        # Generate a detailed status using the prompt
        prompt = self.prompts.GOAL_STATUS_PROMPT.format(
            goal_type=goal['Goal Type'],
            target_amount=goal['Target Amount'],
            current_savings=goal['Current Savings'],
            progress_percentage=goal['Progress (%)'],
            target_date=goal['Target Date'],
            days_remaining=days_remaining,
            monthly_contribution=goal['Monthly Contribution'],
            on_track=on_track
        )
        
        system_prompt = self.prompts.SYSTEM_PROMPT
        
        # Use enhanced system prompt with explicit formatting instructions
        enhanced_system_prompt = system_prompt + """

IMPORTANT FORMATTING INSTRUCTIONS:
1. Use proper spacing between words and sentences.
2. Do not run words together without spaces.
3. Use clear paragraph breaks between sections.
4. Use bullet points with proper spacing.
5. Format all dollar amounts consistently (e.g., $1,000.00).
6. Format all percentages with a space before % (e.g., 50 %).
7. Keep all text properly separated and readable.
"""
        
        response = generate_text(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            temperature=0.4,
            max_tokens=750
        )
        
        return response
    
    def _handle_goal_recommendations(self, customer_id):
        """
        Handle a goal recommendations query.
        
        Args:
            customer_id (str): The customer ID
            
        Returns:
            str: The response to the user
        """
        # Get user goals
        user_goals = self.goal_manager.get_user_goals(customer_id)
        
        if user_goals.empty:
            return (
                "You don't have any financial goals set up yet. "
                "Would you like to create one? I can help you establish goals for things "
                "like retirement, home purchase, education, or emergency funds."
            )
        
        # Get user risk profile
        try:
            user_profiles_path = os.path.join(self.data_path, "expanded_risk_profiles.csv")
            profiles_df = pd.read_csv(user_profiles_path)
            user_profile = profiles_df[profiles_df['Customer ID'] == customer_id.upper()]
            
            if user_profile.empty:
                risk_profile = "Unknown"
            else:
                risk_profile = user_profile.iloc[0]['Risk Category']
        except Exception:
            risk_profile = "Unknown"
        
        # Format goals data for the prompt
        goals_data = self._format_goals_summary(user_goals)
        
        # Generate recommendations using the prompt
        prompt = self.prompts.GOAL_RECOMMENDATIONS_PROMPT.format(
            customer_id=customer_id,
            risk_profile=risk_profile,
            goals_data=goals_data
        )
        
        system_prompt = self.prompts.SYSTEM_PROMPT
        
        # Use enhanced system prompt with explicit formatting instructions
        enhanced_system_prompt = system_prompt + """

IMPORTANT FORMATTING INSTRUCTIONS:
1. Use proper spacing between words and sentences.
2. Do not run words together without spaces.
3. Use clear paragraph breaks between sections.
4. Use bullet points with proper spacing.
5. Format all dollar amounts consistently (e.g., $1,000.00).
6. Format all percentages with a space before % (e.g., 50 %).
7. Keep all text properly separated and readable.
"""
        
        response = generate_text(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            temperature=0.4,
            max_tokens=1000
        )
        
        return response
    
    def _handle_general_goal_query(self, query, customer_id):
        """
        Handle a general goal-related query.
        
        Args:
            query (str): The user's query
            customer_id (str): The customer ID
            
        Returns:
            str: The response to the user
        """
        # Get user goals for context
        user_goals = self.goal_manager.get_user_goals(customer_id)
        has_goals = not user_goals.empty
        
        # Format goals summary
        goals_summary = self._format_goals_summary(user_goals) if has_goals else "No goals found."
        
        # Select the appropriate prompt based on whether the user has goals
        if has_goals:
            prompt = self.prompts.GENERAL_GOAL_PROMPT_WITH_GOALS.format(
                customer_id=customer_id,
                user_query=query,
                goals_summary=goals_summary
            )
        else:
            prompt = self.prompts.GENERAL_GOAL_PROMPT_WITHOUT_GOALS.format(
                customer_id=customer_id,
                user_query=query,
                goals_summary=goals_summary
            )
        
        # Generate a response using the general goal prompt
        system_prompt = self.prompts.SYSTEM_PROMPT
        
        # Use enhanced system prompt with explicit formatting instructions
        enhanced_system_prompt = system_prompt + """

IMPORTANT FORMATTING INSTRUCTIONS:
1. Use proper spacing between words and sentences.
2. Do not run words together without spaces.
3. Use clear paragraph breaks between sections.
4. Use bullet points with proper spacing.
5. Format all dollar amounts consistently (e.g., $1,000.00).
6. Format all percentages with a space before % (e.g., 50 %).
7. Keep all text properly separated and readable.
"""
        
        response = generate_text(
            prompt=prompt,
            system_prompt=enhanced_system_prompt,
            temperature=0.4,
            max_tokens=750
        )
        
        return response
    
    def _extract_value(self, label, text):
        """Helper to extract a labeled value from text."""
        pattern = f"{label}: (.*?)(?:\n|$)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None
    
    def _extract_amount(self, label, text):
        """Helper to extract a dollar amount from text."""
        pattern = f"{label}: \$([\d,]+\.\d+)"
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(',', ''))
        return None
    
    def _extract_goal_type(self, query):
        """Extract goal type from a query."""
        goal_types = [
            "Retirement", "Home Purchase", "Education", "Emergency Fund",
            "Travel", "Car Purchase", "Wedding", "Medical Expenses"
        ]
        
        query_lower = query.lower()
        for goal_type in goal_types:
            if goal_type.lower() in query_lower:
                return goal_type
        
        return "Custom Goal"