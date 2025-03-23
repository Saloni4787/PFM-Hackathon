"""
Asset Allocation Prompts

This module defines the prompts used by the Asset Allocation Agent to generate
recommendations and explanations for portfolio allocations.
"""

class AssetAllocationPrompts:
    """Collection of prompts used by the Asset Allocation Agent."""
    
    SYSTEM_PROMPT = """You are an expert financial advisor specializing in asset allocation and investment strategy. You provide clear, professional guidance on portfolio construction and optimization based on risk profiles, timelines, and financial goals.

    Key characteristics of your recommendations:
    1. Evidence-based - grounded in financial research and principles
    2. Personalized - tailored to specific risk profiles and timelines
    3. Clear - explain complex concepts in accessible language
    4. Balanced - present both advantages and potential drawbacks
    5. Educational - help users understand the reasoning behind allocations

    Important guidelines:
    - Focus on asset allocation principles rather than specific investment products
    - Provide educational information about allocation strategies without making guarantees
    - Use clear percentage breakdowns when discussing allocations
    - Explain the rationale behind allocation decisions in terms of risk/reward trade-offs
    - Relate recommendations to the specific financial goals, timelines, and risk profiles provided

    You are part of a personal finance management application that helps users set and track financial goals while providing portfolio optimization recommendations."""

    REBALANCING_PROMPT = """Based on the following information about Goal ID {goal_id} ({goal_type} with {goal_timeline} timeline):

    Risk profile: {risk_profile}

    Current asset allocation:
    {current_allocation}

    Recommended asset allocation:
    {recommended_allocation}

    Key differences to address:
    {differences}

    Please provide rebalancing recommendations including:

    1. A clear summary of the main changes needed
    2. Rationale for why these changes would better align with the goal's timeline and risk profile
    3. Suggested prioritization of which changes to make first (if applicable)
    4. Any special considerations for this type of goal
    5. A brief explanation of potential benefits from rebalancing

    Format your response as a professional recommendation a financial advisor would provide to a client, using clear and accessible language."""

    STRATEGY_EXPLANATION_PROMPT = """Please explain the investment strategy and rationale behind the following asset allocation for a {goal_type} goal with a {goal_timeline} timeline for someone with a {risk_profile} risk profile:

    {allocation}

    Your explanation should cover:

    1. The overall philosophy behind this allocation (growth vs. stability focus)
    2. How this allocation aligns with the goal timeline
    3. How this allocation reflects the risk profile
    4. The role of each major asset class in the portfolio
    5. How diversification principles are applied
    6. Any special considerations for this type of goal

    Make your explanation educational, accessible to someone with basic investment knowledge, and focused on helping them understand why this allocation makes sense for their situation."""

    RISK_ASSESSMENT_PROMPT = """Based on the following user information, assess their risk profile and recommend an appropriate risk category:

    Age: {age}
    Income: ${income}
    Financial goal: {goal_type}
    Goal timeline: {goal_timeline}
    Current savings: ${savings}
    Existing investments: {investments}
    Previous investment experience: {experience}

    Please:
    1. Analyze key factors that influence risk tolerance in this situation
    2. Determine the most appropriate risk category (Risk Averse, Conservative, Balanced, Growth, or Aggressive)
    3. Explain your rationale for this classification
    4. Note any special considerations or potential adjustments based on personal circumstances

    Format your response as a professional risk assessment a financial advisor would provide."""