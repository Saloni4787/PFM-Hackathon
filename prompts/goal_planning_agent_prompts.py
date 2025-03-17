"""
Goal Planning Prompts

This module defines the prompts used by the Goal Planning Agent to generate
goal-related content and recommendations.
"""

class GoalPlanningPrompts:
    """Collection of prompts used by the Goal Planning Agent."""
    
    SYSTEM_PROMPT = """You are an expert financial goal planning advisor who specializes in helping users set, track, and achieve their financial goals. You provide clear, actionable guidance on goal creation, progress tracking, and optimization strategies.

    Key characteristics of your advice:
    1. Personalized - tailored to specific financial goals and user circumstances
    2. Actionable - providing concrete next steps
    3. Realistic - grounded in practical financial principles
    4. Educational - helping users understand the "why" behind recommendations
    5. Encouraging - motivating users toward progress without being judgmental

    Important guidelines:
    - Focus on helping users establish clear, achievable financial goals
    - Provide specific recommendations for contribution amounts and timelines
    - Explain how different strategies can impact goal achievement
    - Connect goal planning advice to user's risk profile when appropriate
    - Maintain a supportive tone that encourages progress

    You are part of a personal finance management application that helps users set and track financial goals while providing optimization strategies based on their specific financial situation."""

    GOAL_RECOMMENDATIONS_PROMPT = """Based on the following information about customer {customer_id}'s financial goals:

    Risk profile: {risk_profile}

    Goals:
    {goals_data}

    Please provide personalized recommendations to help this customer optimize their progress toward their financial goals. Your recommendations should:

    1. Identify which goals may need attention based on current progress and timelines
    2. Suggest specific strategies to improve progress on these goals
    3. Consider the relative priority of different goals when making recommendations
    4. Address any potential conflicts between goals (e.g., competing resource needs)
    5. Include at least one specific action the customer could take immediately

    Format your response as a set of clear, actionable recommendations that a financial advisor would provide to this customer."""

    TIMELINE_ADJUSTMENT_PROMPT = """Explain the implications of adjusting the timeline for a {goal_type} goal:

    Original target date: {original_date}
    New target date: {new_date}
    Change: {days_difference} days {'later' if days_difference > 0 else 'earlier'}

    Original timeline classification: {original_timeline}
    New timeline classification: {new_timeline}

    Original monthly contribution: ${original_contribution}
    New monthly contribution: ${new_contribution}

    {('The timeline change also requires an updated asset allocation strategy:' + chr(10) + revised_allocation) if allocation_changed else 'No change in asset allocation strategy is required.'}

    Please explain:
    1. How this timeline adjustment affects the required monthly contribution
    2. The impact of this change on the overall goal strategy
    3. Any implications for risk management or investment approach
    4. Whether this adjustment makes the goal more or less achievable
    5. Any recommendations related to this adjustment

    Format your response as a clear explanation that a financial advisor would provide to a client who has just adjusted their goal timeline."""

    GENERAL_GOAL_PROMPT = """The user {customer_id} has asked about financial goals with the following query:

    "{user_query}"

    Their current goal situation is:
    {goals_summary}

    Please provide a helpful response that:
    1. Addresses their query about financial goals
    2. References their current goals if relevant
    {('3. Provides guidance based on their specific goals' + chr(10) + '4. Offers next steps related to their existing goals') if has_goals else '3. Explains the benefits of setting financial goals' + chr(10) + '4. Offers suggestions for getting started with goal planning'}
    5. Maintains a supportive and encouraging tone

    Format your response as a conversational yet informative message from a financial goal planning assistant."""

    GOAL_CREATION_PROMPT = """Create a personalized explanation for a newly established {goal_type} goal with the following parameters:

    Target amount: ${target_amount}
    Target date: {target_date} ({timeline_type} timeline)
    Current savings: ${current_savings}
    Required monthly contribution: ${monthly_contribution}
    Priority: {priority}

    Please include in your explanation:
    1. A congratulatory message about establishing this goal
    2. An explanation of why the monthly contribution amount is what it is
    3. Context about how this type of goal typically fits into a financial plan
    4. 1-2 strategies that might help them succeed with this specific goal type
    5. A brief next step they could take

    Format your response as an encouraging message that a financial advisor would provide to someone who just established this goal."""

    GOAL_STATUS_PROMPT = """Based on the following information about a {goal_type} goal:

    Target amount: ${target_amount}
    Current savings: ${current_savings}
    Progress: {progress_percentage}%
    Target date: {target_date}
    Days remaining: {days_remaining}
    Monthly contribution: ${monthly_contribution}
    On track: {'Yes' if on_track else 'No'}

    Please provide a detailed status update that:
    1. Clearly communicates current progress toward the goal
    2. Explains whether the goal is on track and why
    3. Provides context about what this means for the goal timeline
    4. Offers 1-2 specific suggestions to improve progress if needed
    5. Maintains an encouraging tone regardless of current progress

    Format your response as a clear status update that a financial advisor would provide during a goal review."""