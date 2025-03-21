"""
Fixed GoalDataManager with reliable file synchronization for update operations.
This fixes the issue where updates through chat don't appear in the Goal Planning page.
"""

import os
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('GoalDataManager')

class GoalDataManager:
    """
    Manager for goal-related data operations.
    
    This class handles creation, retrieval, updating, and deletion of goals.
    Fixed to ensure reliable file synchronization for all operations.
    """
    
    def __init__(self, data_path="./data"):
        """
        Initialize the Goal Data Manager.
        
        Args:
            data_path (str): Path to the directory containing data files
        """
        self.data_path = data_path
        self.goals_file = os.path.join(data_path, "enhanced_goal_data.csv")
        
        # Ensure the data files exist
        self._ensure_data_files_exist()
        
        logger.info(f"GoalDataManager initialized with data path: {data_path}")
        logger.info(f"Goals file: {self.goals_file}")
    
    def _ensure_data_files_exist(self):
        """Ensure the necessary data files exist."""
        try:
            if not os.path.exists(self.goals_file):
                # Create the file with headers if it doesn't exist
                headers = [
                    "Goal ID", "Customer ID", "Goal Name", "Target Amount", "Current Savings",
                    "Target Date", "Goal Type", "Goal Timeline", "Monthly Contribution", 
                    "Priority", "Start Date", "Last Updated", "Automatic Contribution", "Progress (%)"
                ]
                
                df = pd.DataFrame(columns=headers)
                df.to_csv(self.goals_file, index=False)
                logger.info(f"Created new goals file: {self.goals_file}")
        except Exception as e:
            logger.error(f"Error ensuring data files exist: {str(e)}")
    
    def _flush_file_after_write(self, file_path):
        """
        Force a file system sync after writing to a file to ensure changes are persisted.
        
        Args:
            file_path: Path to the file to sync
        """
        try:
            # This is a more reliable way to ensure file system sync
            if os.path.exists(file_path):
                with open(file_path, 'r+') as f:
                    f.flush()
                    os.fsync(f.fileno())
                logger.info(f"File sync forced for {file_path}")
        except Exception as e:
            logger.error(f"Error flushing file {file_path}: {str(e)}")
    
    def get_user_goals(self, customer_id):
        """
        Get all goals for a specific customer.
        
        Args:
            customer_id (str): The customer ID
            
        Returns:
            pandas.DataFrame: DataFrame containing the customer's goals
        """
        try:
            # Read directly from file, bypassing any caching
            if os.path.exists(self.goals_file):
                df = pd.read_csv(self.goals_file)
                return df[df['Customer ID'] == customer_id]
            else:
                logger.warning(f"Goals file not found: {self.goals_file}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting user goals: {str(e)}")
            return pd.DataFrame()
    
    def get_goal_by_id(self, goal_id):
        """
        Get a specific goal by ID.
        
        Args:
            goal_id (str): The goal ID
            
        Returns:
            dict or None: Dictionary containing the goal data, or None if not found
        """
        try:
            # Read directly from file, bypassing any caching
            if os.path.exists(self.goals_file):
                df = pd.read_csv(self.goals_file)
                goal = df[df['Goal ID'] == goal_id]
                
                if goal.empty:
                    logger.warning(f"Goal not found: {goal_id}")
                    return None
                
                # Convert to dictionary for easier access
                return goal.iloc[0].to_dict()
            else:
                logger.warning(f"Goals file not found: {self.goals_file}")
                return None
        except Exception as e:
            logger.error(f"Error getting goal by ID: {str(e)}")
            return None
    
    def create_goal(self, customer_id, goal_name, target_amount, target_date,
                   goal_type=None, current_savings=0.0, monthly_contribution=None,
                   priority="Medium"):
        """
        Create a new financial goal.
        
        Args:
            customer_id (str): The customer ID
            goal_name (str): Name of the goal
            target_amount (float): Target amount for the goal
            target_date (str): Target date in MM/DD/YYYY format
            goal_type (str, optional): Type of goal (defaults to goal_name if not provided)
            current_savings (float, optional): Current savings toward the goal
            monthly_contribution (float, optional): Monthly contribution amount
            priority (str, optional): Priority level (Very High, High, Medium, Low)
            
        Returns:
            str: ID of the created goal
        """
        try:
            # Set default goal type to goal name if not provided
            if goal_type is None:
                goal_type = goal_name
            
            # Read existing goals
            if os.path.exists(self.goals_file):
                df = pd.read_csv(self.goals_file)
            else:
                # Create new DataFrame if file doesn't exist
                df = pd.DataFrame(columns=[
                    "Goal ID", "Customer ID", "Goal Name", "Target Amount", "Current Savings",
                    "Target Date", "Goal Type", "Goal Timeline", "Monthly Contribution", 
                    "Priority", "Start Date", "Last Updated", "Automatic Contribution", "Progress (%)"
                ])
            
            # Generate a new goal ID
            if df.empty:
                goal_id = "GOAL1"
            else:
                # Extract numeric part of the last goal ID and increment
                last_id = df['Goal ID'].iloc[-1]
                num = int(last_id.replace("GOAL", ""))
                goal_id = f"GOAL{num + 1}"
            
            # Calculate goal timeline based on target date
            today = datetime.now()
            target_datetime = datetime.strptime(target_date, "%m/%d/%Y")
            months_difference = (target_datetime.year - today.year) * 12 + (target_datetime.month - today.month)
            
            if months_difference <= 12:
                goal_timeline = "Short-term"
            elif months_difference <= 60:
                goal_timeline = "Medium-term"
            else:
                goal_timeline = "Long-term"
            
            # Calculate monthly contribution if not provided
            if monthly_contribution is None:
                remaining_amount = target_amount - current_savings
                if months_difference > 0:
                    monthly_contribution = remaining_amount / months_difference
                else:
                    monthly_contribution = remaining_amount  # Default to full remaining amount
            
            # Calculate progress percentage
            progress_percentage = (current_savings / target_amount * 100) if target_amount > 0 else 0
            
            # Create new goal row
            new_goal = {
                "Goal ID": goal_id,
                "Customer ID": customer_id.lower(),  # Normalize to lowercase for consistency
                "Goal Name": goal_name,
                "Target Amount": float(target_amount),
                "Current Savings": float(current_savings),
                "Target Date": target_date,
                "Goal Type": goal_type,
                "Goal Timeline": goal_timeline,
                "Monthly Contribution": float(monthly_contribution),
                "Priority": priority,
                "Start Date": today.strftime("%m/%d/%Y"),
                "Last Updated": today.strftime("%m/%d/%Y"),
                "Automatic Contribution": "Yes",
                "Progress (%)": float(progress_percentage)
            }
            
            # Add the new goal
            df = pd.concat([df, pd.DataFrame([new_goal])], ignore_index=True)
            
            # Save to file with explicit sync
            df.to_csv(self.goals_file, index=False)
            self._flush_file_after_write(self.goals_file)
            
            logger.info(f"Goal created: {goal_id} for customer {customer_id}")
            return goal_id
            
        except Exception as e:
            logger.error(f"Error creating goal: {str(e)}")
            raise
    
    def update_goal(self, goal_id, **kwargs):
        """
        Update an existing goal.
        
        Args:
            goal_id (str): ID of the goal to update
            **kwargs: Goal attributes to update (in snake_case)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate the goal ID format
            if not isinstance(goal_id, str) or not goal_id.startswith("GOAL"):
                logger.error(f"Invalid goal ID format: {goal_id}")
                return False
            
            # Read existing goals
            if not os.path.exists(self.goals_file):
                logger.error(f"Goals file not found: {self.goals_file}")
                return False
            
            df = pd.read_csv(self.goals_file)
            
            # Check if the goal exists
            goal_mask = df['Goal ID'] == goal_id
            if not any(goal_mask):
                logger.error(f"Goal not found: {goal_id}")
                return False
            
            # Map snake_case parameter names to Title Case column names
            column_mapping = {
                'goal_type': 'Goal Type',
                'goal_name': 'Goal Name',
                'target_amount': 'Target Amount',
                'current_savings': 'Current Savings',
                'target_date': 'Target Date',
                'monthly_contribution': 'Monthly Contribution',
                'priority': 'Priority',
                'progress_percentage': 'Progress (%)'
            }
            
            # Log original values for debugging
            original_values = {}
            for key, column in column_mapping.items():
                if key in kwargs and column in df.columns:
                    original_values[column] = df.loc[goal_mask, column].values[0]
            
            logger.info(f"Updating goal {goal_id}: {kwargs}")
            logger.info(f"Original values: {original_values}")
            
            # Apply updates with column name mapping
            for key, value in kwargs.items():
                # Map snake_case keys to actual column names
                if key in column_mapping and column_mapping[key] in df.columns:
                    column = column_mapping[key]
                    df.loc[goal_mask, column] = value
                    logger.info(f"Updated {column} to {value}")
                else:
                    logger.warning(f"Column not found for parameter {key}")
            
            # Update Last Updated field
            today = datetime.now()
            df.loc[goal_mask, 'Last Updated'] = today.strftime("%m/%d/%Y")
            
            # Recalculate Progress (%) if Current Savings or Target Amount changed
            if 'current_savings' in kwargs or 'target_amount' in kwargs:
                current_savings = df.loc[goal_mask, 'Current Savings'].values[0]
                target_amount = df.loc[goal_mask, 'Target Amount'].values[0]
                progress_percentage = (current_savings / target_amount * 100) if target_amount > 0 else 0
                df.loc[goal_mask, 'Progress (%)'] = progress_percentage
            
            # Recalculate Goal Timeline if Target Date changed
            if 'target_date' in kwargs:
                target_date = df.loc[goal_mask, 'Target Date'].values[0]
                try:
                    target_datetime = datetime.strptime(target_date, "%m/%d/%Y")
                    months_difference = (target_datetime.year - today.year) * 12 + (target_datetime.month - today.month)
                    
                    if months_difference <= 12:
                        df.loc[goal_mask, 'Goal Timeline'] = "Short-term"
                    elif months_difference <= 60:
                        df.loc[goal_mask, 'Goal Timeline'] = "Medium-term"
                    else:
                        df.loc[goal_mask, 'Goal Timeline'] = "Long-term"
                except Exception as e:
                    logger.error(f"Error calculating timeline: {str(e)}")
            
            # Save changes with explicit sync to ensure file is updated
            df.to_csv(self.goals_file, index=False)
            
            # Force sync to disk
            self._flush_file_after_write(self.goals_file)
            
            # Verify that the update was actually applied to the file
            verification_df = pd.read_csv(self.goals_file)
            verification_mask = verification_df['Goal ID'] == goal_id
            
            # Check if the goal still exists
            if not any(verification_mask):
                logger.error(f"Verification failed: Goal {goal_id} not found after update")
                return False
            
            # Verify each updated field
            for key, value in kwargs.items():
                if key in column_mapping and column_mapping[key] in verification_df.columns:
                    column = column_mapping[key]
                    actual_value = verification_df.loc[verification_mask, column].values[0]
                    
                    # For numeric comparisons, handle floating point precision
                    if isinstance(value, (int, float)) and isinstance(actual_value, (int, float)):
                        if abs(actual_value - value) > 0.001:
                            logger.error(f"Verification failed: {column} expected {value}, got {actual_value}")
                            return False
                    elif str(actual_value) != str(value):
                        logger.error(f"Verification failed: {column} expected {value}, got {actual_value}")
                        return False
            
            logger.info(f"Goal {goal_id} updated successfully and verified")
            return True
            
        except Exception as e:
            logger.error(f"Error updating goal: {str(e)}")
            return False
    
    def delete_goal(self, goal_id):
        """
        Delete a goal.
        
        Args:
            goal_id (str): ID of the goal to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate the goal ID format
            if not isinstance(goal_id, str) or not goal_id.startswith("GOAL"):
                logger.error(f"Invalid goal ID format: {goal_id}")
                return False
            
            # Read existing goals
            if not os.path.exists(self.goals_file):
                logger.error(f"Goals file not found: {self.goals_file}")
                return False
            
            df = pd.read_csv(self.goals_file)
            
            # Check if the goal exists
            goal_mask = df['Goal ID'] == goal_id
            if not any(goal_mask):
                logger.error(f"Goal not found: {goal_id}")
                return False
            
            # Delete the goal
            df = df[~goal_mask]
            
            # Save changes with explicit sync
            df.to_csv(self.goals_file, index=False)
            self._flush_file_after_write(self.goals_file)
            
            logger.info(f"Goal deleted: {goal_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting goal: {str(e)}")
            return False
    
    def contribute_to_goal(self, goal_id, amount):
        """
        Add a contribution to a goal.
        
        Args:
            goal_id (str): ID of the goal
            amount (float): Amount to contribute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input
            if not isinstance(amount, (int, float)) or amount <= 0:
                logger.error(f"Invalid contribution amount: {amount}")
                return False
            
            # Get the goal
            goal = self.get_goal_by_id(goal_id)
            if goal is None:
                logger.error(f"Goal not found: {goal_id}")
                return False
            
            # Calculate new current savings
            new_savings = goal['Current Savings'] + amount
            
            # Update the goal
            return self.update_goal(goal_id, Current_Savings=new_savings)
            
        except Exception as e:
            logger.error(f"Error contributing to goal: {str(e)}")
            return False