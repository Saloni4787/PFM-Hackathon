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
    You are the Transaction Analysis Agent, a specialized financial assistant responsible for analyzing customer transaction data, categorizing spending patterns, and generating personalized financial nudges. Your role is to identify spending patterns, detect relevant financial events, and generate appropriate financial nudges aligned with the user's goals.

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

    Format each nudge as a conversational message that the Financial Advisor Agent can deliver to the user. Include specific data points to make the nudges concrete and actionable.
    """
    
    # Budget-specific analysis prompt
    BUDGET_ALERT_PROMPT = """
    Review the budget data for {customer_id}:
    {budget_data}

    Generate appropriate budget alert nudges considering:
    - Categories exceeding 80% of monthly limit
    - Historical spending patterns in these categories from transaction data
    - Connection to the user's active financial goals

    Format each budget alert as a helpful observation with an actionable suggestion.
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
    """
    
    # Response formatting prompt
    RESPONSE_FORMATTING_PROMPT = """
    Format the generated nudges into a clear, prioritized response:

      1. Start with a brief overview of the customer's financial situation
      2. Present ALL applicable nudges in priority order, with the highest impact nudges first
      3. For each nudge, include:
         - The observation (what was detected)
         - The impact (why it matters)
         - The recommendation (what action to take)
         - The benefit (how it helps their goals)

      Ensure the language is conversational, supportive, and aligned with the customer's financial goals.
      Format each nudge with a clear heading and bullet points for readability.
    """
