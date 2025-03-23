"""
Transaction Analysis Agent Prompts

This module contains all the prompt templates required for the Transaction Analysis Agent
in the Personal Finance Manager application.
"""

class TransactionAnalysisPrompts:
    """
    Collection of prompts for the Transaction Analysis Agent functionality.
    
    These prompts are designed to work with the sample data structure and
    focus on transaction categorization and nudge generation.
    """
    
    # System initialization prompt that defines the agent's role and capabilities
    SYSTEM_PROMPT = """
    You are the Transaction Analysis Agent, a specialized financial assistant responsible for analyzing customer transaction data, categorizing spending patterns, and generating personalized financial nudges. 
    ONLY OUTPUT the Nudges
   
    Your capabilities include:
    1. Categorizing transactions based on merchant category codes
    2. Detecting spending patterns across transaction history
    3. Identifying potential financial events (like salary deposits or bill payments)
    4. Generating personalized financial nudges based on predefined templates
    5. Aligning nudges with the user's financial goals

    When prompted, analyze the provided transaction data and user information, then generate appropriate financial nudges that would be valuable for the user.

    When responding:
    1. Keep your analysis focused on patterns relevant to the user's goals
    2. Prioritize nudges by potential impact and relevance
    3. Format nudges in natural, conversational language
    4. Include relevant transaction data as supporting evidence
    5. Do not make assumptions and stick to the given data.
    6. If a nudge is already prvided on a certain transaction, do not provide another nudge on the same transaction.

   CRITICAL FORMATTING REQUIREMENTS:
   1. ALWAYS format monetary values as "$ 123.45" with a space after the dollar sign
   2. ALWAYS add spaces between words - never allow words to run together
   3. ALWAYS format transaction IDs with a space after them: "TX12345 "
   4. NEVER allow character-by-character spacing in the output (like "1 0 0")
   5. ALWAYS use proper spacing in descriptive phrases (like "per month" not "permonth")

   These formatting standards are non-negotiable and must be followed perfectly.
   
   Make sure to ONLY OUTPUT Nudges.
    """
    
    # Main transaction analysis prompt
    TRANSACTION_ANALYSIS_PROMPT = """
    Analyze the following transaction data for {customer_id}:

    {transaction_data}

    The customer has the following profile information:
    {user_profile}

    The customer has set these financial goals:
    {financial_goals}

    The customer's budget information:
    {budget_data}

    The customer has these active subscriptions:
    {subscription_data}

    Based on this information:
    1. Identify the top spending categories
    2. Detect any unusual spending patterns
    3. Identify any relevant financial events
    4. Generate personalized financial nudges that are aligned with the customer's goals
    5. Prioritize the nudges by importance and potential impact
    6. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
    7. Use % sign where necessary
      
   Make sure you are separating TEXT such as "$ 283.96 in the Diningcategory" not "283.96intheDiningcategory"

    """
    
    # General nudge generation prompt
    NUDGE_GENERATION_PROMPT = """
    Based on the transaction analysis for {customer_id}, generate personalized financial nudges for the following patterns:

    1. Budget Threshold Alerts: 
    - Check if any budget category is approaching or exceeding the monthly limit
    - Consider the user's goal priorities when suggesting adjustments

    2. Subscription Review Opportunities:
    - Identify total subscription spending
    - Highlight potential savings opportunities

    3. Spending Pattern Insights:
    - Compare spending against historical patterns
    - Connect spending behaviors to goal progress

    4. Goal Progress Acceleration:
    - Suggest specific actions that could accelerate progress toward financial goals
    - Quantify the potential impact of recommended changes

    5. Event-Based Nudges:
    - Identify financial events such as salary deposits, bill payments, or unusual transactions
    - Provide context-specific recommendations based on these events

   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary
   
    """
    
    # Budget-specific analysis prompt
    BUDGET_ALERT_PROMPT = """
    Review the budget data for {customer_id}:
    {budget_data}

    Generate appropriate budget alert nudges considering:
    - Categories exceeding 80% of monthly limit
    - Explain in detail about the budget allocated, and how much has been used.
    - Historical spending patterns in these categories from transaction data
    - Connection to the user's active financial goals
    Please follow the Sample output strictly.
    Sample Output: "You have spent $ 283.96  in the Dining category, which is 70.45.96 % of the allocated budget of $ 403.08"

    Format each budget alert as a helpful observation with an actionable suggestion.
    
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary
      
    """
    
    # Subscription-specific analysis prompt
    SUBSCRIPTION_ANALYSIS_PROMPT = """
    Analyze the subscription data for {customer_id}:
    {subscription_data}

    Calculate:
    - Total monthly subscription cost
    - Annual subscription expenditure
    - Percentage of income spent on subscriptions
    - Potential savings opportunities

    Generate subscription-related nudges that highlight:
    - Total subscription burden
    - Specific high-cost subscriptions
    - Impact of subscription costs on financial goals
    - Actionable recommendations for optimization
    
   
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary      
    """
    
    # Goal alignment analysis prompt
    GOAL_ALIGNMENT_PROMPT = """
    Based on the financial goals for {customer_id}:
    {financial_goals}

    And recent transaction data:
    {transaction_data}

    Generate goal-oriented nudges that:
    - Connect spending behaviors to goal progress
    - Highlight specific transactions that either support or hinder goal achievement
    - Suggest concrete adjustments that could accelerate goal achievement
    - Quantify the impact of suggested changes (e.g., "Reducing dining expenses by $100/month could help you reach your vacation goal 2 months sooner")
   
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary
        
    """
    
    # Recurring charge change prompt (event-based)
    RECURRING_CHARGE_PROMPT = """
    Analyze the subscription and transaction data for {customer_id}:
    
    Subscription Data:
    {subscription_data}
    
    Transaction Data:
    {transaction_data}
    
    Generate a recurring charge change nudge that:
    1. Identifies any subscription charges that have changed in amount
    2. Compares the new amount to the previous amount
    3. Calculates the impact of this change over time (monthly, yearly)
    4. Provides context on whether this change was expected
    5. Suggests actions the customer might want to take based on the change
    
    
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary     
    """
    
    # Goal milestone prompt (event-based)
    GOAL_MILESTONE_PROMPT = """
    Analyze the following financial goals for {customer_id}:
    {financial_goals}
    
    Generate a goal milestone nudge that:
    1. Identifies specific goals that have reached significant milestones (e.g., 25%, 50%, 75%) and explain in detail about the goal and how much is remaning.
    2. Congratulates the customer on their progress and tell them the progress
    3. Provides an updated timeline for goal completion based on current progress
    4. Suggests ways to accelerate progress even further
    5. Relates this achievement to their overall financial health
    
    
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary     
    """
    
    # Salary deposit prompt (event-based)
    SALARY_DEPOSIT_PROMPT = """
    Analyze the transaction data for {customer_id} to identify salary deposit patterns:
    
    Transaction Data:
    {transaction_data}
    
    User Profile:
    {user_profile}
    
    Financial Goals:
    {financial_goals}
    
    Generate a salary deposit nudge that:
    1. Identifies the recent salary deposit with amount and date
    2. Suggests optimal allocation of this income based on their goals
    3. Recommends specific actions that align with their financial priorities
    4. If applicable, suggests automating transfers to savings or investment accounts
    
   
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary    
    """
    
    # Unusual activity prompt (event-based)
    UNUSUAL_ACTIVITY_PROMPT = """
    Analyze the transaction data for {customer_id}:
    
    Transaction Data:
    {transaction_data}
    
    Generate an unusual activity nudge that:
    1. Identifies specific transactions that appear unusual (based on amount, merchant, location, etc.)
    2. You must Explain why these transactions stand out from normal patterns
    3. Ask if these transactions were authorized
    4. Provide guidance on monitoring account activity
    5. Suggest security measures if appropriate
    
    
   1. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"
   2. Use % sign where necessary     
    """

    TRANSACTION_FORMATTING_GUIDE = """
CRITICAL FORMATTING REQUIREMENTS:

1. FORMAT ALL MONETARY VALUES with these exact rules:
   - Always include a dollar sign with a space after it: "$ 100" NOT "$100"
   - When mentioning dollar amounts in text: "$ 100 per month" NOT "100permonth"
   - Include commas for thousands: "$ 1,200" NOT "$ 1200"

2. FORMAT ALL TRANSACTION IDs with these exact rules:
   - Always include a space after the transaction ID: "TX12345 " NOT "TX12345"
   - When referencing transaction amounts: "TX12345 ($ 100)" NOT "TX12345($100)"
   - Include spaces inside and outside parentheses: " ($ 100) " NOT "(100)"

3. ENSURE PROPER SPACING between all words:
   - Words must have spaces between them: "towards the Education goal" NOT "towardstheEducationgoal"
   - Numbers and words must have spaces: "$ 100 per month" NOT "$ 100permonth"
   - Transaction IDs and descriptions must have spaces: "TX12345 from Merchant" NOT "TX12345fromMerchant"

4. FORMAT RANGES correctly:
   - Use proper spacing around hyphens: "$ 200 - $ 500" NOT "$ 200-$ 500"

EVERY numeric value, transaction ID, and piece of text MUST follow these exact formatting rules.
"""

   # Enhance the RESPONSE_FORMATTING_PROMPT with these explicit instructions
    RESPONSE_FORMATTING_PROMPT = """
   Format the financial nudges into a cohesive response for the customer. 

   CRITICAL FORMATTING REQUIREMENTS:
   1. Every single monetary amount must be formatted as "$ 123.45" (with a space after the $ sign)
   2. Every single transaction ID must have a space after it: "TX12345 " not "TX12345"
   3. All words must have proper spacing between them - NO words should run together
   4. All parenthetical amounts must be formatted as " ($ 123.45) " (with spaces inside and outside)
   5. Descriptions like "per month" or "towards the goal" must have proper spaces between words
   6. EVERY descriptive phrase must have proper spaces: "per month" not "permonth"
   7. NEVER output text with character-by-character spacing (like "1 0 0" or "p e r")
   8. NUMBERS running into TEXT must be separated: "$ 100 per month" not "$ 100permonth"

   Start with a brief overview of the customer's financial situation, then present the nudges in order of priority.
   For each nudge, include:
   - Observation: What was detected in the data
   - Impact: Why this matters to the customer
   - Recommendation: Specific action the customer can take
   - Benefit: The positive outcome of taking this action

   Organize the nudges in a clean, readable format with clear headings and concise language.
   """