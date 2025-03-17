"""
Asset Allocation Agent

This script implements the Asset Allocation Agent for the Personal Finance Manager,
which provides portfolio allocation recommendations based on risk profile and goal parameters.
"""

import os
import sys
import pandas as pd
from typing import Dict, Optional

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Compute the path to the project root (one level up from the 'agents' folder)
project_root = os.path.join(current_dir, '..')

# Add the project root to sys.path
sys.path.append(project_root)

# Import the LLM utility and prompts
from utils.llm_response import generate_text, DekaLLMClient
from prompts.asset_allocation_agent_prompts import AssetAllocationPrompts

class AssetAllocationAgent:
    """
    Provides asset allocation recommendations and portfolio optimization.
    
    This agent specializes in determining appropriate investment allocations
    based on risk profiles, goal timelines, and other factors.
    """
    
    def __init__(self, data_path: str = "./synthetic_data"):
        """
        Initialize the Asset Allocation Agent.
        
        Args:
            data_path: Path to directory containing CSV data files
        """
        self.data_path = data_path
        self.llm_client = DekaLLMClient()
        
        # Load necessary data files
        self._load_data_files()
        
        print("Asset Allocation Agent initialized successfully.")
    
    def _load_data_files(self):
        """Load all necessary data files from the data directory."""
        try:
            # Load asset allocation matrix
            self.allocation_matrix_df = pd.read_csv(f"{self.data_path}/asset_allocation_matrix.csv")
            
            # Load user risk profiles
            self.risk_profiles_df = pd.read_csv(f"{self.data_path}/expanded_risk_profiles.csv")
            
            # Load current asset allocations
            self.current_allocations_df = pd.read_csv(f"{self.data_path}/current_asset_allocation.csv")
            
            # Load goal-specific allocations
            self.goal_allocations_df = pd.read_csv(f"{self.data_path}/goal_specific_allocations.csv")
            
            print("All allocation data files loaded successfully.")
        except Exception as e:
            print(f"Error loading data files: {str(e)}")
            raise
    
    def get_allocation_recommendation(self, 
                                     risk_profile: str,
                                     goal_timeline: str,
                                     goal_type: str = None) -> Dict[str, float]:
        """
        Get recommended asset allocation based on risk profile and timeline.
        
        Args:
            risk_profile: User's risk profile or risk category
            goal_timeline: Timeline for the goal (Short-term, Medium-term, Long-term)
            goal_type: Type of financial goal (optional)
            
        Returns:
            Dictionary mapping asset classes to allocation percentages
        """
        print(f"Generating allocation recommendation for {risk_profile} profile with {goal_timeline} timeline")
        
        # Convert risk profile name to risk category if needed
        risk_category = self._map_risk_profile_to_category(risk_profile)
        
        # Look up the recommended allocation from the matrix
        try:
            # Filter the allocation matrix for the matching risk and timeline
            filtered_df = self.allocation_matrix_df[
                (self.allocation_matrix_df['Risk Category'] == risk_category) & 
                (self.allocation_matrix_df['Goal Timeline'] == goal_timeline)
            ]
            
            if filtered_df.empty:
                # Fallback if no exact match is found
                print(f"No exact match found for {risk_category} and {goal_timeline}. Using default allocation.")
                filtered_df = self.allocation_matrix_df[
                    (self.allocation_matrix_df['Risk Category'] == 'Balanced') & 
                    (self.allocation_matrix_df['Goal Timeline'] == 'Medium-term')
                ]
            
            # Convert the row to a dictionary of allocations
            allocation_row = filtered_df.iloc[0]
            allocation = {
                'Cash': float(allocation_row['Cash %']),
                'Bonds': float(allocation_row['Bonds %']),
                'Large Cap': float(allocation_row['Large Cap %']),
                'Mid Cap': float(allocation_row['Mid Cap %']),
                'Small Cap': float(allocation_row['Small Cap %']),
                'International': float(allocation_row['International %']),
                'Real Estate': float(allocation_row['Real Estate %']),
                'Commodities': float(allocation_row['Commodities %'])
            }
            
            # If goal type is provided, check if we need to adjust for specific goal types
            if goal_type:
                allocation = self._adjust_for_goal_type(allocation, goal_type, goal_timeline)
            
            return allocation
            
        except Exception as e:
            print(f"Error generating allocation recommendation: {str(e)}")
            # Return a default balanced allocation
            return {
                'Cash': 15.0,
                'Bonds': 35.0,
                'Large Cap': 25.0,
                'Mid Cap': 7.5,
                'Small Cap': 5.0,
                'International': 7.5,
                'Real Estate': 5.0,
                'Commodities': 0.0
            }
    
    def _map_risk_profile_to_category(self, risk_profile: str) -> str:
        """Map various risk profile names to standard risk categories."""
        # Direct mapping if already a standard category
        standard_categories = [
            "Risk Averse", "Conservative", "Balanced", "Growth", "Aggressive"
        ]
        
        if risk_profile in standard_categories:
            return risk_profile
        
        # Common mappings
        mappings = {
            "Very Low": "Risk Averse",
            "Low": "Conservative",
            "Medium": "Balanced", 
            "High": "Growth",
            "Very High": "Aggressive"
        }
        
        return mappings.get(risk_profile, "Balanced")
    
    def _adjust_for_goal_type(self, 
                             allocation: Dict[str, float], 
                             goal_type: str,
                             goal_timeline: str) -> Dict[str, float]:
        """
        Adjust allocation based on specific goal type.
        
        Some goals have special considerations beyond timeline and risk profile.
        This method makes those adjustments.
        """
        adjusted = allocation.copy()
        
        # Emergency Fund adjustments (always more conservative)
        if goal_type == "Emergency Fund":
            # Increase cash allocation for emergency funds
            cash_increase = min(30, 100 - adjusted["Cash"])
            if cash_increase > 0:
                adjusted["Cash"] += cash_increase
                
                # Proportionally reduce other allocations
                total_other = sum(v for k, v in adjusted.items() if k != "Cash")
                if total_other > 0:
                    reduction_factor = (total_other - cash_increase) / total_other
                    for k in adjusted:
                        if k != "Cash":
                            adjusted[k] = adjusted[k] * reduction_factor
        
        # Education or Medical Expenses (depends on timeline)
        elif goal_type in ["Education", "Medical Expenses"] and goal_timeline == "Short-term":
            # More conservative for short-term education or medical goals
            if adjusted["Cash"] < 40:
                adjusted["Cash"] = 40
                adjusted["Bonds"] = 40
                adjusted["Large Cap"] = 15
                adjusted["Mid Cap"] = 0
                adjusted["Small Cap"] = 0
                adjusted["International"] = 5
                adjusted["Real Estate"] = 0
                adjusted["Commodities"] = 0
        
        # Round all values to one decimal place
        adjusted = {k: round(v, 1) for k, v in adjusted.items()}
        
        # Ensure the allocation still sums to 100%
        total = sum(adjusted.values())
        if abs(total - 100) > 0.1:  # If more than 0.1% off from 100%
            # Adjust the largest allocation to make the total 100%
            largest_key = max(adjusted, key=adjusted.get)
            adjusted[largest_key] += (100 - total)
        
        return adjusted
    
    def get_current_allocation(self, customer_id: str) -> Dict[str, float]:
        """
        Get a customer's current overall asset allocation.
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Dictionary mapping asset classes to allocation percentages
        """
        try:
            # Filter for the customer
            customer_allocation = self.current_allocations_df[
                self.current_allocations_df['Customer ID'] == customer_id
            ]
            
            if customer_allocation.empty:
                print(f"No allocation data found for customer {customer_id}")
                return {}
            
            # Convert to dictionary
            allocation_row = customer_allocation.iloc[0]
            allocation = {
                'Cash': float(allocation_row['Cash %']),
                'Bonds': float(allocation_row['Bonds %']),
                'Large Cap': float(allocation_row['Large Cap %']),
                'Mid Cap': float(allocation_row['Mid Cap %']),
                'Small Cap': float(allocation_row['Small Cap %']),
                'International': float(allocation_row['International %']),
                'Real Estate': float(allocation_row['Real Estate %']),
                'Commodities': float(allocation_row['Commodities %'])
            }
            
            return allocation
            
        except Exception as e:
            print(f"Error retrieving current allocation: {str(e)}")
            return {}
    
    def get_goal_allocation(self, goal_id: str) -> Dict[str, float]:
        """
        Get the current asset allocation for a specific goal.
        
        Args:
            goal_id: ID of the goal
            
        Returns:
            Dictionary mapping asset classes to allocation percentages
        """
        try:
            # Filter for the goal
            goal_allocation = self.goal_allocations_df[
                self.goal_allocations_df['Goal ID'] == goal_id
            ]
            
            if goal_allocation.empty:
                print(f"No allocation data found for goal {goal_id}")
                return {}
            
            # Convert to dictionary
            allocation_row = goal_allocation.iloc[0]
            allocation = {
                'Cash': float(allocation_row['Cash %']),
                'Bonds': float(allocation_row['Bonds %']),
                'Large Cap': float(allocation_row['Large Cap %']),
                'Mid Cap': float(allocation_row['Mid Cap %']),
                'Small Cap': float(allocation_row['Small Cap %']),
                'International': float(allocation_row['International %']),
                'Real Estate': float(allocation_row['Real Estate %']),
                'Commodities': float(allocation_row['Commodities %'])
            }
            
            return allocation
            
        except Exception as e:
            print(f"Error retrieving goal allocation: {str(e)}")
            return {}
    
    def generate_rebalancing_recommendations(self, 
                                           goal_id: str, 
                                           customer_id: str,
                                           goal_type: str,
                                           goal_timeline: str,
                                           risk_profile: str,
                                           current_allocation: Optional[Dict[str, float]] = None) -> str:
        """
        Generate rebalancing recommendations by comparing current vs recommended allocations.
        
        Args:
            goal_id: ID of the goal
            customer_id: ID of the customer
            goal_type: Type of financial goal
            goal_timeline: Timeline of the goal
            risk_profile: User's risk profile
            current_allocation: Current allocation (optional, will be looked up if not provided)
            
        Returns:
            Formatted rebalancing recommendations
        """
        # Get current allocation if not provided
        if not current_allocation:
            current_allocation = self.get_goal_allocation(goal_id)
            
            # If still empty, try to use overall allocation
            if not current_allocation:
                current_allocation = self.get_current_allocation(customer_id)
                
                # If still empty, use a default allocation
                if not current_allocation:
                    current_allocation = {
                        'Cash': 50.0,
                        'Bonds': 30.0,
                        'Large Cap': 10.0,
                        'Mid Cap': 5.0,
                        'Small Cap': 0.0,
                        'International': 5.0,
                        'Real Estate': 0.0,
                        'Commodities': 0.0
                    }
        
        # Get recommended allocation
        recommended_allocation = self.get_allocation_recommendation(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline,
            goal_type=goal_type
        )
        
        # Generate prompt for LLM with the comparison
        prompt = self._create_rebalancing_prompt(
            goal_id=goal_id,
            goal_type=goal_type,
            goal_timeline=goal_timeline,
            risk_profile=risk_profile,
            current_allocation=current_allocation,
            recommended_allocation=recommended_allocation
        )
        
        # Generate the recommendation
        system_prompt = AssetAllocationPrompts.SYSTEM_PROMPT
        recommendation = generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=1000
        )
        
        return recommendation
    
    def _create_rebalancing_prompt(self,
                                 goal_id: str,
                                 goal_type: str,
                                 goal_timeline: str,
                                 risk_profile: str,
                                 current_allocation: Dict[str, float],
                                 recommended_allocation: Dict[str, float]) -> str:
        """
        Create a prompt for generating rebalancing recommendations.
        
        Args:
            goal_id: ID of the goal
            goal_type: Type of financial goal
            goal_timeline: Timeline of the goal
            risk_profile: User's risk profile
            current_allocation: Current asset allocation
            recommended_allocation: Recommended asset allocation
            
        Returns:
            Formatted prompt for LLM
        """
        # Format the allocations for display
        current_text = "\n".join([f"- {asset}: {pct}%" for asset, pct in current_allocation.items()])
        recommended_text = "\n".join([f"- {asset}: {pct}%" for asset, pct in recommended_allocation.items()])
        
        # Calculate the differences
        differences = {}
        for asset in recommended_allocation:
            current_pct = current_allocation.get(asset, 0)
            recommended_pct = recommended_allocation[asset]
            diff = recommended_pct - current_pct
            if abs(diff) >= 0.1:  # Only include meaningful differences
                differences[asset] = diff
        
        # Format the differences for display
        differences_text = "\n".join([
            f"- {asset}: {'increase' if diff > 0 else 'decrease'} by {abs(diff):.1f}%" 
            for asset, diff in differences.items()
        ])
        
        # Create the prompt
        prompt = AssetAllocationPrompts.REBALANCING_PROMPT.format(
            goal_id=goal_id,
            goal_type=goal_type,
            goal_timeline=goal_timeline,
            risk_profile=risk_profile,
            current_allocation=current_text,
            recommended_allocation=recommended_text,
            differences=differences_text
        )
        
        return prompt
    
    def explain_allocation_strategy(self, 
                                   risk_profile: str, 
                                   goal_timeline: str,
                                   goal_type: str = None) -> str:
        """
        Explain the investment strategy behind a recommended allocation.
        
        Args:
            risk_profile: User's risk profile
            goal_timeline: Timeline of the goal
            goal_type: Type of financial goal (optional)
            
        Returns:
            Explanation of the allocation strategy
        """
        # Get the recommended allocation
        allocation = self.get_allocation_recommendation(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline,
            goal_type=goal_type
        )
        
        # Format the allocation for the prompt
        allocation_text = "\n".join([f"- {asset}: {pct}%" for asset, pct in allocation.items()])
        
        # Create prompt for LLM
        prompt = AssetAllocationPrompts.STRATEGY_EXPLANATION_PROMPT.format(
            risk_profile=risk_profile,
            goal_timeline=goal_timeline,
            goal_type=goal_type if goal_type else "general investing",
            allocation=allocation_text
        )
        
        # Generate the explanation
        system_prompt = AssetAllocationPrompts.SYSTEM_PROMPT
        explanation = generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=1e-8,
            max_tokens=800
        )
        
        return explanation


def main():
    """Main function to demonstrate the Asset Allocation Agent."""
    # Initialize the agent
    agent = AssetAllocationAgent()
    
    # Test getting allocation recommendation
    risk_profile = "Growth"
    goal_timeline = "Long-term"
    goal_type = "Retirement"
    
    allocation = agent.get_allocation_recommendation(
        risk_profile=risk_profile,
        goal_timeline=goal_timeline,
        goal_type=goal_type
    )
    
    print("\n" + "="*50)
    print(f"ALLOCATION RECOMMENDATION FOR: {risk_profile.upper()} PROFILE, {goal_timeline.upper()} TIMELINE")
    print("="*50)
    for asset, pct in allocation.items():
        print(f"{asset}: {pct}%")
    print("="*50)
    
    # Test generating rebalancing recommendations
    customer_id = "CUSTOMER1"
    goal_id = "GOAL1"
    
    current_allocation = {
        'Cash': 25.0,
        'Bonds': 35.0,
        'Large Cap': 20.0,
        'Mid Cap': 10.0,
        'Small Cap': 5.0,
        'International': 5.0,
        'Real Estate': 0.0,
        'Commodities': 0.0
    }
    
    rebalancing = agent.generate_rebalancing_recommendations(
        goal_id=goal_id,
        customer_id=customer_id,
        goal_type=goal_type,
        goal_timeline=goal_timeline,
        risk_profile=risk_profile,
        current_allocation=current_allocation
    )
    
    print("\n" + "="*50)
    print(f"REBALANCING RECOMMENDATIONS FOR GOAL: {goal_id}")
    print("="*50)
    print(rebalancing)
    print("="*50)
    
    # Test explaining allocation strategy
    strategy_explanation = agent.explain_allocation_strategy(
        risk_profile=risk_profile,
        goal_timeline=goal_timeline,
        goal_type=goal_type
    )
    
    print("\n" + "="*50)
    print(f"ALLOCATION STRATEGY EXPLANATION FOR: {goal_type.upper()} GOAL")
    print("="*50)
    print(strategy_explanation)
    print("="*50)


if __name__ == "__main__":
    main()