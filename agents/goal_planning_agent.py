"""
Goal Planning Agent

This script implements the Goal Planning Agent for the Personal Finance Manager,
which enables users to set, manage and achieve financial goals through personalized
planning and tailored asset allocation strategies.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Compute the path to the project root (one level up from the 'agents' folder)
project_root = os.path.join(current_dir, '..')

# Add the project root to sys.path
sys.path.append(project_root)

# Import the LLM utility and prompts
from utils.llm_response import generate_text, DekaLLMClient
from prompts.goal_planning_agent_prompts import GoalPlanningPrompts

# Import the Education and Asset Allocation agents
from agents.education_agent import EducationAgent
from agents.asset_allocation_agent import AssetAllocationAgent

class GoalPlanningAgent:
    """
    Manages financial goals including creation, tracking, and recommendations.
    
    This agent works with the Asset Allocation Agent and Education Agent
    to provide comprehensive goal planning services.
    """
    
    def __init__(self, 
                data_path: str = "./data",
                asset_allocation_agent: Optional[AssetAllocationAgent] = None,
                education_agent: Optional[EducationAgent] = None):
        """
        Initialize the Goal Planning Agent.
        
        Args:
            data_path: Path to directory containing CSV data files
            asset_allocation_agent: Instance of AssetAllocationAgent (created if None)
            education_agent: Instance of EducationAgent (created if None)
        """
        self.data_path = data_path
        self.llm_client = DekaLLMClient()
        
        # Initialize dependent agents if not provided
        self.asset_allocation_agent = asset_allocation_agent or AssetAllocationAgent(data_path)
        self.education_agent = education_agent or EducationAgent(data_path)
        
        # Load all data files
        self._load_data_files()
        
        print("Goal Planning Agent initialized successfully.")
    
    def _load_data_files(self):
        """Load all necessary data files from the data directory."""
        try:
            # Load user profiles
            self.user_profiles_df = pd.read_csv(f"{self.data_path}/user_profile_data.csv")
            
            # Load financial goals
            self.financial_goals_df = pd.read_csv(f"{self.data_path}/financial_goals_data.csv")
            
            # Load enhanced goal data
            self.enhanced_goals_df = pd.read_csv(f"{self.data_path}/enhanced_goal_data.csv")
            
            # Load risk profiles
            self.risk_profiles_df = pd.read_csv(f"{self.data_path}/expanded_risk_profiles.csv")
            
            print("All goal planning data files loaded successfully.")
        except Exception as e:
            print(f"Error loading data files: {str(e)}")
            raise
    
    def handle_goal_request(self, request: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a goal-related request and delegate to appropriate method.
        
        Args:
            request: User's request text
            user_context: User information and context
            
        Returns:
            Response data containing the result of the operation
        """
        customer_id = user_context.get("customer_id", "")
        intent = self._determine_goal_intent(request)
        
        # Route to appropriate method based on intent
        if intent == "create_goal":
            goal_params = self._extract_goal_params(request)
            return self.create_goal(customer_id, goal_params)
            
        elif intent == "modify_goal":
            goal_id = self._extract_goal_id(request)
            goal_params = self._extract_goal_params(request)
            return self.modify_goal(goal_id, goal_params)
            
        elif intent == "delete_goal":
            goal_id = self._extract_goal_id(request)
            return self.delete_goal(goal_id)
            
        elif intent == "get_goal_status":
            goal_id = self._extract_goal_id(request)
            return self.get_goal_status(goal_id)
            
        elif intent == "get_all_goals":
            return self.get_all_goals(customer_id)
            
        elif intent == "get_goal_recommendations":
            return self.get_goal_recommendations(customer_id)
            
        elif intent == "adjust_goal_timeline":
            goal_id = self._extract_goal_id(request)
            target_date = self._extract_date(request)
            return self.adjust_goal_timeline(goal_id, target_date)
            
        elif intent == "goal_education":
            # Extract topic and route to education agent
            topic = self._extract_educational_topic(request)
            goal_type = self._extract_goal_type(request)
            
            # Enhance user context with goal info
            if goal_type:
                user_context["goal_type"] = goal_type
            
            return {
                "response_type": "education",
                "content": self.education_agent.get_educational_content(
                    topic=topic,
                    user_context=user_context
                )
            }
        
        else:
            # Default: generate a general response about goals
            return self._generate_general_goal_response(customer_id, request)
    
    def create_goal(self, customer_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new financial goal.
        
        Args:
            customer_id: ID of the customer
            params: Goal parameters including type, amount, date, etc.
            
        Returns:
            Response containing the created goal information
        """
        print(f"Creating goal for customer {customer_id} with params: {params}")
        
        # Use lowercase customer ID in goals data
        customer_id_lower = customer_id.lower()
        
        # Validate required parameters
        required_params = ["goal_type", "target_amount", "target_date"]
        for param in required_params:
            if param not in params:
                return {
                    "success": False,
                    "error": f"Missing required parameter: {param}"
                }
        
        try:
            # Load customer's risk profile
            risk_profile = self._get_customer_risk_profile(customer_id)
            
            # Calculate missing goal parameters
            goal_data = self._calculate_goal_parameters(
                customer_id=customer_id_lower,
                goal_type=params["goal_type"],
                target_amount=params["target_amount"],
                target_date=params["target_date"],
                current_savings=params.get("current_savings", 0),
                start_date=params.get("start_date", datetime.now().strftime("%m/%d/%Y")),
                priority=params.get("priority", None)
            )
            
            # Generate a new goal ID (simple increment from highest existing goal ID)
            existing_goal_ids = self.financial_goals_df['Goal ID'].str.replace('GOAL', '').astype(int)
            new_goal_number = existing_goal_ids.max() + 1 if not existing_goal_ids.empty else 1
            goal_id = f"GOAL{new_goal_number}"
            
            # Add the goal ID to the data
            goal_data["goal_id"] = goal_id
            
            # Get asset allocation recommendation
            allocation = self.asset_allocation_agent.get_allocation_recommendation(
                risk_profile=risk_profile["Risk Category"],
                goal_timeline=goal_data["goal_timeline"],
                goal_type=goal_data["goal_type"]
            )
            
            # Get goal strategy explanation
            strategy_explanation = self.asset_allocation_agent.explain_allocation_strategy(
                risk_profile=risk_profile["Risk Category"],
                goal_timeline=goal_data["goal_timeline"],
                goal_type=goal_data["goal_type"]
            )
            
            # In a real system, we'd save the goal to the database here
            # For demo purposes, we'll just return the goal data
            
            return {
                "success": True,
                "response_type": "goal_created",
                "goal_id": goal_id,
                "goal_data": goal_data,
                "recommended_allocation": allocation,
                "strategy_explanation": strategy_explanation
            }
            
        except Exception as e:
            print(f"Error creating goal: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating goal: {str(e)}"
            }
    
    def modify_goal(self, goal_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Modify an existing financial goal.
        
        Args:
            goal_id: ID of the goal to modify
            params: Updated goal parameters
            
        Returns:
            Response containing the updated goal information
        """
        print(f"Modifying goal {goal_id} with params: {params}")
        
        try:
            # Get the existing goal
            goal = self._get_goal_by_id(goal_id)
            if not goal:
                return {
                    "success": False,
                    "error": f"Goal not found: {goal_id}"
                }
            
            # Update goal parameters
            goal_data = goal.copy()
            for key, value in params.items():
                if key in goal_data:
                    goal_data[key] = value
            
            # Recalculate dependent parameters if necessary
            if "target_amount" in params or "target_date" in params or "current_savings" in params:
                # Get customer ID from the goal
                customer_id = goal_data["customer_id"]
                
                # Recalculate parameters
                goal_data = self._calculate_goal_parameters(
                    customer_id=customer_id,
                    goal_type=goal_data["goal_type"],
                    target_amount=goal_data["target_amount"],
                    target_date=goal_data["target_date"],
                    current_savings=goal_data["current_savings"],
                    start_date=goal_data["start_date"],
                    priority=goal_data["priority"]
                )
                
                # Preserve the goal ID
                goal_data["goal_id"] = goal_id
            
            # In a real system, we'd update the goal in the database here
            # For demo purposes, we'll just return the updated goal data
            
            return {
                "success": True,
                "response_type": "goal_modified",
                "goal_id": goal_id,
                "goal_data": goal_data,
                "message": "Goal updated successfully"
            }
            
        except Exception as e:
            print(f"Error modifying goal: {str(e)}")
            return {
                "success": False,
                "error": f"Error modifying goal: {str(e)}"
            }
    
    def delete_goal(self, goal_id: str) -> Dict[str, Any]:
        """
        Delete a financial goal.
        
        Args:
            goal_id: ID of the goal to delete
            
        Returns:
            Response indicating success or failure
        """
        print(f"Deleting goal {goal_id}")
        
        try:
            # Get the existing goal
            goal = self._get_goal_by_id(goal_id)
            if not goal:
                return {
                    "success": False,
                    "error": f"Goal not found: {goal_id}"
                }
            
            # In a real system, we'd delete the goal from the database here
            # For demo purposes, we'll just return success
            
            return {
                "success": True,
                "response_type": "goal_deleted",
                "goal_id": goal_id,
                "message": f"Goal {goal_id} ({goal['goal_type']}) deleted successfully"
            }
            
        except Exception as e:
            print(f"Error deleting goal: {str(e)}")
            return {
                "success": False,
                "error": f"Error deleting goal: {str(e)}"
            }
    
    def get_goal_status(self, goal_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific goal.
        
        Args:
            goal_id: ID of the goal
            
        Returns:
            Response containing detailed goal status
        """
        print(f"Getting status for goal {goal_id}")
        
        try:
            # Get the existing goal
            goal = self._get_enhanced_goal_by_id(goal_id)
            if not goal:
                return {
                    "success": False,
                    "error": f"Goal not found: {goal_id}"
                }
            
            # Get current allocation if available
            allocation = self.asset_allocation_agent.get_goal_allocation(goal_id)
            
            # Get the customer's risk profile
            customer_id = self._get_customer_id_from_goal(goal_id)
            risk_profile = self._get_customer_risk_profile(customer_id)
            
            # Get recommendation for allocation changes if current allocation exists
            rebalancing_recommendation = None
            if allocation and risk_profile:
                rebalancing_recommendation = self.asset_allocation_agent.generate_rebalancing_recommendations(
                    goal_id=goal_id,
                    customer_id=customer_id,
                    goal_type=goal["goal_type"],
                    goal_timeline=goal["goal_timeline"],
                    risk_profile=risk_profile["Risk Category"],
                    current_allocation=allocation
                )
            
            # Calculate time remaining
            now = datetime.now()
            target_date = datetime.strptime(goal["target_date"], "%m/%d/%Y")
            days_remaining = (target_date - now).days
            months_remaining = days_remaining // 30
            
            # Calculate progress metrics
            progress_percentage = goal["progress_percentage"]
            remaining_amount = goal["target_amount"] - goal["current_savings"]
            
            # Calculate on track status
            elapsed_time = (now - datetime.strptime(goal["start_date"], "%m/%d/%Y")).days
            total_time = (target_date - datetime.strptime(goal["start_date"], "%m/%d/%Y")).days
            expected_progress = min(100, (elapsed_time / total_time * 100)) if total_time > 0 else 0
            
            on_track = progress_percentage >= expected_progress
            
            # Format response
            status = {
                "goal_id": goal_id,
                "goal_type": goal["goal_type"],
                "target_amount": goal["target_amount"],
                "current_savings": goal["current_savings"],
                "remaining_amount": remaining_amount,
                "progress_percentage": progress_percentage,
                "target_date": goal["target_date"],
                "days_remaining": days_remaining,
                "months_remaining": months_remaining,
                "monthly_contribution": goal["monthly_contribution"],
                "priority": goal["priority"],
                "on_track": on_track,
                "current_allocation": allocation if allocation else None,
                "rebalancing_recommendation": rebalancing_recommendation
            }
            
            return {
                "success": True,
                "response_type": "goal_status",
                "status": status
            }
            
        except Exception as e:
            print(f"Error getting goal status: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting goal status: {str(e)}"
            }
    
    def get_all_goals(self, customer_id: str) -> Dict[str, Any]:
        """
        Get all goals for a customer.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Response containing all customer goals
        """
        print(f"Getting all goals for customer {customer_id}")
        
        try:
            # Use lowercase customer ID to match goals data
            customer_id_lower = customer_id.lower()
            
            # Get all goals for the customer using the enhanced goals dataframe
            customer_goals = self.enhanced_goals_df[
                self.enhanced_goals_df['Customer ID'] == customer_id_lower
            ]
            
            if customer_goals.empty:
                return {
                    "success": True,
                    "response_type": "all_goals",
                    "customer_id": customer_id,
                    "goals": [],
                    "message": "No goals found for this customer"
                }
            
            # Convert to list of dictionaries
            goals_list = customer_goals.to_dict('records')
            
            # Add goal summaries
            for goal in goals_list:
                # Calculate time remaining
                now = datetime.now()
                target_date = datetime.strptime(goal["Target Date"], "%m/%d/%Y")
                days_remaining = (target_date - now).days
                
                # Add to goal record
                goal["Days Remaining"] = days_remaining
                goal["Remaining Amount"] = goal["Target Amount"] - goal["Current Savings"]
            
            return {
                "success": True,
                "response_type": "all_goals",
                "customer_id": customer_id,
                "goals": goals_list
            }
            
        except Exception as e:
            print(f"Error getting all goals: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting all goals: {str(e)}"
            }
    
    def get_goal_recommendations(self, customer_id: str) -> Dict[str, Any]:
        """
        Get recommendations for improving goal progress.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Response containing goal recommendations
        """
        print(f"Getting goal recommendations for customer {customer_id}")
        
        try:
            # Get all customer goals
            goals_response = self.get_all_goals(customer_id)
            if not goals_response["success"] or not goals_response["goals"]:
                return {
                    "success": True,
                    "response_type": "goal_recommendations",
                    "customer_id": customer_id,
                    "recommendations": [],
                    "message": "No goals found for this customer"
                }
            
            # Get the customer's risk profile
            risk_profile = self._get_customer_risk_profile(customer_id)
            risk_category = risk_profile["Risk Category"] if risk_profile else "Balanced"
            
            # Prepare data for LLM prompt
            goals_data = goals_response["goals"]
            
            # Format goals data for prompt
            goals_text = ""
            for goal in goals_data:
                goals_text += f"Goal ID: {goal['Goal ID']}\n"
                goals_text += f"Type: {goal['Goal Type']}\n"
                goals_text += f"Target Amount: ${goal['Target Amount']}\n"
                goals_text += f"Current Savings: ${goal['Current Savings']}\n"
                goals_text += f"Progress: {goal['Progress %']}%\n"
                goals_text += f"Target Date: {goal['Target Date']}\n"
                goals_text += f"Monthly Contribution: ${goal['Monthly Contribution']}\n"
                goals_text += f"Priority: {goal['Priority']}\n"
                goals_text += f"Days Remaining: {goal['Days Remaining']}\n\n"
            
            # Create prompt for LLM
            prompt = GoalPlanningPrompts.GOAL_RECOMMENDATIONS_PROMPT.format(
                customer_id=customer_id,
                risk_profile=risk_category,
                goals_data=goals_text
            )
            
            # Generate recommendations
            system_prompt = GoalPlanningPrompts.SYSTEM_PROMPT
            recommendations = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,
                max_tokens=1200
            )
            
            return {
                "success": True,
                "response_type": "goal_recommendations",
                "customer_id": customer_id,
                "recommendations": recommendations,
                "goals": goals_data
            }
            
        except Exception as e:
            print(f"Error getting goal recommendations: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting goal recommendations: {str(e)}"
            }
    
    def adjust_goal_timeline(self, goal_id: str, new_target_date: str) -> Dict[str, Any]:
        """
        Adjust a goal's timeline and recalculate required contributions.
        
        Args:
            goal_id: ID of the goal
            new_target_date: New target date for the goal (MM/DD/YYYY)
            
        Returns:
            Response containing updated goal information
        """
        print(f"Adjusting timeline for goal {goal_id} to {new_target_date}")
        
        try:
            # Get the existing goal
            goal = self._get_enhanced_goal_by_id(goal_id)
            if not goal:
                return {
                    "success": False,
                    "error": f"Goal not found: {goal_id}"
                }
            
            # Parse dates
            current_target_date = datetime.strptime(goal["target_date"], "%m/%d/%Y")
            new_target_date_obj = datetime.strptime(new_target_date, "%m/%d/%Y")
            
            # Validate new date is in the future
            if new_target_date_obj < datetime.now():
                return {
                    "success": False,
                    "error": "Target date must be in the future"
                }
            
            # Calculate new parameters
            remaining_amount = goal["target_amount"] - goal["current_savings"]
            days_difference = (new_target_date_obj - current_target_date).days
            
            # Determine new timeline classification
            months_to_target = (new_target_date_obj - datetime.now()).days // 30
            timeline_type = self._classify_timeline(months_to_target)
            
            # Calculate new monthly contribution
            months_remaining = max(1, (new_target_date_obj - datetime.now()).days / 30)
            new_monthly_contribution = remaining_amount / months_remaining
            
            # Format new parameters
            adjustment = {
                "target_date": new_target_date,
                "goal_timeline": timeline_type,
                "monthly_contribution": round(new_monthly_contribution, 2),
                "days_difference": days_difference
            }
            
            # Get a revised allocation recommendation if the timeline type changed
            revised_allocation = None
            if timeline_type != goal["goal_timeline"]:
                # Get the customer's risk profile
                customer_id = self._get_customer_id_from_goal(goal_id)
                risk_profile = self._get_customer_risk_profile(customer_id)
                
                # Get revised allocation
                revised_allocation = self.asset_allocation_agent.get_allocation_recommendation(
                    risk_profile=risk_profile["Risk Category"],
                    goal_timeline=timeline_type,
                    goal_type=goal["goal_type"]
                )
            
            # Generate explanation of the adjustment
            explanation = self._generate_timeline_adjustment_explanation(
                goal=goal,
                adjustment=adjustment,
                revised_allocation=revised_allocation
            )
            
            # In a real system, we'd update the goal in the database here
            # For demo purposes, we'll just return the response
            
            return {
                "success": True,
                "response_type": "timeline_adjusted",
                "goal_id": goal_id,
                "original_date": goal["target_date"],
                "new_date": new_target_date,
                "original_contribution": goal["monthly_contribution"],
                "new_contribution": round(new_monthly_contribution, 2),
                "timeline_changed": timeline_type != goal["goal_timeline"],
                "new_timeline": timeline_type,
                "revised_allocation": revised_allocation,
                "explanation": explanation
            }
            
        except Exception as e:
            print(f"Error adjusting goal timeline: {str(e)}")
            return {
                "success": False,
                "error": f"Error adjusting goal timeline: {str(e)}"
            }
    
    def calculate_required_contribution(self, goal_id: str) -> Dict[str, Any]:
        """
        Calculate the required monthly contribution to meet a goal.
        
        Args:
            goal_id: ID of the goal
            
        Returns:
            Response containing contribution calculations
        """
        print(f"Calculating required contribution for goal {goal_id}")
        
        try:
            # Get the existing goal
            goal = self._get_enhanced_goal_by_id(goal_id)
            if not goal:
                return {
                    "success": False,
                    "error": f"Goal not found: {goal_id}"
                }
            
            # Calculate required contribution
            remaining_amount = goal["target_amount"] - goal["current_savings"]
            target_date = datetime.strptime(goal["target_date"], "%m/%d/%Y")
            months_remaining = max(1, (target_date - datetime.now()).days / 30)
            
            required_contribution = remaining_amount / months_remaining
            
            # Calculate contribution options
            options = {
                "standard": round(required_contribution, 2),
                "accelerated": round(required_contribution * 1.25, 2),
                "minimum": round(required_contribution * 0.75, 2)
            }
            
            # Calculate projected completion dates
            standard_date = target_date.strftime("%m/%d/%Y")
            
            # Accelerated completion (25% higher contribution)
            accel_months = months_remaining * 0.8  # 20% faster
            accel_date = (datetime.now() + timedelta(days=accel_months * 30)).strftime("%m/%d/%Y")
            
            # Minimum contribution (25% lower contribution)
            min_months = months_remaining * 1.33  # 33% slower
            min_date = (datetime.now() + timedelta(days=min_months * 30)).strftime("%m/%d/%Y")
            
            # Format response
            contribution_data = {
                "goal_id": goal_id,
                "goal_type": goal["goal_type"],
                "target_amount": goal["target_amount"],
                "current_savings": goal["current_savings"],
                "remaining_amount": remaining_amount,
                "current_contribution": goal["monthly_contribution"],
                "required_contribution": round(required_contribution, 2),
                "months_remaining": round(months_remaining, 1),
                "target_date": goal["target_date"],
                "options": {
                    "standard": {
                        "amount": options["standard"],
                        "completion_date": standard_date
                    },
                    "accelerated": {
                        "amount": options["accelerated"],
                        "completion_date": accel_date
                    },
                    "minimum": {
                        "amount": options["minimum"],
                        "completion_date": min_date
                    }
                }
            }
            
            return {
                "success": True,
                "response_type": "contribution_calculation",
                "contribution_data": contribution_data
            }
            
        except Exception as e:
            print(f"Error calculating required contribution: {str(e)}")
            return {
                "success": False,
                "error": f"Error calculating required contribution: {str(e)}"
            }
    
    def _get_customer_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get a customer's risk profile."""
        try:
            # Find the customer in the risk profiles dataframe
            customer_profile = self.risk_profiles_df[
                self.risk_profiles_df['Customer ID'] == customer_id
            ]
            
            if customer_profile.empty:
                print(f"No risk profile found for customer {customer_id}")
                # Return a default profile
                return {
                    "Risk Profile": "Medium",
                    "Risk Score": 50,
                    "Risk Category": "Balanced",
                    "Investment Experience": "Limited",
                    "Time Horizon": "Mid-term"
                }
            
            # Convert to dictionary
            profile_row = customer_profile.iloc[0]
            
            return {
                "Risk Profile": profile_row['Risk Profile'],
                "Risk Score": profile_row['Risk Score'],
                "Risk Category": profile_row['Risk Category'],
                "Investment Experience": profile_row['Investment Experience'],
                "Time Horizon": profile_row['Time Horizon']
            }
            
        except Exception as e:
            print(f"Error getting customer risk profile: {str(e)}")
            # Return a default profile
            return {
                "Risk Profile": "Medium",
                "Risk Score": 50,
                "Risk Category": "Balanced",
                "Investment Experience": "Limited",
                "Time Horizon": "Mid-term"
            }
    
    def _get_goal_by_id(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get a goal by ID from the financial goals dataframe."""
        try:
            # Find the goal
            goal = self.financial_goals_df[
                self.financial_goals_df['Goal ID'] == goal_id
            ]
            
            if goal.empty:
                print(f"Goal not found: {goal_id}")
                return None
            
            # Convert to dictionary
            goal_dict = goal.iloc[0].to_dict()
            
            return goal_dict
            
        except Exception as e:
            print(f"Error getting goal by ID: {str(e)}")
            return None
    
    def _get_enhanced_goal_by_id(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get a goal by ID from the enhanced goals dataframe."""
        try:
            # Find the goal
            goal = self.enhanced_goals_df[
                self.enhanced_goals_df['Goal ID'] == goal_id
            ]
            
            if goal.empty:
                print(f"Goal not found in enhanced data: {goal_id}")
                return None
            
            # Convert to dictionary
            goal_dict = goal.iloc[0].to_dict()
            
            # Convert column names to lowercase for consistent access
            goal_dict = {k.lower(): v for k, v in goal_dict.items()}
            
            return goal_dict
            
        except Exception as e:
            print(f"Error getting enhanced goal by ID: {str(e)}")
            return None
    
    def _get_customer_id_from_goal(self, goal_id: str) -> str:
        """Get the customer ID associated with a goal."""
        try:
            # Find the goal
            goal = self.financial_goals_df[
                self.financial_goals_df['Goal ID'] == goal_id
            ]
            
            if goal.empty:
                print(f"Goal not found: {goal_id}")
                return ""
            
            # Get the customer ID
            customer_id = goal.iloc[0]['Customer ID']
            
            # Convert lowercase customer ID to uppercase for consistency with other data
            if isinstance(customer_id, str) and customer_id.startswith('customer'):
                return customer_id.replace('customer', 'CUSTOMER')
            
            return customer_id
            
        except Exception as e:
            print(f"Error getting customer ID from goal: {str(e)}")
            return ""
    
    def _calculate_goal_parameters(self,
                                 customer_id: str,
                                 goal_type: str,
                                 target_amount: float,
                                 target_date: str,
                                 current_savings: float = 0,
                                 start_date: str = None,
                                 priority: str = None) -> Dict[str, Any]:
        """Calculate goal parameters based on inputs."""
        try:
            # Parse dates
            if not start_date:
                start_date = datetime.now().strftime("%m/%d/%Y")
            
            start_date_obj = datetime.strptime(start_date, "%m/%d/%Y")
            target_date_obj = datetime.strptime(target_date, "%m/%d/%Y")
            
            # Calculate time parameters
            days_to_target = (target_date_obj - datetime.now()).days
            months_to_target = days_to_target / 30  # Approximate
            
            # Determine timeline type
            timeline_type = self._classify_timeline(months_to_target)
            
            # Calculate progress percentage
            progress_percentage = (current_savings / target_amount * 100) if target_amount > 0 else 0
            
            # Calculate required monthly contribution
            remaining_amount = target_amount - current_savings
            months_remaining = max(1, months_to_target)  # Avoid division by zero
            monthly_contribution = remaining_amount / months_remaining
            
            # Determine priority if not provided
            if not priority:
                priority = self._determine_priority_for_goal_type(goal_type)
            
            # Format the goal data
            goal_data = {
                "customer_id": customer_id,
                "goal_type": goal_type,
                "target_amount": target_amount,
                "current_savings": current_savings,
                "target_date": target_date,
                "start_date": start_date,
                "goal_timeline": timeline_type,
                "monthly_contribution": round(monthly_contribution, 2),
                "progress_percentage": round(progress_percentage, 1),
                "priority": priority,
                "automatic_contribution": True  # Default to true
            }
            
            return goal_data
            
        except Exception as e:
            print(f"Error calculating goal parameters: {str(e)}")
            raise
    
    def _classify_timeline(self, months: float) -> str:
        """Classify a timeline based on number of months."""
        if months <= 12:
            return "Short-term"
        elif months <= 36:
            return "Medium-term"
        else:
            return "Long-term"
    
    def _determine_priority_for_goal_type(self, goal_type: str) -> str:
        """Determine default priority based on goal type."""
        # Priority mappings
        high_priority = ["Emergency Fund", "Debt Repayment", "Retirement"]
        medium_priority = ["Education", "Home Purchase", "Medical Expenses"]
        
        if goal_type in high_priority:
            return "High"
        elif goal_type in medium_priority:
            return "Medium"
        else:
            return "Low"
    
    def _generate_timeline_adjustment_explanation(self,
                                              goal: Dict[str, Any],
                                              adjustment: Dict[str, Any],
                                              revised_allocation: Optional[Dict[str, float]] = None) -> str:
        """Generate an explanation of a timeline adjustment."""
        try:
            # Format the data for the prompt
            revised_allocation_text = ""
            if revised_allocation:
                revised_allocation_text = "\n".join([f"- {asset}: {pct}%" for asset, pct in revised_allocation.items()])
            
            # Create prompt
            prompt = GoalPlanningPrompts.TIMELINE_ADJUSTMENT_PROMPT.format(
                goal_type=goal["goal_type"],
                original_date=goal["target_date"],
                new_date=adjustment["target_date"],
                original_timeline=goal["goal_timeline"],
                new_timeline=adjustment["goal_timeline"],
                original_contribution=goal["monthly_contribution"],
                new_contribution=adjustment["monthly_contribution"],
                days_difference=adjustment["days_difference"],
                allocation_changed=revised_allocation is not None,
                revised_allocation=revised_allocation_text if revised_allocation else ""
            )
            
            # Generate explanation
            system_prompt = GoalPlanningPrompts.SYSTEM_PROMPT
            explanation = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,
                max_tokens=800
            )
            
            return explanation
            
        except Exception as e:
            print(f"Error generating timeline adjustment explanation: {str(e)}")
            return "There was an error generating the explanation for the timeline adjustment."
    
    def _generate_general_goal_response(self, customer_id: str, query: str) -> Dict[str, Any]:
        """Generate a general response about goals."""
        try:
            # Get the customer's goals
            goals_response = self.get_all_goals(customer_id)
            goals_data = goals_response.get("goals", [])
            
            # Format goals summary
            goals_summary = ""
            if goals_data:
                for goal in goals_data:
                    goals_summary += f"- {goal['Goal Type']}: ${goal['Target Amount']} by {goal['Target Date']} (currently at {goal['Progress %']}%)\n"
            else:
                goals_summary = "You don't have any financial goals set up yet."
            
            # Create prompt
            prompt = GoalPlanningPrompts.GENERAL_GOAL_PROMPT.format(
                customer_id=customer_id,
                user_query=query,
                goals_summary=goals_summary,
                has_goals=len(goals_data) > 0
            )
            
            # Generate response
            system_prompt = GoalPlanningPrompts.SYSTEM_PROMPT
            response = generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=1e-8,
                max_tokens=800
            )
            
            return {
                "success": True,
                "response_type": "general_goal_response",
                "content": response
            }
            
        except Exception as e:
            print(f"Error generating general goal response: {str(e)}")
            return {
                "success": False,
                "error": f"Error generating response: {str(e)}"
            }
    
    def _determine_goal_intent(self, request: str) -> str:
        """
        Determine the intent of a goal-related request.
        
        Args:
            request: User's request text
            
        Returns:
            Intent classification string
        """
        # For a production system, this would use a more sophisticated intent classifier
        # For demo purposes, we'll use simple keyword matching
        
        request_lower = request.lower()
        
        # Create goal intent
        if any(phrase in request_lower for phrase in ["create goal", "new goal", "add goal", "start goal"]):
            return "create_goal"
        
        # Modify goal intent
        if any(phrase in request_lower for phrase in ["modify goal", "update goal", "change goal", "edit goal"]):
            return "modify_goal"
        
        # Delete goal intent
        if any(phrase in request_lower for phrase in ["delete goal", "remove goal", "cancel goal"]):
            return "delete_goal"
        
        # Goal status intent
        if any(phrase in request_lower for phrase in ["goal status", "progress", "how am i doing"]):
            return "get_goal_status"
        
        # All goals intent
        if any(phrase in request_lower for phrase in ["all goals", "my goals", "list goals", "show goals"]):
            return "get_all_goals"
        
        # Goal recommendations intent
        if any(phrase in request_lower for phrase in ["recommend", "suggestion", "advice", "improve"]):
            return "get_goal_recommendations"
        
        # Adjust timeline intent
        if any(phrase in request_lower for phrase in ["adjust timeline", "change date", "extend goal", "shorten goal"]):
            return "adjust_goal_timeline"
        
        # Goal education intent
        if any(phrase in request_lower for phrase in ["explain", "how does", "what is", "tell me about"]):
            return "goal_education"
        
        # Default to general response
        return "general_goal"
    
    def _extract_goal_params(self, request: str) -> Dict[str, Any]:
        """
        Extract goal parameters from a request.
        
        Args:
            request: User's request text
            
        Returns:
            Dictionary of extracted parameters
        """
        # For a production system, this would use a more sophisticated entity extractor
        # For demo purposes, we'll use simple regex patterns
        
        params = {}
        
        # Extract goal type
        goal_type = self._extract_goal_type(request)
        if goal_type:
            params["goal_type"] = goal_type
        
        # Extract amount
        amount_patterns = [
            r'(?:amount|goal|save|target) (?:of )?[$]?(\d+[,.]?\d*[k|K|m|M]?)',
            r'[$](\d+[,.]?\d*[k|K|m|M]?) (?:amount|goal|to save|target)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, request)
            if match:
                amount_str = match.group(1).replace(',', '')
                # Handle k/K and m/M suffixes
                if amount_str.endswith(('k', 'K')):
                    amount = float(amount_str[:-1]) * 1000
                elif amount_str.endswith(('m', 'M')):
                    amount = float(amount_str[:-1]) * 1000000
                else:
                    amount = float(amount_str)
                
                params["target_amount"] = amount
                break
        
        # Extract date
        date = self._extract_date(request)
        if date:
            params["target_date"] = date
        
        # Extract priority
        priority_match = re.search(r'priority (?:is |of )?(high|medium|low|very high)', request.lower())
        if priority_match:
            params["priority"] = priority_match.group(1).title()
        
        return params
    
    def _extract_goal_type(self, request: str) -> Optional[str]:
        """Extract goal type from request."""
        request_lower = request.lower()
        
        # Common goal types
        goal_types = {
            "emergency fund": ["emergency fund", "emergency savings", "rainy day fund"],
            "home purchase": ["home purchase", "house down payment", "buy a home", "buy a house"],
            "retirement": ["retirement", "retire", "retirement savings"],
            "education": ["education", "college fund", "school", "university", "tuition"],
            "travel": ["travel", "vacation", "trip"],
            "wedding": ["wedding", "marriage"],
            "car purchase": ["car purchase", "buy a car", "vehicle", "automobile"],
            "medical expenses": ["medical expenses", "health costs", "healthcare"],
            "debt repayment": ["debt repayment", "pay off debt", "debt free"]
        }
        
        for goal_type, phrases in goal_types.items():
            if any(phrase in request_lower for phrase in phrases):
                return goal_type.title()
        
        return None
    
    def _extract_goal_id(self, request: str) -> Optional[str]:
        """Extract goal ID from request."""
        # Look for patterns like "GOAL1", "Goal 3", etc.
        match = re.search(r'(?:goal|GOAL)[ ]?(\d+)', request)
        if match:
            return f"GOAL{match.group(1)}"
        
        return None
    
    def _extract_date(self, request: str) -> Optional[str]:
        """Extract target date from request."""
        # Look for common date formats
        date_patterns = [
            # MM/DD/YYYY
            r'(\d{1,2}/\d{1,2}/\d{4})',
            # Month DD, YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2})(?:st|nd|rd|th)?,? (\d{4})',
            # MM-DD-YYYY
            r'(\d{1,2}-\d{1,2}-\d{4})',
            # Relative time frames
            r'in (\d+) (year|years|month|months)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, request)
            if match:
                if pattern == date_patterns[0]:
                    # MM/DD/YYYY
                    return match.group(1)
                elif pattern == date_patterns[1]:
                    # Month DD, YYYY
                    month_names = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_names[match.group(1).lower()]
                    day = int(match.group(2))
                    year = int(match.group(3))
                    return f"{month:02d}/{day:02d}/{year}"
                elif pattern == date_patterns[2]:
                    # MM-DD-YYYY
                    parts = match.group(1).split('-')
                    return f"{parts[0]}/{parts[1]}/{parts[2]}"
                elif pattern == date_patterns[3]:
                    # Relative time frames
                    amount = int(match.group(1))
                    unit = match.group(2)
                    
                    now = datetime.now()
                    if unit.startswith('year'):
                        target_date = now + timedelta(days=amount*365)
                    else:  # months
                        target_date = now + timedelta(days=amount*30)
                    
                    return target_date.strftime("%m/%d/%Y")
        
        return None
    
    def _extract_educational_topic(self, request: str) -> str:
        """Extract educational topic from request."""
        # Look for patterns like "explain X", "what is X", "tell me about X"
        explain_patterns = [
            r'explain (?:to me )?(?:what|how) (.*?)(?:is|works|means)(?:\?|$|\.)',
            r'explain (?:to me )?(?:about )?(.*?)(?:\?|$|\.)',
            r'what (?:is|are) (.*?)(?:\?|$|\.)',
            r'tell me about (.*?)(?:\?|$|\.)',
            r'how (?:does|do) (.*?) work(?:\?|$|\.)'
        ]
        
        for pattern in explain_patterns:
            match = re.search(pattern, request.lower())
            if match:
                # Captured topic might need cleaning
                topic = match.group(1).strip()
                # Remove filler words
                filler_words = ["the ", "a ", "an "]
                for word in filler_words:
                    if topic.startswith(word):
                        topic = topic[len(word):]
                return topic
        
        # If no specific topic is found, return a general finance topic
        if "goal" in request.lower():
            return "goal-based financial planning"
        elif "invest" in request.lower():
            return "investment strategies"
        else:
            return "personal finance basics"


def main():
    """Main function to demonstrate the Goal Planning Agent."""
    # Initialize the agent
    agent = GoalPlanningAgent()
    
    # Test creating a goal
    customer_id = "CUSTOMER1"
    goal_params = {
        "goal_type": "Retirement",
        "target_amount": 500000,
        "target_date": "02/15/2040",
        "current_savings": 50000
    }
    
    create_response = agent.create_goal(customer_id, goal_params)
    
    print("\n" + "="*50)
    print(f"GOAL CREATION FOR: {customer_id}")
    print("="*50)
    print(f"Success: {create_response['success']}")
    if create_response['success']:
        print(f"Goal ID: {create_response['goal_id']}")
        print(f"Monthly Contribution: ${create_response['goal_data']['monthly_contribution']}")
        print(f"Timeline: {create_response['goal_data']['goal_timeline']}")
    print("="*50)
    
    # Test getting all goals
    goals_response = agent.get_all_goals(customer_id)
    
    print("\n" + "="*50)
    print(f"ALL GOALS FOR: {customer_id}")
    print("="*50)
    if goals_response['success'] and goals_response['goals']:
        for goal in goals_response['goals']:
            print(f"Goal ID: {goal['Goal ID']}")
            print(f"Type: {goal['Goal Type']}")
            print(f"Target: ${goal['Target Amount']}")
            print(f"Progress: {goal['Progress %']}%")
            print()
    else:
        print("No goals found or error occurred.")
    print("="*50)
    
    # Test getting goal recommendations
    recommendations = agent.get_goal_recommendations(customer_id)
    
    print("\n" + "="*50)
    print(f"GOAL RECOMMENDATIONS FOR: {customer_id}")
    print("="*50)
    if recommendations['success']:
        print(recommendations['recommendations'])
    else:
        print("Error generating recommendations.")
    print("="*50)


if __name__ == "__main__":
    main()