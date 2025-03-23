"""
Personal Finance Manager - Streamlit Application

This is the main application file for the Personal Finance Manager Streamlit frontend.
Updated with improved integrations for goal handling and context management.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import sys
import re
import time
import traceback

# Add parent directory to system path to import our agents
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import the Financial Advisor Agent
from utils.goal_data_manager import GoalDataManager
from agents.financial_advisor_agent import FinancialAdvisorAgent
from agents.transaction_analysis_agent import TransactionAnalysisAgent
from agents.asset_allocation_agent import AssetAllocationAgent

# Path to data directory
DATA_PATH = "./synthetic_data"

# Initialize agents (only done once at startup)
@st.cache_resource
def get_financial_advisor():
    return FinancialAdvisorAgent(data_path=DATA_PATH)

@st.cache_resource
def get_transaction_agent():
    return TransactionAnalysisAgent(data_path=DATA_PATH)

# Load user data
@st.cache_data
def load_user_data():
    users_df = pd.read_csv(f"{DATA_PATH}/user_profile_data.csv")
    return users_df

@st.cache_data
def load_goals_data():
    goals_df = pd.read_csv(f"{DATA_PATH}/enhanced_goal_data.csv")
    return goals_df

@st.cache_data
def load_transactions_data():
    transactions_df = pd.read_csv(f"{DATA_PATH}/transactions_data.csv")
    return transactions_df

@st.cache_data
def load_budget_data():
    budget_df = pd.read_csv(f"{DATA_PATH}/budget_data.csv")
    return budget_df

@st.cache_data
def load_allocations_data():
    allocations_df = pd.read_csv(f"{DATA_PATH}/current_asset_allocation.csv")
    return allocations_df

@st.cache_resource
def get_goal_manager():
    return GoalDataManager(data_path=DATA_PATH)

def clear_goals_cache():
    """Clear the goals data cache to ensure fresh data is loaded."""
    if hasattr(load_goals_data, "clear"):
        load_goals_data.clear()
        print("Goals cache cleared")

def format_currency(value):
    """Format a numeric value as currency with commas and 2 decimal places."""
    try:
        return f"${value:,.2f}"
    except:
        return str(value)

def format_percentage(value):
    """Format a numeric value as a percentage with 1 decimal place."""
    try:
        return f"{value:.1f}%"
    except:
        return str(value)

def clean_response_text(text):
    """
    Clean up formatting issues in AI-generated text.
    
    Args:
        text (str): The text to clean
        
    Returns:
        str: Cleaned text
    """
    # Fix dollar amounts missing spaces
    text = re.sub(r'(\$\d+(?:,\d+)*(?:\.\d+)?)([a-zA-Z])', r'\1 \2', text)
    
    # Fix missing spaces between words
    text = re.sub(r'([a-zA-Z])(\$)', r'\1 \2', text)
    
    # Fix words running together
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Fix percentage formatting
    text = re.sub(r'(\d+)%', r'\1 %', text)
    
    # Fix dates without spaces
    text = re.sub(r'(\d{1,2}/\d{1,2}/\d{4})([a-zA-Z])', r'\1 \2', text)
    
    return text

def display_formatted_response(response):
    """Display a response with enhanced formatting."""
    # Clean the response text
    response = clean_response_text(response)
    
    # Split response by sections (if they exist)
    sections = response.split("\n\n")
    
    for section in sections:
        if ":" in section and len(section.split(":")[0]) < 50:
            # This might be a heading
            heading, content = section.split(":", 1)
            st.subheader(heading.strip())
            st.write(content.strip())
            print(content.strip())
        else:
            # Regular paragraph or content
            st.write(section)

def display_goals_card(goal):
    """Display a goal in a well-formatted card."""
    with st.container():
        # Create a card-like container with border
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px;">
            <h3>{goal['Goal Name']}</h3>
            <p><strong>Target:</strong> ${goal['Target Amount']:,.2f} by {goal['Target Date']}</p>
            <p><strong>Current:</strong> ${goal['Current Savings']:,.2f} ({goal['Progress (%)']:.1f}% complete)</p>
            <p><strong>Monthly Contribution:</strong> ${goal['Monthly Contribution']:,.2f}</p>
            <div style="background-color:#f0f2f6; border-radius:3px; height:10px; width:100%;">
                <div style="background-color:#4e8df5; border-radius:3px; height:10px; width:{min(goal['Progress (%)'], 100)}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "selected_user" not in st.session_state:
        # Default to first user
        users_df = load_user_data()
        if not users_df.empty:
            st.session_state.selected_user = users_df['Customer ID'].iloc[0]
        else:
            st.session_state.selected_user = None
    
    if "nudges" not in st.session_state:
        st.session_state.nudges = None
    
    if "goals" not in st.session_state:
        st.session_state.goals = None

def user_selector():
    """Display user selection dropdown and return the selected user ID."""
    users_df = load_user_data()
    
    # Create a list of user options with name and ID
    user_options = [f"{row['Name']} ({row['Customer ID']})" for _, row in users_df.iterrows()]
    
    # Get the index of the currently selected user
    current_user_id = st.session_state.selected_user
    current_user_idx = 0
    for i, user_id in enumerate(users_df['Customer ID']):
        if user_id == current_user_id:
            current_user_idx = i
            break
    
    # Display the dropdown
    selected_option = st.sidebar.selectbox(
        "Select User",
        user_options,
        index=current_user_idx
    )
    
    # Extract the user ID from the selected option
    selected_user_id = selected_option.split("(")[1].split(")")[0]
    
    # Update session state if user changed
    if selected_user_id != st.session_state.selected_user:
        st.session_state.selected_user = selected_user_id
        st.session_state.chat_history = []  # Reset chat history for new user
        st.session_state.nudges = None  # Reset nudges for new user
    
    return selected_user_id

def display_user_info(user_id):
    """Display basic user information."""
    users_df = load_user_data()
    user_info = users_df[users_df['Customer ID'] == user_id].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Checking Balance", f"${user_info['Checking Balance']:,.2f}")
    with col2:
        st.metric("Savings Balance", f"${user_info['Savings Balance']:,.2f}")
    with col3:
        st.metric("Risk Profile", user_info['Risk Profile'])

def home_page():
    """Display the home page content."""
    st.title("Personal Finance Manager")
    
    st.markdown("""
    ## Welcome to Your Personal Finance Manager
    
    This tool helps you make smarter financial decisions through:
    
    - **Personalized Financial Advice**: Chat with our AI financial advisor for tailored guidance
    - **Spending Insights**: Receive nudges about your spending patterns and saving opportunities
    - **Goal Planning**: Set and track progress on your financial goals
    - **Data Visualization**: Visualize your financial data for better understanding
    
    ### Getting Started
    
    1. Select a user from the dropdown menu in the sidebar
    2. Navigate to different sections using the sidebar menu
    3. Explore your financial data and receive personalized recommendations
    
    ### Demo Features
    
    This demonstration showcases how AI can transform personal finance management through:
    
    - Natural language conversations with contextual awareness
    - Specialized financial agents working together to provide holistic advice
    - Data-driven insights that help optimize financial decision-making
    - Goal-based planning with actionable recommendations
    """)
    
    # Select a user
    selected_user = user_selector()
    
    # Display user info
    if selected_user:
        st.subheader(f"Current User: {selected_user}")
        display_user_info(selected_user)

def chatbot_page():
    """Display the chatbot interface with improved formatting and context management."""
    st.title("Financial Advisor Chat")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize or get the advisor agent
    advisor = get_financial_advisor()
    
    # Display chat history with improved formatting
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            # Use the improved formatter for assistant messages
            with st.chat_message("assistant"):
                display_formatted_response(message["content"])
    
    # Chat input
    if prompt := st.chat_input("How can I help with your finances today?"):
        # Display user message
        st.chat_message("user").write(prompt)
        
        # Add to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Analyze the message for potential goal creation/management intent
        is_goal_related = False
        # Expanded pattern list to include modifications
        goal_patterns = [
            r"create (?:a |new |)goal",
            r"set up (?:a |new |)goal",
            r"save for",
            r"emergency fund",
            r"retirement fund",
            r"education fund",
            r"home purchase",
            r"update (?:my |the |)goal",
            r"modify (?:my |the |)goal",
            r"change (?:my |the |)goal",
            r"adjust (?:my |the |)goal", 
            r"increase (?:my |the |)goal",
            r"decrease (?:my |the |)goal",
            r"delete (?:my |the |)goal",
            r"remove (?:my |the |)goal"
        ]
        
        for pattern in goal_patterns:
            if re.search(pattern, prompt.lower()):
                is_goal_related = True
                break
                
        # Get response from advisor, now passing the chat history
        with st.spinner("Thinking..."):
            if is_goal_related:
                # Log additional context for debugging
                st.session_state.debug_goal_intent = True
                print(f"Potential goal operation detected: '{prompt}'")
                
                # Pass the chat history to the advisor for context management
                response = advisor.process_query_with_formatting(
                    prompt, 
                    selected_user,
                    st.session_state.chat_history
                )
                
                # Clear goals cache after goal-related operations
                clear_goals_cache()
            else:
                # Pass the chat history to the advisor for context management
                response = advisor.process_query_with_formatting(
                    prompt, 
                    selected_user,
                    st.session_state.chat_history
                )
        
        # Display assistant response with improved formatting
        with st.chat_message("assistant"):
            display_formatted_response(response)
        
        # Add to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # After handling a likely goal operation, refresh the goals if needed
        if is_goal_related:
            # Give direct feedback about cache clearing for goal operations
            print("Goal operation detected: Cleared goals cache")

def nudges_page():
    """Display financial nudges."""
    st.title("Financial Nudges")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize transaction agent
    transaction_agent = get_transaction_agent()
    
    # Generate nudges button
    if st.button("Generate Nudges") or st.session_state.nudges:
        with st.spinner("Analyzing your transactions..."):
            if not st.session_state.nudges:
                # Only generate new nudges if we don't already have them
                nudges = transaction_agent.generate_nudges(selected_user)
                st.session_state.nudges = nudges
                print(nudges)
            else:
                nudges = st.session_state.nudges
        
        # Display nudges
        st.subheader("Here are your personalized financial nudges:")
        display_formatted_response(nudges)
    
    else:
        st.info("Click 'Generate Nudges' to receive personalized financial insights based on your transaction history.")
        
        # Example of what nudges look like
        st.subheader("Example Nudges:")
        st.markdown("""
        ### Subscription Management
        * **Observation**: You're currently spending $42.97 monthly on streaming services.
        * **Recommendation**: Consider consolidating to fewer services or using family plans.
        * **Potential Savings**: Up to $15/month or $180 annually.
        
        ### Dining Expense Pattern
        * **Observation**: Your dining expenses increased by 25% compared to last month.
        * **Recommendation**: Consider meal planning to reduce restaurant expenses.
        * **Potential Savings**: Reducing dining out by 2 meals/week could save approximately $80/month.
        """)

def goal_planning_page():
    """Display goal planning interface with direct goal modification capability."""
    st.title("Goal Planning")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize financial advisor and goal manager
    goal_manager = GoalDataManager(data_path=DATA_PATH)
    
    # Create tabs for different goal planning activities
    tab1, tab2, tab3 = st.tabs(["View Goals", "Create Goal", "Get Recommendations"])
    
    with tab1:
        st.subheader("Your Financial Goals")
        
        # Force direct read from file
        goals_file = os.path.join(DATA_PATH, "enhanced_goal_data.csv")
        
        try:
            # Read the file directly
            if os.path.exists(goals_file):
                user_goals = pd.read_csv(goals_file)
                # Filter for the selected user - try both cases
                user_goals_lower = user_goals[user_goals['Customer ID'] == selected_user.lower()]
                user_goals_upper = user_goals[user_goals['Customer ID'] == selected_user.upper()]
                user_goals = pd.concat([user_goals_lower, user_goals_upper])
                
                st.sidebar.success(f"Loaded {len(user_goals)} goals from file")
            else:
                st.error(f"Goals file not found: {goals_file}")
                user_goals = pd.DataFrame()
        except Exception as e:
            st.error(f"Error reading goals file: {str(e)}")
            user_goals = pd.DataFrame()
        
        if user_goals.empty:
            st.info("You don't have any financial goals yet. Create one in the 'Create Goal' tab.")
        else:
            # Add a refresh button
            if st.button("🔄 Refresh Goals"):
                st.rerun()
                
            # Display goals with modification button
            for _, goal in user_goals.iterrows():
                goal_id = goal['Goal ID']
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 2])
                    
                    with col1:
                        st.subheader(f"{goal['Goal Name']}")
                        st.write(f"Target: ${goal['Target Amount']:,.2f} by {goal['Target Date']}")
                        st.write(f"Current Savings: ${goal['Current Savings']:,.2f}")
                        st.write(f"Monthly Contribution: ${goal['Monthly Contribution']:,.2f}")
                        st.write(f"Priority: {goal['Priority']}")
                    
                    with col2:
                        # Create a progress bar
                        progress = goal['Progress (%)'] / 100
                        st.metric("Progress", f"{goal['Progress (%)']:.1f}%")
                        st.progress(progress)
                    
                    with col3:
                        # Add actions for this goal
                        st.write("Actions:")
                        
                        # Add modify button - this is the new functionality
                        if st.button(f"✏️ Modify Goal", key=f"modify_{goal_id}"):
                            # Store the goal ID in session state
                            st.session_state.modifying_goal_id = goal_id
                            st.session_state.show_modification_form = True
                        
                        # Add contribution button
                        if st.button(f"💰 Add Contribution", key=f"contrib_{goal_id}"):
                            st.session_state.contribute_goal_id = goal_id
                            st.session_state.show_contribute_form = True
                        
                        # Add delete button
                        if st.button(f"🗑️ Delete Goal", key=f"delete_{goal_id}"):
                            # Directly modify the CSV file
                            try:
                                df = pd.read_csv(goals_file)
                                # Filter out the goal
                                df = df[df['Goal ID'] != goal_id]
                                # Write back to file
                                df.to_csv(goals_file, index=False)
                                st.success(f"Goal '{goal['Goal Name']}' deleted successfully!")
                                # Force page reload
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete goal: {str(e)}")
                    
                    st.divider()
            
            # Display modification form if button was clicked
            if hasattr(st.session_state, 'show_modification_form') and st.session_state.show_modification_form:
                goal_id = st.session_state.modifying_goal_id
                
                # Get current goal data from dataframe
                goal_data = user_goals[user_goals['Goal ID'] == goal_id].iloc[0]
                
                st.subheader(f"Modify Goal: {goal_data['Goal Name']}")
                
                with st.form("goal_modification_form"):
                    # Goal name
                    goal_name = st.text_input("Goal Name", value=goal_data['Goal Name'])
                    
                    # Goal type selection
                    goal_type = st.selectbox(
                        "Goal Type",
                        ["Retirement", "Home Purchase", "Education", "Emergency Fund", 
                         "Travel", "Car Purchase", "Wedding", "Medical Expenses"],
                        index=["Retirement", "Home Purchase", "Education", "Emergency Fund", 
                               "Travel", "Car Purchase", "Wedding", "Medical Expenses"].index(goal_data['Goal Type'])
                    )
                    
                    # Target amount - this is the key field we need to update
                    target_amount = st.number_input(
                        "Target Amount ($)", 
                        min_value=100.0, 
                        value=float(goal_data['Target Amount']),
                        step=1000.0
                    )
                    
                    # Current savings
                    current_savings = st.number_input(
                        "Current Savings ($)", 
                        min_value=0.0, 
                        value=float(goal_data['Current Savings']),
                        step=100.0
                    )
                    
                    # Target date
                    target_date = datetime.strptime(goal_data['Target Date'], "%m/%d/%Y")
                    new_target_date = st.date_input("Target Date", target_date)
                    
                    # Priority
                    priority = st.selectbox(
                        "Priority",
                        ["Very High", "High", "Medium", "Low"],
                        index=["Very High", "High", "Medium", "Low"].index(goal_data['Priority']) 
                            if goal_data['Priority'] in ["Very High", "High", "Medium", "Low"] else 2
                    )
                    
                    # Submit button
                    submit_button = st.form_submit_button("Save Changes")
                    
                    if submit_button:
                        # Direct modification of the CSV file
                        try:
                            df = pd.read_csv(goals_file)
                            
                            # Find the row with the goal ID
                            mask = df['Goal ID'] == goal_id
                            
                            if any(mask):
                                # Update fields
                                df.loc[mask, 'Goal Name'] = goal_name
                                df.loc[mask, 'Goal Type'] = goal_type
                                df.loc[mask, 'Target Amount'] = target_amount
                                df.loc[mask, 'Current Savings'] = current_savings
                                df.loc[mask, 'Target Date'] = new_target_date.strftime("%m/%d/%Y")
                                df.loc[mask, 'Priority'] = priority
                                
                                # Calculate progress
                                progress = (current_savings / target_amount * 100) if target_amount > 0 else 0
                                df.loc[mask, 'Progress (%)'] = progress
                                
                                # Update Last Updated field
                                df.loc[mask, 'Last Updated'] = datetime.now().strftime("%m/%d/%Y")
                                
                                # Calculate goal timeline
                                months_difference = ((new_target_date.year - datetime.now().year) * 12 + 
                                                   (new_target_date.month - datetime.now().month))
                                
                                if months_difference <= 12:
                                    timeline = "Short-term"
                                elif months_difference <= 60:
                                    timeline = "Medium-term"
                                else:
                                    timeline = "Long-term"
                                
                                df.loc[mask, 'Goal Timeline'] = timeline
                                
                                # Save the changes
                                df.to_csv(goals_file, index=False)
                                
                                # Force a file sync
                                with open(goals_file, 'r+') as f:
                                    f.flush()
                                    os.fsync(f.fileno())
                                
                                # Verify the change
                                verification_df = pd.read_csv(goals_file)
                                verify_mask = verification_df['Goal ID'] == goal_id
                                
                                if any(verify_mask) and abs(verification_df.loc[verify_mask, 'Target Amount'].values[0] - target_amount) < 0.01:
                                    st.success(f"Goal updated successfully!")
                                    # Reset form state
                                    st.session_state.show_modification_form = False
                                    # Force page reload
                                    st.rerun()
                                else:
                                    st.error("Failed to verify the update. Please try again.")
                            else:
                                st.error(f"Goal {goal_id} not found in file.")
                        except Exception as e:
                            st.error(f"Error updating goal: {str(e)}")
                
                # Add a cancel button outside the form
                if st.button("Cancel"):
                    st.session_state.show_modification_form = False
                    st.rerun()
            
            # Handle contribution form if shown
            if hasattr(st.session_state, 'show_contribute_form') and st.session_state.show_contribute_form:
                goal_id = st.session_state.contribute_goal_id
                
                with st.form("contribution_form"):
                    st.subheader("Add Contribution")
                    contribution_amount = st.number_input("Contribution Amount ($)", min_value=1.0, value=100.0, step=10.0)
                    submit_contribution = st.form_submit_button("Submit Contribution")
                    
                    if submit_contribution:
                        # Direct modification of the CSV file
                        try:
                            df = pd.read_csv(goals_file)
                            
                            # Find the row with the goal ID
                            mask = df['Goal ID'] == goal_id
                            
                            if any(mask):
                                # Update Current Savings
                                current = df.loc[mask, 'Current Savings'].values[0]
                                new_savings = current + contribution_amount
                                df.loc[mask, 'Current Savings'] = new_savings
                                
                                # Update Progress
                                target = df.loc[mask, 'Target Amount'].values[0]
                                progress = (new_savings / target * 100) if target > 0 else 0
                                df.loc[mask, 'Progress (%)'] = progress
                                
                                # Update Last Updated field
                                df.loc[mask, 'Last Updated'] = datetime.now().strftime("%m/%d/%Y")
                                
                                # Save the changes
                                df.to_csv(goals_file, index=False)
                                
                                # Force a file sync
                                with open(goals_file, 'r+') as f:
                                    f.flush()
                                    os.fsync(f.fileno())
                                
                                st.success(f"Added ${contribution_amount:.2f} to your goal!")
                                st.session_state.show_contribute_form = False
                                # Force page reload
                                st.rerun()
                            else:
                                st.error(f"Goal {goal_id} not found in file.")
                        except Exception as e:
                            st.error(f"Error adding contribution: {str(e)}")
                
                # Add a cancel button outside the form
                if st.button("Cancel Contribution"):
                    st.session_state.show_contribute_form = False
                    st.rerun()

    with tab2:
        st.subheader("Create New Financial Goal")
        
        # Goal creation form
        with st.form("goal_creation_form"):
            # Goal name
            goal_name = st.text_input("Goal Name", "")
            
            # Goal type selection
            goal_type = st.selectbox(
                "Goal Type",
                ["Retirement", "Home Purchase", "Education", "Emergency Fund", 
                 "Travel", "Car Purchase", "Wedding", "Medical Expenses"]
            )
            
            # Target amount
            target_amount = st.number_input("Target Amount ($)", min_value=100.0, value=10000.0, step=1000.0)
            
            # Current savings
            current_savings = st.number_input("Current Savings ($)", min_value=0.0, value=0.0, step=100.0)
            
            # Target date
            today = datetime.now()
            next_year = datetime(today.year + 1, today.month, today.day)
            target_date = st.date_input("Target Date", next_year)
            
            # Priority
            priority = st.selectbox(
                "Priority",
                ["Very High", "High", "Medium", "Low"]
            )
            
            # Monthly contribution (optional)
            include_monthly = st.checkbox("Specify Monthly Contribution", False)
            monthly_contribution = None
            if include_monthly:
                monthly_contribution = st.number_input("Monthly Contribution ($)", min_value=10.0, value=500.0, step=50.0)
            
            # Submit button
            submitted = st.form_submit_button("Create Goal")
            
            if submitted:
                if not goal_name:
                    st.error("Please provide a name for your goal.")
                else:
                    # Format the target date
                    formatted_date = target_date.strftime("%m/%d/%Y")
                    
                    # Use the goal manager to create the goal
                    try:
                        goal_id = goal_manager.create_goal(
                            customer_id=selected_user,
                            goal_name=goal_name,
                            target_amount=target_amount,
                            current_savings=current_savings,
                            target_date=formatted_date,
                            goal_type=goal_type,
                            priority=priority,
                            monthly_contribution=monthly_contribution
                        )
                        
                        # Get the created goal
                        created_goal = goal_manager.get_goal_by_id(goal_id)
                        
                        # Display success message
                        st.success(f"Goal '{goal_name}' created successfully!")
                        
                        # Create a query for the advisor to get explanation
                        query = (
                            f"Explain my new {goal_type} goal with a target amount of ${target_amount:,.2f}, "
                            f"current savings of ${current_savings:,.2f}, target date of {formatted_date}, "
                            f"and {priority} priority."
                        )
                        
                        # Process the query to get natural language explanation
                        with st.spinner("Generating explanation..."):
                            response = get_financial_advisor().process_query(query, selected_user)
                        
                        # Display the response with proper formatting
                        display_formatted_response(response)
                        
                        # Clear the goals cache
                        load_goals_data.clear()
                        
                    except Exception as e:
                        st.error(f"Error creating goal: {str(e)}")
    
    with tab3:
        st.subheader("Goal Recommendations")
        
        if st.button("Get Goal Recommendations"):
            # Create a query for the advisor
            query = "What recommendations do you have for my financial goals?"
            
            # Process the query
            with st.spinner("Analyzing your goals..."):
                response = get_financial_advisor().process_query(query, selected_user)
            
            # Display the response with proper formatting
            display_formatted_response(response)
        else:
            st.info("Click 'Get Goal Recommendations' to receive personalized advice for optimizing your financial goals.")

def asset_recommendation_page():
    """Display asset allocation recommendations and rebalancing advice."""
    st.title("Asset Allocation Recommendations")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Initialize asset allocation agent
    allocation_agent = AssetAllocationAgent(data_path=DATA_PATH)
    advisor_agent = get_financial_advisor()
    
    # Load user's risk profile
    try:
        risk_profiles_file = os.path.join(DATA_PATH, "expanded_risk_profiles.csv")
        if os.path.exists(risk_profiles_file):
            risk_profiles_df = pd.read_csv(risk_profiles_file)
            user_profile = risk_profiles_df[risk_profiles_df['Customer ID'] == selected_user]
            
            if not user_profile.empty:
                risk_category = user_profile.iloc[0]['Risk Category']
                risk_score = user_profile.iloc[0]['Risk Score']
                investment_experience = user_profile.iloc[0]['Investment Experience']
                time_horizon = user_profile.iloc[0]['Time Horizon']
                
                # Display user's risk profile information
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Risk Category", risk_category)
                with col2:
                    st.metric("Risk Score", risk_score)
                with col3:
                    st.metric("Experience", investment_experience)
                with col4:
                    st.metric("Time Horizon", time_horizon)
            else:
                st.warning(f"No risk profile found for user {selected_user}")
                risk_category = "Balanced"  # Default
                time_horizon = "Medium-term"
        else:
            st.warning(f"Risk profiles file not found: {risk_profiles_file}")
            risk_category = "Balanced"  # Default
            time_horizon = "Medium-term"
    except Exception as e:
        st.error(f"Error loading risk profile: {str(e)}")
        risk_category = "Balanced"  # Default
        time_horizon = "Medium-term"
        
    # Get portfolio details
    try:
        allocations_df = load_allocations_data()
        user_allocation = allocations_df[allocations_df['Customer ID'] == selected_user]
        
        if not user_allocation.empty:
            portfolio_value = user_allocation.iloc[0]['Total Portfolio Value']
            last_rebalanced = user_allocation.iloc[0]['Last Rebalanced']
            
            # Display portfolio overview
            st.subheader("Portfolio Overview")
            st.info(f"Total Portfolio Value: ${portfolio_value:,.2f} | Last Rebalanced: {last_rebalanced}")
        else:
            st.warning("Portfolio details not available")
            portfolio_value = 0
    except Exception as e:
        st.error(f"Error loading portfolio details: {str(e)}")
        portfolio_value = 0
    
    # Create tabs for different sections - removed the third tab
    tab1, tab2 = st.tabs(["Current vs. Recommended", "Alternative Risk Profile"])
    
    with tab1:
        # Get current allocation
        current_allocation = allocation_agent.get_current_allocation(selected_user)
        
        if not current_allocation:
            st.warning("No current allocation data available.")
        else:
            # Create columns layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Your Current Allocation")
                
                # Create a pie chart of current allocation
                fig = px.pie(
                    values=list(current_allocation.values()),
                    names=list(current_allocation.keys()),
                    title="Current Asset Allocation",
                    color_discrete_sequence=px.colors.sequential.Blues_r,
                    hole=0.3
                )
                fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3))
                st.plotly_chart(fig, use_container_width=True)
                
                # Display allocation in table format
                allocation_df = pd.DataFrame({
                    'Asset Class': list(current_allocation.keys()),
                    'Current Allocation (%)': list(current_allocation.values())
                })
                st.dataframe(allocation_df.set_index('Asset Class'))
            
            # Get recommended allocation based on risk profile and time horizon
            recommended_allocation = allocation_agent.get_allocation_recommendation(
                risk_profile=risk_category,
                goal_timeline=time_horizon
            )
            
            with col2:
                st.subheader(f"Recommended Allocation for {risk_category} Profile")
                
                # Create a pie chart of recommended allocation
                fig = px.pie(
                    values=list(recommended_allocation.values()),
                    names=list(recommended_allocation.keys()),
                    title=f"Recommended Asset Allocation",
                    color_discrete_sequence=px.colors.sequential.Greens_r,
                    hole=0.3
                )
                fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3))
                st.plotly_chart(fig, use_container_width=True)
                
                # Display allocation in table format
                recommended_df = pd.DataFrame({
                    'Asset Class': list(recommended_allocation.keys()),
                    'Recommended Allocation (%)': list(recommended_allocation.values())
                })
                st.dataframe(recommended_df.set_index('Asset Class'))
            
            # Create a comparison chart
            st.subheader("Current vs. Recommended Allocation")
            
            asset_classes = sorted(set(list(current_allocation.keys()) + list(recommended_allocation.keys())))
            current_values = [current_allocation.get(asset, 0) for asset in asset_classes]
            recommended_values = [recommended_allocation.get(asset, 0) for asset in asset_classes]
            
            comparison_df = pd.DataFrame({
                'Asset Class': asset_classes,
                'Current': current_values,
                'Recommended': recommended_values,
                'Difference': [recommended_values[i] - current_values[i] for i in range(len(asset_classes))]
            })
            
            # Create a bar chart showing comparison
            fig = px.bar(
                comparison_df,
                x='Asset Class',
                y=['Current', 'Recommended'],
                title="Current vs. Recommended Allocation",
                barmode='group',
                color_discrete_map={'Current': '#5A9BD5', 'Recommended': '#70AD47'}
            )
            st.plotly_chart(fig)
            
            # Display detailed comparison table with color highlighting
            st.subheader("Allocation Gap Analysis")
            
            # Format the comparison table
            fmt_comparison = comparison_df.copy()
            fmt_comparison['Action'] = fmt_comparison['Difference'].apply(
                lambda x: "Increase" if x > 0.5 else ("Decrease" if x < -0.5 else "Maintain")
            )
            
            # Add estimated dollar values
            if portfolio_value > 0:
                fmt_comparison['Current Value ($)'] = fmt_comparison['Current'] * portfolio_value / 100
                fmt_comparison['Recommended Value ($)'] = fmt_comparison['Recommended'] * portfolio_value / 100
                fmt_comparison['Value Change ($)'] = fmt_comparison['Difference'] * portfolio_value / 100
            
                # Display the formatted table
                display_cols = ['Asset Class', 'Current', 'Recommended', 'Difference', 
                               'Current Value ($)', 'Recommended Value ($)', 'Value Change ($)', 'Action']
                
                # Create custom styling function
                def style_difference(val):
                    if val > 0.5:
                        return 'background-color: rgba(0, 128, 0, 0.2)'
                    elif val < -0.5:
                        return 'background-color: rgba(255, 0, 0, 0.2)'
                    else:
                        return ''
                
                # Format and display table
                st.dataframe(fmt_comparison[display_cols].style
                           .format({
                               'Current': '{:.1f}%',
                               'Recommended': '{:.1f}%',
                               'Difference': '{:+.1f}%',
                               'Current Value ($)': '${:,.2f}',
                               'Recommended Value ($)': '${:,.2f}',
                               'Value Change ($)': '${:+,.2f}'
                           })
                           .applymap(style_difference, subset=['Difference'])
                          )
            else:
                # Display without dollar values if portfolio value not available
                display_cols = ['Asset Class', 'Current', 'Recommended', 'Difference', 'Action']
                st.dataframe(fmt_comparison[display_cols].style
                           .format({
                               'Current': '{:.1f}%',
                               'Recommended': '{:.1f}%',
                               'Difference': '{:+.1f}%'
                           })
                           .applymap(style_difference, subset=['Difference'])
                          )
            
            # Add recommendation rationale at the end of the tab
            st.subheader("Recommendation Rationale")
            
            with st.spinner("Generating allocation strategy explanation..."):
                try:
                    # Get explanation for the recommended allocation
                    explanation = allocation_agent.explain_allocation_strategy(
                        risk_profile=risk_category,
                        goal_timeline=time_horizon
                    )
                    
                    # Display the explanation with proper formatting
                    display_formatted_response(explanation)
                except Exception as e:
                    st.error(f"Error generating allocation explanation: {str(e)}")
    
    with tab2:
        st.subheader("Explore Alternative Risk Profiles")
        
        # Define all available risk profiles
        risk_profiles = ["Risk Averse", "Conservative", "Balanced", "Growth", "Aggressive"]
        
        # Create form for alternative risk profile selection
        with st.form("alternative_risk_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Let user select an alternative risk profile
                alternative_risk = st.selectbox(
                    "Select Alternative Risk Profile",
                    risk_profiles,
                    index=risk_profiles.index(risk_category) if risk_category in risk_profiles else 2
                )
            
            with col2:
                # Time horizon selection
                alternative_timeline = st.selectbox(
                    "Investment Horizon",
                    ["Short-term", "Medium-term", "Long-term"],
                    index=1  # Default to Medium-term
                )
            
            # Submit button
            view_alternative_button = st.form_submit_button("View Alternative Allocation")
        
        if view_alternative_button or "alternative_allocation" in st.session_state:
            # Get current allocation
            current_allocation = allocation_agent.get_current_allocation(selected_user)
            
            # Get alternative allocation based on selected risk profile
            if view_alternative_button:
                alternative_allocation = allocation_agent.get_allocation_recommendation(
                    risk_profile=alternative_risk,
                    goal_timeline=alternative_timeline
                )
                st.session_state.alternative_allocation = alternative_allocation
                st.session_state.alternative_risk = alternative_risk
                st.session_state.alternative_timeline = alternative_timeline
            else:
                alternative_allocation = st.session_state.alternative_allocation
                alternative_risk = st.session_state.alternative_risk
                alternative_timeline = st.session_state.alternative_timeline
            
            if current_allocation and alternative_allocation:
                # Create columns layout for comparison
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"Current ({risk_category}) Allocation")
                    
                    # Create a pie chart of current allocation
                    fig = px.pie(
                        values=list(current_allocation.values()),
                        names=list(current_allocation.keys()),
                        title=f"Current {risk_category} Allocation",
                        color_discrete_sequence=px.colors.sequential.Blues_r,
                        hole=0.3
                    )
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3))
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader(f"Alternative ({alternative_risk}) Allocation")
                    
                    # Create a pie chart of alternative allocation
                    fig = px.pie(
                        values=list(alternative_allocation.values()),
                        names=list(alternative_allocation.keys()),
                        title=f"Alternative {alternative_risk} Allocation",
                        color_discrete_sequence=px.colors.sequential.Reds_r,
                        hole=0.3
                    )
                    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3))
                    st.plotly_chart(fig, use_container_width=True)
                
                # Create a comparison chart
                st.subheader(f"Comparison: {risk_category} vs. {alternative_risk}")
                
                asset_classes = sorted(set(list(current_allocation.keys()) + list(alternative_allocation.keys())))
                current_values = [current_allocation.get(asset, 0) for asset in asset_classes]
                alternative_values = [alternative_allocation.get(asset, 0) for asset in asset_classes]
                
                comparison_df = pd.DataFrame({
                    'Asset Class': asset_classes,
                    f'Current ({risk_category})': current_values,
                    f'Alternative ({alternative_risk})': alternative_values,
                    'Difference': [alternative_values[i] - current_values[i] for i in range(len(asset_classes))]
                })
                
                # Create a bar chart showing comparison
                fig = px.bar(
                    comparison_df,
                    x='Asset Class',
                    y=[f'Current ({risk_category})', f'Alternative ({alternative_risk})'],
                    title=f"Comparing {risk_category} vs. {alternative_risk} Allocation",
                    barmode='group',
                    color_discrete_map={
                        f'Current ({risk_category})': '#5A9BD5', 
                        f'Alternative ({alternative_risk})': '#D64541'
                    }
                )
                st.plotly_chart(fig)
                
                # Display detailed comparison table
                st.subheader("Allocation Shift Analysis")
                
                # Format the comparison table with colors
                fmt_comparison = comparison_df.copy()
                fmt_comparison['Action'] = fmt_comparison['Difference'].apply(
                    lambda x: "Increase" if x > 0.5 else ("Decrease" if x < -0.5 else "Maintain")
                )
                
                # Add dollar values if portfolio value is available
                if portfolio_value > 0:
                    fmt_comparison['Current Value ($)'] = fmt_comparison[f'Current ({risk_category})'] * portfolio_value / 100
                    fmt_comparison['Alternative Value ($)'] = fmt_comparison[f'Alternative ({alternative_risk})'] * portfolio_value / 100
                    fmt_comparison['Value Change ($)'] = fmt_comparison['Difference'] * portfolio_value / 100
                    
                    # Display the formatted table
                    display_cols = ['Asset Class', f'Current ({risk_category})', f'Alternative ({alternative_risk})', 
                                   'Difference', 'Current Value ($)', 'Alternative Value ($)', 
                                   'Value Change ($)', 'Action']
                    
                    # Create custom styling function
                    def style_difference(val):
                        if val > 0.5:
                            return 'background-color: rgba(0, 128, 0, 0.2)'
                        elif val < -0.5:
                            return 'background-color: rgba(255, 0, 0, 0.2)'
                        else:
                            return ''
                    
                    # Format and display table
                    st.dataframe(fmt_comparison[display_cols].style
                               .format({
                                   f'Current ({risk_category})': '{:.1f}%',
                                   f'Alternative ({alternative_risk})': '{:.1f}%',
                                   'Difference': '{:+.1f}%',
                                   'Current Value ($)': '${:,.2f}',
                                   'Alternative Value ($)': '${:,.2f}',
                                   'Value Change ($)': '${:+,.2f}'
                               })
                               .applymap(style_difference, subset=['Difference'])
                              )
                else:
                    # Display without dollar values
                    display_cols = ['Asset Class', f'Current ({risk_category})', 
                                   f'Alternative ({alternative_risk})', 'Difference', 'Action']
                    st.dataframe(fmt_comparison[display_cols].style
                               .format({
                                   f'Current ({risk_category})': '{:.1f}%',
                                   f'Alternative ({alternative_risk})': '{:.1f}%',
                                   'Difference': '{:+.1f}%'
                               })
                               .applymap(style_difference, subset=['Difference'])
                              )
                
                # Add explanation of the alternative strategy
                st.subheader(f"About {alternative_risk} Risk Profile")
                
                with st.spinner(f"Generating explanation of {alternative_risk} strategy..."):
                    try:
                        # Get explanation for the alternative allocation
                        alternative_explanation = allocation_agent.explain_allocation_strategy(
                            risk_profile=alternative_risk,
                            goal_timeline=alternative_timeline
                        )
                        
                        # Display the explanation with proper formatting
                        display_formatted_response(alternative_explanation)
                        
                        # Add risk comparison notice
                        if risk_profiles.index(alternative_risk) > risk_profiles.index(risk_category):
                            st.warning(f"""
                            **Moving to a {alternative_risk} profile from your current {risk_category} profile would increase your portfolio risk.**
                            
                            This could potentially lead to higher returns but also increased volatility and possibility of loss.
                            Consider speaking with a financial advisor before making this change.
                            """)
                        elif risk_profiles.index(alternative_risk) < risk_profiles.index(risk_category):
                            st.info(f"""
                            **Moving to a {alternative_risk} profile from your current {risk_category} profile would decrease your portfolio risk.**
                            
                            This would likely reduce potential volatility but may also limit your long-term growth potential.
                            Consider whether this aligns with your financial goals and time horizon.
                            """)
                    except Exception as e:
                        st.error(f"Error generating explanation: {str(e)}")
            else:
                st.error("Unable to retrieve allocation data for comparison.")
        else:
            # Display explanation when no alternative is selected yet
            st.info("""
            ### Exploring Different Risk Profiles
            
            Your current risk profile is based on your financial situation, goals, and risk tolerance.
            
            Use this tool to explore how your asset allocation would change if you moved to a different risk profile:
            
            - **Risk Averse**: Maximum capital preservation, minimal volatility
            - **Conservative**: Emphasis on stability with modest growth potential
            - **Balanced**: Equal focus on growth and stability
            - **Growth**: Emphasis on long-term growth with higher volatility
            - **Aggressive**: Maximum growth potential with significant volatility
            
            Select an alternative risk profile above to see how your portfolio allocation would change.
            """)

def data_visualization_page():
    """Display data visualizations."""
    st.title("Financial Data Visualization")
    
    # Select a user
    selected_user = user_selector()
    if not selected_user:
        st.warning("Please select a user to continue.")
        return
    
    # Display user info
    display_user_info(selected_user)
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Spending Analysis", "Budget Status", "Asset Allocation", "Goal Progress"])
    
    # Load data
    transactions_df = load_transactions_data()
    user_transactions = transactions_df[transactions_df['Customer ID'] == selected_user]
    
    budget_df = load_budget_data()
    user_budget = budget_df[budget_df['Customer ID'] == selected_user]
    
    goals_df = load_goals_data()
    user_goals = goals_df[goals_df['Customer ID'] == selected_user.lower()]
    
    allocations_df = load_allocations_data()
    user_allocation = allocations_df[allocations_df['Customer ID'] == selected_user]
    
    with tab1:
        st.subheader("Spending Analysis")
        
        if user_transactions.empty:
            st.info("No transaction data available for visualization.")
        else:
            # Filter to only purchases and payments
            spending = user_transactions[user_transactions['Transaction Type'].isin(['Purchase', 'Payment'])]
            
            # Group by merchant category
            category_spending = spending.groupby('Merchant Category Code')['Transaction Amount'].sum().reset_index()
            category_spending = category_spending.sort_values('Transaction Amount', ascending=False)
            
            # Create bar chart
            fig = px.bar(
                category_spending,
                x='Merchant Category Code',
                y='Transaction Amount',
                title='Spending by Category',
                color='Merchant Category Code'
            )
            st.plotly_chart(fig)
            
            # Transaction history table
            st.subheader("Recent Transactions")
            # Sort by date (most recent first) and select recent transactions
            recent_transactions = user_transactions.sort_values('Transaction Date and Time', ascending=False).head(10)
            # Display only relevant columns
            display_cols = ['Transaction Date and Time', 'Merchant Name', 'Transaction Amount', 'Transaction Type']
            st.dataframe(recent_transactions[display_cols])
    
    with tab2:
        st.subheader("Budget Status")
        
        if user_budget.empty:
            st.info("No budget data available for visualization.")
        else:
            # Create budget utilization chart
            fig = go.Figure()
            
            for _, row in user_budget.iterrows():
                fig.add_trace(go.Bar(
                    x=[row['Category']],
                    y=[row['Monthly Limit']],
                    name='Monthly Limit',
                    marker_color='lightgrey'
                ))
                
                fig.add_trace(go.Bar(
                    x=[row['Category']],
                    y=[row['Spent So Far']],
                    name='Spent So Far',
                    marker_color='blue'
                ))
            
            fig.update_layout(
                title='Budget Utilization',
                barmode='overlay',
                yaxis_title='Amount ($)',
                legend_title='Budget vs. Actual'
            )
            
            st.plotly_chart(fig)
            
            # Budget table with utilization percentage
            st.subheader("Budget Details")
            st.dataframe(user_budget[['Category', 'Monthly Limit', 'Spent So Far', '% Utilized']])
    
    with tab3:
        st.subheader("Asset Allocation Analysis")
        
        # Get the user's risk profile
        try:
            # Load risk profile
            risk_profiles_file = os.path.join(DATA_PATH, "expanded_risk_profiles.csv")
            if os.path.exists(risk_profiles_file):
                risk_profiles_df = pd.read_csv(risk_profiles_file)
                user_profile = risk_profiles_df[risk_profiles_df['Customer ID'] == selected_user]
                
                if not user_profile.empty:
                    risk_category = user_profile.iloc[0]['Risk Category']
                    risk_score = user_profile.iloc[0]['Risk Score']
                    investment_experience = user_profile.iloc[0]['Investment Experience']
                    time_horizon = user_profile.iloc[0]['Time Horizon']
                    
                    # Display user's risk profile information
                    st.write("### Your Risk Profile")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Risk Category", risk_category)
                        st.metric("Investment Experience", investment_experience)
                    with col2:
                        st.metric("Risk Score", risk_score)
                        st.metric("Time Horizon", time_horizon)
                else:
                    st.warning(f"No risk profile found for user {selected_user}")
                    risk_category = "Balanced"  # Default
            else:
                st.warning(f"Risk profiles file not found: {risk_profiles_file}")
                risk_category = "Balanced"  # Default
        except Exception as e:
            st.error(f"Error loading risk profile: {str(e)}")
            risk_category = "Balanced"  # Default
        
        # Add a button to analyze asset allocation
        if st.button("📊 Analyze Asset Allocation"):
            try:
                # Get current asset allocation
                current_allocation = AssetAllocationAgent(data_path=DATA_PATH).get_current_allocation(selected_user)
                
                if current_allocation:
                    # Get total portfolio value and last rebalanced date
                    total_portfolio = "Unknown"
                    last_rebalanced = "Unknown"
                    current_allocations_file = os.path.join(DATA_PATH, "current_asset_allocation.csv")
                    if os.path.exists(current_allocations_file):
                        allocations_df = pd.read_csv(current_allocations_file)
                        user_row = allocations_df[allocations_df['Customer ID'] == selected_user]
                        if not user_row.empty:
                            total_portfolio = user_row.iloc[0]['Total Portfolio Value']
                            last_rebalanced = user_row.iloc[0]['Last Rebalanced']
                    
                    # Display current overall allocation
                    st.write("### Current Overall Asset Allocation")
                    st.info(f"Total Portfolio Value: ${total_portfolio:,.2f} (Last rebalanced: {last_rebalanced})")
                    
                    # Create a pie chart of current allocation
                    fig = px.pie(
                        values=list(current_allocation.values()),
                        names=list(current_allocation.keys()),
                        title="Current Asset Allocation",
                        color_discrete_sequence=px.colors.sequential.Blues_r
                    )
                    st.plotly_chart(fig)
                    
                    # Display allocation in table format
                    allocation_df = pd.DataFrame({
                        'Asset Class': list(current_allocation.keys()),
                        'Current Allocation (%)': list(current_allocation.values())
                    })
                    st.dataframe(allocation_df.set_index('Asset Class'))
                    
                    # Get recommended allocation based on risk profile and general timeline
                    recommended_allocation = AssetAllocationAgent(data_path=DATA_PATH).get_allocation_recommendation(
                        risk_profile=risk_category,
                        goal_timeline=time_horizon
                    )
                    
                    # Display recommended allocation
                    st.write(f"### Recommended Allocation for {risk_category} Risk Profile")
                    
                    # Create a pie chart of recommended allocation
                    fig = px.pie(
                        values=list(recommended_allocation.values()),
                        names=list(recommended_allocation.keys()),
                        title=f"Recommended Allocation for {risk_category} Risk Profile",
                        color_discrete_sequence=px.colors.sequential.Greens_r
                    )
                    st.plotly_chart(fig)
                    
                    # Create comparative bar chart
                    st.write("### Current vs. Recommended Allocation")
                    
                    asset_classes = list(recommended_allocation.keys())
                    current_values = [current_allocation.get(asset, 0) for asset in asset_classes]
                    recommended_values = [recommended_allocation.get(asset, 0) for asset in asset_classes]
                    
                    comparison_df = pd.DataFrame({
                        'Asset Class': asset_classes,
                        'Current': current_values,
                        'Recommended': recommended_values
                    })
                    
                    fig = px.bar(
                        comparison_df,
                        x='Asset Class',
                        y=['Current', 'Recommended'],
                        title="Current vs. Recommended Allocation",
                        barmode='group',
                        color_discrete_map={'Current': '#5A9BD5', 'Recommended': '#70AD47'}
                    )
                    st.plotly_chart(fig)
                    
                    # Calculate discrepancies
                    discrepancies = []
                    for asset in asset_classes:
                        current = current_allocation.get(asset, 0)
                        recommended = recommended_allocation.get(asset, 0)
                        diff = recommended - current
                        if abs(diff) >= 1.0:  # Only show meaningful differences
                            discrepancies.append({
                                'Asset Class': asset,
                                'Current (%)': current,
                                'Recommended (%)': recommended,
                                'Difference (%)': diff,
                                'Action': 'Increase' if diff > 0 else 'Decrease'
                            })
                    
                    # Display discrepancies if any
                    if discrepancies:
                        st.write("### Allocation Adjustments Needed")
                        discrepancies_df = pd.DataFrame(discrepancies)
                        
                        # Format the dataframe for display
                        st.dataframe(discrepancies_df.style.format({
                            'Current (%)': '{:.1f}',
                            'Recommended (%)': '{:.1f}',
                            'Difference (%)': '{:.1f}'
                        }).apply(lambda x: ['background-color: #ffcccc' if x['Action'] == 'Decrease' else 'background-color: #ccffcc' for i in x], axis=1))
                        
                        # Create waterfall chart to show adjustments
                        fig = go.Figure(go.Waterfall(
                            name="Allocation Changes",
                            orientation="v",
                            measure=["relative"] * len(discrepancies),
                            x=[f"{d['Asset Class']} ({d['Action']})" for d in discrepancies],
                            y=[d['Difference (%)'] for d in discrepancies],
                            connector={"line": {"color": "rgb(63, 63, 63)"}},
                            decreasing={"marker": {"color": "#EF553B"}},
                            increasing={"marker": {"color": "#00CC96"}},
                            text=[f"{d['Difference (%)']:.1f}%" for d in discrepancies],
                            textposition="outside"
                        ))
                        
                        fig.update_layout(
                            title="Portfolio Rebalancing Adjustments",
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig)
                    else:
                        st.success("Your current allocation is already closely aligned with recommendations!")
                    
                    # Get allocation strategy explanation
                    with st.expander("Asset Allocation Strategy Explanation"):
                        strategy_explanation = AssetAllocationAgent(data_path=DATA_PATH).explain_allocation_strategy(
                            risk_profile=risk_category,
                            goal_timeline=time_horizon
                        )
                        st.markdown(strategy_explanation)
                    
                    # If user has goals, provide goal-specific context
                    if not user_goals.empty:
                        st.write("### Goal-Specific Considerations")
                        
                        # Create a table with goals and their timelines
                        goal_table = []
                        for _, goal in user_goals.iterrows():
                            goal_table.append({
                                'Goal': goal['Goal Name'],
                                'Type': goal['Goal Type'],
                                'Target Amount': goal['Target Amount'],
                                'Timeline': goal['Goal Timeline'],
                                'Recommendation': f"Consider a {goal['Goal Timeline'].lower()} strategy for this goal"
                            })
                        
                        goal_df = pd.DataFrame(goal_table)
                        
                        # Format for display
                        st.dataframe(goal_df.style.format({
                            'Target Amount': '${:,.2f}'
                        }))
                        
                        # Add general advice about goal-specific allocation
                        st.info("""
                        **Goal-Specific Allocation Tip:**
                        
                        While your overall portfolio follows your risk profile, individual goals might benefit 
                        from specific allocation strategies based on their timeframes and purposes.
                        
                        For short-term goals (< 1 year), consider more conservative allocations.
                        For mid-term goals (1-5 years), a balanced approach may be appropriate.
                        For long-term goals (> 5 years), you might consider more growth-oriented allocations.
                        """)
                else:
                    st.warning(f"No current asset allocation data found for user {selected_user}")
            except Exception as e:
                st.error(f"Error analyzing asset allocation: {str(e)}")
    
    with tab4:
        st.subheader("Goal Progress")
        
        if user_goals.empty:
            st.info("No goals data available for visualization.")
        else:
            # Create progress chart
            fig = px.bar(
                user_goals,
                x='Goal Name',
                y=['Current Savings', 'Target Amount'],
                title='Goal Progress',
                barmode='overlay',
                color_discrete_map={'Current Savings': 'blue', 'Target Amount': 'lightgrey'}
            )
            st.plotly_chart(fig)
            
            # Create timeline chart
            goals_with_dates = user_goals.copy()
            goals_with_dates['Target Date'] = pd.to_datetime(goals_with_dates['Target Date'])
            goals_with_dates['Start Date'] = pd.to_datetime(goals_with_dates['Start Date'])
            goals_with_dates = goals_with_dates.sort_values('Target Date')
            
            # Calculate days from now to target
            today = pd.Timestamp.now()
            goals_with_dates['Days Remaining'] = (goals_with_dates['Target Date'] - today).dt.days
            
            fig = px.timeline(
                goals_with_dates,
                x_start='Start Date',
                x_end='Target Date',
                y='Goal Name',
                color='Progress (%)',
                color_continuous_scale='blues',
                title='Goal Timeline',
                labels={'Progress (%)': 'Progress (%)'}
            )
            
            # Update layout for better display
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig)

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Personal Finance Manager",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page",
        ["Home", "Chat with Advisor", "Financial Nudges", "Goal Planning", "Asset Recommendations", "Data Visualization"]
    )
    
    # Show selected page
    if page == "Home":
        home_page()
    elif page == "Chat with Advisor":
        chatbot_page()
    elif page == "Financial Nudges":
        nudges_page()
    elif page == "Goal Planning":
        goal_planning_page()
    elif page == "Asset Recommendations":
        asset_recommendation_page()
    elif page == "Data Visualization":
        data_visualization_page()

if __name__ == "__main__":
    main()